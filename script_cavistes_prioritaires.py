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

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"

# Mémoire des détections précédentes
FICHIER_MEMOIRE  = Path("cavistes_deja_detectes.json")

# ─────────────────────────────────────────────
# 64 DOMAINES CIBLES
# ─────────────────────────────────────────────

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

# ─────────────────────────────────────────────
# 18 CAVISTES PRIORITAIRES
# ─────────────────────────────────────────────

CAVISTES_PRIORITAIRES = [
    ("Clos des Millésimes",  "https://www.closdesmillesimes.com/"),
    ("Cave Spirituelle",     "https://www.cave-spirituelle.com/"),
    ("Stanislas Collin",     "https://stanislascollin.fr/"),
    ("Wine Shop Fronsac",    "https://wineshopfronsac.com/"),
    ("Wine Shop Biarritz",   "https://www.wineshop-biarritz.fr/"),
    ("La Grande Cave",       "https://www.lagrandecave.fr/"),
    ("Cave Briau",           "https://www.briau.com/"),
    ("Cave Pur Jus",         "https://www.cavepurjus.com/fr/"),
    ("La Cave d'Ulysse",     "https://www.caveulysse.com/"),
    ("La Cave de Lill",      "https://www.lacavedelill.fr/"),
    ("Versus Wine",          "https://www.versus.wine/"),
    ("Le Gros Caviste",      "https://legroscaviste.com/"),
    ("Vinum Pro",            "https://vinum.pro/catalogue-en-ligne/"),
    ("Nouvelle Cave",        "https://nouvellecave.com/"),
    ("Au Millésime",         "https://www.aumillesime.com/boutique-en-ligne"),
    ("La Champagnerie",      "https://www.la-champagnerie.com/"),
    ("75 Centilitres",       "https://www.75-centilitres.fr/"),
    ("Le 520",               "https://le520.fr/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────
# MEMOIRE DES DETECTIONS
# ─────────────────────────────────────────────

def charger_memoire():
    """Charge les détections précédentes {caviste: [domaines]}"""
    if FICHIER_MEMOIRE.exists():
        with open(FICHIER_MEMOIRE, "r") as f:
            return json.load(f)
    return {}

def sauvegarder_memoire(memoire):
    with open(FICHIER_MEMOIRE, "w") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)

def filtrer_nouveautes(nom_site, domaines_trouves, memoire):
    """Retourne uniquement les domaines nouvellement détectés."""
    deja_vus = set(memoire.get(nom_site, []))
    nouveaux = [d for d in domaines_trouves if d not in deja_vus]
    # Met à jour la mémoire avec tous les domaines actuels
    memoire[nom_site] = list(set(list(deja_vus) + domaines_trouves))
    return nouveaux

# ─────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────

def normaliser(texte):
    return unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode().lower()

# ─────────────────────────────────────────────
# ENVOI EMAIL
# ─────────────────────────────────────────────

def envoyer_alerte(nouveautes):
    if not nouveautes:
        return

    total = sum(len(d["domaines"]) for d in nouveautes)
    sujet = f"🏪 Alerte Caviste — {total} nouveau(x) domaine(s) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    corps_html = """
    <html><body>
    <h2 style="color:#2C5F2E;">🏪 Nouveaux domaines détectés chez vos cavistes</h2>
    <p>Ces domaines viennent d'apparaître chez vos cavistes prioritaires :</p>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;font-family:Arial;width:100%;">
      <tr style="background:#2C5F2E;color:white;">
        <th>Caviste</th>
        <th>Nouveaux domaines détectés</th>
        <th>Lien</th>
      </tr>
    """
    for d in nouveautes:
        corps_html += f"""
      <tr>
        <td><b>{d['caviste']}</b></td>
        <td>{'<br>'.join(f"🍷 {dom}" for dom in d['domaines'])}</td>
        <td><a href="{d['url']}">{d['url'][:50]}...</a></td>
      </tr>"""

    corps_html += f"""
    </table>
    <p style="color:gray;font-size:12px;">Scan effectué le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p>
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
        print(f"✅ Email envoyé : {total} nouveau(x) domaine(s)")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

# ─────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────

def scraper_caviste(nom_site, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        texte_norm = normaliser(soup.get_text(separator=" "))

        domaines_trouves = []
        for domaine in DOMAINES:
            if normaliser(domaine) in texte_norm:
                domaines_trouves.append(domaine)

        return domaines_trouves

    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout : {nom_site}")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"⚠️  HTTP {e.response.status_code} : {nom_site}")
        return []
    except Exception as e:
        print(f"⚠️  Erreur {nom_site} : {e}")
        return []

# ─────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"🏪 SCAN CAVISTES PRIORITAIRES — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}")
    print(f"  Cavistes surveillés : {len(CAVISTES_PRIORITAIRES)}")
    print(f"  Domaines cibles     : {len(DOMAINES)}")
    print(f"{'='*55}\n")

    memoire = charger_memoire()
    toutes_nouveautes = []

    for nom_site, url in CAVISTES_PRIORITAIRES:
        print(f"🔍 Scan : {nom_site}...")
        domaines_trouves = scraper_caviste(nom_site, url)

        if domaines_trouves:
            nouveaux = filtrer_nouveautes(nom_site, domaines_trouves, memoire)
            if nouveaux:
                print(f"   🆕 {len(nouveaux)} nouveau(x) : {', '.join(nouveaux)}")
                toutes_nouveautes.append({
                    "caviste": nom_site,
                    "domaines": nouveaux,
                    "url": url,
                })
            else:
                print(f"   — {len(domaines_trouves)} domaine(s) déjà connu(s), pas de nouveauté")
        else:
            print(f"   — Aucun domaine cible trouvé")

    sauvegarder_memoire(memoire)

    print(f"\n{'='*55}")
    nouveautes_total = sum(len(d["domaines"]) for d in toutes_nouveautes)
    print(f"RÉSULTAT : {nouveautes_total} nouveau(x) domaine(s) détecté(s)")
    print(f"{'='*55}\n")

    if toutes_nouveautes:
        envoyer_alerte(toutes_nouveautes)
    else:
        print("Aucune nouveauté — pas d'alerte envoyée.")

if __name__ == "__main__":
    main()
