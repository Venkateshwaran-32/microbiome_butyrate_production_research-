from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mplconfig"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


INPUT_CSV = Path("Results/cobrapy_fba/tables/01_single_species_growth_and_butyrate_by_diet.csv")
OUTPUT_PNG = Path("Results/cobrapy_fba/figures/01_single_species_growth_comparison.png")

DIET_ORDER = ["western", "high_fiber"]
PALETTE = {"western": "#c46c2b", "high_fiber": "#2f7d4a"}


def short_species_label(species_name: str) -> str:
    parts = species_name.split("_")
    return f"{parts[0]} {parts[1]}" if len(parts) >= 2 else species_name


def load_plot_frame(path: Path) -> tuple[pd.DataFrame, list[str]]:
    df = pd.read_csv(path)
    df["short_species_name"] = df["species_name"].map(short_species_label)

    species_order = (
        df.groupby("short_species_name")["growth_value"]
        .max()
        .sort_values(ascending=False)
        .index.tolist()
    )
    return df, species_order


def main() -> None:
    sns.set_theme(
        style="whitegrid",
        rc={
            "axes.facecolor": "#fcfbf7",
            "figure.facecolor": "#fcfbf7",
            "grid.color": "#d9e2ec",
            "axes.edgecolor": "#4a5568",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        },
    )

    df, species_order = load_plot_frame(INPUT_CSV)
    max_growth = df["growth_value"].max()

    fig, ax = plt.subplots(figsize=(12, 8.5))
    sns.barplot(
        data=df,
        x="growth_value",
        y="short_species_name",
        hue="diet_name",
        order=species_order,
        hue_order=DIET_ORDER,
        palette=PALETTE,
        orient="h",
        dodge=True,
        ax=ax,
    )

    ax.set_title("Single-species growth by diet", fontsize=20, weight="bold", pad=16)
    ax.set_xlabel("Growth value", labelpad=12)
    ax.set_ylabel("")
    ax.set_xlim(0, max_growth * 1.22)
    ax.legend(title="", frameon=False, loc="upper right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", length=0)

    for container in ax.containers:
        labels = [f"{bar.get_width():.3f}" for bar in container]
        ax.bar_label(container, labels=labels, padding=5, fontsize=9)

    fig.tight_layout()
    OUTPUT_PNG.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PNG, dpi=220, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Wrote {OUTPUT_PNG}")


if __name__ == "__main__":
    main()
