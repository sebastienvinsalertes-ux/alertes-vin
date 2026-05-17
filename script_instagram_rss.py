import requests
import feedparser
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import json
from datetime import datetime
from pathlib import Path
import unicodedata

GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"
FICHIER_VUES     = Path("posts_deja_vus.json")

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

FLUX_RSS = [
    ("Le Carré des Vins",       "https://www.lecarredesvins.com/blog/rss"),
    ("iDealwine Blog",          "https://www.idealwine.net/feed/"),
    ("Lavinia Blog",            "https://www.lavinia.com/fr-fr/blog?format=atom"),
    ("Chateaunet Blog",         "https://www.chateaunet.com/blog?format=atom"),
    ("Demain les Vins",         "https://www.demainlesvins.com/feed/"),
    ("La Route des Blancs",     "https://www.laroutedesblancs.com/blog/rss"),
    ("Terres de Rouges",        "https://terresderouges.com/blog/rss"),
    ("Twil Blog",               "https://www.twil.fr/blog?format=atom"),
    ("Wine Guru Blog",          "https://www.wineguru.fr/blog/rss"),
    ("Vente à la Propriété",    "https://www.ventealapropriete.com/fr/blog?format=atom"),
]

MOTS_PERTINENCE = [
    "vente", "stock", "disponible", "allocation",
    "nouveau", "nouvelle", "arrivage", "millésime",
    "livraison", "commande", "bouteille", "flacon"
]

def normaliser(texte):
    return unicodedata.normalize("NFD", texte).encode("ascii", "ignore").decode().lower()

def charger_vus():
    if FICHIER_VUES.exists():
        with open(FICHIER_VUES, "r") as f:
            return set(json.load(f))
    return set()

def sauvegarder_vus(vus):
    liste = list(vus)[-2000:]
    with open(FICHIER_VUES, "w") as f:
        json.dump(liste, f)

def est_pertinent(texte_norm):
    return any(mot in texte_norm for mot in MOTS_PERTINENCE)

def envoyer_alerte(detections):
    if not detections:
        return
    sujet = f"📝 Alerte Posts Vin — {len(detections)} nouveau(x) post(s) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    corps_html = """
    <html><body>
    <h2 style="color:#722F37;">📝 Nouveaux posts — Domaines cibles détectés</h2>
    <p>Les publications suivantes mentionnent vos domaines :</p>
    """
    for d in detections:
        corps_html += f"""
    <div style="border:1px solid #ddd;padding:12px;margin:10px 0;border-radius:6px;">
      <b style="color:#722F37;">{d['domaine']}</b> mentionné sur <b>{d['source']}</b><br>
      <a href="{d['lien']}">{d['titre']}</a><br>
      <small style="color:gray;">Publié le {d['date']}</small>
    </div>"""
    corps_html += f"""
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
        print(f"✅ Email envoyé : {len(detections)} post(s)")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

def scanner_rss(nom_source, url_rss, posts_vus):
    detections = []
    try:
        feed = feedparser.parse(url_rss)
        for entry in feed.entries[:20]:
            lien  = getattr(entry, "link", "")
            titre = getattr(entry, "title", "")
            desc  = getattr(entry, "summary", "")
            date  = getattr(entry, "published", datetime.now().strftime("%d/%m/%Y"))
            if lien in posts_vus:
                continue
            texte_norm = normaliser(f"{titre} {desc}")
            for domaine in DOMAINES:
                if normaliser(domaine) in texte_norm and est_pertinent(texte_norm):
                    detections.append({
                        "domaine": domaine,
                        "source":  nom_source,
                        "titre":   titre,
                        "lien":    lien,
                        "date":    date,
                    })
                    posts_vus.add(lien)
                    break
    except Exception as e:
        print(f"⚠️  Erreur RSS {nom_source} : {e}")
    return detections, posts_vus

def main():
    print(f"\n{'='*55}")
    print(f"📝 SCAN RSS VIN — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}")
    posts_vus = charger_vus()
    toutes_detections = []
    for nom_source, url_rss in FLUX_RSS:
        print(f"🔍 Scan RSS : {nom_source}...")
        detections, posts_vus = scanner_rss(nom_source, url_rss, posts_vus)
        if detections:
            print(f"   ✅ {len(detections)} post(s) trouvé(s)")
            toutes_detections.extend(detections)
        else:
            print(f"   — Aucun nouveau post pertinent")
    sauvegarder_vus(posts_vus)
    print(f"\nRÉSULTAT : {len(toutes_detections)} post(s) détecté(s)\n")
    if toutes_detections:
        envoyer_alerte(toutes_detections)
    else:
        print("Aucune alerte à envoyer.")

if __name__ == "__main__":
    main()
