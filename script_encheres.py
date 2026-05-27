import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime
import unicodedata
import json
from pathlib import Path
import time
import re

# ─────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────

GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"
FICHIER_MEMOIRE  = Path("memoire_encheres.json")

# ─────────────────────────────────────────────────────
# DOMAINES CIBLES — NE PAS MODIFIER
# ─────────────────────────────────────────────────────

DOMAINES = [
    "Reynaud", "Chateau des Tours", "Emmanuel Reynaud",
    "La Closerie", "Savart", "Domaine des Tours", "Chateau Rayas", "Rayas",
    "Leclere Minard Clement", "Guiberteau", "Guffens", "Gonon",
    "Gangloff", "Foillard", "Jean Foillard", "Dureil Janthial", "Dureuil Janthial",
    "Dancer", "Dagueneau", "Morey Caroline", "Caroline Morey",
    "Chartogne Taillet", "Carillon Jacques", "Jacques Carillon",
    "Bretaudeau Jerome", "Jerome Bretaudeau",
    "Boillot Henri", "Henri Boillot", "Barthod", "Arnoux Lachaux",
    "Nowack", "Allemand", "Anglore", "Anne Gros",
    "Auvenay", "Bizot", "Cecile Tremblay", "Chaillon Alexandre",
    "Chave", "Clape", "Clos Rougeard", "Coche Dury",
    "Comtes Lafon", "Domaine Leroy", "Leroy",
    "Domaine Rousseau", "Rousseau", "Dujac",
    "Elise Bougy", "Gaspard Brochet", "Gavenat",
    "Granges des Peres", "Grange des Peres",
    "Hubert Lamy", "Jules Brochet", "La Rogerie",
    "Labet", "Leflaive", "Liger Belair",
    "Lurquin Aurelien", "Meo Camuzet",
    "Mugneret Gibourg", "Mugnier", "Paul Pillot",
    "Pierre Peters", "Pierre Yves Colin Morey", "PYCM",
    "Prieure Roch", "Ramonet", "Raveneau",
    "Richard Leroy", "Romanee Conti", "DRC",
    "Roses de Jeanne", "Roumier", "Sauzet",
    "Selosse", "Tino Kuban", "Ulysse Colin",
    "Vincent Dauvissat", "Dauvissat",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ─────────────────────────────────────────────────────
# MÉMOIRE PERSISTANTE
# ─────────────────────────────────────────────────────

def charger_memoire():
    if FICHIER_MEMOIRE.exists():
        with open(FICHIER_MEMOIRE, "r") as f:
            return json.load(f)
    return {"detectes": []}

def sauvegarder_memoire(memoire):
    with open(FICHIER_MEMOIRE, "w") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)

def est_nouveau(source, lot_id, domaine, memoire):
    return f"{source}|{lot_id}|{domaine}" not in memoire.get("detectes", [])

def marquer_vu(source, lot_id, domaine, memoire):
    cle = f"{source}|{lot_id}|{domaine}"
    if cle not in memoire["detectes"]:
        memoire["detectes"].append(cle)
    memoire["detectes"] = memoire["detectes"][-20000:]

# ─────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

def domaines_dans_texte(texte):
    texte_norm = normaliser(texte)
    return [d for d in DOMAINES if normaliser(d) in texte_norm]

def get_soup(url, timeout=15):
    """Retourne (soup, url_finale) ou (None, None) en cas d'échec."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if resp.status_code >= 400:
            print(f"   ⚠️ HTTP {resp.status_code} pour {url}")
            return None, None
        texte = resp.text
        if len(texte.strip()) < 300:
            print(f"   ⚠️ Page vide (JS requis ?) : {url}")
            return None, None
        return BeautifulSoup(texte, "html.parser"), resp.url
    except Exception as e:
        print(f"   ⚠️ Erreur réseau : {e}")
        return None, None

# ─────────────────────────────────────────────────────
# SCRAPER IDEALWINE
# ─────────────────────────────────────────────────────

def scraper_idealwine():
    resultats = []
    print("🔍 Scan iDealwine enchères...")
    for domaine in DOMAINES:
        try:
            url = f"https://www.idealwine.com/fr/acheter-du-vin?styledvintage={requests.utils.quote(domaine)}&type=auction"
            soup, _ = get_soup(url)
            if not soup:
                time.sleep(0.5)
                continue
            lots = soup.find_all(class_=re.compile(r'lot|product|wine-item', re.I))
            for lot in lots[:10]:
                texte = lot.get_text(separator=" ")
                if not domaines_dans_texte(texte):
                    continue
                titre = lot.find(class_=re.compile(r'title|name', re.I))
                prix  = lot.find(class_=re.compile(r'price|bid|enchere', re.I))
                lien  = lot.find("a", href=True)
                href  = lien["href"] if lien else ""
                if href and not href.startswith("http"):
                    href = "https://www.idealwine.com" + href
                resultats.append({
                    "source":   "iDealwine",
                    "lot_id":   href or texte[:50],
                    "titre":    titre.get_text(strip=True) if titre else texte[:80],
                    "prix":     prix.get_text(strip=True) if prix else "N/A",
                    "date_fin": "",
                    "lien":     href or url,
                    "domaines": domaines_dans_texte(texte),
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ iDealwine erreur pour {domaine}: {e}")
    print(f"   → {len(resultats)} lots trouvés")
    return resultats

# ─────────────────────────────────────────────────────
# SCRAPER CATAWIKI
# ─────────────────────────────────────────────────────

def scraper_catawiki():
    resultats = []
    print("🔍 Scan Catawiki...")
    for domaine in DOMAINES:
        try:
            url = f"https://www.catawiki.com/fr/s?q={requests.utils.quote(domaine)}&c=wine-spirits-lots"
            soup, _ = get_soup(url)
            if not soup:
                time.sleep(0.5)
                continue
            lots = soup.find_all("article") or soup.find_all(class_=re.compile(r'lot|auction-item|card', re.I))
            for lot in lots[:10]:
                texte = lot.get_text(separator=" ")
                if not domaines_dans_texte(texte):
                    continue
                titre_el = lot.find(class_=re.compile(r'title|name|lot-title', re.I)) or lot.find("h2") or lot.find("h3")
                prix_el  = lot.find(class_=re.compile(r'price|bid|estimate', re.I))
                date_el  = lot.find(class_=re.compile(r'date|end|closing', re.I))
                lien_el  = lot.find("a", href=True)
                href = lien_el["href"] if lien_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.catawiki.com" + href
                resultats.append({
                    "source":   "Catawiki",
                    "lot_id":   href or texte[:50],
                    "titre":    titre_el.get_text(strip=True) if titre_el else texte[:80],
                    "prix":     prix_el.get_text(strip=True) if prix_el else "Voir site",
                    "date_fin": date_el.get_text(strip=True) if date_el else "",
                    "lien":     href or url,
                    "domaines": domaines_dans_texte(texte),
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ Catawiki erreur pour {domaine}: {e}")
    print(f"   → {len(resultats)} lots trouvés")
    return resultats

# ─────────────────────────────────────────────────────
# SCRAPER INTERENCHÈRES
# ─────────────────────────────────────────────────────

def scraper_interencheres():
    resultats = []
    print("🔍 Scan Interenchères...")
    for domaine in DOMAINES:
        try:
            url = f"https://www.interencheres.com/art-decoration/vin-et-spiritueux/lots?query={requests.utils.quote(domaine)}"
            soup, _ = get_soup(url)
            if not soup:
                time.sleep(0.5)
                continue
            lots = soup.find_all(class_=re.compile(r'lot|product|item', re.I))
            for lot in lots[:10]:
                texte = lot.get_text(separator=" ")
                if not domaines_dans_texte(texte):
                    continue
                titre_el = lot.find(class_=re.compile(r'title|name|description', re.I)) or lot.find("h2") or lot.find("h3")
                prix_el  = lot.find(class_=re.compile(r'price|estimate|estimation', re.I))
                date_el  = lot.find(class_=re.compile(r'date|vente', re.I))
                lien_el  = lot.find("a", href=True)
                href = lien_el["href"] if lien_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.interencheres.com" + href
                resultats.append({
                    "source":   "Interenchères",
                    "lot_id":   href or texte[:50],
                    "titre":    titre_el.get_text(strip=True) if titre_el else texte[:80],
                    "prix":     prix_el.get_text(strip=True) if prix_el else "Voir site",
                    "date_fin": date_el.get_text(strip=True) if date_el else "",
                    "lien":     href or url,
                    "domaines": domaines_dans_texte(texte),
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ Interenchères erreur pour {domaine}: {e}")
    print(f"   → {len(resultats)} lots trouvés")
    return resultats

# ─────────────────────────────────────────────────────
# SCRAPER EBAY FRANCE
# ─────────────────────────────────────────────────────

def scraper_ebay():
    resultats = []
    print("🔍 Scan eBay France...")
    for domaine in DOMAINES:
        try:
            url = f"https://www.ebay.fr/sch/i.html?_nkw={requests.utils.quote(domaine)}+vin&_sacat=0&LH_Auction=1"
            soup, _ = get_soup(url)
            if not soup:
                time.sleep(0.5)
                continue
            lots = soup.find_all("li", class_=re.compile(r's-item', re.I))
            for lot in lots[:10]:
                texte = lot.get_text(separator=" ")
                if not domaines_dans_texte(texte):
                    continue
                titre_el = lot.find(class_=re.compile(r's-item__title|title', re.I))
                prix_el  = lot.find(class_=re.compile(r's-item__price|price', re.I))
                date_el  = lot.find(class_=re.compile(r's-item__time|time-left', re.I))
                lien_el  = lot.find("a", href=True)
                href = lien_el["href"] if lien_el else ""
                resultats.append({
                    "source":   "eBay France",
                    "lot_id":   href or texte[:50],
                    "titre":    titre_el.get_text(strip=True) if titre_el else texte[:80],
                    "prix":     prix_el.get_text(strip=True) if prix_el else "Voir site",
                    "date_fin": date_el.get_text(strip=True) if date_el else "",
                    "lien":     href or url,
                    "domaines": domaines_dans_texte(texte),
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ eBay erreur pour {domaine}: {e}")
    print(f"   → {len(resultats)} lots trouvés")
    return resultats

# ─────────────────────────────────────────────────────
# SCRAPER DROUOT
# Approche : scraper la page catégorie vins + recherche
# par domaine sur gazette-drouot.com (plus accessible)
# ─────────────────────────────────────────────────────

def scraper_drouot():
    resultats = []
    print("🔍 Scan Drouot...")
    for domaine in DOMAINES:
        try:
            # gazette-drouot.com est plus scrapable que drouot.com
            url = f"https://www.gazette-drouot.com/ventes-aux-encheres?q={requests.utils.quote(domaine)}&c=vins-et-alcools"
            soup, url_finale = get_soup(url)
            if not soup:
                time.sleep(0.5)
                continue
            # Cherche les blocs de lots/ventes
            lots = (
                soup.find_all(class_=re.compile(r'lot|sale|card|auction|vente', re.I)) or
                soup.find_all("article") or
                soup.find_all("li", class_=re.compile(r'item|result', re.I))
            )
            for lot in lots[:10]:
                texte = lot.get_text(separator=" ")
                domaines_trouves = domaines_dans_texte(texte)
                if not domaines_trouves:
                    continue
                titre_el = lot.find(class_=re.compile(r'title|name|heading', re.I)) or lot.find("h2") or lot.find("h3") or lot.find("h4")
                prix_el  = lot.find(class_=re.compile(r'price|estimate|estimation', re.I))
                date_el  = lot.find(class_=re.compile(r'date|when|time', re.I))
                lien_el  = lot.find("a", href=True)
                href = lien_el["href"] if lien_el else ""
                if href and not href.startswith("http"):
                    href = "https://www.gazette-drouot.com" + href
                resultats.append({
                    "source":   "Drouot",
                    "lot_id":   href or texte[:50],
                    "titre":    titre_el.get_text(strip=True) if titre_el else texte[:100],
                    "prix":     prix_el.get_text(strip=True) if prix_el else "Voir site",
                    "date_fin": date_el.get_text(strip=True) if date_el else "",
                    "lien":     href or url,
                    "domaines": domaines_trouves,
                })
            time.sleep(0.5)
        except Exception as e:
            print(f"   ⚠️ Drouot erreur pour {domaine}: {e}")
    print(f"   → {len(resultats)} lots trouvés")
    return resultats

# ─────────────────────────────────────────────────────
# SCRAPER BAGHERA/WINES
# Approche : scraper la page des ventes en cours
# et chercher les domaines dans les titres de lots
# ─────────────────────────────────────────────────────

def scraper_baghera():
    resultats = []
    print("🔍 Scan Baghera/Wines...")

    # Page principale des ventes en cours
    urls_a_scanner = [
        "https://www.bagherawines.com/fr/ventes/",
        "https://www.bagherawines.com/fr/lots/",
    ]

    for url_base in urls_a_scanner:
        soup, _ = get_soup(url_base)
        if not soup:
            continue

        # Cherche les liens vers les lots/ventes individuelles
        liens_ventes = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.bagherawines.com" + href
            if "/lot" in href or "/vente" in href or "/wine-o-clock" in href or "/kipling" in href:
                if href not in liens_ventes:
                    liens_ventes.append(href)

        # Scanner chaque page de vente trouvée (max 5)
        for lien in liens_ventes[:5]:
            soup_vente, _ = get_soup(lien)
            if not soup_vente:
                time.sleep(0.5)
                continue
            texte_page = soup_vente.get_text(separator=" ")
            domaines_trouves = domaines_dans_texte(texte_page)
            if not domaines_trouves:
                time.sleep(0.3)
                continue
            # Cherche les blocs de lots dans la page
            lots = (
                soup_vente.find_all(class_=re.compile(r'lot|wine|item|product', re.I)) or
                soup_vente.find_all("article") or
                [soup_vente]  # fallback : page entière
            )
            for lot in lots[:20]:
                texte = lot.get_text(separator=" ")
                doms = domaines_dans_texte(texte)
                if not doms:
                    continue
                titre_el = lot.find(class_=re.compile(r'title|name', re.I)) or lot.find("h2") or lot.find("h3")
                prix_el  = lot.find(class_=re.compile(r'price|estimate|estimation', re.I))
                lot_lien = lot.find("a", href=True)
                href = lot_lien["href"] if lot_lien else lien
                if href and not href.startswith("http"):
                    href = "https://www.bagherawines.com" + href
                resultats.append({
                    "source":   "Baghera/Wines",
                    "lot_id":   href or texte[:50],
                    "titre":    titre_el.get_text(strip=True) if titre_el else texte[:100],
                    "prix":     prix_el.get_text(strip=True) if prix_el else "Voir site",
                    "date_fin": "",
                    "lien":     href or lien,
                    "domaines": doms,
                })
            time.sleep(0.5)

    print(f"   → {len(resultats)} lots trouvés")
    return resultats

# ─────────────────────────────────────────────────────
# SCRAPER AGUTTES
# Approche : récupérer les ventes vins en cours
# puis scanner chaque catalogue
# ─────────────────────────────────────────────────────

def scraper_aguttes():
    resultats = []
    print("🔍 Scan Aguttes...")

    # Page des ventes vins en cours
    url_ventes = "https://www.aguttes.com/fr/ventes/vins-spiritueux"
    soup, _ = get_soup(url_ventes)

    if not soup:
        # Fallback : page générale des ventes
        soup, _ = get_soup("https://www.aguttes.com/fr/ventes")

    liens_catalogues = []
    if soup:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if not href.startswith("http"):
                href = "https://www.aguttes.com" + href
            # Les catalogues Aguttes ont des URLs type /catalogue/XXXXX ou /vente/XXXXX
            if re.search(r'/(catalogue|vente)/\d+', href):
                if href not in liens_catalogues:
                    liens_catalogues.append(href)

    # Si pas de catalogue trouvé, essayer l'URL directe vins connue
    if not liens_catalogues:
        liens_catalogues = [
            "https://www.aguttes.com/fr/ventes/vins-spiritueux",
        ]

    for url_catalogue in liens_catalogues[:3]:
        soup_cat, _ = get_soup(url_catalogue)
        if not soup_cat:
            time.sleep(0.5)
            continue

        texte_page = soup_cat.get_text(separator=" ")
        if not domaines_dans_texte(texte_page):
            time.sleep(0.3)
            continue

        # Cherche les blocs de lots
        lots = (
            soup_cat.find_all(class_=re.compile(r'lot|product|item|card', re.I)) or
            soup_cat.find_all("article") or
            soup_cat.find_all("li", class_=re.compile(r'lot|item', re.I))
        )

        for lot in lots[:30]:
            texte = lot.get_text(separator=" ")
            doms = domaines_dans_texte(texte)
            if not doms:
                continue
            titre_el = lot.find(class_=re.compile(r'title|name|designation', re.I)) or lot.find("h2") or lot.find("h3") or lot.find("h4")
            prix_el  = lot.find(class_=re.compile(r'price|estimate|estimation', re.I))
            date_el  = lot.find(class_=re.compile(r'date|vente', re.I))
            lien_el  = lot.find("a", href=True)
            href = lien_el["href"] if lien_el else ""
            if href and not href.startswith("http"):
                href = "https://www.aguttes.com" + href
            resultats.append({
                "source":   "Aguttes",
                "lot_id":   href or texte[:50],
                "titre":    titre_el.get_text(strip=True) if titre_el else texte[:100],
                "prix":     prix_el.get_text(strip=True) if prix_el else "Voir site",
                "date_fin": date_el.get_text(strip=True) if date_el else "",
                "lien":     href or url_catalogue,
                "domaines": doms,
            })
        time.sleep(0.5)

    print(f"   → {len(resultats)} lots trouvés")
    return resultats

# ─────────────────────────────────────────────────────
# FILTRAGE NOUVEAUTÉS
# ─────────────────────────────────────────────────────

def filtrer_nouveautes(tous_resultats, memoire):
    nouveautes = []
    for lot in tous_resultats:
        for domaine in lot["domaines"]:
            if est_nouveau(lot["source"], lot["lot_id"], domaine, memoire):
                nouveautes.append({**lot, "domaine_detecte": domaine})
                marquer_vu(lot["source"], lot["lot_id"], domaine, memoire)
    return nouveautes

# ─────────────────────────────────────────────────────
# ENVOI EMAIL
# ─────────────────────────────────────────────────────

COULEURS_SOURCE = {
    "iDealwine":      "#1a3a5c",
    "Catawiki":       "#e85f04",
    "Interenchères":  "#2d6a4f",
    "eBay France":    "#e53935",
    "Drouot":         "#8B0000",
    "Baghera/Wines":  "#4a0e6e",
    "Aguttes":        "#1a5276",
}

def envoyer_email(nouveautes, stats):
    heure = datetime.now().strftime("%d/%m/%Y %H:%M")
    sources_actives = "iDealwine · Catawiki · Interenchères · eBay · Drouot · Baghera · Aguttes"

    if not nouveautes:
        sujet = f"🔨 Enchères — RAS — {heure}"
        corps_html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;">
        <div style="background:#1a1a2e;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
          <h2 style="margin:0;">🔨 Scan Enchères — {heure}</h2>
          <p style="margin:6px 0 0;font-size:13px;">{sources_actives}</p>
        </div>
        <div style="padding:16px 20px;background:#f9f9f9;border-left:4px solid #1a1a2e;margin:16px 0;">
          <p style="margin:0;color:#555;">✅ Aucun nouveau lot détecté sur vos domaines cibles.</p>
        </div>
        </body></html>
        """
    else:
        sujet = f"🔨 {len(nouveautes)} nouveau(x) lot(s) aux enchères — {heure}"

        par_source = {}
        for lot in nouveautes:
            src = lot["source"]
            if src not in par_source:
                par_source[src] = []
            par_source[src].append(lot)

        corps_html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;">
        <div style="background:#1a1a2e;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
          <h2 style="margin:0;">🔨 Enchères — {len(nouveautes)} nouveau(x) lot(s)</h2>
          <p style="margin:6px 0 0;font-size:13px;">{heure} · {sources_actives}</p>
        </div>
        """

        for source, lots in par_source.items():
            couleur = COULEURS_SOURCE.get(source, "#333")
            corps_html += f"""
        <div style="margin:16px 0;">
          <h3 style="color:{couleur};border-left:4px solid {couleur};padding-left:10px;margin-bottom:8px;">
            📍 {source} — {len(lots)} lot(s)
          </h3>
          <table border="1" cellpadding="10" cellspacing="0"
                 style="border-collapse:collapse;width:100%;font-size:13px;">
            <tr style="background:{couleur};color:white;">
              <th>Domaine</th><th>Lot</th><th>Prix / Estimation</th><th>Fin</th><th>Lien</th>
            </tr>"""
            for lot in lots:
                corps_html += f"""
            <tr>
              <td><b>🍷 {lot['domaine_detecte']}</b></td>
              <td style="max-width:250px;">{lot['titre'][:120]}</td>
              <td><b>{lot['prix']}</b></td>
              <td style="font-size:12px;">{lot['date_fin']}</td>
              <td><a href="{lot['lien']}" style="color:{couleur};">→ Voir lot</a></td>
            </tr>"""
            corps_html += "</table></div>"

        corps_html += f"""
        <p style="color:#aaa;font-size:11px;padding:0 20px 16px;">
          Scan du {heure} · memoire_encheres.json mis à jour
        </p></body></html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"]    = GMAIL_EXPEDITEUR
    msg["To"]      = DESTINATAIRE
    msg.attach(MIMEText(corps_html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_EXPEDITEUR, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_EXPEDITEUR, DESTINATAIRE, msg.as_string())
        print(f"✅ Email enchères envoyé : {sujet[:60]}")
    except Exception as e:
        print(f"❌ Erreur envoi : {e}")

# ─────────────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"🔨 SCAN ENCHÈRES — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  {len(DOMAINES)} domaines · 7 sources")
    print(f"{'='*55}\n")

    memoire = charger_memoire()

    tous_resultats = []
    tous_resultats += scraper_idealwine()
    tous_resultats += scraper_catawiki()
    tous_resultats += scraper_interencheres()
    tous_resultats += scraper_ebay()
    tous_resultats += scraper_drouot()
    tous_resultats += scraper_baghera()
    tous_resultats += scraper_aguttes()

    nouveautes = filtrer_nouveautes(tous_resultats, memoire)
    sauvegarder_memoire(memoire)

    print(f"\n{'='*55}")
    print(f"RÉSULTAT : {len(nouveautes)} nouveau(x) lot(s) sur {len(tous_resultats)} scannés")
    print(f"{'='*55}\n")

    envoyer_email(nouveautes, {})

if __name__ == "__main__":
    main()
