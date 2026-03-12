import sys; sys.path.insert(0,".")
from app.services.scenario_health_service import get_all_scenario_health
reports = get_all_scenario_health()
with open("tmp/issues.txt","w") as f:
    for r in reports:
        for c in r.checks:
            if c.status != "good":
                f.write(f"{r.theme_key}|{c.name}|{c.message}\n")
print("OK")
