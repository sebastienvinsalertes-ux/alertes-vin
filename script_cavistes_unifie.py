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

# ─────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────

GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"
FICHIER_MEMOIRE  = Path("memoire_cavistes.json")

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

# ─────────────────────────────────────────────────────
# LISTE CAVISTES
# Mis à jour le 28/05/2026 — suppression de 20 sites
# problématiques (12 crash, 4 Cloudflare, 2 JS, 1 timeout, 1 erreur)
# Sites supprimés :
#   💀 CRASH    : Caves Amiel, Le Temps des Vendanges, Badie,
#                 Les Bons Plans du Vin, La Grande Cave, Philovino,
#                 L'Intendant, La Cavisterie, Vins et Terroir,
#                 Au Chai Vous, La Champagnerie, La Cave d'Ulysse
#   🚫 CLOUDFLARE: Cave Spirituelle, La CUV, Sourire des Saveurs,
#                  75 Centilitres
#   ⚠️ JS VIDE  : La Cave de Max, Le 520
#   ⏱️ TIMEOUT  : Domaine Le Cellier
#   ❌ ERREUR   : Cousin & Compagnie
# Pour ajouter un caviste : ajouter une ligne ici
# ─────────────────────────────────────────────────────

CAVISTES = [
    # ── ⭐ VIP Confirmés ──
    ("Cellier des Docks",         "https://cellierdesdocks.com"),
    ("Clos des Millésimes",       "https://closdesmillesimes.com"),
    ("BGC Vins Rares",            "https://bgcvinsrares.com"),
    ("V Marchand de Vins",        "https://vpoint.fr"),
    ("Mademoiselle Wine",         "https://mademoiselle-wine.com"),
    ("Le Sang des Vignes",        "https://la-cave-bidart.fr"),
    ("Cave de la Rousselle",      "https://cavedelarousselle.fr"),
    ("Le Chai Billière",          "https://lechai.fr"),
    ("La Cour des Vins",          "https://lacourdesvins.fr"),
    ("Domaine de Lastours",       "https://domaine-de-lastours.fr"),
    ("Stanislas Collin",          "https://stanislascollin.fr"),
    ("Comptoir des Millésimes",   "https://comptoirdesmillesimes.com"),
    ("La Route des Blancs",       "https://laroutedesblancs.com"),

    # ── 🔍 Site + Domaines Détectés ──
    ("Vins et Millésimes",        "https://vinsetmillesimes.com"),
    ("Le Carré des Vins",         "https://lecarredesvins.com"),
    ("Oenovinia",                 "https://oenovinia.com"),
    ("Vins Grands Crus",          "https://vinsgrandscrus.fr"),
    ("Mes Bourgognes Beaune",     "https://mesbourgognesbeaune.com"),
    ("Premium Grands Crus",       "https://premiumgrandscrus.com"),
    ("Caves Carrière",            "https://caves-carriere.fr"),
    ("La Cave du Marché",         "https://lacavedumarche.fr"),
    ("Millesimes.com",            "https://millesimes.com"),
    ("Petites Caves",             "https://petitescaves.com"),
    ("iDealwine",                 "https://idealwine.com"),
    ("Les Zinzins du Vin",        "https://leszinzinsduvin.eu"),
    ("Cave de Chaz",              "https://cavedechaz.com"),
    ("Prestige Cellar",           "https://prestige-cellar.fr"),
    ("Sphere Wine",               "https://sphere-wine.com"),
    ("Vintageandco",              "https://vintageandco.com"),
    ("Parcellaire",               "https://parcellaire.com"),
    ("Demain les Vins",           "https://demainlesvins.com"),
    ("Terres de Rouges",          "https://terresderouges.com"),
    ("Chais d'Oeuvre",            "https://chaisdoeuvre.fr"),
    ("Vente à la Propriété",      "https://ventealapropriete.com"),
    ("Les Caves",                 "https://les-caves.fr"),
    ("Vougeot.vin",               "https://vougeot.vin"),
    ("Le Gros Caviste",           "https://legroscaviste.com"),
    ("Winenot",                   "https://winenot.fr"),
    ("Cave des Grands Vins",      "https://cave-des-grands-vins.com"),
    ("La Vinothèque de Bordeaux", "https://vinotheque-bordeaux.com"),
    ("Wine Shop Biarritz",        "https://wineshop-biarritz.fr"),
    ("Wine Shop Fronsac",         "https://wineshopfronsac.com"),
    ("Ardoneo",                   "https://vin-bio-ardoneo.com"),
    ("Vintage Select",            "https://vintageselect31.fr"),
    ("Millesima",                 "https://millesima.fr"),
    ("Cave Pur Jus",              "https://cavepurjus.com"),
    ("La Cave de Lill",           "https://lacavedelill.fr"),

    # ── 🌐 Site Web À Scanner ──
    ("La Crypte du Vin",          "https://lacrypteduvin.fr"),
    ("Cave Pourpre",              "https://cavepourpre.com"),
    ("La Cavisterie",             "https://lacavisterie.fr"),
    ("Le Pied à Terre",           "https://lepiedaterre-cave.com"),
    ("La Maison Gabin",           "https://1.lamaisongabin.com"),
    ("Cave Briau",                "https://briau.com"),
    ("Amour du Vin",              "https://amourduvin.com"),
    ("La Cave des Darons",        "https://lacavedesdarons.com"),
    ("Cave Saint-Jean d'Août",    "https://cave-montdemarsan.fr"),
    ("Au Chai Vous",              "https://auchaivous.com"),
    ("Vinothèque de Dax",         "https://vinotheque-dax.fr"),
    ("Plaisirs du Vin Dax",       "https://dax.plaisirsduvin.com"),
    ("La Bouteille 40",           "https://labouteille40.com"),
    ("La Cave 40 Narrosse",       "https://lacave40.fr"),
    ("Caves Bacqué",              "https://cavesbacque.com"),
    ("Cave du Palais",            "https://cavedupalais.shop"),
    ("Cave Nobel",                "https://cave-nobel.com"),
    ("Les 4 Pépins",              "https://les4pepins.com"),
    ("Des Bouchons",              "https://desbouchons.fr"),
    ("Boutique des Vins",         "https://boutiquedesvins.com"),
    ("Vins d'Une Oreille",        "https://vinsduneoreille.com"),
    ("Chai Vincent",              "https://chai-vincent.fr"),
    ("Le Comptoir des Vins",      "https://lecomptoirdesvins-toulouse.com"),
    ("In Vino Fredo",             "https://invinofredo.fr"),
    ("Lacrima Vini",              "https://lacrimavini.fr"),
    ("Les 3 Caves Rive Gauche",   "https://les3caves-rivegauche.fr"),
    ("Wine Notes",                "https://wine-notes.fr"),
    ("Cave de César",             "https://lacavedecesar.fr"),
    ("Cavissima",                 "https://cavissima.com"),
    ("1Jour1Vin",                 "https://1jour1vin.com"),
    ("Wineguru",                  "https://wineguru.fr"),
    ("Au Millésime",              "https://aumillesime.com"),
    ("Versus Wine",               "https://versus.wine"),
    ("Vinum Pro",                 "https://vinum.pro"),
    ("Nouvelle Cave",             "https://nouvellecave.com"),
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
    memoire["detectes"] = memoire["detectes"][-20000:]

# ─────────────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────────────

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

def scraper_site(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        texte = soup.get_text(separator=" ")
        # Vérifie que la page n'est pas vide (JS requis)
        if len(texte.strip()) < 500:
            return [], {}
        texte_norm = normaliser(texte)
        domaines_trouves = [d for d in DOMAINES if normaliser(d) in texte_norm]
        # Tente de trouver un lien direct vers une page produit pour chaque domaine
        liens = {}
        for a in soup.find_all("a", href=True):
            texte_lien = normaliser(a.get_text())
            href = a["href"]
            if not href.startswith("http"):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            for d in domaines_trouves:
                if normaliser(d) in texte_lien and d not in liens:
                    liens[d] = href
        return domaines_trouves, liens
    except Exception:
        return None, {}

# ─────────────────────────────────────────────────────
# ENVOI EMAIL
# ─────────────────────────────────────────────────────

BATCH_SIZE = 30

def construire_corps(batch, num_email, total_emails, heure, total_scannes, total_ok, total_echecs, nb_total_nouveautes):
    corps_html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;">
    <div style="background:#722F37;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
      <h2 style="margin:0;">🍷 Scan Cavistes — {heure}</h2>
      <p style="margin:6px 0 0;font-size:13px;">
        {total_scannes} sites scannés · {total_ok} accessibles · {total_echecs} inaccessibles
        · {nb_total_nouveautes} nouveauté(s) au total
      </p>
      {"" if total_emails == 1 else f'<p style="margin:4px 0 0;font-size:12px;opacity:0.85;">Email {num_email}/{total_emails}</p>'}
    </div>
    <div style="padding:16px 20px;">
      <h3 style="color:#722F37;border-bottom:2px solid #722F37;padding-bottom:6px;">
        🆕 Nouveaux domaines détectés
      </h3>
      <table border="1" cellpadding="10" cellspacing="0"
             style="border-collapse:collapse;width:100%;font-size:14px;">
        <tr style="background:#722F37;color:white;">
          <th>Caviste</th>
          <th>Domaine(s) détecté(s)</th>
          <th>Lien direct</th>
        </tr>
    """
    for d in batch:
        domaines_html = ""
        for dom in d["domaines"]:
            lien_direct = d["liens"].get(dom, "")
            if lien_direct:
                domaines_html += f'🍷 <a href="{lien_direct}" style="color:#722F37;">{dom}</a><br>'
            else:
                domaines_html += f"🍷 {dom}<br>"
        corps_html += f"""
        <tr>
          <td><b>{d['nom']}</b></td>
          <td>{domaines_html}</td>
          <td><a href="{d['url']}" style="color:#722F37;">{d['url']}</a></td>
        </tr>"""
    corps_html += f"""
      </table>
    </div>
    <p style="color:#aaa;font-size:11px;padding:0 20px 16px;">
      Scan du {heure} · memoire_cavistes.json mis à jour
    </p>
    </body></html>
    """
    return corps_html

def envoyer_email(nouveautes, total_scannes, total_ok, total_echecs):
    heure = datetime.now().strftime("%d/%m/%Y %H:%M")
    nb_total = sum(len(d["domaines"]) for d in nouveautes)

    if not nouveautes:
        sujet = f"🔍 Scan cavistes — RAS — {heure}"
        corps_html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;">
        <div style="background:#722F37;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
          <h2 style="margin:0;">🍷 Scan Cavistes — {heure}</h2>
          <p style="margin:6px 0 0;font-size:13px;">
            {total_scannes} sites scannés · {total_ok} accessibles · {total_echecs} inaccessibles
          </p>
        </div>
        <div style="padding:16px 20px;background:#f9f9f9;border-left:4px solid #722F37;margin:16px 0;">
          <p style="margin:0;color:#555;">✅ Aucune nouveauté — tous les domaines déjà en mémoire.</p>
        </div>
        </body></html>
        """
        _envoyer(sujet, corps_html)
        return

    batches = [nouveautes[i:i+BATCH_SIZE] for i in range(0, len(nouveautes), BATCH_SIZE)]
    total_emails = len(batches)

    for num, batch in enumerate(batches, 1):
        nb_batch = sum(len(d["domaines"]) for d in batch)
        if total_emails == 1:
            sujet = f"🍷 {nb_total} nouveau(x) domaine(s) — {heure}"
        else:
            sujet = f"🍷 {nb_batch} nouveauté(s) [{num}/{total_emails}] — {heure}"

        corps_html = construire_corps(
            batch, num, total_emails, heure,
            total_scannes, total_ok, total_echecs, nb_total
        )
        _envoyer(sujet, corps_html)
        time.sleep(2)

def _envoyer(sujet, corps_html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"]    = GMAIL_EXPEDITEUR
    msg["To"]      = DESTINATAIRE
    msg.attach(MIMEText(corps_html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_EXPEDITEUR, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_EXPEDITEUR, DESTINATAIRE, msg.as_string())
        print(f"✅ Email envoyé : {sujet[:60]}")
    except Exception as e:
        print(f"❌ Erreur envoi : {e}")

# ─────────────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"🍷 SCAN CAVISTES — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"  {len(CAVISTES)} cavistes · {len(DOMAINES)} domaines cibles")
    print(f"{'='*55}\n")

    memoire = charger_memoire()
    nouveautes = []
    total_ok = 0
    total_echecs = 0

    for i, (nom, url) in enumerate(CAVISTES):
        print(f"🔍 [{i+1}/{len(CAVISTES)}] {nom}...")
        domaines_trouves, liens = scraper_site(url)

        if domaines_trouves is None:
            total_echecs += 1
            print(f"   ⚠️  Inaccessible")
            time.sleep(0.3)
            continue

        total_ok += 1

        if not domaines_trouves:
            print(f"   — Aucun domaine cible")
            time.sleep(0.3)
            continue

        nouveaux = [d for d in domaines_trouves if est_nouveau(url, d, memoire)]

        if nouveaux:
            print(f"   🆕 {', '.join(nouveaux[:5])}")
            nouveautes.append({
                "nom":      nom,
                "url":      url,
                "domaines": nouveaux,
                "liens":    liens,
            })
            for d in nouveaux:
                marquer_vu(url, d, memoire)
        else:
            print(f"   — {len(domaines_trouves)} domaine(s) déjà connu(s)")

        time.sleep(0.3)

    sauvegarder_memoire(memoire)

    total = sum(len(d["domaines"]) for d in nouveautes)
    print(f"\n{'='*55}")
    print(f"RÉSULTAT : {total} nouveau(x) · {total_ok} OK · {total_echecs} échecs")
    print(f"{'='*55}\n")

    envoyer_email(nouveautes, len(CAVISTES), total_ok, total_echecs)

if __name__ == "__main__":
    main()
