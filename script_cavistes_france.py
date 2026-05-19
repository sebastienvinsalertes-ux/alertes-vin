import requests
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

SERPAPI_KEY      = os.environ.get("SERPAPI_KEY", "")
GMAIL_EXPEDITEUR = "sebastien.vins.alertes@gmail.com"
GMAIL_PASSWORD   = os.environ.get("GMAIL_PASSWORD", "")
DESTINATAIRE     = "sebastiengarat64@gmail.com"

# Mémoire des détections précédentes
FICHIER_MEMOIRE  = Path("cavistes_france_deja_detectes.json")

# ─────────────────────────────────────────────
# 64 DOMAINES CIBLES — groupés par 8
# pour minimiser le nombre de requêtes
# 8 groupes x 1 recherche = 8 recherches/scan
# 2 scans/jour = 16 recherches/jour
# ─────────────────────────────────────────────

GROUPES_DOMAINES = [
    ["Roumier", "Raveneau", "Dauvissat", "Selosse", "Leflaive", "Coche Dury", "DRC", "Romanee Conti"],
    ["Rousseau", "Leroy", "Dujac", "Mugnier", "Liger Belair", "Meo Camuzet", "Arnoux Lachaux", "Mugneret Gibourg"],
    ["Chave", "Clape", "Allemand", "Gonon", "Gangloff", "Grange des Peres", "Rayas", "Reynaud"],
    ["Dagueneau", "Savart", "Chartogne Taillet", "Pierre Peters", "Selosse", "Roses de Jeanne", "Nowack", "Lurquin"],
    ["Hubert Lamy", "Sauzet", "Ramonet", "Comtes Lafon", "Bizot", "Cecile Tremblay", "Prieure Roch", "Labet"],
    ["Foillard", "Dancer", "Guiberteau", "Barthod", "Anne Gros", "Auvenay", "Clos Rougeard", "Guffens"],
    ["Henri Boillot", "Caroline Morey", "PYCM", "Jacques Carillon", "Paul Pillot", "Hubert Lamy", "Richard Leroy", "Gavenat"],
    ["Anglore", "Bizot", "Chaillon Alexandre", "Elise Bougy", "Gaspard Brochet", "Jules Brochet", "La Rogerie", "Tino Kuban"],
]

# Mots clés pour cibler les cavistes français
MOTS_CLES_CAVISTE = "caviste france vin vente stock"

# ─────────────────────────────────────────────
# MEMOIRE
# ─────────────────────────────────────────────

def charger_memoire():
    if FICHIER_MEMOIRE.exists():
        with open(FICHIER_MEMOIRE, "r") as f:
            return json.load(f)
    return {}

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
    # Garde max 5000 entrées
    memoire["detectes"] = memoire["detectes"][-5000:]

# ─────────────────────────────────────────────
# UTILITAIRES
# ─────────────────────────────────────────────

def normaliser(texte):
    return unicodedata.normalize("NFD", str(texte)).encode("ascii", "ignore").decode().lower()

def est_caviste_pertinent(url, titre, snippet):
    """Filtre les résultats non pertinents."""
    texte = normaliser(f"{url} {titre} {snippet}")
    # Exclure Wikipedia, blogs, presse généraliste
    exclusions = ["wikipedia", "tripadvisor", "pagesjaunes", "leboncoin",
                  "vinatis", "idealwine", "millesima", "vinogusto"]
    if any(ex in texte for ex in exclusions):
        return False
    # Inclure si ça ressemble à un caviste/boutique
    inclusions = ["caviste", "cave", "vin", "boutique", "shop", "vente",
                  "stock", "achat", "bouteille", "millésime"]
    return any(inc in texte for inc in inclusions)

# ─────────────────────────────────────────────
# RECHERCHE SERPAPI
# ─────────────────────────────────────────────

def rechercher_groupe(domaines):
    """Fait une recherche Google pour un groupe de domaines."""
    query = " OR ".join(f'"{d}"' for d in domaines)
    query += f" {MOTS_CLES_CAVISTE}"

    params = {
        "engine": "google",
        "q": query,
        "hl": "fr",
        "gl": "fr",
        "num": 10,
        "api_key": SERPAPI_KEY,
    }

    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("organic_results", [])
    except Exception as e:
        print(f"⚠️  Erreur SerpAPI : {e}")
        return []

# ─────────────────────────────────────────────
# ENVOI EMAIL
# ─────────────────────────────────────────────

def envoyer_alerte(nouveautes):
    if not nouveautes:
        return

    total = len(nouveautes)
    sujet = f"🌍 Alerte Cavistes France — {total} nouveau(x) résultat(s) — {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    corps_html = """
    <html><body>
    <h2 style="color:#8B4513;">🌍 Nouveaux cavistes français détectés</h2>
    <p>Ces cavistes mentionnent vos domaines cibles :</p>
    <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;font-family:Arial;width:100%;">
      <tr style="background:#8B4513;color:white;">
        <th>Domaine(s)</th>
        <th>Caviste</th>
        <th>Extrait</th>
        <th>Lien</th>
      </tr>
    """

    for d in nouveautes:
        corps_html += f"""
      <tr>
        <td><b>{'<br>'.join(f"🍷 {dom}" for dom in d['domaines'])}</b></td>
        <td>{d['titre']}</td>
        <td><i>{d['snippet'][:150]}...</i></td>
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
        print(f"✅ Email envoyé : {total} nouveau(x) résultat(s)")
    except Exception as e:
        print(f"❌ Erreur envoi email : {e}")

# ─────────────────────────────────────────────
# PROGRAMME PRINCIPAL
# ─────────────────────────────────────────────

def main():
    print(f"\n{'='*55}")
    print(f"🌍 SCAN CAVISTES FRANCE — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}")
    print(f"  Groupes de domaines : {len(GROUPES_DOMAINES)}")
    print(f"  Recherches SerpAPI  : {len(GROUPES_DOMAINES)}")
    print(f"{'='*55}\n")

    memoire = charger_memoire()
    toutes_nouveautes = []

    for i, groupe in enumerate(GROUPES_DOMAINES):
        print(f"🔍 Recherche groupe {i+1}/{len(GROUPES_DOMAINES)} : {', '.join(groupe[:3])}...")
        resultats = rechercher_groupe(groupe)
        print(f"   → {len(resultats)} résultat(s) Google")

        for r in resultats:
            url     = r.get("link", "")
            titre   = r.get("title", "")
            snippet = r.get("snippet", "")

            if not est_caviste_pertinent(url, titre, snippet):
                continue

            # Identifie quels domaines du groupe apparaissent dans ce résultat
            texte_norm = normaliser(f"{titre} {snippet}")
            domaines_trouves = []
            for domaine in groupe:
                if normaliser(domaine) in texte_norm:
                    domaines_trouves.append(domaine)

            if not domaines_trouves:
                continue

            # Filtre les nouveautés
            nouveaux_domaines = [d for d in domaines_trouves if est_nouveau(url, d, memoire)]

            if nouveaux_domaines:
                print(f"   🆕 {', '.join(nouveaux_domaines)} → {titre[:50]}")
                toutes_nouveautes.append({
                    "domaines": nouveaux_domaines,
                    "titre":    titre,
                    "snippet":  snippet,
                    "url":      url,
                })
                for d in nouveaux_domaines:
                    marquer_vu(url, d, memoire)

    sauvegarder_memoire(memoire)

    print(f"\n{'='*55}")
    print(f"RÉSULTAT : {len(toutes_nouveautes)} nouveau(x) résultat(s)")
    print(f"{'='*55}\n")

    if toutes_nouveautes:
        envoyer_alerte(toutes_nouveautes)
    else:
        print("Aucune nouveauté — pas d'alerte envoyée.")

if __name__ == "__main__":
    main()
