import csv
import io
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# ── Configuración ─────────────────────────────────────────────────────────────
TARGET_CSV  = "target.csv"
HUNTER_CSV  = "ttpxhunter.csv"
OUTPUT_PNG  = "heatmap_ttpxhunter_apt29.png"
# ─────────────────────────────────────────────────────────────────────────────


def parse_csv(path):
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        return {row["title"]: set(row["ttps"].split()) for row in reader if row.get("ttps")}


def compute_metrics(target, hunter):
    rows = []
    for title, gt in target.items():
        pred = hunter.get(title, set())
        tp = len(gt & pred)
        p  = tp / len(pred) if pred else 0.0
        r  = tp / len(gt)   if gt   else 0.0
        f  = 2 * p * r / (p + r) if (p + r) else 0.0
        rows.append({
            "Report":        title,
            "Precision":     round(p, 3),
            "Recall":        round(r, 3),
            "F1":            round(f, 3),
            "TP":            tp,
            "Total_GT":      len(gt),
            "Total_Hunter":  len(pred),
        })
    return pd.DataFrame(rows).set_index("Report")


def build_heatmap(df, output_path):
    # Eliminar filas con todo a 0
    df = df[(df["Precision"] + df["Recall"] + df["F1"]) > 0]

    max_gt     = df["Total_GT"].max()
    max_hunter = df["Total_Hunter"].max()

    df_color = df[["Precision", "Recall", "F1"]].copy()
    df_color["TTPs\nCoincidence"]         = df["TP"] / df["Total_GT"]
    df_color["Total TTPs\n(CTI-HAL)"]    = df["Total_GT"]     / max_gt
    df_color["Total TTPs\n(TTPXHunter)"] = df["Total_Hunter"] / max_hunter

    # Anotaciones: 3 decimales para métricas, enteros para el resto
    annot = df_color.copy().astype(object)
    for col in ["Precision", "Recall", "F1"]:
        annot[col] = df_color[col].map(lambda x: f"{x:.3f}")
    annot["TTPs\nCoincidence"]         = df["TP"].map(lambda x: str(int(x)))
    annot["Total TTPs\n(CTI-HAL)"]    = df["Total_GT"].map(lambda x: str(int(x)))
    annot["Total TTPs\n(TTPXHunter)"] = df["Total_Hunter"].map(lambda x: str(int(x)))

    fig, ax = plt.subplots(figsize=(12, 7.5))
    sns.heatmap(
        df_color, annot=annot, fmt="", cmap="Blues", vmin=0, vmax=1,
        linewidths=0.5, linecolor="white",
        annot_kws={"size": 10, "weight": "bold"}, ax=ax,
        cbar_kws={"shrink": 0.7, "label": "Score"},
    )
    ax.set_title(
        "TTPXHunter vs CTI-HAL — APT29 (Caso 1)\n(Positive class metrics, TN excluded)",
        fontsize=12, fontweight="bold", pad=14,
    )
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", labelsize=10, length=0)
    ax.tick_params(axis="y", labelsize=9,  length=0)
    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Guardado: {output_path}")


if __name__ == "__main__":
    target = parse_csv(TARGET_CSV)
    hunter = parse_csv(HUNTER_CSV)
    df     = compute_metrics(target, hunter)
    build_heatmap(df, OUTPUT_PNG)
