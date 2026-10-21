# 🚀 Getting Started with Coach Cockpit NFL

## Démarrage Rapide (5 minutes)

### Étape 1 : Vérifier l'Environnement

```bash
# Naviguer vers le répertoire du projet
cd Teams-AWS-BJS

# Vérifier que les données sont présentes
ls nfl-big-data-bowl-regional-event-data/data/tracking/ | head
```

**Résultat attendu** : Liste de fichiers `tracking_YYYYMMDDXX.csv`

---

### Étape 2 : Installer les Dépendances

```bash
# Python (pour scripts d'analyse)
pip install pandas numpy scipy matplotlib

# Si vous voulez développer l'interface React
# npm install
```

---

### Étape 3 : Lancer la Première Validation

```bash
# Valider les contraintes physiques sur un fichier tracking
python scripts/validate_physics.py --tracking-file nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv --verbose
```

**Que fait ce script ?**
- Vérifie que les vitesses ne dépassent pas 13.0 yards/s
- Détecte les accélérations impossibles (>8.0 yards/s²)
- Identifie les joueurs hors limites du terrain
- Génère un rapport de qualité des données

---

### Étape 4 : Explorer avec Kiro

#### 4a. Demander à Kiro d'utiliser les Skills

Dans le chat Kiro, tapez :

```
Utilise le skill nfl-geometry pour analyser le fichier 
tracking_2021091200.csv et montre-moi comment normaliser 
la direction d'un jeu où play_direction == 'left'
```

Kiro va :
1. Activer automatiquement `.kiro/skills/nfl-geometry/SKILL.md`
2. Lire le fichier tracking
3. Appliquer la fonction `normalize_play_direction()`
4. Afficher le code exemple

---

#### 4b. Demander une Implémentation depuis la Spec

```
Implémente REQ-ENGINE-1 de la spec coach-cockpit : 
"Isolation de la Phase de Vol"
```

Kiro va :
1. Lire `.kiro/specs/coach-cockpit/spec.md`
2. Générer le code Python dans `src/engine/isolation.py`
3. Créer les tests unitaires dans `tests/test_isolation.py`
4. Exécuter pytest pour valider

---

### Étape 5 : Tester le Hook Physics Guardrail

#### 5a. Créer un fichier Python avec violation

```bash
# Créer fichier test
cat > test_violation.py << 'EOF'
# Constantes physiques (avec violations intentionnelles)
MAX_SPEED = 15.0  # ⚠️ Dépasse limite!
MAX_ACCELERATION = 10.0  # ⚠️ Trop élevé!
FIELD_LENGTH = 120.0  # ✅ Correct
EOF
```

#### 5b. Sauvegarder avec Kiro

Dans le chat Kiro :
```
Sauvegarde le fichier test_violation.py
```

**Résultat** : Le hook `physics-validation` va s'exécuter automatiquement et afficher :

```
======================================================================
🔬 Physics Guardrail Validation Report
======================================================================
File: test_violation.py
Tool: fs_write

⚠️  VIOLATIONS DETECTED:
  ❌ MAX_SPEED = 15.0 yards/s exceeds physical limit of 13.0 yards/s
     Reason: Vitesse maximale humaine (~23 mph, record NFL)
  ❌ MAX_ACCELERATION = 10.0 yards/s² exceeds physical limit of 8.0 yards/s²
     Reason: Accélération maximale biomécaniquement plausible

Action Required:
  Please review and correct the constants above.
  Reference: .kiro/AGENTS.md Section 2.3 (Physical Constraints)
======================================================================
```

---

## Cas d'Usage Concrets

### Cas 1 : "Quelles routes sont les plus vulnérables en Cover 2 ?"

**Workflow** :

1. **Demander à Kiro** :
   ```
   Charge les données de tracking pour tous les jeux de passe contre Cover 2.
   Calcule le closing rate moyen par type de route (slant, go, out, corner, post).
   Génère un heatmap avec Plotly.
   ```

2. **Kiro va** :
   - Utiliser `nfl-geometry` pour normaliser les directions
   - Calculer les closing rates avec `compute_closing_rate()`
   - Créer un composant `<HeatmapMatchup />` basé sur le skill `react-coach-ui`
   - Afficher le résultat interactif

---

### Cas 2 : "Rejouer l'animation d'une passe interceptée"

**Workflow** :

1. **Identifier le jeu** :
   ```sql
   SELECT gameId, playId, playDescription 
   FROM plays 
   WHERE passResult = 'I'  -- Interception
   LIMIT 1;
   ```

2. **Demander à Kiro** :
   ```
   Crée une animation 2D du terrain pour gameId=2021091200, playId=97.
   Montre les trajectoires du WR et du CB, avec vecteurs de vitesse.
   ```

3. **Kiro va** :
   - Générer `<RouteVisualization />` avec Recharts
   - Implémenter hook `useAnimation()` pour contrôle frame-by-frame
   - Afficher terrain + trajectoires + contrôles play/pause

---

### Cas 3 : "Exporter les métriques en CSV pour analyse R"

**Workflow** :

```
Calcule les métriques suivantes pour tous les jeux de passe :
- gameId, playId
- route_type
- closing_rate_avg
- min_separation
- success (boolean : fenêtre reste ouverte)

Sauvegarde dans exports/closing_rate_metrics.csv
```

Kiro va générer le CSV formaté RFC 4180.

---

## Commandes Kiro Avancées

### Activer un Skill Manuellement

Si un skill n'est pas chargé automatiquement, utilisez :

```
#.kiro/skills/nfl-geometry/SKILL.md
```

Cela force Kiro à inclure le contenu du skill dans son contexte.

---

### Référencer une Section Spécifique de la Spec

```
Implémente la requête MCP 4 de PLAN.md : "Extraire Phase Vol d'un Jeu"
```

Kiro va chercher directement dans `.kiro/PLAN.md` → Phase 2 → Section 2.1.

---

### Modifier un Hook Existant

```bash
# Lister les hooks actifs
cat .kiro/hooks/physics-validation.json

# Modifier via Kiro
"Modifie le hook physics-validation pour aussi vérifier MIN_REACTION_TIME"
```

Kiro va éditer `.kiro/hooks/physics-guardrail.py` pour ajouter la validation.

---

## Troubleshooting

### Erreur : "ModuleNotFoundError: No module named 'pandas'"

**Solution** :
```bash
pip install pandas numpy scipy
```

---

### Hook ne s'exécute pas après sauvegarde

**Solution** :
1. Vérifier que le hook existe :
   ```bash
   cat .kiro/hooks/physics-validation.json
   ```

2. Redémarrer Kiro (fermer/rouvrir la session)

3. Vérifier les logs :
   ```
   Kiro, montre-moi les logs du dernier hook exécuté
   ```

---

### Données tracking introuvables

**Solution** :
```bash
# Vérifier chemin relatif
pwd
ls -la nfl-big-data-bowl-regional-event-data/data/

# Si le dossier n'existe pas :
cd Teams-AWS-BJS
git submodule update --init --recursive
```

---

## Prochaines Étapes

### Semaine 1 : Exploration
- [ ] Valider physique sur 5+ fichiers tracking
- [ ] Exécuter Requête MCP 1-3 de PLAN.md
- [ ] Identifier un jeu de passe intéressant pour analyse

### Semaine 2 : Moteur de Calcul
- [ ] Implémenter `isolation.py` (REQ-ENGINE-1)
- [ ] Implémenter `closing_rate.py` (REQ-ENGINE-2)
- [ ] Écrire tests unitaires avec pytest

### Semaine 3 : Interface React
- [ ] Créer `<HeatmapMatchup />` avec Plotly
- [ ] Créer `<TimeSeriesClosing />` avec Recharts
- [ ] Tests composants avec Vitest

---

## Ressources

| Ressource | Lien/Chemin |
|-----------|-------------|
| Documentation Kiro | https://kiro.dev/docs |
| Spec Formelle EARS | `.kiro/specs/coach-cockpit/spec.md` |
| Skills NFL Geometry | `.kiro/skills/nfl-geometry/SKILL.md` |
| Plan d'Action | `.kiro/PLAN.md` |
| Constitution | `.kiro/AGENTS.md` |
| README Setup | `README-KIRO-SETUP.md` |

---

## Support

**Questions sur Kiro** :
- Commande Kiro : `/help`
- Documentation : https://kiro.dev/docs

**Questions Projet** :
- Consulter `.kiro/AGENTS.md` Section "Sources de Vérité"
- Demander à Kiro : "Explique-moi la structure du projet Coach Cockpit"

---

**Bon démarrage! 🏈🚀**

**Version** : 1.0.0  
**Dernière MAJ** : 2026-10-21
