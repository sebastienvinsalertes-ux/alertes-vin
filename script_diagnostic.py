import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime
import unicodedata
import time

# ─────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────

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

CAVISTES = [
    # ── ⭐ VIP Confirmés ──
    ("Caves Amiel",               "https://caves-amiel.fr"),
    ("Cellier des Docks",         "https://cellierdesdocks.com"),
    ("Cave Spirituelle",          "https://cave-spirituelle.com"),
    ("Clos des Millésimes",       "https://closdesmillesimes.com"),
    ("BGC Vins Rares",            "https://bgcvinsrares.com"),
    ("Le Temps des Vendanges",    "https://letempsdesvendanges.com"),
    ("V Marchand de Vins",        "https://vpoint.fr"),
    ("Mademoiselle Wine",         "https://mademoiselle-wine.com"),
    ("Le Sang des Vignes",        "https://la-cave-bidart.fr"),
    ("Badie",                     "https://badie.com"),
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
    ("Les Bons Plans du Vin",     "https://lesbonsplansduvin.com"),
    ("Parcellaire",               "https://parcellaire.com"),
    ("Demain les Vins",           "https://demainlesvins.com"),
    ("Terres de Rouges",          "https://terresderouges.com"),
    ("La Grande Cave",            "https://lagrandecave.fr"),
    ("Chais d'Oeuvre",            "https://chaisdoeuvre.fr"),
    ("Vente à la Propriété",      "https://ventealapropriete.com"),
    ("Les Caves",                 "https://les-caves.fr"),
    ("Vougeot.vin",               "https://vougeot.vin"),
    ("Le Gros Caviste",           "https://legroscaviste.com"),
    ("Philovino",                 "https://philovino.com"),
    ("Winenot",                   "https://winenot.fr"),
    ("Cave des Grands Vins",      "https://cave-des-grands-vins.com"),
    ("La Vinothèque de Bordeaux", "https://vinotheque-bordeaux.com"),
    ("Wine Shop Biarritz",        "https://wineshop-biarritz.fr"),
    ("Wine Shop Fronsac",         "https://wineshopfronsac.com"),
    ("Ardoneo",                   "https://vin-bio-ardoneo.com"),
    ("Domaine Le Cellier",        "https://domainelecellier.fr"),
    ("Vintage Select",            "https://vintageselect31.fr"),
    ("Millesima",                 "https://millesima.fr"),
    ("Cave Pur Jus",              "https://cavepurjus.com"),
    ("La Cave de Lill",           "https://lacavedelill.fr"),
    # ── 🌐 Site Web À Scanner ──
    ("La Crypte du Vin",          "https://lacrypteduvin.fr"),
    ("L'Intendant",               "https://intendant.com"),
    ("La CUV",                    "https://la-cuv.com"),
    ("Cousin & Compagnie",        "https://cousin.fr"),
    ("Cave Pourpre",              "https://cavepourpre.com"),
    ("La Cavisterie",             "https://lacavisterie.fr"),
    ("Le Pied à Terre",           "https://lepiedaterre-cave.com"),
    ("La Maison Gabin",           "https://1.lamaisongabin.com"),
    ("Cave Briau",                "https://briau.com"),
    ("Amour du Vin",              "https://amourduvin.com"),
    ("La Cave des Darons",        "https://lacavedesdarons.com"),
    ("Vins et Terroir",           "https://vins-et-terroir.com"),
    ("Cave Saint-Jean d'Août",    "https://cave-montdemarsan.fr"),
    ("Au Chai Vous",              "https://auchaivous.com"),
    ("Vinothèque de Dax",         "https://vinotheque-dax.fr"),
    ("Plaisirs du Vin Dax",       "https://dax.plaisirsduvin.com"),
    ("La Bouteille 40",           "https://labouteille40.com"),
    ("La Cave 40 Narrosse",       "https://lacave40.fr"),
    ("Caves Bacqué",              "https://cavesbacque.com"),
    ("Cave du Palais",            "https://cavedupalais.shop"),
    ("Cave Nobel",                "https://cave-nobel.com"),
    ("La Cave de Max",            "https://la-cave-de-max.fr"),
    ("Les 4 Pépins",              "https://les4pepins.com"),
    ("Des Bouchons",              "https://desbouchons.fr"),
    ("Boutique des Vins",         "https://boutiquedesvins.com"),
    ("Vins d'Une Oreille",        "https://vinsduneoreille.com"),
    ("Chai Vincent",              "https://chai-vincent.fr"),
    ("Le Comptoir des Vins",      "https://lecomptoirdesvins-toulouse.com"),
    ("In Vino Fredo",             "https://invinofredo.fr"),
    ("Lacrima Vini",              "https://lacrimavini.fr"),
    ("Les 3 Caves Rive Gauche",   "https://les3caves-rivegauche.fr"),
    ("Sourire des Saveurs",       "https://souriredessaveurs.com"),
    ("Wine Notes",                "https://wine-notes.fr"),
    ("Cave de César",             "https://lacavedecesar.fr"),
    ("Cavissima",                 "https://cavissima.com"),
    ("1Jour1Vin",                 "https://1jour1vin.com"),
    ("Wineguru",                  "https://wineguru.fr"),
    ("La Champagnerie",           "https://la-champagnerie.com"),
    ("75 Centilitres",            "https://75-centilitres.fr"),
    ("Le 520",                    "https://le520.fr"),
    ("Au Millésime",              "https://aumillesime.com"),
    ("La Cave d'Ulysse",          "https://caveulysse.com"),
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
# STATUTS
# ─────────────────────────────────────────────────────

STATUT_OK          = "OK"           # Scanné, texte récupéré
STATUT_VIDE        = "VIDE"         # Réponse OK mais texte < 500 chars (JS requis)
STATUT_BLOQUE      = "BLOQUE"       # 403, 429, 503, Cloudflare
STATUT_ERREUR      = "ERREUR"       # 404, 500, autre code HTTP
STATUT_TIMEOUT     = "TIMEOUT"      # Timeout réseau
STATUT_CRASH       = "CRASH"        # Exception inattendue

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

def diagnostiquer_site(nom, url):
    """Retourne un dict avec statut, détails et domaines trouvés."""
    result = {
        "nom": nom,
        "url": url,
        "statut": None,
        "code_http": None,
        "taille_texte": 0,
        "domaines": [],
        "detail": "",
    }
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        result["code_http"] = resp.status_code

        # Codes bloquants
        if resp.status_code in (403, 429, 503):
            result["statut"] = STATUT_BLOQUE
            result["detail"] = f"HTTP {resp.status_code}"
            # Détection Cloudflare
            if "cloudflare" in resp.text.lower() or "cf-ray" in str(resp.headers).lower():
                result["detail"] += " (Cloudflare)"
            return result

        if resp.status_code >= 400:
            result["statut"] = STATUT_ERREUR
            result["detail"] = f"HTTP {resp.status_code}"
            return result

        # Parse HTML
        soup = BeautifulSoup(resp.text, "html.parser")
        texte = soup.get_text(separator=" ")
        texte_norm = normaliser(texte)
        taille = len(texte.strip())
        result["taille_texte"] = taille

        # Texte trop court = page JS vide
        if taille < 500:
            result["statut"] = STATUT_VIDE
            result["detail"] = f"Texte trop court ({taille} chars) — JS requis ?"
            return result

        # Cherche domaines cibles
        domaines_trouves = [d for d in DOMAINES if normaliser(d) in texte_norm]
        result["domaines"] = domaines_trouves
        result["statut"] = STATUT_OK
        result["detail"] = f"{taille:,} chars récupérés"
        return result

    except requests.exceptions.Timeout:
        result["statut"] = STATUT_TIMEOUT
        result["detail"] = "Timeout (>15s)"
        return result
    except Exception as e:
        result["statut"] = STATUT_CRASH
        result["detail"] = str(e)[:80]
        return result


# ─────────────────────────────────────────────────────
# CONSTRUCTION EMAIL DIAGNOSTIC
# ─────────────────────────────────────────────────────

COULEURS = {
    STATUT_OK:      ("#1a7a3a", "✅"),
    STATUT_VIDE:    ("#e67e00", "⚠️"),
    STATUT_BLOQUE:  ("#c0392b", "🚫"),
    STATUT_ERREUR:  ("#8e44ad", "❌"),
    STATUT_TIMEOUT: ("#2980b9", "⏱️"),
    STATUT_CRASH:   ("#555555", "💀"),
}

def construire_email_diagnostic(resultats, heure):
    # Stats globales
    compteurs = {s: 0 for s in [STATUT_OK, STATUT_VIDE, STATUT_BLOQUE, STATUT_ERREUR, STATUT_TIMEOUT, STATUT_CRASH]}
    for r in resultats:
        compteurs[r["statut"]] += 1

    total = len(resultats)
    sites_avec_domaines = [r for r in resultats if r["domaines"]]

    # Barre de stats
    stats_html = f"""
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin:16px 0;">
      <span style="background:#1a7a3a;color:white;padding:4px 10px;border-radius:20px;font-size:13px;">✅ OK : {compteurs[STATUT_OK]}</span>
      <span style="background:#e67e00;color:white;padding:4px 10px;border-radius:20px;font-size:13px;">⚠️ Vide/JS : {compteurs[STATUT_VIDE]}</span>
      <span style="background:#c0392b;color:white;padding:4px 10px;border-radius:20px;font-size:13px;">🚫 Bloqué : {compteurs[STATUT_BLOQUE]}</span>
      <span style="background:#8e44ad;color:white;padding:4px 10px;border-radius:20px;font-size:13px;">❌ Erreur : {compteurs[STATUT_ERREUR]}</span>
      <span style="background:#2980b9;color:white;padding:4px 10px;border-radius:20px;font-size:13px;">⏱️ Timeout : {compteurs[STATUT_TIMEOUT]}</span>
      <span style="background:#555;color:white;padding:4px 10px;border-radius:20px;font-size:13px;">💀 Crash : {compteurs[STATUT_CRASH]}</span>
    </div>
    """

    # Section domaines trouvés
    domaines_html = ""
    if sites_avec_domaines:
        domaines_html = """
        <h3 style="color:#722F37;border-bottom:2px solid #722F37;padding-bottom:6px;margin-top:24px;">
          🍷 Domaines détectés lors du diagnostic
        </h3>
        <table border="1" cellpadding="8" cellspacing="0"
               style="border-collapse:collapse;width:100%;font-size:13px;margin-bottom:20px;">
          <tr style="background:#722F37;color:white;">
            <th>Caviste</th><th>Domaines trouvés</th>
          </tr>
        """
        for r in sites_avec_domaines:
            domaines_html += f"""
          <tr>
            <td><a href="{r['url']}" style="color:#722F37;">{r['nom']}</a></td>
            <td>{"🍷 " + " · ".join(r['domaines'])}</td>
          </tr>"""
        domaines_html += "</table>"

    # Tableau complet
    lignes_html = ""
    for r in resultats:
        couleur, icone = COULEURS.get(r["statut"], ("#333", "?"))
        domaines_str = ", ".join(r["domaines"]) if r["domaines"] else "—"
        bg = "#f0fff4" if r["statut"] == STATUT_OK else (
             "#fff8f0" if r["statut"] == STATUT_VIDE else (
             "#fff0f0" if r["statut"] in (STATUT_BLOQUE, STATUT_ERREUR) else
             "#f5f5f5"))
        lignes_html += f"""
        <tr style="background:{bg};">
          <td style="font-size:12px;">{r['nom']}</td>
          <td style="font-size:11px;color:#666;"><a href="{r['url']}" style="color:#666;">{r['url']}</a></td>
          <td style="text-align:center;"><span style="color:{couleur};font-weight:bold;">{icone} {r['statut']}</span></td>
          <td style="font-size:11px;color:#555;">{r['detail']}</td>
          <td style="font-size:11px;color:#722F37;">{domaines_str}</td>
        </tr>"""

    html = f"""
    <html><body style="font-family:Arial,sans-serif;max-width:900px;margin:auto;">
    <div style="background:#2c2c2c;color:white;padding:16px 20px;border-radius:8px 8px 0 0;">
      <h2 style="margin:0;">🔬 Diagnostic Scraping Cavistes — {heure}</h2>
      <p style="margin:6px 0 0;font-size:13px;">{total} sites analysés</p>
    </div>
    <div style="padding:16px 20px;">
      {stats_html}
      {domaines_html}
      <h3 style="color:#2c2c2c;border-bottom:2px solid #ccc;padding-bottom:6px;margin-top:24px;">
        📋 Rapport complet site par site
      </h3>
      <table border="1" cellpadding="8" cellspacing="0"
             style="border-collapse:collapse;width:100%;font-size:12px;">
        <tr style="background:#2c2c2c;color:white;">
          <th>Caviste</th>
          <th>URL</th>
          <th>Statut</th>
          <th>Détail</th>
          <th>Domaines trouvés</th>
        </tr>
        {lignes_html}
      </table>
      <div style="margin-top:20px;padding:12px;background:#fffbe6;border-left:4px solid #e67e00;font-size:12px;">
        <b>Légende :</b><br>
        ✅ <b>OK</b> — scanné correctement · 
        ⚠️ <b>Vide/JS</b> — page reçue mais vide, le catalogue est en JavaScript (non scrapable) · 
        🚫 <b>Bloqué</b> — 403/429/Cloudflare · 
        ❌ <b>Erreur</b> — 404/500 · 
        ⏱️ <b>Timeout</b> — site trop lent · 
        💀 <b>Crash</b> — erreur réseau
      </div>
    </div>
    <p style="color:#aaa;font-size:11px;padding:0 20px 16px;">
      Diagnostic du {heure} — script_diagnostic.py
    </p>
    </body></html>
    """
    return html


def envoyer_email(html, heure, compteurs):
    ok = compteurs.get(STATUT_OK, 0)
    pb = sum(v for k, v in compteurs.items() if k != STATUT_OK)
    sujet = f"🔬 Diagnostic scraping — {ok} OK · {pb} problèmes — {heure}"
    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"]    = GMAIL_EXPEDITEUR
    msg["To"]      = DESTINATAIRE
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(GMAIL_EXPEDITEUR, GMAIL_PASSWORD)
            smtp.sendmail(GMAIL_EXPEDITEUR, DESTINATAIRE, msg.as_string())
        print(f"✅ Email diagnostic envoyé : {sujet}")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")


# ─────────────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────────────

def main():
    heure = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"\n{'='*60}")
    print(f"🔬 DIAGNOSTIC SCRAPING — {heure}")
    print(f"   {len(CAVISTES)} sites à analyser")
    print(f"{'='*60}\n")

    resultats = []
    for i, (nom, url) in enumerate(CAVISTES):
        print(f"[{i+1:>3}/{len(CAVISTES)}] {nom[:35]:<35}", end=" ")
        r = diagnostiquer_site(nom, url)
        resultats.append(r)
        icone = COULEURS.get(r["statut"], ("", "?"))[1]
        print(f"{icone} {r['statut']:<8} {r['detail'][:50]}")
        time.sleep(0.5)

    # Stats finales
    compteurs = {s: 0 for s in [STATUT_OK, STATUT_VIDE, STATUT_BLOQUE, STATUT_ERREUR, STATUT_TIMEOUT, STATUT_CRASH]}
    for r in resultats:
        compteurs[r["statut"]] += 1

    print(f"\n{'='*60}")
    print(f"RÉSULTATS :")
    for statut, count in compteurs.items():
        if count:
            icone = COULEURS.get(statut, ("", "?"))[1]
            print(f"  {icone} {statut:<10} : {count}")
    print(f"{'='*60}\n")

    html = construire_email_diagnostic(resultats, heure)
    envoyer_email(html, heure, compteurs)


if __name__ == "__main__":
    main()
