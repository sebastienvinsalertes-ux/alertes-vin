import imaplib
import email
from email.header import decode_header
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime, timedelta
import unicodedata
import json
from pathlib import Path

GMAIL_SCAN       = "sebastiengarat64@gmail.com"
GMAIL_SCAN_PWD   = os.environ.get("GMAIL_SCAN_PASSWORD", "")
GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_ALERT_PWD  = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"
FICHIER_TRAITES  = Path("emails_deja_traites.json")

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

EXPEDITEURS_VENTES = [
    "ventealapropriete", "20h33", "cuvee-privee", "leclos-prive",
    "lesgrappes", "lavinia", "petitescaves", "pepites-en-champagne",
    "premiumgrandscrus", "chateaunet", "chaisdoeuvre", "twil",
    "cashvin", "les-caves", "le-bourguignon", "lecarredesvins",
    "oenovinia", "lacaveduchateau", "lesbonsplansduvin",
    "mesbourgognesbeaune", "parcellaire", "demainlesvins",
    "lalettredesvignerons", "lagrandecave", "idealwine",
    "1jour1vin", "wineguru", "vinsgrandscrus", "cave-des-grands-vins",
    "terresderouges", "laroutedesblancs", "vistavin",
]

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

def charger_traites():
    if FICHIER_TRAITES.exists():
        with open(FICHIER_TRAITES, "r") as f:
            return set(json.load(f))
    return set()

def sauvegarder_traites(traites):
    liste = list(traites)[-5000:]
    with open(FICHIER_TRAITES, "w") as f:
        json.dump(liste, f)

def decoder_entete(entete):
    try:
        parties = decode_header(entete)
        resultat = ""
        for partie, encoding in parties:
            if isinstance(partie, bytes):
                resultat += partie.decode(encoding or "utf-8", errors="ignore")
            else:
                resultat += str(partie)
        return resultat
    except:
        return str(entete)

def extraire_corps(msg):
    corps = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    corps += payload.decode(charset, errors="ignore")
                except:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            corps = payload.decode(charset, errors="ignore")
        except:
            pass
    return corps

def envoyer_alerte(detections):
    if not detections:
        return
    sujet = f"📬 Alerte Gmail Vins — {len(detections)} email(s) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    corps_html = "<html><body><h2 style='color:#722F37;'>📬 Domaines détectés dans vos emails</h2>"
    for d in detections:
        corps_html += f"""
    <div style="border:1px solid #ddd;padding:12px;margin:10px 0;border-radius:6px;font-family:Arial;">
      <b style="color:#722F37;font-size:16px;">🍷 {', '.join(d['domaines'])}</b><br><br>
      <b>Objet :</b> {d['sujet']}<br>
      <b>De :</b> {d['expediteur']}<br>
      <b>Reçu le :</b> {d['date']}<br>
    </div>"""
    corps_html += f"<p style='color:gray;font-size:12px;'>Scan effectué le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p></body></html>"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"]    = GMAIL_EXPEDITEUR
    msg["To"]      = DESTINATAIRE
    msg.attach(MIMEText(corps_html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_EXPEDITEUR, GMAIL_ALERT_PWD)
            smtp.sendmail(GMAIL_EXPEDITEUR, DESTINATAIRE, msg.as_string())
        print(f"✅ Alerte envoyée : {len(detections)} email(s) détecté(s)")
    except Exception as e:
        print(f"❌ Erreur envoi alerte : {e}")

def scanner_gmail():
    detections = []
    emails_traites = charger_traites()
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_SCAN, GMAIL_SCAN_PWD)
        mail.select("inbox")
        date_hier = (datetime.now() - timedelta(days=1)).strftime("%d-%b-%Y")
        _, messages = mail.search(None, f'(SINCE "{date_hier}")')
        ids = messages[0].split()
        print(f"  📬 {len(ids)} email(s) des dernières 24h")
        for email_id in ids:
            email_id_str = email_id.decode()
            if email_id_str in emails_traites:
                continue
            _, msg_data = mail.fetch(email_id, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
            expediteur = decoder_entete(msg.get("From", ""))
            sujet      = decoder_entete(msg.get("Subject", ""))
            date_email = msg.get("Date", "")
            if not any(site in normaliser(expediteur) for site in EXPEDITEURS_VENTES):
                emails_traites.add(email_id_str)
                continue
            texte_norm = normaliser(f"{sujet} {extraire_corps(msg)}")
            domaines_trouves = [d for d in DOMAINES if normaliser(d) in texte_norm]
            emails_traites.add(email_id_str)
            if domaines_trouves:
                print(f"   ✅ {', '.join(domaines_trouves)} — {sujet[:50]}")
                detections.append({
                    "domaines": domaines_trouves,
                    "sujet": sujet,
                    "expediteur": expediteur,
                    "date": date_email,
                })
        mail.logout()
        sauvegarder_traites(emails_traites)
    except Exception as e:
        print(f"❌ Erreur Gmail : {e}")
    return detections

def main():
    print(f"\n{'='*55}")
    print(f"📬 SCAN GMAIL — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}")
    detections = scanner_gmail()
    print(f"\nRÉSULTAT : {len(detections)} email(s) avec domaines cibles\n")
    if detections:
        envoyer_alerte(detections)
    else:
        print("Aucune alerte à envoyer.")

if __name__ == "__main__":
    main()
