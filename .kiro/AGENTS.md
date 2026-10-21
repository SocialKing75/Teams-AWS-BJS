# CONSTITUTION DU PROJET (AGENTS.md)

## 1. PHILOSOPHIE & CADRAGE PRODUIT

### A. Persona & Problématique
- **Persona Unique** : Coordinateur Offensif / Coach NFL
- **Problématique Centrale** : « Dans quelles situations tactiques la fenêtre de réception se referme-t-elle le moins (ou le plus vite) ? »

### B. Approche SDD (Spec-Driven Development)
**⚠️ RÈGLE ABSOLUE** : La spécification formelle est le contrat prioritaire.

**Interdiction Stricte** : L'agent ne doit générer AUCUN composant sans spécification préalable dans `.kiro/specs/`.

**Workflow Obligatoire** :
1. Lire la spec EARS (`.kiro/specs/*/requirements.md`)
2. Valider la compréhension avec l'humain si ambiguïté
3. Implémenter strictement selon la spec
4. Ne jamais ajouter de features non spécifiées

### C. Stack Technique (Non Négociable)
- **Frontend** : React (Vite), Tailwind CSS, Plotly.js/Recharts
- **Backend** : DuckDB via MCP (Model Context Protocol)
- **Analysis** : Python (pandas, numpy, scipy)

---

## 2. INVARIANTS PHYSIQUES & SPATIAUX (NFL NGS)

### A. Repère Spécialisé NFL ⚠️ CRITIQUE

**Convention d'Orientation NFL** : 
- **0° = Nord** (ligne de touche haute, vers end zone attaque)
- Évolution dans le **sens horaire**
- **90° = Est**, **180° = Sud**, **270° = Ouest**

**⚠️ OBLIGATION IMPÉRATIVE** : L'agent doit **TOUJOURS** convertir vers le repère cartésien standard **AVANT** tout calcul vectoriel.

**Conversion Obligatoire** :
```python
def nfl_to_math_radians(angle_nfl: float) -> float:
    """
    Convertit angle NFL (0° Nord horaire) vers radians mathématiques (0° Est anti-horaire).
    
    ⚠️ Cette conversion est OBLIGATOIRE avant tout calcul trigonométrique.
    
    Args:
        angle_nfl: Angle NFL en degrés (0° = Nord)
    
    Returns:
        Angle mathématique en radians (0 = Est, π/2 = Nord)
    """
    # NFL: 0°=Nord → Math: π/2 (90°)
    # NFL: 90°=Est → Math: 0° (0)
    # NFL: 180°=Sud → Math: 3π/2 (270°)
    # NFL: 270°=Ouest → Math: π (180°)
    angle_math = (90 - angle_nfl) % 360
    return math.radians(angle_math)
```

### B. Normalisation de Trajectoire (Obligatoire)

**Règle** : Tous les jeux où l'attaque progresse vers la gauche doivent être **miroités spatialement** pour que l'attaque avance **toujours vers la droite** (X croissant de 0 à 120 yards).

```python
def normalize_play_direction(
    x: float, 
    y: float, 
    dir_nfl: float, 
    o_nfl: float,
    play_direction: str
) -> tuple[float, float, float, float]:
    """
    Normalise les coordonnées pour attaque vers droite.
    
    ⚠️ OBLIGATOIRE avant tout calcul spatial.
    """
    if play_direction == 'left':
        # Miroir horizontal complet
        x_norm = 120 - x
        y_norm = 53.3 - y
        dir_norm = (dir_nfl + 180) % 360
        o_norm = (o_nfl + 180) % 360
    else:
        x_norm, y_norm = x, y
        dir_norm, o_norm = dir_nfl, o_nfl
    
    return x_norm, y_norm, dir_norm, o_norm
```

### C. Limites du Terrain (Absolues)
- **Longueur totale** : 120 yards
  - 0-10 yards : End zone défense
  - 10-110 yards : Terrain de jeu (100 yards)
  - 110-120 yards : End zone attaque
- **Largeur** : 53.3 yards (53 yards 1 pied)

### D. Plafonds Cinématiques Physiques (Non Négociables)
- **Vitesse maximale** : `s_max = 13.0` yards/seconde (~42 km/h, ~23 mph)
- **Accélération maximale** : `a_max = 8.0` yards/seconde²

**⚠️ RÈGLE DE REJET** : Si une valeur calculée dépasse ces limites, l'agent doit **rejeter le résultat** et revoir sa formule mathématique.

---

## 3. PÉRIMÈTRE DES AUTORISATIONS (Règle des 3 Tiers)

### A. ACTIONS AUTOMATIQUES (Always Do) ✅

L'agent peut exécuter **sans validation humaine** :
1. **Requêtes SQL SELECT** via serveur MCP DuckDB
2. **Scripts de validation** (`validate_physics.py`, `test_*.py`)
3. **Mise à jour des fichiers de tâches** (`.kiro/specs/*/tasks.md`)
4. **Génération de code** strictement conforme aux specs EARS
5. **Calculs mathématiques** respectant les invariants physiques

### B. VALIDATION HUMAINE REQUISE (Ask First) ⚠️

L'agent doit **demander confirmation** avant :
1. **Modification de la structure React** principale (`App.tsx`, routing)
2. **Ajout de bibliothèques tierces** non listées dans le stack
3. **Modification du schéma de données** (colonnes DuckDB, format CSV)
4. **Implémentation de features** non spécifiées dans `.kiro/specs/`
5. **Modification des hooks** (`.kiro/hooks/*.json`)

### C. INTERDICTIONS ABSOLUES (Never Do) ❌

L'agent ne doit **JAMAIS** :
1. **Modifier la base de données source** (DuckDB, fichiers CSV originaux)
2. **Altérer les règles de la Constitution** (ce fichier AGENTS.md)
3. **Écrire des secrets/clés API en dur** (credentials, tokens)
4. **Ignorer les erreurs de validation physique** (vitesse > 13.0, etc.)
5. **Committer des fichiers > 100MB** (données volumineuses)
6. **Push directement vers `main`** sans tests passants

---

## 4. SPÉCIFICATION DES HOOKS (AUTOMATISATION)

### A. Intercepteur A Priori (PreToolUse)

**Rôle** : Examiner chaque commande **avant** son exécution.

**Règles de Blocage** :
- Bloquer toute suppression de base de données
- Bloquer modification de fichiers système (`.git/`, `.kiro/AGENTS.md`)
- Bloquer installation de paquets non validés

**Implémentation** : Voir `.kiro/hooks/pre-tool-check.json` (à créer)

### B. Intercepteur Physique A Posteriori (PostToolUse)

**Rôle** : Examiner les résultats de calculs produits par l'agent.

**Règles de Rejet** :
- Si `vitesse > 13.0 yards/s` → Rejeter résultat
- Si `accélération > 8.0 yards/s²` → Rejeter résultat
- Si `x ∉ [0, 120]` ou `y ∉ [0, 53.3]` → Rejeter résultat

**Implémentation** : Voir `.kiro/hooks/physics-validation.json` (✅ existe)

### C. Intercepteur de Validation Finale (OnSpecComplete)

**Rôle** : Vérifier la conformité du projet avant de déclarer une tâche terminée.

**Règles de Contrôle** :
1. ✅ Vérifier que `README.md` existe à la racine
2. ✅ Compter les phrases du README : **doit être entre 3 et 5 phrases** ⚠️
3. ✅ Vérifier que l'application React compile sans erreur critique
4. Vérifier que tous les tests `pytest` passent
5. Vérifier que tous les composants ont des specs correspondantes

**Implémentation** : Voir `.kiro/hooks/readme-length-check.json` (✅ existe partiellement)

---

## 5. PROTOCOLE D'INSPECTION & VÉRIFICATION (Agent-as-Judge)

### A. Rôle de l'Inspecteur

Un **second rôle d'agent vérificateur** s'exécute de manière **contradictoire** par rapport à l'agent exécutant.

### B. Méthode d'Évaluation

**Pour chaque exigence EARS** (`.kiro/specs/*/requirements.md`) :

1. **L'Inspecteur lit** l'exigence (ex: "WHEN le coach applique un filtre, THE SYSTEM SHALL recalculer la matrice")
2. **L'Inspecteur teste** le code React généré :
   - Change le filtre "Cover 2" → "Cover 3"
   - Vérifie que la matrice se met à jour en temps réel
   - Vérifie que les valeurs affichées changent
3. **Si l'exigence n'est pas satisfaite** :
   - L'Inspecteur **rejette la tâche**
   - Fournit une **consigne de correction ciblée** à l'exécutant
   - Ex: "US-C2 non satisfaite : le filtre man/zone ne déclenche pas de recalcul"

### C. Critères de Validation Stricte

**Une tâche est validée SI ET SEULEMENT SI** :
- ✅ Tous les tests unitaires (`pytest`, `npm test`) passent
- ✅ Toutes les user stories EARS sont satisfaites
- ✅ Aucune violation des invariants physiques
- ✅ README.md contient exactement 3-5 phrases
- ✅ Aucun warning critique de compilation

---

## 6. SPÉCIFICATION DU SERVEUR MCP (MODEL CONTEXT PROTOCOL)

### A. Rôle du Serveur MCP

Agir comme **intermédiaire** entre l'agent IA et la base de données DuckDB/SQLite contenant plusieurs millions de lignes de tracking.

### B. Règles d'Économie de Contexte ⚠️ CRITIQUE

**INTERDICTION ABSOLUE** : Injecter des fichiers CSV bruts directement dans le contexte de prompt du modèle.

**Workflow Obligatoire** :
1. L'agent **formule une requête SQL d'agrégation ciblée**
2. Le serveur MCP **exécute la requête** sur DuckDB
3. Le serveur MCP **retourne uniquement les résultats agrégés légers** (matrices, tableaux condensés)
4. L'agent **n'accède jamais aux données brutes**

**Exemple de Requête Conforme** :
```sql
-- ✅ CONFORME : Agrégation pré-filtrée
SELECT 
  coverage_type,
  route,
  AVG(closing_rate) as avg_closing,
  COUNT(*) as n
FROM calculated_windows
WHERE event_phase = 'pass_release_to_ball_land'
GROUP BY coverage_type, route
HAVING n >= 5;  -- Seuil minimal échantillon
```

**Exemple de Requête NON Conforme** :
```sql
-- ❌ NON CONFORME : Sélection brute sans agrégation
SELECT * FROM tracking_data;  -- Des millions de lignes !
```

---

## 7. CONVENTIONS DE NOMMAGE

### A. Python (snake_case)
```python
# Fonctions
calculate_closing_speed()
normalize_play_direction()
identify_closest_defender()

# Variables
window_arrival: float
closing_rate: float
separation_label: str
```

### B. React/TypeScript (camelCase + PascalCase)
```typescript
// Composants (PascalCase)
<MatchupHeatmap />
<Field2DCanvas />
<TacticalInsightCard />

// Props & variables (camelCase)
const { coverageType, routeType } = props;
const closingRate = calculateClosing(data);
```

### C. Fichiers
```
snake_case.py       # Modules Python
kebab-case.tsx      # Composants React
PascalCase.tsx      # Fichiers composants principaux
UPPERCASE.md        # Documentation
```

---

## 8. EXIGENCE STRICTE DE SOUMISSION JURY

### A. Fichier de Résumé Exécutif (README.md)

À la fin de l'implémentation, l'agent **DOIT** générer un fichier `README.md` à la racine.

**Contraintes Strictes** :
- **Exactement 3 à 5 phrases** (ni moins, ni plus)
- Résumer l'**insight tactique principal**
- Langage **clair et concis**
- Format **non-technique** (pour jury)

**Exemple Conforme** :
```markdown
# Coach Cockpit NFL

Ce cockpit analyse 2,4 millions de frames de tracking NFL pour identifier les situations où la fenêtre de réception reste ouverte. Les routes "Go" contre Cover 3 présentent le meilleur taux de maintien d'ouverture (fenêtre moyenne de 3,8 yards à l'arrivée). L'outil permet aux coordinateurs offensifs de cibler les failles défensives en filtrant par down et distance.
```

**✅ Validation** : Hook `readme-length-check` vérifie automatiquement le respect de cette contrainte.

---

## 9. SOURCES DE VÉRITÉ (Hiérarchie)

**Ordre de Priorité en Cas de Conflit** :

1. **AGENTS.md** (ce fichier) : Constitution, règles absolues
2. **`.kiro/specs/*/requirements.md`** : User stories EARS
3. **`.kiro/specs/*/design.md`** : Définitions métriques & dimensions
4. **`.kiro/skills/*.md`** : Implémentation technique
5. **`.kiro/PLAN.md`** : Roadmap développement

**En cas de contradiction** : La source la plus haute dans la hiérarchie prime.

---

**Version** : 2.0.0 (Pack Spécifications Complet)  
**Dernière mise à jour** : 2026-10-21  
**Mainteneur** : Équipe Coach Cockpit NFL  
**Status** : ⚠️ Constitution renforcée selon pack de spécifications
