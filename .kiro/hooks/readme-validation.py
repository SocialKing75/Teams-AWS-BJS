#!/usr/bin/env python3
"""
Hook de validation du README.md
Critères obligatoires (max 5 phrases):
1. Problématique + Solution
2. Personas (Coach/Scout/Broadcast)
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

def validate_readme_content(content):
    """Valide les 5 critères obligatoires"""
    errors = []
    
    # 1. Problématique + Solution
    if not re.search(r'Problématique.*:.*', content, re.IGNORECASE):
        errors.append("❌ Manque: Problématique")
    if not re.search(r'Solution.*:.*', content, re.IGNORECASE):
        errors.append("❌ Manque: Solution")
    
    # 2. Personas
    persona_count = sum([
        'coach' in content.lower(),
        'scout' in content.lower(),
        'broadcast' in content.lower()
    ])
    if persona_count < 2:
        errors.append("❌ Manque: Au moins 2 personas (Coach/Scout/Broadcast)")
    
    # 3. Lien Vercel
    if not re.search(r'vercel\.app', content, re.IGNORECASE):
        errors.append("❌ Manque: Lien Vercel final")
    
    # 4. Installation
    if not re.search(r'npm|install|setup', content, re.IGNORECASE):
        errors.append("❌ Manque: Instructions d'installation")
    
    # 5. Brief global
    if not re.search(r'architecture|pipeline|dashboard|etl', content, re.IGNORECASE):
        errors.append("❌ Manque: Brief global de la solution")
    
    # Validation longueur: MAX 5 phrases
    sentence_count = count_sentences(content)
    if sentence_count > 5:
        errors.append(f"❌ Trop de phrases: {sentence_count}/5 max")
    
    return errors, sentence_count

def main():
    try:
        # Lire le contexte du hook
        hook_input = json.load(sys.stdin)
        
        # Lire le README
        readme_path = Path('README.md')
        if not readme_path.exists():
            sys.exit(0)
        
        content = readme_path.read_text(encoding='utf-8')
        errors, sentence_count = validate_readme_content(content)
        
        if errors:
            print("🚨 README.md NON CONFORME:", file=sys.stderr)
            for error in errors:
                print(f"  {error}", file=sys.stderr)
            print(f"\n📊 Phrases détectées: {sentence_count}/5", file=sys.stderr)
            print("\n📋 Critères obligatoires (MAX 5 phrases):", file=sys.stderr)
            print("  1. Problématique + Solution", file=sys.stderr)
            print("  2. Personas (Coach/Scout/Broadcast)", file=sys.stderr)
            print("  3. Lien Vercel final", file=sys.stderr)
            print("  4. Instructions d'installation", file=sys.stderr)
            print("  5. Brief global de la solution", file=sys.stderr)
            sys.exit(0)  # Ne pas bloquer, juste avertir
        
        print(f"✅ README.md conforme ({sentence_count}/5 phrases)", file=sys.stdout)
        sys.exit(0)
        
    except Exception as e:
        print(f"⚠️  Erreur validation README: {e}", file=sys.stderr)
        sys.exit(0)  # Ne pas bloquer en cas d'erreur du hook

if __name__ == "__main__":
    main()
