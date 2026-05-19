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

GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"

FICHIER_MEMOIRE  = Path("cavistes_france_v2_detectes.json")
FICHIER_URLS     = Path("cavistes_france_urls.json")

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

SITES_EXCLUS = [
    "ventealapropriete", "20h33", "cuvee-privee", "leclos-prive",
    "lesgrappes", "lavinia", "petitescaves", "pepites-en-champagne",
    "premiumgrandscrus", "chateaunet", "chaisdoeuvre", "twil",
    "cashvin", "les-caves", "le-bourguignon", "lecarredesvins",
    "oenovinia", "lacaveduchateau", "lesbonsplansduvin",
    "mesbourgognesbeaune", "parcellaire", "demainlesvins",
    "lalettredesvignerons", "lagrandecave", "idealwine",
    "1jour1vin", "wineguru", "vinsgrandscrus", "cave-des-grands-vins",
    "terresderouges", "laroutedesblancs",
    "closdesmillesimes", "cave-spirituelle", "stanislascollin",
    "wineshopfronsac", "wineshop-biarritz", "briau", "cavepurjus",
    "caveulysse", "lacavedelill", "versus.wine", "legroscaviste",
    "vinum.pro", "nouvellecave", "aumillesime", "la-champagnerie",
    "75-centilitres", "le520",
]

REGIONS = [
    "alsace", "aquitaine", "auvergne", "basse-normandie",
    "bourgogne", "bretagne", "centre", "champagne-ardenne",
    "franche-comte", "haute-normandie", "ile-de-france",
    "languedoc-roussillon", "limousin", "lorraine", "midi-pyrenees",
    "nord-pas-de-calais", "pays-de-la-loire", "picardie",
    "poitou-charentes", "provence-alpes-cote-d-azur(paca)", "rhone-alpes",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

def charger_memoire():
    if FICHIER_MEMOIRE.exists():
        with open(FICHIER_MEMOIRE, "r") as f:
            return json.load(f)
    return {"detectes": []}

def sauvegarder_memoire(memoire):
    with open(FICHIER_MEMOIRE, "w") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)

def charger_urls():
    if FICHIER_URLS.exists():
        with open(FICHIER_URLS, "r") as f:
            return json.load(f)
    return []

def sauvegarder_urls(urls):
    with open(FICHIER_URLS, "w") as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)

def est_exclu(url):
    url_norm = normaliser(url)
    return any(exclu in url_norm for exclu in SITES_EXCLUS)

def est_nouveau(url, domaine, memoire):
    cle = f"{url}|{domaine}"
    return cle not in memoire.get("detectes", [])

def marquer_vu(url, domaine, memoire):
    if "detectes" not in memoire:
        memoire["detectes"] = []
    cle = f"{url}|{domaine}"
    if cle not in memoire["detectes"]:
        memoire["detectes"].append(cle)
    memoire["detectes"] = memoire["detectes"][-5000:]

def extraire_urls_region(region):
    urls = []
    url_annuaire = f"http://www.annuaire-des-cavistes.fr/caviste/{region}"
    try:
        resp = requests.get(url_annuaire, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            texte = a.get_text(strip=True).lower()
            if (href.startswith("http") and
                "annuaire-des-cavistes" not in href and
                "google" not in href and
                len(href) > 10):
                if any(mot in texte for mot in ["site", "www", ".fr", ".com"]) or \
                   any(mot in href for mot in [".fr", ".com", ".net"]):
                    if not est_exclu(href):
                        urls.append(href.rstrip("/"))
    except Exception as e:
        print(f"⚠️  Erreur annuaire {region} : {e}")
    return list(set(urls))

def collecter_tous_cavistes():
    print("📚 Collecte des URLs depuis l'annuaire des cavistes...")
    toutes_urls = []
    for region in REGIONS:
        print(f"  → Région : {region}...")
        urls = extraire_urls_region(region)
        toutes_urls.extend(urls)
        time.sleep(1)
    toutes_urls = list(set(toutes_urls))
    print(f"  ✅ {len(toutes_urls)} URLs collectées")
    return toutes_urls

def scraper_caviste(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        texte_norm = normaliser(soup.get_text(separator=" "))
        return [d for d in DOMAINES if normaliser(d) in texte_norm]
    except:
        return []

def envoyer_alerte(nouveautes):
    if not nouveautes:
        return
    total = sum(len(d["domaines"]) for d in nouveautes)
    sujet = f"🌍 Alerte Cavistes France — {total} nouveau(x) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    corps_html = """
    <html><body>
    <h2 style="color:#8B4513;">🌍 Nouveaux domaines chez des cavistes français</h2>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;font-family:Arial;width:100%;">
      <tr style="background:#8B4513;color:white;">
        <th>Domaine(s)</th><th>Site caviste</th>
      </tr>
    """
    for d in nouveautes:
        corps_html += f"""
      <tr>
        <td>{'<br>'.join(f"🍷 {dom}" for dom in d['domaines'])}</td>
        <td><a href="{d['url']}">{d['url'][:60]}</a></td>
      </tr>"""
    corps_html += f"</table><p style='color:gray;font-size:12px;'>Scan effectué le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p></body></html>"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"]    = GMAIL_EXPEDITEUR
    msg["To"]      = DESTINATAIRE
    msg.attach(MIMEText(corps_html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_EXPEDITEUR, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_EXPEDITEUR, DESTINATAIRE, msg.as_string())
        print(f"✅ Email envoyé : {total} nouveau(x)")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

def main():
    print(f"\n{'='*55}")
    print(f"🌍 SCAN CAVISTES FRANCE — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}\n")

    memoire = charger_memoire()
    urls_cavistes = charger_urls()
    if not urls_cavistes:
        urls_cavistes = collecter_tous_cavistes()
        sauvegarder_urls(urls_cavistes)

    print(f"  Sites à scanner : {len(urls_cavistes)}")
    print(f"  Domaines cibles : {len(DOMAINES)}\n")

    toutes_nouveautes = []
    for i, url in enumerate(urls_cavistes):
        if i % 20 == 0:
            print(f"  Progression : {i}/{len(urls_cavistes)}...")
        domaines_trouves = scraper_caviste(url)
        if not domaines_trouves:
            continue
        nouveaux = [d for d in domaines_trouves if est_nouveau(url, d, memoire)]
        if nouveaux:
            print(f"  🆕 {', '.join(nouveaux)} → {url[:50]}")
            toutes_nouveautes.append({"domaines": nouveaux, "url": url})
            for d in nouveaux:
                marquer_vu(url, d, memoire)
        time.sleep(0.3)

    sauvegarder_memoire(memoire)

    print(f"\n{'='*55}")
    print(f"RÉSULTAT : {len(toutes_nouveautes)} site(s) avec nouveaux domaines")
    print(f"{'='*55}\n")

    if toutes_nouveautes:
        envoyer_alerte(toutes_nouveautes)
    else:
        print("Aucune nouveauté — pas d'alerte envoyée.")

if __name__ == "__main__":
    main()
