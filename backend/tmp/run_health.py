import sys; sys.path.insert(0,".")
from app.services.scenario_health_service import get_all_scenario_health
reports = get_all_scenario_health()
reports.sort(key=lambda r: r.percentage, reverse=True)
avg = sum(r.percentage for r in reports)/len(reports)
a=sum(1 for r in reports if r.grade=="A")
b=sum(1 for r in reports if r.grade=="B")
out=[]
out.append(f"# Senaryo Saglik Raporu (Duzeltme Sonrasi)")
out.append(f"")
out.append(f"**{len(reports)} senaryo** | Ortalama: **%{avg:.0f}** | A: {a} | B: {b}")
out.append(f"")
out.append(f"| Not | % | Senaryo | Sorunlar |")
out.append(f"|-----|---|---------|----------|")
for r in reports:
    issues=[]
    for c in r.checks:
        if c.status!="good":
            tag="W" if c.status=="warning" else "C"
            issues.append(f"{tag}: {c.message}")
    issue_str=" / ".join(issues) if issues else "Sorun yok"
    out.append(f"| {r.grade} | {r.percentage} | {r.name} | {issue_str} |")
target=r"C:\Users\yusuf\.gemini\antigravity\brain\b8e0d0ed-d821-40d6-8c85-288f789b055b\health_report.md"
with open(target,"w",encoding="utf-8") as f:
    f.write("\n".join(out)+"\n")
print("OK")
