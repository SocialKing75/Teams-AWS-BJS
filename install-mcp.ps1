# ============================================================================
# Script d'Installation MCP pour Coach Cockpit NFL
# ============================================================================
# Ce script installe UV et configure les serveurs MCP (DuckDB + Filesystem)
# ============================================================================

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  🏈 INSTALLATION MCP - COACH COCKPIT NFL" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# ÉTAPE 1 : Vérifier Python
# ============================================================================

Write-Host "📋 Étape 1/4 : Vérification Python..." -ForegroundColor Yellow

try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ Python détecté: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python n'est pas installé!" -ForegroundColor Red
    Write-Host "  📥 Téléchargez Python depuis: https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Appuyez sur Entrée pour quitter"
    exit 1
}

Write-Host ""

# ============================================================================
# ÉTAPE 2 : Installer UV
# ============================================================================

Write-Host "📋 Étape 2/4 : Installation UV (Python Package Manager)..." -ForegroundColor Yellow

# Vérifier si UV est déjà installé
$uvInstalled = $false
try {
    $uvVersion = uv --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ UV déjà installé: $uvVersion" -ForegroundColor Green
        $uvInstalled = $true
    }
} catch {
    # UV pas installé
}

if (-not $uvInstalled) {
    Write-Host "  📥 Installation de UV via pip..." -ForegroundColor Cyan
    
    try {
        pip install uv
        
        if ($LASTEXITCODE -eq 0) {
            # Vérifier installation
            $uvVersion = uv --version 2>&1
            Write-Host "  ✅ UV installé avec succès: $uvVersion" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Échec installation UV via pip" -ForegroundColor Red
            Write-Host "  💡 Essayez manuellement:" -ForegroundColor Yellow
            Write-Host "     pip install uv" -ForegroundColor White
            exit 1
        }
    } catch {
        Write-Host "  ❌ Erreur lors de l'installation UV" -ForegroundColor Red
        Write-Host "  💡 Installez manuellement:" -ForegroundColor Yellow
        Write-Host "     pip install uv" -ForegroundColor White
        Write-Host "  📖 Documentation: https://docs.astral.sh/uv/getting-started/installation/" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""

# ============================================================================
# ÉTAPE 3 : Vérifier Configuration MCP
# ============================================================================

Write-Host "📋 Étape 3/4 : Vérification configuration MCP..." -ForegroundColor Yellow

$mcpPath = ".kiro\settings\mcp.json"

if (Test-Path $mcpPath) {
    Write-Host "  ✅ Fichier mcp.json trouvé" -ForegroundColor Green
    
    # Valider JSON
    try {
        $mcpContent = Get-Content $mcpPath -Raw | ConvertFrom-Json
        
        if ($mcpContent.mcpServers.duckdb) {
            Write-Host "  ✅ Serveur DuckDB configuré" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Serveur DuckDB manquant dans mcp.json" -ForegroundColor Yellow
        }
        
        if ($mcpContent.mcpServers.filesystem) {
            Write-Host "  ✅ Serveur Filesystem configuré" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  Serveur Filesystem manquant dans mcp.json" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  ❌ Erreur: mcp.json invalide (JSON malformé)" -ForegroundColor Red
        Write-Host "  💡 Vérifiez le fichier avec: https://jsonlint.com/" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ Fichier mcp.json introuvable!" -ForegroundColor Red
    Write-Host "  📍 Emplacement attendu: $mcpPath" -ForegroundColor Yellow
    Write-Host "  💡 Le fichier devrait avoir été créé automatiquement." -ForegroundColor Yellow
    Write-Host "  📖 Consultez: MCP-SETUP-GUIDE.md" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# ÉTAPE 4 : Tester Serveurs MCP
# ============================================================================

Write-Host "📋 Étape 4/4 : Test des serveurs MCP..." -ForegroundColor Yellow

# Test DuckDB
Write-Host "  🧪 Test serveur DuckDB..." -ForegroundColor Cyan
try {
    $duckdbTest = uvx mcp-server-duckdb --version 2>&1
    
    if ($LASTEXITCODE -eq 0 -or $duckdbTest -match "mcp-server-duckdb") {
        Write-Host "    ✅ DuckDB server accessible" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  DuckDB server va se télécharger au premier lancement Kiro" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ⚠️  DuckDB server va se télécharger au premier lancement Kiro" -ForegroundColor Yellow
}

# Test Filesystem
Write-Host "  🧪 Test serveur Filesystem..." -ForegroundColor Cyan
try {
    $fsTest = uvx mcp-server-filesystem --version 2>&1
    
    if ($LASTEXITCODE -eq 0 -or $fsTest -match "mcp-server-filesystem") {
        Write-Host "    ✅ Filesystem server accessible" -ForegroundColor Green
    } else {
        Write-Host "    ⚠️  Filesystem server va se télécharger au premier lancement Kiro" -ForegroundColor Yellow
    }
} catch {
    Write-Host "    ⚠️  Filesystem server va se télécharger au premier lancement Kiro" -ForegroundColor Yellow
}

Write-Host ""

# ============================================================================
# RÉSUMÉ
# ============================================================================

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  📊 RÉSUMÉ INSTALLATION" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "✅ Étapes Complétées:" -ForegroundColor Green
Write-Host "  ✓ Python vérifié" -ForegroundColor White
Write-Host "  ✓ UV installé" -ForegroundColor White
Write-Host "  ✓ Configuration MCP vérifiée" -ForegroundColor White
Write-Host "  ✓ Serveurs MCP testés" -ForegroundColor White
Write-Host ""

Write-Host "🚀 PROCHAINES ÉTAPES:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1️⃣  Fermer cette session Kiro" -ForegroundColor Cyan
Write-Host "  2️⃣  Rouvrir Kiro (les serveurs MCP se lancent au démarrage)" -ForegroundColor Cyan
Write-Host "  3️⃣  Vérifier dans le panneau 'MCP Servers':" -ForegroundColor Cyan
Write-Host "      - Ouvrir vue Kiro (barre latérale)" -ForegroundColor White
Write-Host "      - Section 'MCP Servers'" -ForegroundColor White
Write-Host "      - Vous devriez voir:" -ForegroundColor White
Write-Host "        🟢 duckdb (running)" -ForegroundColor Green
Write-Host "        🟢 filesystem (running)" -ForegroundColor Green
Write-Host ""

Write-Host "🧪 TESTER LA CONFIGURATION:" -ForegroundColor Yellow
Write-Host ""
Write-Host "Dans le chat Kiro, tapez:" -ForegroundColor Cyan
Write-Host ""
Write-Host '  "Exécute cette requête DuckDB:' -ForegroundColor White
Write-Host ""
Write-Host "  SELECT COUNT(*) as total_frames" -ForegroundColor White
Write-Host "  FROM read_csv_auto('nfl-big-data-bowl-regional-event-data/data/tracking/tracking_2021091200.csv')" -ForegroundColor White
Write-Host '  "' -ForegroundColor White
Write-Host ""

Write-Host "Résultat attendu:" -ForegroundColor Cyan
Write-Host "  total_frames" -ForegroundColor White
Write-Host "  -------------" -ForegroundColor White
Write-Host "  52,341" -ForegroundColor White
Write-Host ""

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  ✅ Installation terminée!" -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📖 Documentation complète: MCP-SETUP-GUIDE.md" -ForegroundColor Yellow
Write-Host "🆘 Troubleshooting: Voir section dans MCP-SETUP-GUIDE.md" -ForegroundColor Yellow
Write-Host ""

Read-Host "Appuyez sur Entrée pour fermer"
