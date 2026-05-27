# CONTEXTE — Système de veille vins Sébastien Garat
Dernière mise à jour : 27/05/2026

## Repo GitHub
https://github.com/sebastienvinsalertes-ux/alertes-vin

## Ce que fait ce système
Surveillance automatique de cavistes, ventes privées, Gmail et enchères pour détecter les domaines cibles (81 domaines de grands vins). Alertes par email à sebastiengarat64@gmail.com.

**Scans cavistes/ventes/Gmail : 4x/jour** — 10h, 12h, 17h, 19h (heure Paris UTC+2)
**Scan enchères : 1x/jour** — 9h (heure Paris UTC+2)

## Scripts actifs
- `script_cavistes_unifie.py` : scan 100 cavistes, emails par batch de 30 max
- `script_ventes_privees.py` : scan 31 sites ventes privées, mémoire persistante, lien direct
- `script_scan_gmail.py` : scan inbox Gmail newsletters/ventes, lien direct Gmail + liens produits
- `script_encheres.py` : scan iDealwine, Catawiki, Interenchères, eBay France — email séparé
- `script_instagram_rss.py` : scan RSS blogs cavistes (NE fait PAS Instagram — à retravailler)
- `.github/workflows/alertes.yml` : 4 runs/jour, commit mémoire automatique, keep-alive
- `.github/workflows/encheres.yml` : 1 run/jour à 9h, mémoire enchères
- `.github/workflows/trigger.yml` : backup déclenchement workflow principal

## Scripts supprimés
- `script_cavistes_france.py` (doublon supprimé)
- `script_cavistes_prioritaires.py` (doublon supprimé)

## Fichiers mémoire (commités automatiquement après chaque run)
- `memoire_cavistes.json`
- `memoire_ventes_privees.json`
- `memoire_gmail.json`
- `memoire_encheres.json`

## Fichier Excel de référence
`cavistes_fusion_final_MAJ.xlsx` — 8 onglets dont :
- ⭐ VIP Confirmés (44 cavistes, 17 avec site web)
- 🔍 Site + Domaines Détectés (42 cavistes)
- 🌐 Site Web À Scanner (48 cavistes)
- Colonne Instagram mise à jour (6 comptes renseignés)
Total : 100 cavistes avec site web, dédupliqués

## Comptes ouverts — enchères
- iDealwine
- Catawiki
- Interenchères
- Drouot
- Baghera/Wines
- Acker

## Problèmes résolus
- Mémoire repartait à zéro → fichiers JSON commités dans le repo
- Emails trop gros bloqués → batch 30 cavistes max par email
- Doublons entre scripts → scripts France et Prioritaires supprimés
- SIRENE supprimé → liste manuelle uniquement
- Liens directs vers produits ajoutés dans les 3 scripts
- Email envoyé à chaque run même si RAS
- Scans automatiques qui sautaient → keep-alive + trigger.yml ajoutés
- Keep-alive conflit push → corrigé avec needs:scan + git pull rebase
- Script enchères créé et testé → email RAS reçu ✅
- Fichier Excel mis à jour avec comptes Instagram

## Règles importantes
- NE PAS modifier la liste DOMAINES dans les scripts
- Ajouter un caviste = ajouter une ligne dans CAVISTES dans `script_cavistes_unifie.py`
- En octobre : ajuster les crons dans `alertes.yml` ET `encheres.yml` (heure d'hiver UTC+1)
- Les valeurs UTC hiver sont déjà commentées dans les deux fichiers

## À FAIRE — prochaine session
- Diagnostic scraping : ajouter logs détaillés pour vérifier ce que chaque site retourne vraiment
- Vérifier site par site lesquels sont réellement scannés vs bloqués
- `script_instagram_rss.py` : renommer en `script_rss_blogs.py`, améliorer, ajouter au workflow
- Instagram : Apify token à retrouver, email illisible à corriger, budget $5/$5 épuisé
- Nouvelles sources enchères à ajouter : Drouot, Baghera, Aguttes
- VPS à envisager si ponctualité des scans devient critique (retards GitHub Actions)
- Scan prix cavistes (à venir)
- Ajout ponctuel de cavistes manuellement ou via pages web fournies
