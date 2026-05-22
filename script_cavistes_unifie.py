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
FICHIER_MEMOIRE  = Path("cavistes_unifies_detectes.json")
FICHIER_URLS     = Path("cavistes_unifies_urls.json")

# ─────────────────────────────────────────────────────
# 64 DOMAINES CIBLES
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
# CAVISTES PRIORITAIRES — scannés à chaque run
# Liste complète : VIP connus + onglet "Site Web À Scanner"
# ─────────────────────────────────────────────────────

CAVISTES_PRIORITAIRES = [
    # ── VIP & Grands spécialistes en ligne ──
    ("Clos des Millésimes",      "https://www.closdesmillesimes.com"),
    ("Cave Spirituelle",         "https://www.cave-spirituelle.com"),
    ("Stanislas Collin",         "https://stanislascollin.fr"),
    ("Vins et Millésimes",       "https://www.vinsetmillesimes.com"),
    ("Comptoir des Millésimes",  "https://www.comptoirdesmillesimes.com"),
    ("La Cave du Marché",        "https://www.lacavedumarche.fr"),
    ("Millesimes.com",           "https://millesimes.com"),
    ("Vougeot.vin",              "https://vougeot.vin"),
    ("Prestige Cellar",          "https://www.prestige-cellar.fr"),
    ("Sphere Wine",              "https://sphere-wine.com"),
    ("Caves Carrière",           "https://www.caves-carriere.fr"),
    ("Cave de Chaz",             "https://cavedechaz.com"),
    ("Plus de Bulles",           "https://www.plus-de-bulles.com"),
    ("Vintageandco",             "https://www.vintageandco.com"),
    ("Les Grandes Caves Paris",  "https://www.lesgrandescaves.fr"),
    ("Les Zinzins du Vin",       "https://leszinzinsduvin.eu"),
    ("Mister Wine",              "https://www.mister-wine.fr"),
    ("Millesima",                "https://www.millesima.fr"),
    ("Vinatis",                  "https://www.vinatis.com"),
    ("Vins Grands Crus",         "https://www.vinsgrandscrus.fr"),
    ("Cave des Grands Vins",     "https://www.cave-des-grands-vins.com"),
    ("Wineguru",                 "https://www.wineguru.fr"),
    ("Parcellaire",              "https://www.parcellaire.com"),
    ("Demain les Vins",          "https://www.demainlesvins.com"),
    ("Le Carré des Vins",        "https://www.lecarredesvins.com"),
    ("Mes Bourgognes Beaune",    "https://mesbourgognesbeaune.com"),
    ("Oenovinia",                "https://www.oenovinia.com"),
    ("Le Bourguignon",           "https://www.le-bourguignon.fr"),
    ("Les Caves",                "https://www.les-caves.fr"),
    ("Chais d'Oeuvre",           "https://www.chaisdoeuvre.fr"),
    ("Terres de Rouges",         "https://terresderouges.com"),
    ("La Route des Blancs",      "https://www.laroutedesblancs.com"),
    ("Cave Pur Jus",             "https://www.cavepurjus.com"),
    ("La Cave d'Ulysse",         "https://www.caveulysse.com"),
    ("La Cave de Lill",          "https://www.lacavedelill.fr"),
    ("Versus Wine",              "https://www.versus.wine"),
    ("Le Gros Caviste",          "https://legroscaviste.com"),
    ("Vinum Pro",                "https://vinum.pro"),
    ("Nouvelle Cave",            "https://nouvellecave.com"),
    ("Au Millésime",             "https://www.aumillesime.com"),
    ("La Champagnerie",          "https://www.la-champagnerie.com"),
    ("75 Centilitres",           "https://www.75-centilitres.fr"),
    ("Le 520",                   "https://le520.fr"),
    ("Cavissima",                "https://www.cavissima.com"),
    ("1Jour1Vin",                "https://www.1jour1vin.com"),
    ("Wine Shop Biarritz",       "https://www.wineshop-biarritz.fr"),
    ("Wine Shop Fronsac",        "https://wineshopfronsac.com"),
    ("Cave Briau",               "https://www.briau.com"),
    # ── Bordeaux & Gironde ──
    ("La Vinothèque de Bordeaux", "https://vinotheque-bordeaux.com"),
    ("La Crypte du Vin",          "https://lacrypteduvin.fr"),
    ("L'Intendant",               "https://intendant.com"),
    ("La CUV",                    "https://la-cuv.com"),
    ("Cousin & Compagnie",        "https://cousin.fr"),
    ("Cave Pourpre",              "https://cavepourpre.com"),
    ("La Cavisterie",             "https://lacavisterie.fr"),
    ("Le Pied à Terre",           "https://lepiedaterre-cave.com"),
    ("La Maison Gabin",           "https://1.lamaisongabin.com"),
    ("Amour du Vin",              "https://amourduvin.com"),
    ("La Cave des Darons",        "https://lacavedesdarons.com"),
    ("Vins et Terroir",           "https://vins-et-terroir.com"),
    # ── Landes & Pays Basque ──
    ("Cave Saint-Jean d'Août",    "https://cave-montdemarsan.fr"),
    ("Ardoneo",                   "https://vin-bio-ardoneo.com"),
    ("Au Chai Vous",              "https://auchaivous.com"),
    ("Vinothèque de Dax",         "https://vinotheque-dax.fr"),
    ("Plaisirs du Vin Dax",       "https://dax.plaisirsduvin.com"),
    ("La Bouteille 40",           "https://labouteille40.com"),
    ("La Cave 40 Narrosse",       "https://lacave40.fr"),
    # ── Pau & Béarn ──
    ("Caves Bacqué",              "https://cavesbacque.com"),
    ("Cave du Palais",            "https://cavedupalais.shop"),
    ("Cave Nobel",                "https://cave-nobel.com"),
    ("La Cave de Max",            "https://la-cave-de-max.fr"),
    ("Les 4 Pépins",              "https://les4pepins.com"),
    # ── Toulouse & Occitanie ──
    ("Domaine de Lastours",       "https://domaine-de-lastours.fr"),
    ("Des Bouchons",              "https://desbouchons.fr"),
    ("Boutique des Vins",         "https://boutiquedesvins.com"),
    ("Vins d'Une Oreille",        "https://vinsduneoreille.com"),
    ("Chai Vincent",              "https://chai-vincent.fr"),
    ("Le Comptoir des Vins",      "https://lecomptoirdesvins-toulouse.com"),
    ("Caves Amiel",               "https://caves-amiel.fr"),
    ("In Vino Fredo",             "https://invinofredo.fr"),
    ("Lacrima Vini",              "https://lacrimavini.fr"),
    ("Les 3 Caves Rive Gauche",   "https://les3caves-rivegauche.fr"),
    ("Sourire des Saveurs",       "https://souriredessaveurs.com"),
    ("Domaine Le Cellier",        "https://domainelecellier.fr"),
    ("Wine Notes",                "https://wine-notes.fr"),
    ("Vintage Select",            "https://vintageselect31.fr"),
    ("Cave de César",             "https://lacavedecesar.fr"),
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# ─────────────────────────────────────────────────────
# API SIRENE — Cavistes français avec site web
# ─────────────────────────────────────────────────────

def recuperer_cavistes_sirene():
    print("📡 Récupération cavistes via API SIRENE...")
    urls_sirene = {}
    page = 1
    total_avec_site = 0

    while True:
        try:
            resp = requests.get(
                "https://recherche-entreprises.api.gouv.fr/search",
                params={
                    "activite_principale": "47.25Z",
                    "page": page,
                    "per_page": 25,
                },
                timeout=15
            )
            data = resp.json()
            resultats = data.get("results", [])

            if not resultats:
                break

            for entreprise in resultats:
                nom = entreprise.get("nom_complet", "")
                for etab in entreprise.get("matching_etablissements", []):
                    site = etab.get("site_internet", "")
                    if site and site.startswith("http"):
                        urls_sirene[site.rstrip("/")] = nom
                        total_avec_site += 1
                        break

            total_pages = data.get("total_pages", 1)
            if page >= total_pages or page >= 50:
                break
            page += 1
            time.sleep(0.3)

        except Exception as e:
            print(f"⚠️  Erreur API SIRENE page {page}: {e}")
            break

    print(f"  ✅ {total_avec_site} cavistes avec site web trouvés via SIRENE")
    return urls_sirene

# ─────────────────────────────────────────────────────
# MÉMOIRE
# ─────────────────────────────────────────────────────

def charger_memoire():
    if FICHIER_MEMOIRE.exists():
        with open(FICHIER_MEMOIRE, "r") as f:
            return json.load(f)
    return {"detectes": [], "derniere_maj_sirene": ""}

def sauvegarder_memoire(memoire):
    with open(FICHIER_MEMOIRE, "w") as f:
        json.dump(memoire, f, ensure_ascii=False, indent=2)

def charger_urls_sirene():
    if FICHIER_URLS.exists():
        with open(FICHIER_URLS, "r") as f:
            return json.load(f)
    return {}

def sauvegarder_urls_sirene(urls):
    with open(FICHIER_URLS, "w") as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)

def est_nouveau(url, domaine, memoire):
    return f"{url}|{domaine}" not in memoire.get("detectes", [])

def marquer_vu(url, domaine, memoire):
    cle = f"{url}|{domaine}"
    if cle not in memoire["detectes"]:
        memoire["detectes"].append(cle)
    memoire["detectes"] = memoire["detectes"][-15000:]

# ─────────────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────────────

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

def scraper_site(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        texte_norm = normaliser(soup.get_text(separator=" "))
        return [d for d in DOMAINES if normaliser(d) in texte_norm]
    except:
        return []

# ─────────────────────────────────────────────────────
# ENVOI EMAIL
# ─────────────────────────────────────────────────────

def envoyer_alerte(nouveautes_prio, nouveautes_sirene):
    total = sum(len(d["domaines"]) for d in nouveautes_prio + nouveautes_sirene)
    if total == 0:
        return

    sujet = f"🍷 Alerte Cavistes — {total} nouveau(x) domaine(s) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
    corps_html = "<html><body style='font-family:Arial;'>"

    if nouveautes_prio:
        corps_html += """
        <h2 style="color:#722F37;">⭐ Cavistes Prioritaires</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;">
        <tr style="background:#722F37;color:white;"><th>Caviste</th><th>Domaine(s)</th><th>Lien</th></tr>
        """
        for d in nouveautes_prio:
            corps_html += f"""
            <tr>
                <td><b>{d['nom']}</b></td>
                <td>{'<br>'.join(f"🍷 {dom}" for dom in d['domaines'])}</td>
                <td><a href="{d['url']}">{d['url'][:55]}</a></td>
            </tr>"""
        corps_html += "</table>"

    if nouveautes_sirene:
        corps_html += """
        <h2 style="color:#8B4513;margin-top:20px;">🌍 Cavistes France (SIRENE)</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;">
        <tr style="background:#8B4513;color:white;"><th>Caviste</th><th>Domaine(s)</th><th>Lien</th></tr>
        """
        for d in nouveautes_sirene:
            corps_html += f"""
            <tr>
                <td><b>{d['nom']}</b></td>
                <td>{'<br>'.join(f"🍷 {dom}" for dom in d['domaines'])}</td>
                <td><a href="{d['url']}">{d['url'][:55]}</a></td>
            </tr>"""
        corps_html += "</table>"

    corps_html += f"<p style='color:gray;font-size:12px;'>Scan effectué le {datetime.now().strftime('%d/%m/%Y à %H:%M')}</p></body></html>"

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

# ─────────────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"🍷 SCAN CAVISTES UNIFIÉ — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}")
    print(f"  Cavistes prioritaires : {len(CAVISTES_PRIORITAIRES)}")
    print(f"  Domaines cibles       : {len(DOMAINES)}")
    print(f"{'='*55}\n")

    memoire = charger_memoire()

    # ── Cavistes prioritaires ──
    print("⭐ SCAN CAVISTES PRIORITAIRES")
    nouveautes_prio = []

    for nom, url in CAVISTES_PRIORITAIRES:
        print(f"  🔍 {nom}...")
        domaines = scraper_site(url)
        nouveaux = [d for d in domaines if est_nouveau(url, d, memoire)]
        if nouveaux:
            print(f"     🆕 {', '.join(nouveaux[:4])}")
            nouveautes_prio.append({"nom": nom, "domaines": nouveaux, "url": url})
            for d in nouveaux:
                marquer_vu(url, d, memoire)
        time.sleep(0.3)

    # ── Cavistes SIRENE ──
    print(f"\n🌍 SCAN CAVISTES FRANCE (SIRENE)")
    urls_sirene = charger_urls_sirene()

    # Recharge SIRENE une fois par semaine (lundi)
    aujourd_hui = datetime.now().strftime("%Y-%m-%d")
    derniere_maj = memoire.get("derniere_maj_sirene", "")
    if not urls_sirene or (aujourd_hui > derniere_maj and datetime.now().weekday() == 0):
        urls_sirene = recuperer_cavistes_sirene()
        sauvegarder_urls_sirene(urls_sirene)
        memoire["derniere_maj_sirene"] = aujourd_hui

    # Exclut les URLs déjà dans les prioritaires
    urls_prio = {url for _, url in CAVISTES_PRIORITAIRES}
    urls_a_scanner = {url: nom for url, nom in urls_sirene.items() if url not in urls_prio}
    print(f"   {len(urls_a_scanner)} sites supplémentaires à scanner\n")

    nouveautes_sirene = []
    for i, (url, nom) in enumerate(urls_a_scanner.items()):
        if i % 30 == 0 and i > 0:
            print(f"   Progression : {i}/{len(urls_a_scanner)}")
        domaines = scraper_site(url)
        nouveaux = [d for d in domaines if est_nouveau(url, d, memoire)]
        if nouveaux:
            print(f"  🆕 {nom} : {', '.join(nouveaux[:4])}")
            nouveautes_sirene.append({"nom": nom, "domaines": nouveaux, "url": url})
            for d in nouveaux:
                marquer_vu(url, d, memoire)
        time.sleep(0.3)

    sauvegarder_memoire(memoire)

    # ── Résumé ──
    total = sum(len(d["domaines"]) for d in nouveautes_prio + nouveautes_sirene)
    print(f"\n{'='*55}")
    print(f"RÉSULTAT : {total} nouveau(x) domaine(s)")
    print(f"  ⭐ Prioritaires : {sum(len(d['domaines']) for d in nouveautes_prio)}")
    print(f"  🌍 SIRENE       : {sum(len(d['domaines']) for d in nouveautes_sirene)}")
    print(f"{'='*55}\n")

    if nouveautes_prio or nouveautes_sirene:
        envoyer_alerte(nouveautes_prio, nouveautes_sirene)
    else:
        print("Aucune nouveauté — pas d'alerte envoyée.")

if __name__ == "__main__":
    main()
