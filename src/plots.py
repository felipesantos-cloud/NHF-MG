from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, LinearSegmentedColormap, ListedColormap


def figura_localizacao_barras(
    mg_muni,
    muni_alvo,
    nome_oficial,
    lat_real,
    lon_real,
    tb_alvo,
    meta,
    valores_plot,
    titulo_barras,
):
    tb_minus = tb_alvo - 3.0
    tb_plus = tb_alvo + 3.0

    fig, (ax1, ax2) = plt.subplots(
        1,
        2,
        figsize=(15, 5.8),
        gridspec_kw={"width_ratios": [1.2, 1]},
        dpi=120,
    )

    mg_muni.plot(ax=ax1, color="#E8ECEF", edgecolor="#FFFFFF", linewidth=0.25)
    muni_alvo.plot(ax=ax1, color="#1565C0", edgecolor="black", linewidth=1.4)
    ax1.set_title(
        f"{nome_oficial} - MG\nLAT: {lat_real:.2f} | LON: {lon_real:.2f}",
        fontsize=12,
        fontweight="bold",
    )
    ax1.axis("off")

    labels = [
        f"< {tb_minus:.1f}°C",
        f"< {tb_alvo:.1f}°C\n(Limiar base)",
        f"< {tb_plus:.1f}°C",
    ]
    cores = ["#1E88E5", "#004D40", "#43A047"]
    bars = ax2.bar(labels, valores_plot, color=cores, width=0.52, edgecolor="black")
    ax2.set_ylabel("Horas de frio acumuladas (h)", fontsize=11, fontweight="bold")
    ax2.set_title(titulo_barras, fontsize=12.5, fontweight="bold")
    ax2.grid(axis="y", linestyle="--", alpha=0.35)
    ax2.axhline(
        y=meta,
        color="red",
        linestyle="--",
        linewidth=1.5,
        label=f"Meta de aptidão ({meta:g} h)",
    )
    ax2.legend(loc="upper right")

    y_max = max(list(map(float, valores_plot)) + [float(meta), 1.0]) * 1.2
    ax2.set_ylim(0, y_max)
    for bar in bars:
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + y_max * 0.02,
            f"{bar.get_height():.1f} h",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    fig.tight_layout()
    return fig


def figura_historico(df_hist, tb_alvo, meta, media_base, nome_oficial):
    fig, ax = plt.subplots(figsize=(15, 6.2), dpi=120)

    anos = df_hist["Ano"].astype(str).values
    valores = df_hist["NHF"].values
    cores = ["#2a699b" if v >= meta else "#e68438" for v in valores]

    bars = ax.bar(anos, valores, color=cores, width=0.65, edgecolor="#1a1a1a", zorder=2)
    ax.axhline(
        y=media_base,
        color="#113a63",
        linestyle="-",
        linewidth=2.4,
        label=f"Média climatológica ({media_base:.1f} h)",
        zorder=3,
    )
    ax.axhline(
        y=meta,
        color="#d95f0e",
        linestyle="--",
        linewidth=1.8,
        label=f"Meta de aptidão ({meta:g} h)",
        zorder=3,
    )

    ax.set_ylabel(f"Horas de frio acumuladas (< {tb_alvo:g}°C) [h]", fontweight="bold")
    ax.set_title(
        f"Climatologia de acúmulo de frio - {nome_oficial} MG\n"
        f"{anos[0]} a {anos[-1]}",
        fontsize=14,
        fontweight="bold",
        pad=12,
    )

    limite_y = max(list(map(float, valores)) + [float(media_base), float(meta), 1.0]) * 1.18
    ax.set_ylim(0, limite_y)

    for bar in bars:
        yval = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            yval + limite_y * 0.012,
            f"{yval:.0f}",
            ha="center",
            va="bottom",
            fontsize=7.5,
            rotation=90,
        )

    ax.tick_params(axis="x", rotation=45, labelsize=8.5)
    ax.legend(loc="upper right", framealpha=0.95)
    ax.grid(axis="y", linestyle=":", color="#cccccc", alpha=0.7, zorder=1)
    fig.tight_layout()
    return fig


def _limites_dinamicos(meta):
    target_max = meta * 1.25 if meta > 0 else 10
    passo_teorico = target_max / 8.0
    magnitude = 10 ** math.floor(math.log10(max(passo_teorico, 1e-9)))
    fator = passo_teorico / magnitude

    if fator <= 1.2:
        passo = 1 * magnitude
    elif fator <= 2.5:
        passo = 2 * magnitude
    elif fator <= 4:
        passo = 2.5 * magnitude
    elif fator <= 7:
        passo = 5 * magnitude
    else:
        passo = 10 * magnitude

    passo = max(int(round(passo)), 1)
    teto = math.ceil(target_max / passo) * passo
    limites = list(range(0, teto + passo, passo))
    if len(limites) < 2:
        limites = [0, passo]
    return limites


def figura_mapa_espacial(
    da_espacial,
    lat_coord,
    lon_coord,
    mg_muni,
    mg_estado,
    muni_alvo,
    nome_oficial,
    lon_alvo,
    lat_alvo,
    tb_alvo,
    meta,
    ano,
):
    limites = _limites_dinamicos(meta)

    fig, ax = plt.subplots(figsize=(12, 9), dpi=120)
    cores_suaves = [
        "#ebd9b4",
        "#fbf0d5",
        "#e3ebd3",
        "#bce0d2",
        "#8bc5cc",
        "#5698b8",
        "#2a699b",
        "#113a63",
        "#081d38",
    ]
    cmap_cont = LinearSegmentedColormap.from_list("SuaveAgro", cores_suaves, N=256)
    cores = cmap_cont(np.linspace(0, 1, len(limites)))
    cmap = ListedColormap(cores)
    norm = BoundaryNorm(limites, cmap.N, extend="max")

    mesh = da_espacial.plot.pcolormesh(
        ax=ax,
        x=lon_coord,
        y=lat_coord,
        cmap=cmap,
        norm=norm,
        add_colorbar=False,
        zorder=1,
    )

    mg_muni.plot(ax=ax, facecolor="none", edgecolor="#444444", linewidth=0.18, alpha=0.4, zorder=2)
    mg_estado.plot(ax=ax, facecolor="none", edgecolor="#1a1a1a", linewidth=1.5, zorder=3)
    muni_alvo.plot(ax=ax, facecolor="none", edgecolor="#ff00ff", linewidth=3.0, zorder=4)

    cbar = plt.colorbar(mesh, ax=ax, orientation="vertical", shrink=0.75, pad=0.02, drawedges=True)
    cbar.set_label(f"Acúmulo de frio < {tb_alvo:g}°C (horas)", fontweight="bold", labelpad=12)
    cbar.set_ticks(limites)
    labels = [str(x) for x in limites]
    labels[-1] = f"> {limites[-1]}"
    cbar.set_ticklabels(labels)

    ax.set_title(
        f"Distribuição espacial de frio abaixo de {tb_alvo:g}°C - Minas Gerais ({ano})\n"
        f"Destaque: {nome_oficial} | Meta: {meta:g} h",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    ax.set_xlabel("Longitude", fontweight="bold")
    ax.set_ylabel("Latitude", fontweight="bold")

    bounds = mg_estado.total_bounds
    ax.set_xlim(bounds[0] - 0.2, bounds[2] + 0.2)
    ax.set_ylim(bounds[1] - 0.2, bounds[3] + 0.2)
    ax.grid(True, linestyle=":", alpha=0.35)

    ax.annotate(
        nome_oficial,
        xy=(lon_alvo, lat_alvo),
        xytext=(lon_alvo + 1, lat_alvo - 1),
        arrowprops=dict(facecolor="black", shrink=0.05, width=1.2, headwidth=6),
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="black", lw=1, alpha=0.85),
        zorder=5,
    )

    fig.tight_layout()
    return fig
