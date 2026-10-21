# 🏈 Coach Cockpit NFL

> Analyse tactique des fenêtres de réception pour coordinateurs offensifs NFL

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.0%2B-61dafb.svg)](https://reactjs.org/)
[![DuckDB](https://img.shields.io/badge/DuckDB-MCP-yellow.svg)](https://duckdb.org/)
[![Kiro](https://img.shields.io/badge/Kiro-Powered-purple.svg)](https://kiro.dev/)

---

## 🎯 Problématique

**« Dans quelles situations tactiques la fenêtre de réception se referme-t-elle le moins (ou le plus vite) ? »**

Ce projet analyse les données de tracking NFL (Next Gen Stats) pour calculer le **taux d'érosion de la fenêtre de réception** (Δd/Δt entre receveur et défenseur) durant la phase de vol du ballon.

---

## 🚀 Démarrage Rapide

### Prérequis
- Python 3.9+
- Node.js 18+
- Git

### Installation

```bash
# Cloner le projet avec données
git clone --recursive https://github.com/your-org/coach-cockpit-nfl.git
cd coach-cockpit-nfl

# Installation Python
pip install pandas numpy scipy matplotlib pytest

# Installation React (optionnel pour interface)
npm install

# Valider données
python scripts/validate_physics.py --tracking-file nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv
```

### Premiers Pas avec Kiro

```bash
# Ouvrir dans Kiro IDE
kiro .

# Dans le chat Kiro:
# "Utilise le skill nfl-geometry pour normaliser le fichier tracking_2021091200.csv"
```

📖 **Guide Complet** : Voir [`.kiro/GETTING-STARTED.md`](.kiro/GETTING-STARTED.md)

---

## 📂 Structure du Projet

```
.
├── .kiro/                      # Configuration Kiro
│   ├── AGENTS.md              # Constitution & Invariants Physiques
│   ├── PLAN.md                # Feuille de route (6 semaines)
│   ├── specs/                 # Requirements EARS
│   ├── skills/                # Skills Kiro (nfl-geometry, react-coach-ui)
│   └── hooks/                 # Validation automatique (physics-guardrail)
│
├── nfl-big-data-bowl-regional-event-data/
│   └── data/                  # Données NFL (submodule)
│       ├── tracking/          # 122 fichiers CSV (10 Hz GPS)
│       ├── plays.csv
│       └── pffScoutingData.csv
│
├── scripts/
│   └── validate_physics.py    # Script validation contraintes
│
├── src/                       # Code source (à créer via Kiro)
│   ├── engine/                # Moteur calcul (isolation, closing_rate)
│   └── components/            # Composants React (Heatmap, TimeSeries)
│
└── tests/                     # Tests unitaires
```

📖 **Détails** : Voir [`PROJECT-STRUCTURE.md`](PROJECT-STRUCTURE.md)

---

## 🎨 Livrables

### 1. Moteur de Calcul Python
- **Isolation Phase de Vol** : Extraire frames entre `pass_release` et `ball_land`
- **Closing Rate** : Calculer Δd/Δt entre WR et CB (yards/seconde)
- **Agrégation** : Statistiques par type de route (slant, go, out, etc.)

### 2. Interface React
- **Heatmap** : Routes × CB Alignment → Closing Rate moyen (Plotly.js)
- **TimeSeries** : Distance et Closing Rate vs Temps (Recharts)
- **Animation 2D** : Terrain NFL avec trajectoires joueurs

### 3. Intégration DuckDB
- Requêtes SQL via MCP (Model Context Protocol)
- Jointures tracking + plays + pffScoutingData
- Performance : < 500ms pour analyser 1 jeu

---

## 🧪 Validation Physique

Le projet intègre des **garde-fous physiques** pour garantir la cohérence des données :

| Contrainte | Valeur Limite | Référence |
|------------|---------------|-----------|
| Vitesse maximale | 13.0 yards/s (~23 mph) | Record NFL (Tyreek Hill) |
| Accélération max | 8.0 yards/s² | Biomécanique sprint |
| Dimensions terrain | 120 × 53.3 yards | Règlement NFL |

**Hook Automatique** : Le hook `physics-validation` s'exécute après chaque édition de fichier Python pour valider les constantes.

---

## 🛠️ Technologies

### Backend
- **Python 3.9+** : pandas, numpy, scipy
- **DuckDB** : Requêtes SQL haute performance sur CSV

### Frontend
- **React 18** : Vite, TypeScript
- **Plotly.js** : Heatmaps interactives
- **Recharts** : Graphiques temporels
- **Tailwind CSS** : Styling

### DevOps
- **Kiro AI** : Skills, Specs, Hooks automatiques
- **Pytest** : Tests unitaires Python
- **Vitest** : Tests composants React

---

## 📊 Exemple d'Utilisation

### Cas d'Usage : "Quelles routes battent Cover 2 ?"

```python
# 1. Charger données
import pandas as pd
from src.engine.closing_rate import calculate_closing_rate

tracking = pd.read_csv('data/tracking/tracking_2021091200.csv')
plays = pd.read_csv('data/plays.csv')
pff = pd.read_csv('data/pffScoutingData.csv')

# 2. Filtrer Cover 2
cover2_plays = pff[pff['pff_coverageType'] == 'Cover 2']

# 3. Calculer closing rates par route
results = {}
for route_type in ['slant', 'go', 'out', 'corner', 'post']:
    route_plays = cover2_plays[cover2_plays['pff_routeConcept'] == route_type]
    # ... (voir .kiro/PLAN.md Phase 2 pour code complet)
    results[route_type] = avg_closing_rate

# 4. Visualiser avec Plotly
import plotly.express as px
fig = px.bar(x=results.keys(), y=results.values(), 
             title='Closing Rate par Route contre Cover 2')
fig.show()
```

**Résultat Attendu** :
- Routes "go" et "post" : Closing rate < -1.5 (fenêtre reste ouverte)
- Routes "slant" contre Cover 2 : Closing rate ~ -3.0 (fermeture rapide)

---

## 🤖 Développement avec Kiro

### Skills Disponibles

#### `nfl-geometry`
Fonctions géométriques & physiques NFL :
- `normalize_play_direction()` : Attaque vers droite
- `nfl_to_math_radians()` : Conversion angles
- `compute_closing_rate()` : Calcul Δd/Δt

**Activation** :
```
Kiro, utilise le skill nfl-geometry pour calculer la distance entre deux joueurs
```

#### `react-coach-ui`
Templates composants React :
- `<HeatmapMatchup />` : Heatmap Plotly
- `<TimeSeriesClosing />` : Graphiques Recharts
- `useNFLData()` : Fetch DuckDB

**Activation** :
```
Kiro, crée le composant <HeatmapMatchup /> selon le skill react-coach-ui
```

📖 **Documentation** : Voir [`.kiro/skills/`](.kiro/skills/)

---

### Specs EARS

Format de requirements structuré :

```
[REQ-ENGINE-1 : Isolation de la Phase de Vol]
WHEN le jeu atteint l'événement 'pass_release',
THE SYSTEM SHALL isoler les coordonnées du WR ciblé jusqu'à 'ball_land'.
```

**Usage** :
```
Kiro, implémente REQ-ENGINE-1 de la spec coach-cockpit
```

📖 **Spec Complète** : Voir [`.kiro/specs/coach-cockpit/spec.md`](.kiro/specs/coach-cockpit/spec.md)

---

## 🧪 Tests

```bash
# Tests Python
pytest tests/ -v --cov=src

# Tests React
npm run test

# Validation physique
python scripts/validate_physics.py --verbose
```

---

## 📈 Roadmap

| Phase | Durée | Livrables | Status |
|-------|-------|-----------|--------|
| **1. Exploration** | Semaine 1 | Validation données + Requêtes DuckDB | ⏳ |
| **2. Moteur Calcul** | Semaines 2-3 | Isolation + Closing Rate + Agrégation | ⏳ |
| **3. Interface React** | Semaines 3-4 | Heatmap + TimeSeries + Animation | ⏳ |
| **4. Automatisation** | Semaine 5 | Hooks + Tests E2E | ⏳ |
| **5. Production** | Semaine 6 | Build + Docs utilisateur | ⏳ |

📖 **Plan Détaillé** : Voir [`.kiro/PLAN.md`](.kiro/PLAN.md)

---

## 🔗 Ressources

| Document | Description |
|----------|-------------|
| [`.kiro/GETTING-STARTED.md`](.kiro/GETTING-STARTED.md) | Guide démarrage 5 minutes |
| [`.kiro/AGENTS.md`](.kiro/AGENTS.md) | Constitution & Invariants physiques |
| [`.kiro/PLAN.md`](.kiro/PLAN.md) | Feuille de route & Requêtes SQL |
| [`README-KIRO-SETUP.md`](README-KIRO-SETUP.md) | Configuration Kiro détaillée |
| [`PROJECT-STRUCTURE.md`](PROJECT-STRUCTURE.md) | Architecture complète |

---

## 🤝 Contribution

Contributions bienvenues ! Workflow :

1. Fork le projet
2. Créer branche feature : `git checkout -b feature/nouvelle-metrique`
3. Développer avec Kiro (skills + specs)
4. Tests : `pytest tests/ && npm run test`
5. Push : `git push origin feature/nouvelle-metrique`
6. Créer Pull Request

**Important** : Toute PR doit passer le hook `physics-validation` sans violations.

---

## 📄 License

MIT License - Voir [LICENSE](LICENSE)

---

## 🙏 Remerciements

- **NFL Big Data Bowl** : Données de tracking
- **Pro Football Focus (PFF)** : Annotations routes/coverages
- **Kiro Team** : Plateforme de développement AI-powered

---

## 📧 Contact

**Mainteneur** : Équipe Coach Cockpit NFL  
**Email** : coach-cockpit@example.com  
**Documentation** : https://coach-cockpit.docs

---

**Fait avec ❤️ et 🤖 (Kiro AI)**

*Dernière mise à jour : 21 octobre 2026*
