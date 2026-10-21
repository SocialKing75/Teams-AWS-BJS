# Vérification et robustesse — Données 2023

- Écart max entre pipeline pandas et recalcul numpy sur 300 actions tirées au sort : 4.44e-16 yard
- Case la plus fermée (COVER_1_MAN × GO) recalculée par boucle Python : n = 473 (pipeline 473), fenêtre à l'arrivée = 1.740 (pipeline 1.74)
- Fenêtre moyenne à l'arrivée par résultat (C = complète, I = incomplète, IN = interceptée) : {'C': 4.24, 'I': 2.67, 'IN': 3.34} yd
- IC 95 % bootstrap (500 tirages) de la fenêtre à l'arrivée, cases de synthèse : {'MAN_COVERAGE / Courte (< 15 yd)': (2.93, 3.13), 'MAN_COVERAGE / Profonde (>= 15 yd)': (2.14, 2.47), 'ZONE_COVERAGE / Courte (< 15 yd)': (4.02, 4.15), 'ZONE_COVERAGE / Profonde (>= 15 yd)': (4.08, 4.46)}
- Stabilité première / seconde moitié de saison : 52 cases communes, corrélation de rang 0.945
- Seuil passe profonde = 10 yd, fenêtre à l'arrivée : {('MAN_COVERAGE', 'Courte (< 10 yd)'): 3.17, ('MAN_COVERAGE', 'Profonde (>= 10 yd)'): 2.33, ('ZONE_COVERAGE', 'Courte (< 10 yd)'): 4.15, ('ZONE_COVERAGE', 'Profonde (>= 10 yd)'): 4.1}
- Seuil passe profonde = 15 yd, fenêtre à l'arrivée : {('MAN_COVERAGE', 'Courte (< 15 yd)'): 3.02, ('MAN_COVERAGE', 'Profonde (>= 15 yd)'): 2.29, ('ZONE_COVERAGE', 'Courte (< 15 yd)'): 4.08, ('ZONE_COVERAGE', 'Profonde (>= 15 yd)'): 4.27}
- Seuil passe profonde = 20 yd, fenêtre à l'arrivée : {('MAN_COVERAGE', 'Courte (< 20 yd)'): 2.96, ('MAN_COVERAGE', 'Profonde (>= 20 yd)'): 2.14, ('ZONE_COVERAGE', 'Courte (< 20 yd)'): 4.12, ('ZONE_COVERAGE', 'Profonde (>= 20 yd)'): 4.16}
- Actions extrêmes (fenêtre > 15 yd ou vol > 3 s) : 178 (1.4 %) ; corrélation de rang des cases sans elles : 0.978
- Cases couverture × route retenues selon n_min : {15: 72, 30: 62, 50: 56}
