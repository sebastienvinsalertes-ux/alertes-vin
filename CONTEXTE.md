# CONTEXTE.md — Alertes Vin
Dernière mise à jour : 31/07/2026

---

## Session du 31/07/2026 — corrections critiques (via Claude Code)

### 1. Bug ventes privées corrigé
`script_ventes_privees.py` déclenchait des alertes sur de simples mentions
catalogue/statiques (domaine + mot "vente privée" à proximité), pas sur de
vraies nouvelles ventes. Corrections :
- Exige désormais un signal de nouveauté réel (date, "jusqu'au", compte à
  rebours...) EN PLUS du mot-clé, dans la même fenêtre de texte.
- Clé mémoire basée sur une empreinte du contenu détecté (domaine + hash du
  passage), plus sur l'URL fixe du site — une vraie nouvelle vente sur un
  domaine déjà vu redéclenche maintenant correctement une alerte.
- 2 sites confirmés morts (crash SSL, déjà identifiés le 28/05) retirés :
  La Grande Cave, Les Bons Plans du Vin.
- Étape "Scan ventes privées" réactivée dans `alertes.yml`.

### 2. Bug critique découvert : la mémoire n'a JAMAIS été sauvegardée
Contrairement à ce qu'indiquait cette page ("problème résolu"), les fichiers
`memoire_*.json` n'existaient **dans aucun commit du repo**, sur aucun run,
depuis le début. Cause : le `GITHUB_TOKEN` automatique fourni aux workflows
n'a pas de permission d'écriture par défaut, et aucun bloc `permissions:`
n'était déclaré dans les .yml — donc chaque `git push` en fin de run échouait
silencieusement (masqué par `|| true`), même si le job entier s'affichait
"success" sur GitHub. **Conséquence probable** : le système a pu re-scanner
et potentiellement re-alerter sans aucune mémoire persistante d'un run à
l'autre depuis sa création.

Fix : ajout de `permissions: contents: write` dans `alertes.yml` et
`encheres.yml`. Vérifié en conditions réelles le 31/07/2026 : commit mémoire
`afa05fe` poussé avec succès sur `main`.

### 3. Point de vigilance restant
3 sites de la liste ventes privées renvoient une erreur HTTP 403 lors du
scan (bloquent les requêtes simples, pas de vrai CAPTCHA) : Le Clos Privé,
Vins Grands Crus, La Route des Blancs. Le script les ignore proprement
(catch + log), mais ils ne sont donc jamais réellement scannés. À
approfondir si besoin (rotation de user-agent, ou accepter qu'ils restent
hors scope pour ce script).

### 4. Accès
Un token GitHub fine-grained ("Claude Code", repo `alertes-vin` uniquement,
permissions Contents + Workflows + Actions en Read/write) a été créé pour
permettre les interventions directes. Expire le 30/08/2026.

---

## Repo GitHub
https://github.com/sebastienvinsalertes-ux/alertes-vin

---

## Ce que fait ce système
Surveillance automatique de cavistes, ventes privées, Gmail et enchères pour détecter les domaines cibles (81 domaines de grands vins). Alertes par email à sebastiengarat64@gmail.com.

- Scans cavistes/ventes/Gmail : 4x/jour — 10h, 12h, 17h, 19h (heure Paris)
- Scan enchères : 1x/jour — 9h (heure Paris)

---

## Déclenchement — IMPORTANT
**Les crons GitHub Actions ont été abandonnés** (trop peu fiables, retards de plusieurs heures, runs groupés la nuit).

**Nouveau système : cron-job.org** déclenche les workflows via l'API GitHub (`workflow_dispatch`). Fiable à la minute près.

### 5 jobs actifs sur cron-job.org :
| Job | Workflow | Heure Paris |
|-----|----------|-------------|
| Alertes Vins 10h | `alertes.yml` | 10h00 |
| Alertes Vins 12h | `alertes.yml` | 12h00 |
| Alertes Vins 17h | `alertes.yml` | 17h00 |
| Alertes Vins 19h | `alertes.yml` | 19h00 |
| Enchères 9h | `encheres.yml` | 09h00 |

**En octobre (heure d'hiver)** : ajuster les horaires sur cron-job.org uniquement (plus rien à toucher dans les .yml).

---

## Scripts actifs

- `script_cavistes_unifie.py` : scan **80 cavistes** (était 100 — 20 sites morts/bloqués supprimés le 28/05/2026), emails par batch de 30 max
- `script_ventes_privees.py` : scan 31 sites ventes privées, mémoire persistante, lien direct
- `script_scan_gmail.py` : scan inbox Gmail newsletters/ventes, lien direct Gmail + liens produits
- `script_encheres.py` : scan **7 sources** — iDealwine, Catawiki, Interenchères, eBay France, Drouot, Baghera/Wines, Aguttes — email séparé
- `script_instagram_rss.py` : scan RSS blogs cavistes (NE fait PAS Instagram — en attente de décision)
- `script_diagnostic.py` : diagnostic scraping site par site — à lancer manuellement via workflow `diagnostic.yml` — retourne un rapport email détaillé
- `.github/workflows/alertes.yml` : workflow_dispatch uniquement (plus de schedule), déclenché par cron-job.org
- `.github/workflows/encheres.yml` : workflow_dispatch uniquement, déclenché par cron-job.org
- `.github/workflows/diagnostic.yml` : workflow_dispatch manuel uniquement

---

## Scripts supprimés
- `script_cavistes_france.py` (doublon supprimé)
- `script_cavistes_prioritaires.py` (doublon supprimé)
- `.github/workflows/trigger.yml` (supprimé — remplacé par cron-job.org)

---

## Fichiers mémoire (commités automatiquement après chaque run)
- `memoire_cavistes.json`
- `memoire_ventes_privees.json`
- `memoire_gmail.json`
- `memoire_encheres.json`

---

## Fichier Excel de référence
`cavistes_fusion_final_MAJ.xlsx` — 8 onglets dont :
- ⭐ VIP Confirmés (44 cavistes, 17 avec site web)
- 🔍 Site + Domaines Détectés (42 cavistes)
- 🌐 Site Web À Scanner (48 cavistes)
- Colonne Instagram mise à jour (6 comptes renseignés)
Total : 80 cavistes actifs avec site web, dédupliqués et nettoyés

---

## 20 sites supprimés le 28/05/2026
Suite au diagnostic scraping (`script_diagnostic.py`) :

| Site | Raison |
|------|--------|
| Caves Amiel | 💀 Crash SSL |
| Le Temps des Vendanges | 💀 Crash SSL |
| Badie | 💀 Crash SSL |
| Les Bons Plans du Vin | 💀 Crash SSL |
| La Grande Cave | 💀 Crash SSL |
| Philovino | 💀 Crash SSL |
| L'Intendant | 💀 Crash SSL |
| La Cavisterie | 💀 Crash SSL |
| Vins et Terroir | 💀 Crash SSL |
| Au Chai Vous | 💀 Crash SSL |
| La Champagnerie | 💀 Crash SSL |
| La Cave d'Ulysse | 💀 Crash SSL |
| Cave Spirituelle | 🚫 Cloudflare 403 |
| La CUV | 🚫 Cloudflare 403 |
| Sourire des Saveurs | 🚫 Cloudflare 403 |
| 75 Centilitres | 🚫 403 |
| La Cave de Max | ⚠️ JS requis |
| Le 520 | ⚠️ JS requis |
| Domaine Le Cellier | ⏱️ Timeout |
| Cousin & Compagnie | ❌ HTTP 500 |

---

## Sources enchères (7 au total)
- iDealwine ✅
- Catawiki ✅
- Interenchères ✅
- eBay France ✅
- Drouot (via gazette-drouot.com) — ajouté 28/05/2026
- Baghera/Wines — ajouté 28/05/2026
- Aguttes — ajouté 28/05/2026

Comptes ouverts : iDealwine, Catawiki, Interenchères, Drouot, Baghera/Wines, Acker

---

## Problèmes résolus
- Mémoire repartait à zéro → fichiers JSON commités dans le repo
- Emails trop gros bloqués → batch 30 cavistes max par email
- Doublons entre scripts → scripts France et Prioritaires supprimés
- SIRENE supprimé → liste manuelle uniquement
- Liens directs vers produits ajoutés dans les 3 scripts
- Email envoyé à chaque run même si RAS
- Scans automatiques qui sautaient → migré vers cron-job.org ✅
- Keep-alive conflit push → supprimé (inutile avec cron-job.org)
- trigger.yml supprimé (inutile avec cron-job.org)
- Script enchères créé et testé → email RAS reçu ✅
- 20 sites morts/bloqués supprimés → diagnostic scraping ✅
- Bug stats cavistes corrigé (None vs [] pour les erreurs) ✅
- 3 nouvelles sources enchères ajoutées ✅

---

## Règles importantes
- NE PAS modifier la liste DOMAINES dans les scripts
- Ajouter un caviste = ajouter une ligne dans CAVISTES dans `script_cavistes_unifie.py`
- En octobre : ajuster les horaires sur **cron-job.org** uniquement (pas les .yml)
- Relancer le diagnostic (`diagnostic.yml`) après tout ajout de cavistes

---

## À FAIRE — prochaine session
- Instagram stories : relancer Apify (~$5/mois) pour surveiller les 6 comptes VIP — en attente de décision
- Vérifier que Drouot, Baghera, Aguttes remontent bien des résultats (premiers runs)
- `script_instagram_rss.py` : renommer en `script_rss_blogs.py` si on décide de garder le RSS
- Nouvelles sources enchères à envisager : Acker
- VPS à envisager si ponctualité critique (cron-job.org gratuit = fiable mais limité)
- Ajout ponctuel de cavistes manuellement ou via pages web fournies
- Scan prix cavistes (à venir)
