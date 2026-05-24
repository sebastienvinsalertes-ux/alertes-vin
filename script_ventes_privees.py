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
from urllib.parse import urljoin

# ─────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────

GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"
FICHIER_MEMOIRE  = Path("memoire_ventes_privees.json")

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

MOTS_VENTE_PRIVEE = [
    "vente privee", "vente exclusive", "offre exclusive",
    "offre confidentielle", "allocation", "quantites limitees",
    "stock limite", "disponibilite limitee", "offre speciale",
    "acces prive", "membres", "arrivage", "pre-vente",
]

SITES_VENTES_PRIVEES = [
    ("Vente à la Propriété",   "https://www.ventealapropriete.com/fr/ventes-privees"),
    ("20h33",                  "https://www.20h33.com/"),
    ("Cuvée Privée",           "https://cuvee-privee.com/"),
    ("Le Clos Privé",          "https://www.leclos-prive.com/shop/"),
    ("Les Grappes",            "https://www.lesgrappes.com/"),
    ("Lavinia",                "https://www.lavinia.com/fr-fr/ufr/ventes-privees-club-france"),
    ("Petites Caves",          "https://www.petitescaves.com/collections/vente-privee-champagnes-2024"),
    ("Pépites en Champagne",   "https://pepites-en-champagne.fr/"),
    ("Premium Grands Crus",    "https://www.premiumgrandscrus.com/fr/pages/4-ventes-privees"),
    ("Chateaunet",             "https://www.chateaunet.com/nos-ventes-privees"),
    ("Chais d'Oeuvre",         "https://www.chaisdoeuvre.fr/pages/ventes-privees"),
    ("Twil",                   "https://www.twil.fr/ventes-privees"),
    ("Cash Vin",               "https://www.cashvin.com/ventes-privees/"),
    ("Les Caves",              "https://www.les-caves.fr/fr/1148-vente-privee-bourgogne"),
    ("Le Bourguignon",         "https://www.le-bourguignon.fr/fr/89-vente-privee-vins-de-bourgogne"),
    ("Le Carré des Vins",      "https://www.lecarredesvins.com/"),
    ("Oenovinia",              "https://www.oenovinia.com/"),
    ("La Cave du Château",     "https://www.lacaveduchateau.com/ventes-privees.html"),
    ("Les Bons Plans du Vin",  "https://www.lesbonsplansduvin.com/"),
    ("Mes Bourgognes Beaune",  "https://mesbourgognesbeaune.com/"),
    ("Parcellaire",            "https://www.parcellaire.com/"),
    ("Demain les Vins",        "https://www.demainlesvins.com/"),
    ("La Lettre des Vignerons","https://www.lalettredesvignerons.com/"),
    ("La Grande Cave",         "https://www.lagrandecave.fr/rayon/ventes-privees"),
    ("iDealwine",              "https://www.idealwine.com/fr/acheter-du-vin"),
    ("1Jour1Vin",              "https://www.1jour1vin.com/fr"),
    ("Wine Guru",              "https://www.wineguru.fr/830-allocations"),
    ("Vins Grands Crus",       "https://www.vinsgrandscrus.fr/"),
    ("Cave des Grands Vins",   "https://www.cave-des-grands-vins.com/"),
    ("Terres de Rouges",       "https://terresderouges.com/"),
    ("La Route des Blancs",    "https://www.laroutedesblancs.com/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
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

def est_nouveau(url, domaine, memoire):
    return f"{url}|{domaine}" not in memoire.get("detectes", [])

def marquer_vu(url, domaine, memoire):
    cle = f"{url}|{domaine}"
    if cle not in memoire["detectes"]:
        memoire["detectes"].append(cle)
    memoire["detectes"] = memoire["detectes"][-10000:]

# ─────────────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────────────

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

def scraper_site(nom_site, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        texte_norm = normaliser(soup.get_text(separator=" "))

        mots_trouves = [m for m in MOTS_VENTE_PRIVEE if m in texte_norm]
        if not mots_trouves:
            return []

        detections = []
        for domaine in DOMAINES:
            domaine_norm = normaliser(domaine)
            if domaine_norm not in texte_norm:
                continue

            # Vérifie proximité (300 caractères)
            pos = 0
            trouve_proche = False
            lien_direct = url
            while True:
                idx = texte_norm.find(domaine_norm, pos)
                if idx == -1:
                    break
                fenetre = texte_norm[max(0, idx - 300):idx + 300]
                if any(mot in fenetre for mot in mots_trouves):
                    trouve_proche = True
                    break
                pos = idx + 1

            if not trouve_proche:
                continue

            # Cherche un lien direct vers la page produit
            for a in soup.find_all("a", href=True):
                if normaliser(domaine) in normaliser(a.get_text()):
                    href = a["href"]
                    if not href.startswith("http"):
                        href = urljoin(url, href)
                    lien_direct = href
                    break

            detections.append({
                "domaine":      domaine,
                "site":         nom_site,
                "url":          url,
                "lien_direct":  lien_direct,
                "mots_trouves": mots_trouves[:3],
            })

        return detections

    except requests.exceptions.Timeout:
        print(f"   ⏱️  Timeout : {nom_site}")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"   ⚠️  HTTP {e.response.status_code} : {nom_site}")
        return []
    except Exception as e:
        print(f"   ⚠️  Erreur {nom_site} : {e}")
        return []

# ─────────────────────────────────────────────────────
# ENVOI EMAIL
# ─────────────────────────────────────────────────────

def envoyer_email(nouveautes, total_scannes):
    heure = datetime.now().strftime("%d/%m/%Y %H:%M")
    nb = len(nouveautes)

    if nb > 0:
        sujet = f"🍾 {nb} vente(s) privée(s) détectée(s) — {heure}"
    else:
        sujet = f"🍾 Ventes privées — RAS — {heure}"

    corps_html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;">
    <div style="background:#8B4513;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
      <h2 style="margin:0;">🍾 Scan Ventes Privées — {heure}</h2>
      <p style="margin:6px 0 0;font-size:13px;">{total_scannes} sites scannés</p>
    </div>
    """

    if nouveautes:
        corps_html += """
    <div style="padding:16px 20px;">
      <h3 style="color:#8B4513;border-bottom:2px solid #8B4513;padding-bottom:6px;">
        🆕 Domaines en contexte de vente privée
      </h3>
      <table border="1" cellpadding="10" cellspacing="0"
             style="border-collapse:collapse;width:100%;font-size:14px;">
        <tr style="background:#8B4513;color:white;">
          <th>Domaine</th><th>Site</th><th>Mots clés</th><th>Lien direct</th>
        </tr>
        """
        for d in nouveautes:
            corps_html += f"""
        <tr>
          <td><b>🍷 {d['domaine']}</b></td>
          <td>{d['site']}</td>
          <td><i>{', '.join(d['mots_trouves'])}</i></td>
          <td><a href="{d['lien_direct']}" style="color:#8B4513;">👉 Voir</a></td>
        </tr>"""
        corps_html += "</table></div>"
    else:
        corps_html += """
    <div style="padding:16px 20px;background:#f9f9f9;border-left:4px solid #8B4513;margin:16px 0;">
      <p style="margin:0;color:#555;">✅ Aucune vente privée avec vos domaines cibles détectée.</p>
    </div>
    """

    corps_html += f"""
    <p style="color:#aaa;font-size:11px;padding:0 20px 16px;">
      Scan effectué le {heure} · memoire_ventes_privees.json mis à jour
    </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"]    = GMAIL_EXPEDITEUR
    msg["To"]      = DESTINATAIRE
    msg.attach(MIMEText(corps_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_EXPEDITEUR, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_EXPEDITEUR, DESTINATAIRE, msg.as_string())
        print(f"✅ Email envoyé ({nb} détection(s))")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

# ─────────────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"🍾 SCAN VENTES PRIVÉES — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  {len(SITES_VENTES_PRIVEES)} sites · {len(DOMAINES)} domaines cibles")
    print(f"{'='*55}\n")

    memoire = charger_memoire()
    nouveautes = []

    for nom_site, url in SITES_VENTES_PRIVEES:
        print(f"🔍 {nom_site}...")
        detections = scraper_site(nom_site, url)

        for d in detections:
            if est_nouveau(d["url"], d["domaine"], memoire):
                print(f"   🆕 {d['domaine']}")
                nouveautes.append(d)
                marquer_vu(d["url"], d["domaine"], memoire)
            else:
                print(f"   — {d['domaine']} déjà connu")

        if not detections:
            print(f"   — Aucun domaine en vente privée")

        time.sleep(0.3)

    sauvegarder_memoire(memoire)

    print(f"\n{'='*55}")
    print(f"RÉSULTAT : {len(nouveautes)} nouvelle(s) détection(s)")
    print(f"{'='*55}\n")

    envoyer_email(nouveautes, len(SITES_VENTES_PRIVEES))

if __name__ == "__main__":
    main()
