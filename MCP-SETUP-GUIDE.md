# 🔧 Guide Configuration MCP - Coach Cockpit NFL

## ⚠️ Important

La configuration MCP doit être créée **manuellement** car Kiro protège le dossier `.kiro/settings/` pour des raisons de sécurité.

---

## 🚀 Installation en 3 Étapes

### Étape 1 : Installer UV (Python Package Manager)

**Windows PowerShell** :
```powershell
# Option recommandée : Via PowerShell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Alternative : Via pip (si Python déjà installé)
pip install uv
```

**Vérification** :
```powershell
uv --version
# Attendu : uv 0.5.x ou supérieur
```

---

### Étape 2 : Créer Fichier de Configuration MCP

**Créer le fichier** : `.kiro/settings/mcp.json`

**Contenu à copier** :

```json
{
  "mcpServers": {
    "duckdb": {
      "command": "uvx",
      "args": [
        "mcp-server-duckdb",
        "--db-path",
        "nfl_analysis.duckdb"
      ],
      "env": {
        "DUCKDB_ENABLE_OBJECT_CACHE": "true"
      },
      "disabled": false
    },
    "filesystem": {
      "command": "uvx",
      "args": [
        "mcp-server-filesystem",
        "C:\\Users\\nguen\\Teams-AWS-BJS\\nfl-big-data-bowl-regional-event-data\\data"
      ],
      "env": {},
      "disabled": false
    }
  }
}
```

**Via PowerShell** :
```powershell
# Créer le fichier mcp.json
$mcpConfig = @'
{
  "mcpServers": {
    "duckdb": {
      "command": "uvx",
      "args": [
        "mcp-server-duckdb",
        "--db-path",
        "nfl_analysis.duckdb"
      ],
      "env": {
        "DUCKDB_ENABLE_OBJECT_CACHE": "true"
      },
      "disabled": false
    },
    "filesystem": {
      "command": "uvx",
      "args": [
        "mcp-server-filesystem",
        "C:\\Users\\nguen\\Teams-AWS-BJS\\nfl-big-data-bowl-regional-event-data\\data"
      ],
      "env": {},
      "disabled": false
    }
  }
}
'@

# Créer dossier si nécessaire
New-Item -ItemType Directory -Force -Path ".kiro\settings"

# Écrire fichier
$mcpConfig | Out-File -FilePath ".kiro\settings\mcp.json" -Encoding UTF8
```

---

### Étape 3 : Redémarrer Kiro

1. **Fermer** la session Kiro actuelle
2. **Rouvrir** Kiro (les serveurs MCP se lancent au démarrage)
3. **Vérifier** dans le panneau "MCP Servers" :
   - Ouvrir la vue Kiro (icône Kiro dans la barre latérale)
   - Section "MCP Servers"
   - Vous devriez voir :
     - 🟢 **duckdb** (running)
     - 🟢 **filesystem** (running)

---

## 📋 Vérification Installation

### Test 1 : DuckDB Fonctionne

**Dans le chat Kiro, tapez** :

```
Exécute cette requête DuckDB:

SELECT COUNT(*) as total_frames
FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv')
```

**Résultat Attendu** :
```
total_frames
-------------
52,341
```

✅ **Si ça fonctionne** : DuckDB est configuré !  
❌ **Si erreur** : Voir section Troubleshooting ci-dessous

---

### Test 2 : Filesystem Fonctionne

```
Liste les 10 premiers fichiers dans le dossier tracking
```

**Résultat Attendu** :
```
tracking_2021091200.csv
tracking_2021091201.csv
...
```

---

## 🎯 Requêtes Prêtes à l'Emploi

### Requête 1 : Schéma du Tracking
```
Exécute cette requête DuckDB:

DESCRIBE 
SELECT * 
FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv') 
LIMIT 0;
```

**Résultat** : Liste des colonnes (gameId, playId, nflId, x, y, s, dir, o, event...)

---

### Requête 2 : Statistiques Événements
```
Exécute cette requête DuckDB:

SELECT 
  event,
  COUNT(*) AS n_occurrences,
  COUNT(DISTINCT playId) AS n_plays
FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv')
WHERE event IS NOT NULL
GROUP BY event
ORDER BY n_occurrences DESC;
```

**Résultat** : Compte d'événements (pass_release, ball_land, tackle, etc.)

---

### Requête 3 : Top 10 Vitesses
```
Exécute cette requête DuckDB:

SELECT 
  nflId,
  MAX(s) as max_speed_yards_per_sec
FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv')
GROUP BY nflId
ORDER BY max_speed_yards_per_sec DESC
LIMIT 10;
```

**Résultat** : Joueurs les plus rapides du fichier

---

### Requête 4 : Distribution Vitesses (Histogramme)
```
Exécute cette requête DuckDB:

SELECT 
  FLOOR(s) as speed_bucket,
  COUNT(*) as count
FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv')
WHERE s IS NOT NULL AND s > 0
GROUP BY FLOOR(s)
ORDER BY speed_bucket;
```

**Résultat** : Distribution par tranche de vitesse (0-1 yd/s, 1-2 yd/s, etc.)

---

### Requête 5 : Jointure Plays + Tracking
```
Exécute cette requête DuckDB:

SELECT 
  p.playId,
  p.playDescription,
  p.passResult,
  COUNT(DISTINCT t.nflId) as num_players,
  AVG(t.s) as avg_speed
FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/plays.csv') p
JOIN read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv') t
  ON p.gameId = t.gameId AND p.playId = t.playId
WHERE p.passResult IS NOT NULL
GROUP BY p.playId, p.playDescription, p.passResult
LIMIT 5;
```

**Résultat** : Détails jeux de passe avec statistiques joueurs

---

## 🔧 Troubleshooting

### Problème 1 : "uvx: command not found"

**Cause** : UV pas installé

**Solution** :
```powershell
pip install uv
uv --version
```

Puis redémarrer Kiro.

---

### Problème 2 : Serveurs MCP en "Unknown"

**Cause** : Fichier `mcp.json` mal formaté ou chemin incorrect

**Solution** :
1. Vérifier JSON valide : https://jsonlint.com/
2. Vérifier chemin Windows :
   ```json
   "C:\\Users\\nguen\\Teams-AWS-BJS\\..."
   ```
   (Backslashes doublés `\\`)
3. Redémarrer Kiro

---

### Problème 3 : "mcp-server-duckdb not found"

**Cause** : Premier lancement, `uvx` télécharge le package

**Solution** :
- Patienter 30-60 secondes
- Vérifier logs MCP (clic droit sur serveur → "Show Logs")
- Si échec persistant :
  ```powershell
  uvx mcp-server-duckdb --version
  ```

---

### Problème 4 : "Access Denied" (Filesystem)

**Cause** : Chemin filesystem invalide

**Solution** :
1. Vérifier que le dossier existe :
   ```powershell
   Test-Path "C:\Users\nguen\Teams-AWS-BJS\nfl-big-data-bowl-regional-event-data\data"
   ```
2. Corriger chemin dans `mcp.json` si nécessaire

---

### Problème 5 : Requêtes SQL ne retournent rien

**Cause** : Syntaxe DuckDB incorrecte

**Solution** :
- Utiliser `read_csv_auto()` pour chemins relatifs
- Exemple :
  ```sql
  -- ❌ Incorrect
  SELECT * FROM 'data/tracking.csv'
  
  -- ✅ Correct
  SELECT * FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv')
  ```

---

## 📚 Ressources

### Documentation Officielle
- **UV Installation** : https://docs.astral.sh/uv/getting-started/installation/
- **DuckDB SQL** : https://duckdb.org/docs/sql/introduction
- **MCP Protocol** : https://modelcontextprotocol.io/

### Configuration Avancée
- **DuckDB Performance** : https://duckdb.org/docs/guides/performance/
- **MCP Servers List** : https://github.com/modelcontextprotocol/servers

---

## 🎓 Utilisation Avancée

### Créer une Vue DuckDB Persistante

```sql
-- Dans Kiro
CREATE OR REPLACE VIEW pass_plays AS
SELECT 
  p.gameId,
  p.playId,
  p.passResult,
  p.playDirection,
  COUNT(DISTINCT t.nflId) as num_players
FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/plays.csv') p
JOIN read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/*.csv') t
  ON p.gameId = t.gameId AND p.playId = t.playId
WHERE p.passResult IS NOT NULL
GROUP BY p.gameId, p.playId, p.passResult, p.playDirection;

-- Puis utiliser
SELECT * FROM pass_plays LIMIT 10;
```

---

### Exporter Résultats en CSV

```sql
COPY (
  SELECT * FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv')
  WHERE event = 'pass_release'
) TO 'exports/pass_releases.csv' (HEADER, DELIMITER ',');
```

---

### Analyser Plusieurs Fichiers (Wildcard)

```sql
-- Tous les fichiers tracking de septembre 2021
SELECT 
  COUNT(*) as total_frames,
  COUNT(DISTINCT gameId) as num_games
FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_202109*.csv');
```

---

## ✅ Checklist Configuration

- [ ] UV installé (`uv --version` fonctionne)
- [ ] Fichier `.kiro/settings/mcp.json` créé
- [ ] Kiro redémarré
- [ ] Serveur DuckDB 🟢 (running)
- [ ] Serveur Filesystem 🟢 (running)
- [ ] Test Requête 1 réussie (schéma tracking)
- [ ] Test Requête 2 réussie (statistiques événements)

---

## 🎯 Intégration avec .kiro/PLAN.md

Les requêtes de ce guide correspondent aux **Requêtes MCP 1-5** du fichier `.kiro/PLAN.md`.

**Pour exécuter automatiquement** :
```
Kiro, exécute la Requête MCP 2 du PLAN.md
```

Kiro va :
1. Lire `.kiro/PLAN.md` Phase 1 Section 1.2
2. Trouver "Requête MCP 2 : Statistiques Événements"
3. Exécuter via serveur DuckDB
4. Afficher résultats

---

**Version** : 1.0.0  
**Date** : 2026-10-21  
**Mainteneur** : Équipe Coach Cockpit NFL

---

**🚀 Une fois configuré, vous pourrez interroger 122 fichiers CSV (>10M de lignes) en quelques secondes avec DuckDB !**
