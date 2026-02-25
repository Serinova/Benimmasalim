import os
import glob
import re

def replace_in_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    for old, new in replacements:
        content = content.replace(old, new)
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

replacements = [
    # Galata
    ("Hezarfen'in hayaleti", "Hezarfen'in hatırası"),
    ("Hezârfen'in hayaleti", "Hezârfen'in anısı"),
    ("Hezârfen'in Hayaleti", "Hezârfen'in Sesi"),
    ("neşeli hayaleti", "neşeli anısı"),
    # Tac Mahal
    ("Usta Taş Kakmacı Hayaleti", "Bilge Taş Kakmacı Sesi"),
    ("Usta TaÅŸ KakmacÄ± Hayaleti", "Bilge TaÅŸ KakmacÄ± Sesi"),
    ("neÅŸeli hayaleti", "neÅŸeli anÄ±sÄ±"),
    # Abu Simbel
    ("Usta Taş Yontucu Hayaleti", "Bilge Taş Yontucu Sesi"),
    ("Usta TaÅŸ Yontucu Hayaleti", "Bilge TaÅŸ Yontucu Sesi"),
]

# Process scripts
scripts = glob.glob('backend/scripts/create_*_scenario.py') + glob.glob('backend/alembic/versions/*.py')
for script in scripts:
    replace_in_file(script, replacements)
    
print("Replacements complete in scripts and alembic files.")
