#!/usr/bin/env python3
"""
Hook de validation du README.md
Critères obligatoires (max 5 phrases):
1. Problématique + Solution
<<<<<<< HEAD
2. Personas (Coach/Scout/Broadcast)
=======
2. Personas
>>>>>>> 7db2a890808f65cb1ac8e142e64990096374fec2
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

<<<<<<< HEAD
def validate_readme_content(content):
=======
def validate_readme(content):
>>>>>>> 7db2a890808f65cb1ac8e142e64990096374fec2
    """Valide les 5 critères obligatoires"""
    errors = []
    
    # 1. Problématique + Solution
    if not re.search(r'Problématique.*:.*', content, re.IGNORECASE):
        errors.append("❌ Manque: Problématique")
    if not re.search(r'Solution.*:.*', content, re.IGNORECASE):
        errors.append("❌ Manque: Solution")
    
    # 2. Personas
<<<<<<< HEAD
    persona_count = sum([
        'coach' in content.lower(),
        'scout' in content.lower(),
        'broadcast' in content.lower()
    ])
    if persona_count < 2:
        errors.append("❌ Manque: Au moins 2 personas (Coach/Scout/Broadcast)")
=======
    persona_keywords = ['persona', 'coach', 'scout', 'broadcast']
    if not any(kw in content.lower() for kw in persona_keywords):
        errors.append("❌ Manque: Personas (Coach/Scout/Broadcast)")
>>>>>>> 7db2a890808f65cb1ac8e142e64990096374fec2
    
    # 3. Lien Vercel
    if not re.search(r'vercel\.app', content, re.IGNORECASE):
        errors.append("❌ Manque: Lien Vercel final")
    
    # 4. Installation
<<<<<<< HEAD
    if not re.search(r'npm|install|setup', content, re.IGNORECASE):
        errors.append("❌ Manque: Instructions d'installation")
    
    # 5. Brief global
    if not re.search(r'architecture|pipeline|dashboard|etl', content, re.IGNORECASE):
=======
    install_keywords = ['install', 'npm', 'pip', 'setup']
    if not any(kw in content.lower() for kw in install_keywords):
        errors.append("❌ Manque: Instructions d'installation")
    
    # 5. Brief global
    tech_keywords = ['architecture', 'pipeline', 'dashboard', 'analyse', 'etl']
    if not any(kw in content.lower() for kw in tech_keywords):
>>>>>>> 7db2a890808f65cb1ac8e142e64990096374fec2
        errors.append("❌ Manque: Brief global de la solution")
    
    # Validation longueur: MAX 5 phrases
    sentence_count = count_sentences(content)
    if sentence_count > 5:
        errors.append(f"❌ Trop de phrases: {sentence_count}/5 max")
    
<<<<<<< HEAD
    return errors, sentence_count
=======
    return errors
>>>>>>> 7db2a890808f65cb1ac8e142e64990096374fec2

def main():
    try:
        # Lire le contexte du hook
        hook_input = json.load(sys.stdin)
        
<<<<<<< HEAD
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
=======
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
>>>>>>> 7db2a890808f65cb1ac8e142e64990096374fec2
            print("\n📋 Critères obligatoires (MAX 5 phrases):", file=sys.stderr)
            print("  1. Problématique + Solution", file=sys.stderr)
            print("  2. Personas (Coach/Scout/Broadcast)", file=sys.stderr)
            print("  3. Lien Vercel final", file=sys.stderr)
            print("  4. Instructions d'installation", file=sys.stderr)
            print("  5. Brief global de la solution", file=sys.stderr)
<<<<<<< HEAD
            sys.exit(0)  # Ne pas bloquer, juste avertir
        
        print(f"✅ README.md conforme ({sentence_count}/5 phrases)", file=sys.stdout)
        sys.exit(0)
        
    except Exception as e:
        print(f"⚠️  Erreur validation README: {e}", file=sys.stderr)
=======
            sys.exit(2)  # Bloquer l'opération
        
        print("✅ README.md conforme aux 5 critères", file=sys.stdout)
        sys.exit(0)
        
    except Exception as e:
        print(f"Erreur validation README: {e}", file=sys.stderr)
>>>>>>> 7db2a890808f65cb1ac8e142e64990096374fec2
        sys.exit(0)  # Ne pas bloquer en cas d'erreur du hook

if __name__ == "__main__":
    main()
