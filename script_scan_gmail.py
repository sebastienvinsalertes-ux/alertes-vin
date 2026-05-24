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
import re

# ─────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────

GMAIL_SCAN       = "sebastiengarat64@gmail.com"
GMAIL_SCAN_PWD   = os.environ.get("GMAIL_SCAN_PASSWORD", "")
GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_ALERT_PWD  = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"
FICHIER_TRAITES  = Path("memoire_gmail.json")

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

# Expéditeurs surveillés (newsletters, ventes privées, cavistes)
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
    "vinsetmillesimes", "comptoirdesmillesimes", "millesimes",
    "closdesmillesimes", "cave-spirituelle", "stanislascollin",
    "wineshop", "oenovinia", "millesima", "vinatis",
    "vintageandco", "cavissima", "1jour1vin",
]

# ─────────────────────────────────────────────────────
# MÉMOIRE PERSISTANTE
# ─────────────────────────────────────────────────────

def charger_traites():
    if FICHIER_TRAITES.exists():
        with open(FICHIER_TRAITES, "r") as f:
            data = json.load(f)
            return set(data.get("traites", []))
    return set()

def sauvegarder_traites(traites):
    liste = list(traites)[-8000:]
    with open(FICHIER_TRAITES, "w") as f:
        json.dump({"traites": liste}, f)

# ─────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

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

def extraire_liens(corps_html):
    """Extrait tous les liens http(s) du corps de l'email."""
    return re.findall(r'https?://[^\s"\'<>]+', corps_html)

def lien_gmail(email_id_str):
    """Génère un lien direct vers l'email dans Gmail."""
    # Encode l'ID en hex pour Gmail
    try:
        id_int = int(email_id_str)
        hex_id = format(id_int, 'x').upper()
        return f"https://mail.google.com/mail/u/0/#inbox/{hex_id}"
    except:
        return "https://mail.google.com/mail/u/0/#inbox"

# ─────────────────────────────────────────────────────
# SCAN GMAIL
# ─────────────────────────────────────────────────────

def scanner_gmail():
    detections = []
    emails_traites = charger_traites()
    nb_scannes = 0

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

            emails_traites.add(email_id_str)

            # Filtre sur expéditeurs connus
            if not any(site in normaliser(expediteur) for site in EXPEDITEURS_VENTES):
                continue

            nb_scannes += 1
            corps = extraire_corps(msg)
            texte_norm = normaliser(f"{sujet} {corps}")
            domaines_trouves = [d for d in DOMAINES if normaliser(d) in texte_norm]

            if not domaines_trouves:
                continue

            # Liens directs depuis le corps de l'email
            liens_email = extraire_liens(corps)
            # Filtre les liens pertinents (produits, vins)
            liens_pertinents = [
                l for l in liens_email
                if any(mot in l.lower() for mot in ["vin", "wine", "cru", "domaine", "produit", "product", "shop", "boutique"])
            ][:5]

            lien_gmail_direct = lien_gmail(email_id_str)

            print(f"  ✅ {', '.join(domaines_trouves)} — {sujet[:50]}")
            detections.append({
                "domaines":         domaines_trouves,
                "sujet":            sujet,
                "expediteur":       expediteur,
                "date":             date_email,
                "lien_gmail":       lien_gmail_direct,
                "liens_produits":   liens_pertinents,
            })

        mail.logout()
        sauvegarder_traites(emails_traites)

    except Exception as e:
        print(f"❌ Erreur Gmail : {e}")

    return detections, nb_scannes

# ─────────────────────────────────────────────────────
# ENVOI EMAIL
# ─────────────────────────────────────────────────────

def envoyer_email(detections, nb_scannes):
    heure = datetime.now().strftime("%d/%m/%Y %H:%M")
    nb = len(detections)

    if nb > 0:
        sujet = f"📬 {nb} email(s) vin avec domaines cibles — {heure}"
    else:
        sujet = f"📬 Scan Gmail — RAS — {heure}"

    corps_html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:800px;margin:auto;">
    <div style="background:#2C5F8A;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
      <h2 style="margin:0;">📬 Scan Gmail — {heure}</h2>
      <p style="margin:6px 0 0;font-size:13px;">{nb_scannes} email(s) d'expéditeurs surveillés analysés</p>
    </div>
    """

    if detections:
        corps_html += """
    <div style="padding:16px 20px;">
      <h3 style="color:#2C5F8A;border-bottom:2px solid #2C5F8A;padding-bottom:6px;">
        🆕 Emails avec domaines cibles détectés
      </h3>
    """
        for d in detections:
            domaines_str = " · ".join(f"🍷 {dom}" for dom in d["domaines"])
            liens_html = ""
            if d["liens_produits"]:
                liens_html = "<br><b>Liens produits :</b><br>" + "".join(
                    f'&nbsp;&nbsp;→ <a href="{l}" style="color:#2C5F8A;">{l[:70]}...</a><br>'
                    for l in d["liens_produits"]
                )
            corps_html += f"""
      <div style="border:1px solid #ddd;padding:14px;margin:10px 0;border-radius:6px;">
        <div style="font-size:15px;font-weight:bold;color:#2C5F8A;margin-bottom:8px;">
          {domaines_str}
        </div>
        <b>Objet :</b> {d['sujet']}<br>
        <b>De :</b> {d['expediteur']}<br>
        <b>Reçu le :</b> {d['date']}<br>
        {liens_html}
        <br>
        <a href="{d['lien_gmail']}"
           style="display:inline-block;margin-top:8px;padding:8px 16px;
                  background:#2C5F8A;color:white;border-radius:4px;
                  text-decoration:none;font-size:13px;">
          📧 Ouvrir dans Gmail
        </a>
      </div>"""
        corps_html += "</div>"
    else:
        corps_html += """
    <div style="padding:16px 20px;background:#f9f9f9;border-left:4px solid #2C5F8A;margin:16px 0;">
      <p style="margin:0;color:#555;">✅ Aucun email avec vos domaines cibles dans les dernières 24h.</p>
    </div>
    """

    corps_html += f"""
    <p style="color:#aaa;font-size:11px;padding:0 20px 16px;">
      Scan effectué le {heure} · memoire_gmail.json mis à jour
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
            smtp.login(GMAIL_EXPEDITEUR, GMAIL_ALERT_PWD)
            smtp.sendmail(GMAIL_EXPEDITEUR, DESTINATAIRE, msg.as_string())
        print(f"✅ Email envoyé ({nb} détection(s))")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

# ─────────────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"📬 SCAN GMAIL — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}")

    detections, nb_scannes = scanner_gmail()

    print(f"\nRÉSULTAT : {len(detections)} email(s) avec domaines cibles\n")

    envoyer_email(detections, nb_scannes)

if __name__ == "__main__":
    main()
