# CONTEXTE — Système de veille vins Sébastien Garat
## Dernière mise à jour : 25/05/2026

## Repo GitHub
https://github.com/sebastienvinsalertes-ux/alertes-vin

## Ce que fait ce système
Surveillance automatique de cavistes et ventes privées pour détecter
les domaines cibles (81 domaines de grands vins).
Alertes par email à sebastiengarat64@gmail.com.
4 scans/jour : 10h, 12h, 17h, 19h (heure Paris, heure d'été UTC+2).

## Scripts actifs
- script_cavistes_unifie.py : scan 100 cavistes, emails par batch de 30 max
- script_ventes_privees.py : scan 31 sites ventes privées, mémoire persistante, lien direct
- script_scan_gmail.py : scan inbox Gmail newsletters/ventes, lien direct Gmail + liens produits
- script_instagram_rss.py : scan RSS blogs cavistes (NE fait PAS Instagram — à retravailler)
- .github/workflows/alertes.yml : 4 runs/jour, commit mémoire automatique

## Scripts supprimés
- script_cavistes_france.py (doublon supprimé)
- script_cavistes_prioritaires.py (doublon supprimé)

## Fichiers mémoire (commités automatiquement après chaque run)
- memoire_cavistes.json
- memoire_ventes_privees.json
- memoire_gmail.json

## Fichier Excel de référence
cavistes_fusion_final.xlsx — 8 onglets dont :
- ⭐ VIP Confirmés (44 cavistes, 17 avec site web)
- 🔍 Site + Domaines Détectés (42 cavistes)
- 🌐 Site Web À Scanner (48 cavistes)
Total : 100 cavistes avec site web, dédupliqués

## Problèmes résolus
- Mémoire repartait à zéro → fichiers JSON commités dans le repo
- Emails trop gros bloqués → batch 30 cavistes max par email
- Doublons entre scripts → scripts France et Prioritaires supprimés
- SIRENE supprimé → liste manuelle uniquement
- Liens directs vers produits ajoutés dans les 3 scripts
- Email envoyé à chaque run même si RAS

## Règles importantes
- NE PAS modifier la liste DOMAINES dans les scripts
- Ajouter un caviste = ajouter une ligne dans CAVISTES dans script_cavistes_unifie.py
- En octobre : ajuster les crons dans alertes.yml (heure d'hiver UTC+1)
- Les valeurs UTC hiver sont déjà commentées dans alertes.yml

## À FAIRE — prochaine session
- script_instagram_rss.py : renommer en script_rss_blogs.py, améliorer, ajouter au workflow
- Instagram : on avait fait quelque chose avec Apify — retrouver le token et reprendre
- Nouvelles sources à explorer : Le Bon Coin, eBay, Wine-Searcher, enchères (Drouot, Catawiki)
- Scan prix (à venir)
- Ajout ponctuel de cavistes manuellement ou via pages web fournies
