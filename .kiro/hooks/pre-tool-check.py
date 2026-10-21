#!/usr/bin/env python3
"""
Hook Kiro : Pre-Tool Safety Check

Déclencheur : PreToolUse (avant exécution de commandes)
Action : Bloquer les commandes dangereuses selon AGENTS.md Section 3

Exit Codes:
  0 - Command safe, proceed
  2 - Command blocked (critical violation)
"""

import sys
import json
import re

# ============================================================================
# PATTERNS DANGEREUX (Interdictions AGENTS.md Section 3.C)
# ============================================================================

BLOCKED_PATTERNS = {
    'database_deletion': {
        'patterns': [
            r'DROP\s+(TABLE|DATABASE)',
            r'DELETE\s+FROM.*WHERE\s+1\s*=\s*1',
            r'TRUNCATE\s+TABLE',
            r'rm\s+.*\.duckdb',
            r'Remove-Item\s+.*\.duckdb'
        ],
        'message': 'Tentative de suppression de base de données détectée'
    },
    'system_files': {
        'patterns': [
            r'\.git/',
            r'\.kiro/AGENTS\.md',
            r'\.kiro/hooks/.*\.json',  # Modif hooks
            r'/etc/',
            r'C:\\Windows'
        ],
        'message': 'Tentative de modification de fichiers système détectée'
    },
    'credentials': {
        'patterns': [
            r'API[_-]?KEY\s*=\s*["\'][^"\']+["\']',
            r'SECRET[_-]?KEY\s*=\s*["\'][^"\']+["\']',
            r'PASSWORD\s*=\s*["\'][^"\']+["\']',
            r'aws_access_key_id',
            r'GITHUB_TOKEN'
        ],
        'message': 'Tentative d\'écriture de credentials en dur détectée'
    },
    'unvalidated_packages': {
        'patterns': [
            r'npm\s+install\s+(?!react|plotly|recharts|tailwindcss)',
            r'pip\s+install\s+(?!pandas|numpy|scipy|pytest)',
        ],
        'message': 'Tentative d\'installation de package non validé détectée'
    }
}

# ============================================================================
# FONCTIONS
# ============================================================================

def read_stdin_context():
    """Lit le contexte JSON de Kiro."""
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}", file=sys.stderr)
        sys.exit(0)

def check_command_safety(tool_name: str, parameters: dict) -> tuple[bool, str]:
    """
    Vérifie si la commande est sûre.
    
    Returns:
        (is_safe, violation_message)
    """
    # Extraire le contenu à vérifier
    content_to_check = ""
    
    if tool_name == 'execute_pwsh':
        content_to_check = parameters.get('command', '')
    elif tool_name in ['fs_write', 'str_replace']:
        content_to_check = parameters.get('text', '') + parameters.get('path', '')
    elif tool_name == 'delete_file':
        content_to_check = parameters.get('targetFile', '')
    
    if not content_to_check:
        return True, ""
    
    # Vérifier chaque catégorie de patterns dangereux
    for category, config in BLOCKED_PATTERNS.items():
        for pattern in config['patterns']:
            if re.search(pattern, content_to_check, re.IGNORECASE):
                return False, f"{config['message']} (catégorie: {category})"
    
    return True, ""

def main():
    context = read_stdin_context()
    
    tool_name = context.get('toolName', '')
    parameters = context.get('parameters', {})
    
    print("=" * 70)
    print("🛡️  Pre-Tool Safety Check")
    print("=" * 70)
    print(f"Tool: {tool_name}")
    
    # Vérifier sécurité
    is_safe, violation_message = check_command_safety(tool_name, parameters)
    
    if not is_safe:
        print("\n❌ COMMAND BLOCKED")
        print(f"\nRaison: {violation_message}")
        print("\n⚠️  Violation de AGENTS.md Section 3.C (Interdictions Absolues):")
        print("  1. Ne jamais modifier la base de données source")
        print("  2. Ne jamais altérer les règles de la Constitution")
        print("  3. Ne jamais écrire de secrets/clés API en dur")
        print("  4. Ne jamais installer de paquets non validés")
        print("\n📖 Référence: .kiro/AGENTS.md Section 3.C")
        print("=" * 70)
        
        # Exit 2 = Bloquer l'action
        sys.exit(2)
    else:
        print("\n✅ Command is safe, proceeding...")
        print("=" * 70)
        
        # Exit 0 = Autoriser l'action
        sys.exit(0)

if __name__ == '__main__':
    main()
