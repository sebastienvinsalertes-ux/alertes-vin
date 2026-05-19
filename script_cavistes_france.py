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

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"

FICHIER_MEMOIRE  = Path("cavistes_france_v3_detectes.json")

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
# 110 CAVISTES FRANÇAIS SPÉCIALISÉS GRANDS CRUS
# Sélectionnés car ils stockent tes domaines cibles
# ─────────────────────────────────────────────

CAVISTES_FRANCE = [
    # Spécialistes grands crus en ligne
    ("Vins et Millésimes",          "https://www.vinsetmillesimes.com/fr/"),
    ("Comptoir des Millésimes",     "https://www.comptoirdesmillesimes.com/"),
    ("La Cave du Marché",           "https://www.lacavedumarche.fr/"),
    ("Millesimes.com",              "https://millesimes.com/"),
    ("Vougeot.vin (1 Bis)",         "https://vougeot.vin/fr/"),
    ("Prestige Cellar",             "https://www.prestige-cellar.fr/fr/"),
    ("Sphere Wine",                 "https://sphere-wine.com/"),
    ("Mister Wine",                 "https://www.mister-wine.fr/"),
    ("Les Grandes Caves Paris",     "https://www.lesgrandescaves.fr/"),
    ("Les Zinzins du Vin",          "https://leszinzinsduvin.eu/"),
    ("Caves Carrière",              "https://www.caves-carriere.fr/"),
    ("Les Caves du Forum Reims",    "https://www.lescavesduforum.com/"),
    ("Le Caviste des Papilles",     "http://www.lespapillesparis.fr/"),
    ("Sommellerie de France",       "https://www.sommelleriedefrance.com/"),
    ("Vins et Millesimes BGC",      "https://www.bgcvinrares.com/"),
    ("Cave de Chaz",                "https://cavedechaz.com/"),
    ("Plus de Bulles",              "https://www.plus-de-bulles.com/fr/"),
    ("Gare à la Cave",              "https://garealacavebailleul.fr/"),
    ("Les Bons Plans du Vin",       "https://www.lesbonsplansduvin.com/"),
    ("Les Caves du Valet Blanchet", "https://lescavesduvaletblanchet.com/fr/"),
    ("Vintageandco",                "https://www.vintageandco.com/"),
    ("Trouver un vin",              "https://trouver-un-vin.com/"),
    ("Millesimes et Saveurs Reims", "https://www.millesimes-et-saveurs.com/"),
    ("J'adopte un Vin",             "https://jadopteunvin.fr/"),
    ("Les Box de Bacchus",          "https://lesboxdebacchus.com/"),
    ("Les Passionnes du Vin",       "https://www.lespassionnesduvin.com/"),
    ("Cavissima",                   "https://www.cavissima.com/"),
    ("Millesima",                   "https://www.millesima.fr/"),
    ("Vinatis",                     "https://www.vinatis.com/"),
    ("Cave de Lill",                "https://www.lacavedelill.fr/"),
    ("Versus Wine",                 "https://www.versus.wine/"),
    ("Le Gros Caviste",             "https://legroscaviste.com/"),
    ("Vinum Pro",                   "https://vinum.pro/catalogue-en-ligne/"),
    ("Nouvelle Cave",               "https://nouvellecave.com/"),
    ("Au Millésime",                "https://www.aumillesime.com/boutique-en-ligne"),
    ("La Champagnerie",             "https://www.la-champagnerie.com/"),
    ("75 Centilitres",              "https://www.75-centilitres.fr/"),
    ("Le 520",                      "https://le520.fr/"),
    ("Vins Grands Crus",            "https://www.vinsgrandscrus.fr/"),
    ("Cave des Grands Vins",        "https://www.cave-des-grands-vins.com/"),
    ("Wineguru",                    "https://www.wineguru.fr/"),
    ("Parcellaire",                 "https://www.parcellaire.com/"),
    ("Demain les Vins",             "https://www.demainlesvins.com/"),
    ("Le Carré des Vins",           "https://www.lecarredesvins.com/"),
    ("Mes Bourgognes Beaune",       "https://mesbourgognesbeaune.com/"),
    ("Oenovinia",                   "https://www.oenovinia.com/"),
    ("Le Bourguignon",              "https://www.le-bourguignon.fr/"),
    ("Les Caves",                   "https://www.les-caves.fr/"),
    ("Chais d'Oeuvre",              "https://www.chaisdoeuvre.fr/"),
    ("Terres de Rouges",            "https://terresderouges.com/"),
    ("La Route des Blancs",         "https://www.laroutedesblancs.com/"),
    ("Wine Shop Biarritz",          "https://www.wineshop-biarritz.fr/"),
    ("Wine Shop Fronsac",           "https://wineshopfronsac.com/"),
    ("Stanislas Collin",            "https://stanislascollin.fr/"),
    ("Cave Spirituelle",            "https://www.cave-spirituelle.com/"),
    ("Clos des Millésimes",         "https://www.closdesmillesimes.com/"),
    ("La Cave d'Ulysse",            "https://www.caveulysse.com/"),
    ("Cave Pur Jus",                "https://www.cavepurjus.com/"),
    ("Cave Briau",                  "https://www.briau.com/"),
    ("La Grande Cave",              "https://www.lagrandecave.fr/"),
    ("Triple Vins",                 "https://www.triplevins.com/"),
    ("Vins et Millesimes.com",      "https://www.vinsetmillesimes.com/fr/"),
    ("Comptoir Millesimes",         "https://www.comptoirdesmillesimes.com/"),
    ("Caves de la Halle",           "https://www.cavesdelahalle.com/fr/"),
    ("Le Cellier Nancy",            "https://www.caviste-lecellier.com/"),
    ("Philovino",                   "https://www.philovino.com/"),
    ("Vintage and Co",              "https://www.vintageandco.com/"),
    ("Winot",                       "https://winenot.fr/"),
    ("Le Placard à Pinard",         "https://www.le-placard-a-pinard.com/"),
    ("Les Passionnés du Vin",       "https://www.lespassionnesduvin.com/"),
    ("La Bouteillerie",             "https://www.labouteillerie.fr/"),
    ("Evariste",                    "https://www.evariste.eu/"),
    ("Enclave Vinotheque",          "https://www.enclave-vinotheque.com/"),
    ("Vins Grands Crus.fr",         "https://www.vinsgrandscrus.fr/"),
    ("Place des Grands Vins",       "https://www.placedesgrandsvins.com/"),
    ("Maisonduvigneron",            "https://fr.maisonduvigneron.com/"),
    ("Caves Clamecy",               "https://www.caves-clamecy.com/"),
    ("Le Caviste de France",        "https://www.lecaviste.fr/"),
    ("O'Divin",                     "https://www.odivin.fr/"),
    ("Vino et Sens",                "https://www.vinoetsens.com/"),
    ("La Cave des Amis",            "https://www.lacavedesamis.fr/"),
    ("Vinogusto",                   "https://www.vinogusto.com/fr/"),
    ("Vinexus",                     "https://www.vinexus.fr/"),
    ("Caveau de Bacchus",           "https://www.caveaudebacchus.com/"),
    ("Cave du Château",             "https://www.lacaveduchateau.com/"),
    ("Les Zinzins du Vin",          "https://leszinzinsduvin.eu/"),
    ("Vougeot Vin",                 "https://vougeot.vin/fr/"),
    ("Cavedechaz",                  "https://cavedechaz.com/"),
    ("Prestige Cellar",             "https://www.prestige-cellar.fr/fr/"),
    ("Vins Passion",                "https://www.vinspassion.fr/"),
    ("Cave Millésimes",             "https://www.cavemillesimes.com/"),
    ("La Clé des Vins",             "https://www.lacledesvins.fr/"),
    ("Vignobles et Millésimes",     "https://www.vignoblesmillesimes.fr/"),
    ("La Vinothèque",               "https://www.lavinotheque.fr/"),
    ("Art et Vin",                  "https://www.arts-et-vin.fr/"),
    ("Wermeil",                     "https://www.wermeil.com/"),
    ("Cave Conseil",                "https://www.caveconseil.fr/"),
    ("Le Vin en Cave",              "https://www.levinen cave.fr/"),
    ("Epicurien Thionville",        "https://www.lepicurien-thionville.com/"),
    ("Excellence de Loire",         "https://www.excellencedeloire.com/"),
    ("Vins du Monde",               "https://www.vinsdumonde.fr/"),
    ("La Cave du Palais",           "https://www.lacavedupalais.fr/"),
    ("Vin Sur Vin",                 "https://www.vinsurvin.fr/"),
    ("Chateau Online",              "https://www.chateauonline.fr/"),
    ("Lavinia",                     "https://www.lavinia.com/fr-fr/"),
    ("Twil",                        "https://www.twil.fr/"),
    ("1Jour1Vin",                   "https://www.1jour1vin.com/fr"),
    ("iDealwine",                   "https://www.idealwine.com/fr/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────
# MEMOIRE
# ─────────────────────────────────────────────

def charger_memoire():
    if FICHIER_MEMOIRE.exists():
        with open(FICHIER_MEMOIRE, "r") as f:
            return json.load(f)
    return {"detectes": []}

def sauvegarder_memoire(memoire):
    with open(FICHIER_MEMOIRE, "w") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)

def est_nouveau(url, domaine, memoire):
    cle = f"{url}|{domaine}"
    return cle not in memoire.get("detectes", [])

def marquer_vu(url, domaine, memoire):
    if "detectes" not in memoire:
        memoire["detectes"] = []
    cle = f"{url}|{domaine}"
    if cle not in memoire["detectes"]:
        memoire["detectes"].append(cle)
    memoire["detectes"] = memoire["detectes"][-10000:]

# ─────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

# ─────────────────────────────────────────────
# SCRAPING
# ─────────────────────────────────────────────

def scraper_caviste(nom, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        texte_norm = normaliser(soup.get_text(separator=" "))
        return [d for d in DOMAINES if normaliser(d) in texte_norm]
    except:
        return []

# ─────────────────────────────────────────────
# ENVOI EMAIL
# ─────────────────────────────────────────────

def envoyer_alerte(nouveautes):
    if not nouveautes:
        return
    total = sum(len(d["domaines"]) for d in nouveautes)
    sujet = f"🌍 Alerte Cavistes France — {total} nouveau(x) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    corps_html = """
    <html><body>
    <h2 style="color:#8B4513;">🌍 Nouveaux domaines détectés chez des cavistes français</h2>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;font-family:Arial;width:100%;">
      <tr style="background:#8B4513;color:white;">
        <th>Caviste</th><th>Domaine(s) détecté(s)</th><th>Lien</th>
      </tr>
    """
    for d in nouveautes:
        corps_html += f"""
      <tr>
        <td><b>{d['caviste']}</b></td>
        <td>{'<br>'.join(f"🍷 {dom}" for dom in d['domaines'])}</td>
        <td><a href="{d['url']}">{d['url'][:55]}</a></td>
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
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"🌍 SCAN CAVISTES FRANCE — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}")
    print(f"  Cavistes scannés : {len(CAVISTES_FRANCE)}")
    print(f"  Domaines cibles  : {len(DOMAINES)}")
    print(f"{'='*55}\n")

    memoire = charger_memoire()
    toutes_nouveautes = []

    for i, (nom, url) in enumerate(CAVISTES_FRANCE):
        print(f"🔍 [{i+1}/{len(CAVISTES_FRANCE)}] {nom}...")
        domaines_trouves = scraper_caviste(nom, url)

        if domaines_trouves:
            nouveaux = [d for d in domaines_trouves if est_nouveau(url, d, memoire)]
            if nouveaux:
                print(f"   🆕 {len(nouveaux)} nouveau(x) : {', '.join(nouveaux[:5])}")
                toutes_nouveautes.append({
                    "caviste":  nom,
                    "domaines": nouveaux,
                    "url":      url,
                })
                for d in nouveaux:
                    marquer_vu(url, d, memoire)
            else:
                print(f"   — {len(domaines_trouves)} domaine(s) déjà connu(s)")
        else:
            print(f"   — Aucun domaine cible")

        time.sleep(0.5)

    sauvegarder_memoire(memoire)

    print(f"\n{'='*55}")
    total = sum(len(d["domaines"]) for d in toutes_nouveautes)
    print(f"RÉSULTAT : {total} nouveau(x) domaine(s) chez {len(toutes_nouveautes)} caviste(s)")
    print(f"{'='*55}\n")

    if toutes_nouveautes:
        envoyer_alerte(toutes_nouveautes)
    else:
        print("Aucune nouveauté — pas d'alerte envoyée.")

if __name__ == "__main__":
    main()
