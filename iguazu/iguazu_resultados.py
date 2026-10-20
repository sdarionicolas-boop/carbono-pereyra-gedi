#!/usr/bin/env python3
"""Reproduce las cifras principales de Iguazú a partir de la tabla de huellas GEDI (sin Earth Engine).

Entrada : datos/huellas_iguazu_gedi.csv  (lon, lat, RH95_m, AGBD_Mg_ha; un registro por píxel de 25 m con huella GEDI)
Salida  : tabla por pantalla y datos/resumen_iguazu.csv

Estimador: media muestral de las huellas, con IC95 por bootstrap de bloques de 2 km (las huellas vecinas no son independientes).
No es un modelo: es el promedio de lo medido por GEDI. Sin validación de campo.
"""
import argparse
import sys

import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

CF = 0.47          # fracción de carbono de la biomasa
RHO = 0.6          # solo en la ecuación de Pereyra


def ecuacion_pereyra(h):
    """Ecuación usada en el trabajo de Pereyra (tC/ha). Origen no documentado; no validada con parcelas."""
    return 0.0673 * (RHO * np.maximum(h, 0)) ** 1.23 * 100 * CF


def bloques(df, lado_m=2000):
    dx = lado_m / (111320 * np.cos(np.radians(df.lat.mean())))
    dy = lado_m / 110540
    return (np.floor((df.lon - df.lon.min()) / dx) * 100000 + np.floor((df.lat - df.lat.min()) / dy)).astype(np.int64)


def media_bootstrap(valores, grupos, n=2000, seed=0):
    rng = np.random.default_rng(seed)
    g = pd.DataFrame({"v": valores, "g": grupos}).groupby("g").v.agg(["sum", "count"])
    s, c = g["sum"].to_numpy(), g["count"].to_numpy()
    idx = rng.integers(0, len(g), (n, len(g)))
    m = s[idx].sum(1) / c[idx].sum(1)
    return valores.mean(), *np.percentile(m, [2.5, 97.5])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--huellas", default="datos/huellas_iguazu_gedi.csv")
    ap.add_argument("--salida", default="datos/resumen_iguazu.csv")
    ap.add_argument("--bloque-m", type=float, default=2000)
    a = ap.parse_args()

    df = pd.read_csv(a.huellas)
    df["bloque"] = bloques(df, a.bloque_m)
    filas = []

    d = df[df.AGBD_Mg_ha > 0]
    m, lo, hi = media_bootstrap(d.AGBD_Mg_ha.to_numpy() * CF, d.bloque.to_numpy())
    filas.append(("GEDI L4A (AGBD × 0,47)", len(d), m, lo, hi))

    d = df[df.RH95_m > 0]
    m, lo, hi = media_bootstrap(ecuacion_pereyra(d.RH95_m.to_numpy()), d.bloque.to_numpy())
    filas.append(("Ecuación de Pereyra sobre RH95", len(d), m, lo, hi))

    out = pd.DataFrame(filas, columns=["metodo", "n", "tC_ha", "IC95_inf", "IC95_sup"]).round(2)
    print(out.to_string(index=False))
    print(f"\nRH95 mediana {d.RH95_m.median():.1f} m (p5–p95: {d.RH95_m.quantile(.05):.1f}–{d.RH95_m.quantile(.95):.1f} m)")
    out.to_csv(a.salida, index=False)
    print("→", a.salida)


if __name__ == "__main__":
    main()
