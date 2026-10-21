#!/usr/bin/env python3
"""
Hook de validation du README.md
Critères obligatoires (max 5 phrases):
1. Problématique + Solution
2. Personas
3. Lien Vercel final
4. Instructions d'installation
5. Brief global de la solution
"""

import sys
import json
import re
from pathlib import Path

def count_sentences(text):
    """Compte les phrases (terminées par . ! ?)"""
    # Ignore les URLs et les versions (Node 18+, v≤13)
    cleaned = re.sub(r'https?://[^\s]+', '', text)
    cleaned = re.sub(r'v[≤≥<>]\d+', '', cleaned)
    cleaned = re.sub(r'Node \d+\+', '', cleaned)
    
    sentences = re.split(r'[.!?]+\s+', cleaned.strip())
    sentences = [s for s in sentences if s and len(s.strip()) > 10]
    return len(sentences)

def validate_readme(content):
    """Valide les 5 critères obligatoires"""
    errors = []
    
    # 1. Problématique + Solution
    if not re.search(r'Problématique.*:.*', content, re.IGNORECASE):
        errors.append("❌ Manque: Problématique")
    if not re.search(r'Solution.*:.*', content, re.IGNORECASE):
        errors.append("❌ Manque: Solution")
    
    # 2. Personas
    persona_keywords = ['persona', 'coach', 'scout', 'broadcast']
    if not any(kw in content.lower() for kw in persona_keywords):
        errors.append("❌ Manque: Personas (Coach/Scout/Broadcast)")
    
    # 3. Lien Vercel
    if not re.search(r'vercel\.app', content, re.IGNORECASE):
        errors.append("❌ Manque: Lien Vercel final")
    
    # 4. Installation
    install_keywords = ['install', 'npm', 'pip', 'setup']
    if not any(kw in content.lower() for kw in install_keywords):
        errors.append("❌ Manque: Instructions d'installation")
    
    # 5. Brief global
    tech_keywords = ['architecture', 'pipeline', 'dashboard', 'analyse', 'etl']
    if not any(kw in content.lower() for kw in tech_keywords):
        errors.append("❌ Manque: Brief global de la solution")
    
    # Validation longueur: MAX 5 phrases
    sentence_count = count_sentences(content)
    if sentence_count > 5:
        errors.append(f"❌ Trop de phrases: {sentence_count}/5 max")
    
    return errors

def main():
    try:
        # Lire le contexte du hook
        hook_input = json.load(sys.stdin)
        
        # Vérifier si c'est une modification du README
        tool_name = hook_input.get('toolName', '')
        if tool_name not in ['fs_write', 'str_replace', 'fs_append']:
            sys.exit(0)  # Ignorer les autres outils
        
        # Vérifier le fichier modifié
        params = hook_input.get('toolParameters', {})
        file_path = params.get('path', '')
        
        if not file_path.endswith('README.md'):
            sys.exit(0)  # Pas le README
        
        # Valider le contenu
        content = params.get('text', '') or params.get('newStr', '')
        if not content:
            sys.exit(0)
        
        errors = validate_readme(content)
        
        if errors:
            print("🚨 README.md non conforme:", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            print("\n📋 Critères obligatoires (MAX 5 phrases):", file=sys.stderr)
            print("  1. Problématique + Solution", file=sys.stderr)
            print("  2. Personas (Coach/Scout/Broadcast)", file=sys.stderr)
            print("  3. Lien Vercel final", file=sys.stderr)
            print("  4. Instructions d'installation", file=sys.stderr)
            print("  5. Brief global de la solution", file=sys.stderr)
            sys.exit(2)  # Bloquer l'opération
        
        print("✅ README.md conforme aux 5 critères", file=sys.stdout)
        sys.exit(0)
        
    except Exception as e:
        print(f"Erreur validation README: {e}", file=sys.stderr)
        sys.exit(0)  # Ne pas bloquer en cas d'erreur du hook

if __name__ == "__main__":
    main()
