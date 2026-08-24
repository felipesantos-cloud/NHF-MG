from __future__ import annotations

import glob
import math
from pathlib import Path
from typing import Iterable

import geobr
import numpy as np
import pandas as pd
import xarray as xr


MESES_INVERNO = (5, 6, 7, 8, 9)
VARS_IGNORADAS = {"crs", "spatial_ref", "time_bnds", "lat_bnds", "lon_bnds"}


def calcular_nhf_serie(tmin, tmax, tb, ttm1=0, ttm=16, ttm2=24):
    """Calcula NHF para uma série temporal 1D, preservando a lógica original."""
    tmin = np.asarray(tmin, dtype=float)
    tmax = np.asarray(tmax, dtype=float)

    n = len(tmin)
    h = np.zeros(n)
    tm1 = np.zeros(n)
    tm1[0] = tmax[0]
    tm1[1:] = tmax[:-1]

    for i in range(n):
        if (
            np.isnan(tmin[i])
            or np.isnan(tmax[i])
            or tmin[i] == -999.0
            or tmax[i] == -999.0
        ):
            h[i] = np.nan
            continue

        ta, n_k = 0, 0
        for k in range(ttm1, ttm + 1):
            tt1 = tm1[i] + (tmin[i] - tm1[i]) * math.sin(
                abs((math.pi / 2) * (k - ttm1) / (ttm - ttm1))
            )
            if (tt1 - tb) < 0:
                n_k += 1
                if n_k == 1:
                    ta = k

        tt, n_j = 0, 0
        for j in range(ttm, ttm2 + 1):
            tt2 = tmin[i] + (tmax[i] - tmin[i]) * math.sin(
                abs((math.pi / 2) * (j - ttm) / (ttm2 - ttm))
            )
            if (tt2 - tb) > 0:
                n_j += 1
                if n_j == 1:
                    tt = j

        if tm1[i] >= tb and tmax[i] >= tb and tmin[i] >= tb:
            h[i] = 0
        elif tm1[i] < tb and tmax[i] < tb:
            h[i] = 24
        elif tm1[i] > tb and tmax[i] > tb and tmin[i] < tb:
            h[i] = tt - ta
        elif tm1[i] <= tb and tmax[i] > tb and tmin[i] < tb:
            h[i] = tt - ttm1
        elif tm1[i] > tb and tmax[i] <= tb:
            h[i] = ttm2 - ta
        else:
            h[i] = 0

    return h


def calcular_nhf_grade(tmin, tmax, tb, ttm1=0, ttm=16, ttm2=24):
    """Calcula NHF em uma grade 3D (tempo, latitude, longitude)."""
    tmin = np.asarray(tmin, dtype=float)
    tmax = np.asarray(tmax, dtype=float)

    if tmin.shape != tmax.shape:
        raise ValueError("Tmin e Tmax precisam ter a mesma forma.")
    if tmin.ndim != 3:
        raise ValueError("Tmin/Tmax devem ter dimensões (tempo, latitude, longitude).")

    n_dias, n_lat, n_lon = tmin.shape
    h_total = np.zeros((n_lat, n_lon))
    tm1 = np.zeros_like(tmax)
    tm1[0] = tmax[0]
    tm1[1:] = tmax[:-1]

    for i in range(n_dias):
        validos = (
            ~np.isnan(tmin[i])
            & ~np.isnan(tmax[i])
            & (tmin[i] != -999.0)
            & (tmax[i] != -999.0)
        )

        ta = np.zeros((n_lat, n_lon))
        encontrado_ta = np.zeros((n_lat, n_lon), dtype=bool)
        for k in range(ttm1, ttm + 1):
            seno_k = math.sin(abs((math.pi / 2) * (k - ttm1) / (ttm - ttm1)))
            tt1 = tm1[i] + (tmin[i] - tm1[i]) * seno_k
            cond_k = validos & (tt1 < tb) & (~encontrado_ta)
            ta[cond_k] = k
            encontrado_ta[cond_k] = True

        tt = np.zeros((n_lat, n_lon))
        encontrado_tt = np.zeros((n_lat, n_lon), dtype=bool)
        for j in range(ttm, ttm2 + 1):
            seno_j = math.sin(abs((math.pi / 2) * (j - ttm) / (ttm2 - ttm)))
            tt2 = tmin[i] + (tmax[i] - tmin[i]) * seno_j
            cond_j = validos & (tt2 > tb) & (~encontrado_tt)
            tt[cond_j] = j
            encontrado_tt[cond_j] = True

        h_dia = np.zeros((n_lat, n_lon))
        c2 = validos & (tm1[i] < tb) & (tmax[i] < tb)
        h_dia[c2] = 24.0
        c3 = validos & (tm1[i] > tb) & (tmax[i] > tb) & (tmin[i] < tb)
        h_dia[c3] = tt[c3] - ta[c3]
        c4 = validos & (tm1[i] <= tb) & (tmax[i] > tb) & (tmin[i] < tb)
        h_dia[c4] = tt[c4] - ttm1
        c5 = validos & (tm1[i] > tb) & (tmax[i] <= tb)
        h_dia[c5] = ttm2 - ta[c5]

        h_total += np.where(validos, h_dia, 0.0)

    h_total[np.isnan(tmin[0]) | (tmin[0] == -999.0)] = np.nan
    return h_total


def carregar_geometrias_mg(ano: int = 2020):
    """Baixa geometrias oficiais de Minas Gerais via geobr."""
    municipios = geobr.read_municipality(code_muni="MG", year=ano)
    estado = geobr.read_state(code_state="MG", year=ano)
    municipios = municipios.to_crs(4326)
    estado = estado.to_crs(4326)
    return municipios, estado


def localizar_municipio(municipios, nome: str):
    """Localiza um município pelo nome e retorna geometria + centróide."""
    alvo = municipios[municipios["name_muni"].str.casefold() == nome.strip().casefold()]
    if alvo.empty:
        raise ValueError(f'Município "{nome}" não encontrado em Minas Gerais.')

    # Preserva a escolha metodológica do código original: usar o centróide municipal.
    geom_proj = alvo.to_crs(31983)
    centroide_proj = geom_proj.geometry.centroid.iloc[0]
    centroide = (
        __import__("geopandas").GeoSeries([centroide_proj], crs=31983)
        .to_crs(4326)
        .iloc[0]
    )

    return alvo, float(centroide.y), float(centroide.x), alvo["name_muni"].iloc[0]


def listar_arquivos_nc(pasta: str | Path) -> list[str]:
    return sorted(glob.glob(str(Path(pasta) / "*.nc")))


def abrir_datasets(pasta_tmax: str | Path, pasta_tmin: str | Path):
    arquivos_tmax = listar_arquivos_nc(pasta_tmax)
    arquivos_tmin = listar_arquivos_nc(pasta_tmin)

    if not arquivos_tmax:
        raise FileNotFoundError(f"Nenhum .nc encontrado em {pasta_tmax}")
    if not arquivos_tmin:
        raise FileNotFoundError(f"Nenhum .nc encontrado em {pasta_tmin}")

    ds_tmax = xr.open_mfdataset(arquivos_tmax, combine="by_coords")
    ds_tmin = xr.open_mfdataset(arquivos_tmin, combine="by_coords")
    return ds_tmax, ds_tmin


def detectar_coordenadas_e_variaveis(ds_tmax: xr.Dataset, ds_tmin: xr.Dataset):
    lat_coord = "latitude" if "latitude" in ds_tmax.coords else "lat"
    lon_coord = "longitude" if "longitude" in ds_tmax.coords else "lon"

    if lat_coord not in ds_tmax.coords or lon_coord not in ds_tmax.coords:
        raise ValueError("Não foi possível identificar latitude/longitude nos NetCDF.")

    vars_tmax = [v for v in ds_tmax.data_vars if v.lower() not in VARS_IGNORADAS]
    vars_tmin = [v for v in ds_tmin.data_vars if v.lower() not in VARS_IGNORADAS]

    if not vars_tmax or not vars_tmin:
        raise ValueError("Não foi possível identificar as variáveis de Tmax/Tmin.")

    return lat_coord, lon_coord, vars_tmax[0], vars_tmin[0]


def extrair_serie_municipio(
    ds_tmax: xr.Dataset,
    ds_tmin: xr.Dataset,
    lat_alvo: float,
    lon_alvo: float,
):
    lat_coord, lon_coord, var_tmax, var_tmin = detectar_coordenadas_e_variaveis(ds_tmax, ds_tmin)

    lon_busca = lon_alvo
    if float(ds_tmax[lon_coord].max()) > 180 and lon_alvo < 0:
        lon_busca = lon_alvo + 360.0

    ponto_tmax = ds_tmax.sel({lat_coord: lat_alvo, lon_coord: lon_busca}, method="nearest")
    ponto_tmin = ds_tmin.sel({lat_coord: lat_alvo, lon_coord: lon_busca}, method="nearest")

    lat_real = float(ponto_tmax[lat_coord].values)
    lon_real = float(ponto_tmax[lon_coord].values)
    if lon_real > 180:
        lon_real -= 360.0

    s_tmax = ponto_tmax[var_tmax].to_series().rename("Tmax")
    s_tmin = ponto_tmin[var_tmin].to_series().rename("Tmin")
    df_temp = pd.concat([s_tmax, s_tmin], axis=1).dropna()
    df_temp.index = pd.to_datetime(df_temp.index)

    return df_temp, lat_real, lon_real, lat_coord, lon_coord, var_tmax, var_tmin


def filtrar_inverno(df_temp: pd.DataFrame, meses: Iterable[int] = MESES_INVERNO):
    df = df_temp[df_temp.index.month.isin(tuple(meses))].copy()
    df["Ano"] = df.index.year
    return df


def calcular_climatologia_anual(df_inverno: pd.DataFrame, tb_alvo: float, min_dias: int = 140):
    tb_minus = tb_alvo - 3.0
    tb_plus = tb_alvo + 3.0

    resultados_anuais = []
    resultados_historicos_base = []

    for ano in sorted(df_inverno["Ano"].unique()):
        df_ano = df_inverno[df_inverno["Ano"] == ano]
        if len(df_ano) < min_dias:
            continue

        tmin = df_ano["Tmin"].values
        tmax = df_ano["Tmax"].values

        nhf_min = np.nansum(calcular_nhf_serie(tmin, tmax, tb=tb_minus))
        nhf_base = np.nansum(calcular_nhf_serie(tmin, tmax, tb=tb_alvo))
        nhf_plus = np.nansum(calcular_nhf_serie(tmin, tmax, tb=tb_plus))

        resultados_anuais.append(
            {
                "Ano": int(ano),
                f"NHF < {tb_minus}°C": float(nhf_min),
                f"NHF < {tb_alvo}°C": float(nhf_base),
                f"NHF < {tb_plus}°C": float(nhf_plus),
            }
        )
        resultados_historicos_base.append({"Ano": int(ano), "NHF": float(nhf_base)})

    df_clima = pd.DataFrame(resultados_anuais)
    df_hist = pd.DataFrame(resultados_historicos_base)

    if df_clima.empty:
        raise ValueError("Não há anos com dados suficientes para calcular a climatologia.")

    medias = {
        "minus": float(df_clima[f"NHF < {tb_minus}°C"].mean()),
        "base": float(df_clima[f"NHF < {tb_alvo}°C"].mean()),
        "plus": float(df_clima[f"NHF < {tb_plus}°C"].mean()),
    }

    return df_clima, df_hist, medias


def preparar_grade_ano(
    ds_tmax: xr.Dataset,
    ds_tmin: xr.Dataset,
    ano: int,
    tb_alvo: float,
):
    lat_coord, lon_coord, var_tmax, var_tmin = detectar_coordenadas_e_variaveis(ds_tmax, ds_tmin)

    if float(ds_tmax[lon_coord].max()) > 180:
        ds_tmax = ds_tmax.assign_coords(
            {lon_coord: (((ds_tmax[lon_coord] + 180) % 360) - 180)}
        ).sortby(lon_coord)
        ds_tmin = ds_tmin.assign_coords(
            {lon_coord: (((ds_tmin[lon_coord] + 180) % 360) - 180)}
        ).sortby(lon_coord)

    ds_ano_max = ds_tmax.sel(time=str(ano))
    ds_ano_min = ds_tmin.sel(time=str(ano))

    ds_inv_max = ds_ano_max.sel(time=ds_ano_max["time.month"].isin(MESES_INVERNO))
    ds_inv_min = ds_ano_min.sel(time=ds_ano_min["time.month"].isin(MESES_INVERNO))

    if ds_inv_max.sizes.get("time", 0) == 0 or ds_inv_min.sizes.get("time", 0) == 0:
        raise ValueError(f"Não há dados de inverno para {ano}.")

    nhf_matriz = calcular_nhf_grade(
        ds_inv_min[var_tmin].values,
        ds_inv_max[var_tmax].values,
        tb=tb_alvo,
    )

    da_espacial = xr.DataArray(
        nhf_matriz,
        coords={lat_coord: ds_inv_max[lat_coord], lon_coord: ds_inv_max[lon_coord]},
        dims=[lat_coord, lon_coord],
        name=f"NHF_{tb_alvo}C",
    )

    return da_espacial, lat_coord, lon_coord
