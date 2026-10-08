from pie.web.server import analyze_symbol

res = analyze_symbol("DIVISLAB.NS")
print("Symbol:", res["symbol"])
print("Primary Strategy:", res["strategy_display"])
print("Fit Score:", res["fit_score"])
print("Ranked Strategies:")
for r in res.get("ranked_strategies", []):
    print(f" - {r['strategy_display']}: {r['score']}")
