import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime

GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"

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

SITES_VENTES_PRIVEES = [
    ("Vente à la Propriété",    "https://www.ventealapropriete.com/fr/ventes-privees"),
    ("20h33",                   "https://www.20h33.com/"),
    ("Cuvée Privée",            "https://cuvee-privee.com/"),
    ("Le Clos Privé",           "https://www.leclos-prive.com/shop/"),
    ("Les Grappes",             "https://www.lesgrappes.com/"),
    ("Lavinia",                 "https://www.lavinia.com/fr-fr/ufr/ventes-privees-club-france"),
    ("Petites Caves",           "https://www.petitescaves.com/collections/vente-privee-champagnes-2024"),
    ("Pépites en Champagne",    "https://pepites-en-champagne.fr/"),
    ("Premium Grands Crus",     "https://www.premiumgrandscrus.com/fr/pages/4-ventes-privees"),
    ("Chateaunet",              "https://www.chateaunet.com/nos-ventes-privees"),
    ("Chais d'Oeuvre",          "https://www.chaisdoeuvre.fr/pages/ventes-privees"),
    ("Twil",                    "https://www.twil.fr/ventes-privees"),
    ("Cash Vin",                "https://www.cashvin.com/ventes-privees/"),
    ("Les Caves",               "https://www.les-caves.fr/fr/1148-vente-privee-bourgogne"),
    ("Le Bourguignon",          "https://www.le-bourguignon.fr/fr/89-vente-privee-vins-de-bourgogne"),
    ("Le Carré des Vins",       "https://www.lecarredesvins.com/"),
    ("Oenovinia",               "https://www.oenovinia.com/"),
    ("La Cave du Château",      "https://www.lacaveduchateau.com/ventes-privees.html"),
    ("Les Bons Plans du Vin",   "https://www.lesbonsplansduvin.com/"),
    ("Mes Bourgognes Beaune",   "https://mesbourgognesbeaune.com/"),
    ("Parcellaire",             "https://www.parcellaire.com/"),
    ("Demain les Vins",         "https://www.demainlesvins.com/"),
    ("La Lettre des Vignerons", "https://www.lalettredesvignerons.com/"),
    ("La Grande Cave",          "https://www.lagrandecave.fr/rayon/ventes-privees"),
    ("iDealwine",               "https://www.idealwine.com/fr/acheter-du-vin"),
    ("1Jour1Vin",               "https://www.1jour1vin.com/fr"),
    ("Wine Guru",               "https://www.wineguru.fr/830-allocations"),
    ("Vins Grands Crus",        "https://www.vinsgrandscrus.fr/"),
    ("Cave des Grands Vins",    "https://www.cave-des-grands-vins.com/"),
    ("Terres de Rouges",        "https://terresderouges.com/"),
    ("La Route des Blancs",     "https://www.laroutedesblancs.com/"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

def envoyer_alerte(detections):
    if not detections:
        return
    sujet = f"🍷 Alerte Vins — {len(detections)} détection(s) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    corps_html = """
    <html><body>
    <h2 style="color:#722F37;">🍷 Alertes Ventes Privées Vin</h2>
    <p>Les domaines suivants ont été détectés :</p>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;font-family:Arial;">
      <tr style="background:#722F37;color:white;">
        <th>Domaine détecté</th>
        <th>Site</th>
        <th>Lien</th>
      </tr>
    """
    for d in detections:
        corps_html += f"""
      <tr>
        <td><b>{d['domaine']}</b></td>
        <td>{d['site']}</td>
        <td><a href="{d['url']}">{d['url'][:60]}...</a></td>
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
        print(f"✅ Email envoyé : {len(detections)} détection(s)")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

def normaliser(texte):
    import unicodedata
    return unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode().lower()

def scraper_site(nom_site, url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        texte = normaliser(soup.get_text(separator=" "))
        trouves = []
        for domaine in DOMAINES:
            if normaliser(domaine) in texte:
                trouves.append(domaine)
        return trouves
    except requests.exceptions.Timeout:
        print(f"⏱️  Timeout : {nom_site}")
        return []
    except requests.exceptions.HTTPError as e:
        print(f"⚠️  HTTP {e.response.status_code} : {nom_site}")
        return []
    except Exception as e:
        print(f"⚠️  Erreur {nom_site} : {e}")
        return []

def main():
    print(f"\n{'='*55}")
    print(f"🍷 SCAN VENTES PRIVÉES VIN — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}")
    toutes_detections = []
    for nom_site, url in SITES_VENTES_PRIVEES:
        print(f"🔍 Scan : {nom_site}...")
        domaines_trouves = scraper_site(nom_site, url)
        if domaines_trouves:
            print(f"   ✅ {len(domaines_trouves)} domaine(s) trouvé(s) : {', '.join(domaines_trouves)}")
            for domaine in domaines_trouves:
                toutes_detections.append({
                    "domaine": domaine,
                    "site":    nom_site,
                    "url":     url,
                })
        else:
            print(f"   — Aucun domaine cible trouvé")
    print(f"\nRÉSULTAT : {len(toutes_detections)} détection(s) au total\n")
    if toutes_detections:
        envoyer_alerte(toutes_detections)
    else:
        print("Aucune alerte à envoyer.")

if __name__ == "__main__":
    main()
