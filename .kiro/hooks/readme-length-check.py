#!/usr/bin/env python3
"""
Hook Kiro : README Length Validator

Déclencheur : PostToolUse (après édition fichiers)
Action : Vérifier que README.md reste concis (3-5 phrases)

Exit Codes:
  0 - Validation passed
  1 - Warning (trop long, mais ne bloque pas)
"""

import sys
import json
import re
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

MAX_SENTENCES = 5  # Maximum de phrases autorisées
MIN_SENTENCES = 3  # Minimum recommandé
MAX_CHARS = 800    # Maximum de caractères

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

def count_sentences(text):
    """Compte le nombre de phrases (approximatif)."""
    # Supprimer code blocks et liens markdown
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
    text = re.sub(r'\[.*?\]\(.*?\)', '', text)
    
    # Compter phrases (. ! ? suivis d'espace/fin)
    sentences = re.findall(r'[.!?](?:\s|$)', text)
    return len(sentences)

def main():
    context = read_stdin_context()
    
    tool_name = context.get('toolName', '')
    parameters = context.get('parameters', {})
    
    # Vérifier si c'est un fichier README
    file_path = parameters.get('path', '')
    
    if not file_path.lower().endswith('readme.md'):
        # Pas un README, skip
        sys.exit(0)
    
    # Lire contenu
    if tool_name == 'fs_write':
        content = parameters.get('text', '')
    elif tool_name == 'str_replace':
        try:
            content = Path(file_path).read_text(encoding='utf-8')
        except FileNotFoundError:
            sys.exit(0)
    else:
        sys.exit(0)
    
    # Analyser
    num_sentences = count_sentences(content)
    num_chars = len(content.strip())
    num_lines = content.count('\n') + 1
    
    # Rapport
    print("=" * 70)
    print("📄 README Length Validation Report")
    print("=" * 70)
    print(f"File: {file_path}")
    print("")
    print(f"📊 Statistiques:")
    print(f"  Phrases: {num_sentences}")
    print(f"  Caractères: {num_chars}")
    print(f"  Lignes: {num_lines}")
    print("")
    
    # Validation
    violations = []
    
    if num_sentences > MAX_SENTENCES:
        violations.append(
            f"❌ Trop de phrases: {num_sentences} (max: {MAX_SENTENCES})"
        )
    
    if num_sentences < MIN_SENTENCES:
        violations.append(
            f"⚠️  Trop court: {num_sentences} phrases (min recommandé: {MIN_SENTENCES})"
        )
    
    if num_chars > MAX_CHARS:
        violations.append(
            f"❌ Trop de caractères: {num_chars} (max: {MAX_CHARS})"
        )
    
    if violations:
        print("⚠️  VIOLATIONS:")
        for v in violations:
            print(f"  {v}")
        print("")
        print("💡 Recommandation:")
        print("  Le README doit rester ultra-concis (3-5 phrases).")
        print("  Déplacer détails vers QUICK-START.md ou .kiro/GETTING-STARTED.md")
        sys.exit(1)
    else:
        print("✅ README est concis et conforme!")
        print(f"  ✓ {num_sentences} phrases (recommandé: {MIN_SENTENCES}-{MAX_SENTENCES})")
        print(f"  ✓ {num_chars} caractères (< {MAX_CHARS})")
    
    print("=" * 70)
    sys.exit(0)

if __name__ == '__main__':
    main()
