# CONTEXTE — Système de veille vins Sébastien Garat

## Repo GitHub
https://github.com/sebastienvinsalertes-ux/alertes-vin

## Ce que fait ce système
Surveillance automatique de cavistes et ventes privées pour détecter
les domaines cibles (64 domaines de grands vins).
Alertes par email à sebastiengarat64@gmail.com.
4 scans/jour : 10h, 12h, 17h, 19h (heure Paris, heure d'été UTC+2).

## Scripts actifs
- script_cavistes_unifie.py : scan 100 cavistes, emails par batch de 30
- script_ventes_privees.py : scan 31 sites de ventes privées
- script_scan_gmail.py : scan inbox Gmail des newsletters/ventes privées
- .github/workflows/alertes.yml : orchestration GitHub Actions

## Scripts supprimés
- script_cavistes_france.py (doublon)
- script_cavistes_prioritaires.py (doublon)

## Fichiers mémoire (commités automatiquement)
- memoire_cavistes.json
- memoire_ventes_privees.json
- memoire_gmail.json

## Fichier Excel de référence
cavistes_fusion_final.xlsx — 8 onglets dont :
- ⭐ VIP Confirmés (44 cavistes)
- 🔍 Site + Domaines Détectés (42 cavistes)
- 🌐 Site Web À Scanner (48 cavistes)

## Règles importantes
- NE PAS modifier la liste DOMAINES dans les scripts
- Ajouter un caviste = ajouter une ligne dans CAVISTES dans script_cavistes_unifie.py
- En octobre : ajuster les crons dans alertes.yml (heure d'hiver UTC+1)

## Prochaines évolutions prévues
- Scan prix (à venir)
- Ajout ponctuel de cavistes manuellement ou via pages web à scanner
