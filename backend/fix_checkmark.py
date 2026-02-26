import os
import glob

replacements = {
    'ı': 'i', 'İ': 'I', 'ş': 's', 'Ş': 'S', 'ğ': 'g', 'Ğ': 'G', 
    'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C', 'ü': 'u', 'Ü': 'U',
    '✓': 'OK:', '—': '-', '“': '"', '”': '"', '‘': "'", '’': "'"
}

for p in glob.glob('alembic/versions/*.py'):
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # We only care about modifying print statements to avoid altering actual DB schema text
    # But wait, replacing them everywhere might ruin the textual prompts!
    # I should ONLY replace characters inside print(
    import re
    def replacer(match):
        text = match.group(0)
        for k, v in replacements.items():
            text = text.replace(k, v)
        return text

    new_content = re.sub(r'print\([^)]+\)', replacer, content)
    
    if new_content != content:
        with open(p, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Fixed", p)
