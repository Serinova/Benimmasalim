path = \"scripts/update_space_adventure_scenario.py\"`nwith open(path) as f: c=f.read()`ni=c.find(\"scenario.description =\")`nprint(c[i:i+120] if i>=0 else \"not found\")
