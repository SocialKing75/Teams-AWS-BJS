# Journal de bord — Fenêtre de réception (outil coach, données 2023)

## 2026-10-21 — Interface React, vidéo de démo, Vercel, fusion des branches

**Fait**
- Front relié au contrat d'équipe : `web/public/contrat/matchups.json` et `play.json` (écrits par `src/contrat.py`) ; cartes Adversaire rejouant l'action réelle, nouvel onglet Matrice (Σ somme / Σ n, cases n < 10 grisées, fiche avec IC).
- Écran d'ouverture noir NFL | AWS qui s'ouvre en deux volets ; favicon NFL ; version PC (plan de match complet, Man/zone sur 4 colonnes, contenu centré 1440 px) ; « Données 2023 » retiré de l'en-tête (gardé en pied de page).
- Matrice : libellés de filtres explicites, fiche fermée au changement de filtre et par Échap ; cartes et plan de jeu sans arrondi ni bordure colorée (`web/src/App.jsx`, `web/src/styles.css`).
- Vidéo motion design `outputs/demo_app.mp4` (1920×1080, 73 s) générée par `video/enregistrer_demo.py` + `video/studio.html`, chiffres lus dans l'app.
- Hébergement : https://fenetre-reception-coach.vercel.app (`web/vercel.json`, `web/.vercelignore`, déploiement par la CLI).
- Git : commit de joe, fusion de joe puis de stephane dans main en local (historiques séparés) ; journal de bord et cache `.vite/` ajoutés au `.gitignore`.

**Décisions**
- Push laissé à l'utilisateur (interdiction de commit/push levée uniquement pour la fusion).
- README de stephane renommé `README-KIRO.md` ; sous-module `nfl-big-data-bowl-regional-event-data` (sans `.gitmodules`) retiré de la fusion.

**Problèmes**
- Audit d'intégration : une panne de chargement du contrat n'est pas signalée dans l'UI (App.jsx, fetch → `[]`) ; arrondis faits avant calcul (metrique.py:147, export_web.py:48) ; `.pyc` de `src/__pycache__/` commités par erreur.

**Prochaines étapes**
- Pousser main et joe (`git push origin main joe`), avec `.gitignore` et `styles.css` encore non commités.
- Corriger la P1 de l'audit (message d'erreur si le contrat ne charge pas), puis les arrondis (P2).
- Voir avec Stéphane le contenu prévu du sous-module retiré.
