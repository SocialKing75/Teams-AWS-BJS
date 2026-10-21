#!/usr/bin/env python3
"""
Hook Kiro : Physics Guardrail

Déclencheur : PostToolUse (après édition fichiers Python)
Action : Valider que les constantes physiques respectent les invariants NFL

Exit Codes:
  0 - Validation passed
  1 - Validation failed (warnings logged, no block)
  2 - Critical violation (should block, but PostToolUse can't block retroactively)
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# INVARIANTS PHYSIQUES NFL
# ============================================================================

PHYSICS_CONSTRAINTS = {
    'MAX_SPEED': {
        'value': 13.0,
        'unit': 'yards/s',
        'description': 'Vitesse maximale humaine (~23 mph, record NFL)'
    },
    'MAX_ACCELERATION': {
        'value': 8.0,
        'unit': 'yards/s²',
        'description': 'Accélération maximale biomécaniquement plausible'
    },
    'MIN_REACTION_TIME': {
        'value': 0.2,
        'unit': 'seconds',
        'description': 'Temps de réaction neurologique minimum'
    },
    'FIELD_LENGTH': {
        'value': 120.0,
        'unit': 'yards',
        'description': 'Longueur terrain NFL (incluant end zones)'
    },
    'FIELD_WIDTH': {
        'value': 53.3,
        'unit': 'yards',
        'description': 'Largeur terrain NFL'
    }
}

# Patterns regex pour extraire constantes Python
CONSTANT_PATTERN = re.compile(
    r'^([A-Z_]+)\s*=\s*([\d.]+)',
    re.MULTILINE
)

# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def read_stdin_context() -> Dict:
    """
    Lit le contexte JSON fourni par Kiro sur stdin.
    
    Format attendu:
    {
        "toolName": "fs_write" | "str_replace",
        "parameters": {
            "path": "src/engine/constants.py",
            "text": "...",
            ...
        },
        "sessionId": "...",
        ...
    }
    """
    try:
        context = json.load(sys.stdin)
        return context
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)


def extract_constants_from_code(code: str) -> Dict[str, float]:
    """
    Extrait constantes Python de la forme CONSTANT_NAME = value.
    
    Example:
        MAX_SPEED = 13.0
        MAX_ACCELERATION = 8.0
    
    Returns:
        {'MAX_SPEED': 13.0, 'MAX_ACCELERATION': 8.0}
    """
    matches = CONSTANT_PATTERN.findall(code)
    return {name: float(value) for name, value in matches}


def validate_constant(
    name: str, 
    value: float, 
    constraint: Dict
) -> Tuple[bool, str]:
    """
    Valide qu'une constante respecte la contrainte physique.
    
    Returns:
        (is_valid, message)
    """
    max_value = constraint['value']
    unit = constraint['unit']
    description = constraint['description']
    
    if value > max_value:
        return False, (
            f"❌ {name} = {value} {unit} exceeds physical limit of {max_value} {unit}\n"
            f"   Reason: {description}"
        )
    
    return True, f"✅ {name} = {value} {unit} is valid"


# ============================================================================
# LOGIQUE PRINCIPALE
# ============================================================================

def main():
    # 1. Lire contexte Kiro
    context = read_stdin_context()
    tool_name = context.get('toolName', '')
    parameters = context.get('parameters', {})
    
    # 2. Vérifier si un fichier Python a été modifié
    if tool_name not in ['fs_write', 'str_replace']:
        print("[INFO] Hook skipped: tool not file-editing", file=sys.stderr)
        sys.exit(0)
    
    file_path = parameters.get('path', '')
    if not file_path.endswith('.py'):
        print(f"[INFO] Hook skipped: {file_path} is not a Python file", file=sys.stderr)
        sys.exit(0)
    
    # 3. Extraire le contenu du fichier modifié
    if tool_name == 'fs_write':
        code = parameters.get('text', '')
    elif tool_name == 'str_replace':
        # Pour str_replace, on doit lire le fichier résultant
        try:
            code = Path(file_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            print(f"[WARNING] File {file_path} not found after str_replace", file=sys.stderr)
            sys.exit(0)
    else:
        code = ''
    
    # 4. Extraire constantes du code
    constants = extract_constants_from_code(code)
    
    if not constants:
        print(f"[INFO] No constants found in {file_path}", file=sys.stderr)
        sys.exit(0)
    
    # 5. Valider chaque constante
    violations: List[str] = []
    valid_constants: List[str] = []
    
    for const_name, const_value in constants.items():
        if const_name in PHYSICS_CONSTRAINTS:
            is_valid, message = validate_constant(
                const_name, 
                const_value, 
                PHYSICS_CONSTRAINTS[const_name]
            )
            
            if is_valid:
                valid_constants.append(message)
            else:
                violations.append(message)
    
    # 6. Générer rapport
    report = []
    report.append("=" * 70)
    report.append("🔬 Physics Guardrail Validation Report")
    report.append("=" * 70)
    report.append(f"File: {file_path}")
    report.append(f"Tool: {tool_name}")
    report.append("")
    
    if valid_constants:
        report.append("Valid Constants:")
        for msg in valid_constants:
            report.append(f"  {msg}")
        report.append("")
    
    if violations:
        report.append("⚠️  VIOLATIONS DETECTED:")
        for msg in violations:
            report.append(f"  {msg}")
        report.append("")
        report.append("Action Required:")
        report.append("  Please review and correct the constants above.")
        report.append("  Reference: .kiro/AGENTS.md Section 2.3 (Physical Constraints)")
    else:
        report.append("✅ All constants are within physical constraints!")
    
    report.append("=" * 70)
    
    # 7. Écrire rapport sur stdout (visible dans Kiro)
    output = "\n".join(report)
    print(output)
    
    # 8. Exit avec code approprié
    if violations:
        # Exit 1 = warning (ne bloque pas car PostToolUse ne peut pas annuler)
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
