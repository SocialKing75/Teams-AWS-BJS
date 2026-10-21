# NFL Coach Cockpit - Analyse des Fenêtres de Réception

https://github.com/user-attachments/assets/VOTRE_VIDEO_ID

**Problématique :** Les entraîneurs NFL ont besoin d'analyser en temps réel la vitesse de fermeture des fenêtres de réception pour optimiser les décisions de passes. **Solution :** Dashboard React avec analyse prédictive (DuckDB + Plotly) ciblant 3 personas (Coach, Scout, Broadcast) affichant separation, closing velocity et risk scores avec replay 2D synchronisé. **Installation :** `npm install && npm run dev` (nécessite Node 18+, DuckDB via MCP). **Architecture :** Pipeline ETL (tracking NFL → normalization angles 0°=Nord → physics validation v≤13yd/s, a≤8yd/s² → agrégation DuckDB → visualisation React). **Démo live :** [Fenêtre de réception Coach](https://fenetre-reception-coach.vercel.app/)
