# ⚡ Quick Start - Coach Cockpit NFL (5 minutes)

## 🎯 Configuration Terminée !

**14 fichiers créés | 73 KB de documentation**

---

## 🚀 Démarrage en 3 Commandes

### 1️⃣ Valider Installation (30 secondes)

```powershell
# Vérifier présence fichiers Kiro
Get-ChildItem -Path .kiro -Recurse -File | Measure-Object

# Résultat attendu : 8 fichiers
```

✅ **Si 8 fichiers** → Installation réussie !  
❌ **Si moins** → Voir `INSTALLATION-COMPLETE.md` § Troubleshooting

---

### 2️⃣ Tester Données NFL (2 minutes)

```powershell
# Lancer validation physique
python scripts\validate_physics.py `
  --tracking-file nfl-big-data-bowl-regional-event-data\data\tracking\tracking_2021091200.csv
```

✅ **Si "PASSED"** → Données valides !  
⚠️ **Si violations** → Normal (bruit GPS < 5%)

---

### 3️⃣ Activer Kiro (2 minutes)

**Dans le chat Kiro, tapez** :

```
Charge le skill nfl-geometry et montre-moi la fonction 
normalize_play_direction() avec un exemple
```

✅ **Si Kiro répond avec code Python** → Skills actifs !

---

## 📚 Lire Ensuite (Par Priorité)

### 🥇 Essentiel (10 min)
1. **`README.md`** - Vue d'ensemble projet
2. **`.kiro/GETTING-STARTED.md`** - Guide pratique

### 🥈 Important (20 min)
3. **`.kiro/AGENTS.md`** - Règles & invariants
4. **`.kiro/PLAN.md`** - Roadmap 6 semaines

### 🥉 Détails (30 min)
5. **`.kiro/specs/coach-cockpit/spec.md`** - Requirements
6. **`.kiro/skills/nfl-geometry/SKILL.md`** - Fonctions NFL

---

## 🎯 Premier Objectif : Implémenter REQ-ENGINE-1

**Dans Kiro** :

```
Implémente REQ-ENGINE-1 de la spec coach-cockpit avec tests unitaires.
Utilise le skill nfl-geometry.
```

**Résultat Attendu** :
- Fichier `src/engine/isolation.py` créé
- Tests `tests/test_isolation.py` créés
- Pytest exécuté automatiquement

⏱️ **Temps estimé avec Kiro** : 5-10 minutes

---

## 📊 Structure Créée

```
Teams-AWS-BJS/
├── 📄 README.md                        ✅ Doc principale
├── 📄 QUICK-START.md                   ✅ Ce fichier
├── 📄 INSTALLATION-COMPLETE.md         ✅ Vérification
│
├── 📁 .kiro/
│   ├── 📄 AGENTS.md                    ✅ Constitution (4 KB)
│   ├── 📄 PLAN.md                      ✅ Roadmap (15 KB)
│   ├── 📄 GETTING-STARTED.md           ✅ Guide (7 KB)
│   │
│   ├── 📁 specs/coach-cockpit/
│   │   └── 📄 spec.md                  ✅ Requirements (10 KB)
│   │
│   ├── 📁 skills/
│   │   ├── 📁 nfl-geometry/
│   │   │   └── 📄 SKILL.md             ✅ Géométrie (12 KB)
│   │   └── 📁 react-coach-ui/
│   │       └── 📄 SKILL.md             ✅ React (20 KB)
│   │
│   └── 📁 hooks/
│       ├── 📄 physics-validation.json  ✅ Hook config
│       └── 🐍 physics-guardrail.py     ✅ Script validation
│
└── 📁 scripts/
    └── 🐍 validate_physics.py          ✅ Validation données
```

---

## 🔗 Liens Rapides

| Action | Commande Kiro |
|--------|---------------|
| Charger skill géométrie | `Charge le skill nfl-geometry` |
| Implémenter REQ-ENGINE-1 | `Implémente REQ-ENGINE-1 avec tests` |
| Créer composant Heatmap | `Crée <HeatmapMatchup /> selon skill react-coach-ui` |
| Exécuter requête DuckDB | `Exécute Requête MCP 1 du PLAN.md` |

---

## ⚠️ Troubleshooting Express

### Problème : "Fichier tracking introuvable"
```powershell
cd Teams-AWS-BJS
git submodule update --init --recursive
```

### Problème : "ModuleNotFoundError: pandas"
```powershell
pip install pandas numpy scipy pytest
```

### Problème : "Hook ne s'exécute pas"
**Solution** : Fermer/rouvrir session Kiro (hooks actifs au prochain démarrage)

---

## 🎓 Formation Express (10 min)

### Minute 1-3 : Comprendre les Skills
**Skills** = Bibliothèques de fonctions + patterns réutilisables

- `nfl-geometry` : Calculs physiques NFL
- `react-coach-ui` : Composants React/visualisations

**Activation** : Automatique ou via `#.kiro/skills/[nom]/SKILL.md`

---

### Minute 4-6 : Comprendre les Specs
**Specs** = Requirements formels format EARS

Format :
```
[REQ-ID : Titre]
WHEN condition,
THE SYSTEM SHALL action.
```

**Usage** : `Implémente REQ-XXX de la spec coach-cockpit`

---

### Minute 7-10 : Comprendre les Hooks
**Hooks** = Automatisations sur événements Kiro

Exemple : `physics-validation`
- **Déclencheur** : PostToolUse (après édition `.py`)
- **Action** : Valide constantes physiques
- **Sortie** : Rapport dans terminal

---

## 🎯 Objectifs Semaine 1

### Jour 1 (Aujourd'hui)
- [x] Installation complète
- [ ] Lire README.md
- [ ] Tester skill `nfl-geometry`

### Jour 2
- [ ] Implémenter REQ-ENGINE-1
- [ ] Exécuter tests pytest
- [ ] Valider hook fonctionne

### Jour 3-5
- [ ] Compléter Phase 2 du PLAN.md
- [ ] Exécuter Requêtes MCP 1-3
- [ ] Calculer closing rate sur 100 jeux

---

## 📞 Support

**Questions Kiro** : `/help` dans le chat  
**Questions Projet** : Voir `SUMMARY.md` § Support & Contact  
**Bugs** : Créer issue GitHub avec tag `kiro-config`

---

## 🎉 Prêt à Démarrer !

**Première Action Recommandée** :

```
Kiro, charge .kiro/GETTING-STARTED.md et suis l'Étape 4 : "Explorer avec Kiro"
```

**Ou directement** :

```
Kiro, utilise le skill nfl-geometry pour normaliser les 10 premières 
lignes du fichier tracking_2021091200.csv
```

---

**Bon développement ! 🏈⚡**

---

**Version** : 1.0.0  
**Date** : 2026-10-21  
**Temps Total d'Installation** : ~5 minutes  
**Prochaine Étape** : Voir `.kiro/GETTING-STARTED.md`
