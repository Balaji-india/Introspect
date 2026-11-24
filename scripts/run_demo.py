"""Run the full Introspect pipeline on a data folder and print the daily brief.

    python scripts/run_demo.py                     # synthetic sample data
    python scripts/run_demo.py --data path/to/fitbit_export --user 1503960366
    python scripts/run_demo.py --plot              # also save docs/demo_readiness.png
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from introspect import pipeline  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(ROOT / "data" / "sample"))
    ap.add_argument("--user", type=int, default=None)
    ap.add_argument("--plot", action="store_true")
    ap.add_argument("--json", action="store_true", help="print the full JSON result")
    a = ap.parse_args()

    res = pipeline.run(a.data, a.user)
    if a.json:
        print(json.dumps(res, indent=2, default=str))
        return
    print("=" * 64)
    print(" INTROSPECT  -  daily brief")
    print("=" * 64)
    print(res["brief"]["text"], f"\n  [source: {res['brief']['source']}]\n")
    print("Why-engine insights:")
    for i in res["insights"]:
        print(f"  - {i['sentence']}  (rho={i['rho']}, p={i['p_value']}, n={i['n_days']} days)")
    print("\nAnomalies vs your personal baseline:")
    for an in res["anomalies"][-5:]:
        d = ", ".join(f"{x['metric']} {x['value']:g} vs normal {x['your_normal']:g}" for x in an["drift"]) or \
            "unusual combination (Isolation Forest)"
        print(f"  - {an['date']}: {d}")
    f = res["forecast"]
    if f.get("status") == "ok":
        e, w = f["eval"], f["what_if"]
        print(f"\nTomorrow's readiness forecast ({f['model']}): {f['tomorrow_readiness']}")
        print(f"  what-if: screens off by 11 pm -> {w['screens_off_by_11pm']}, usual night -> {w['usual_night']}, "
              f"2 h late-night screen -> {w['late_night_2h']}")
        print(f"  backtest MAE {e['test_mae']} vs persistence {e['persistence_mae']} / personal mean "
              f"{e['personal_mean_mae']} ({e['train_days']} train / {e['test_days']} test days)")
    print("\nFacts released through the privacy gateway (nothing else leaves the device):")
    print(json.dumps(res["facts"], indent=2))

    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import pandas as pd
        tl = pd.DataFrame(res["timeline"])
        tl["date"] = pd.to_datetime(tl["date"])
        fig, ax = plt.subplots(figsize=(10, 3.6))
        ax.plot(tl["date"], tl["readiness"], color="#1B1F6B", lw=2, label="Readiness (50 = your normal)")
        an = tl[tl["is_anomaly"] == True]  # noqa: E712
        ax.scatter(an["date"], an["readiness"], color="#C2410C", zorder=3, s=40, label="Flagged day")
        ex = tl[tl["is_exam_day"] == 1]
        if len(ex):
            ax.axvspan(ex["date"].min(), ex["date"].max(), color="#FD9B36", alpha=0.15, label="Exam week")
        ax.axhline(50, color="#6B6459", ls="--", lw=1)
        ax.set_ylim(0, 100); ax.legend(loc="lower left", frameon=False, fontsize=9)
        ax.spines[["top", "right"]].set_visible(False)
        ax.set_title("Introspect: readiness vs personal baseline (synthetic demo user)", loc="left")
        fig.tight_layout()
        out = ROOT / "docs" / "demo_readiness.png"
        fig.savefig(out, dpi=150)
        print("\nSaved plot ->", out)


if __name__ == "__main__":
    main()
