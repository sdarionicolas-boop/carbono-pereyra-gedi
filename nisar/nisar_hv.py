"""Retrodispersión de NISAR banda L (GCOV, HHHH y HVHV) sobre Iguazú y Pereyra, y su relación con GEDI L4A y ESA CCI a 1 km.
Usa las escenas de datos/ y las celdas de 100 m de pares_cci_gedi.csv (salida local del notebook de cci_biomass; copiarla a nisar/; tiene coordenadas y no se publica).
Uso: python nisar_hv.py -> resumen_nisar_hv.csv, celdas_nisar_hv.csv, nisar_hv_vs_gedi_1km.png"""
import glob
import json
from pathlib import Path

import h5py
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pyproj import Transformer
from scipy import stats
from shapely import contains_xy
from shapely.geometry import shape
from shapely.ops import transform

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
SITIOS = {'Iguazú': (RAIZ / 'iguazu' / 'iguazu_osm.geojson', '154'), 'Pereyra Iraola': (RAIZ / 'pereyra_osm.geojson', '161')}
COLORES = {'Iguazú': '#eb6834', 'Pereyra Iraola': '#2a78d6'}
MIN_CELDAS = 5
pares = pd.read_csv(AQUI / 'pares_cci_gedi.csv')
db = lambda x: 10 * np.log10(x)

resumen, celdas = [], []
for nombre, (ruta, camino) in SITIOS.items():
    poligono = shape(json.loads(ruta.read_text(encoding='utf-8'))['features'][0]['geometry'])
    archivo = glob.glob(str(AQUI / 'datos' / f'*_{camino}_*.h5'))[0]
    with h5py.File(archivo, 'r') as h:
        g = h['science/LSAR/GCOV/grids/frequencyA']
        epsg = int(g['projection'][()])
        x, y = g['xCoordinates'][:], g['yCoordinates'][:]
        a2m = Transformer.from_crs(4326, epsg, always_xy=True)
        pol_m = transform(lambda lon, lat, z=None: a2m.transform(lon, lat), poligono)
        x0, y0, x1, y1 = pol_m.bounds
        ix = np.where((x >= x0 - 200) & (x <= x1 + 200))[0]
        iy = np.where((y >= y0 - 200) & (y <= y1 + 200))[0]
        sx, sy = slice(ix.min(), ix.max() + 1), slice(iy.min(), iy.max() + 1)
        hv, hh, m = g['HVHV'][sy, sx], g['HHHH'][sy, sx], g['mask'][sy, sx]
        xs, ys = x[sx], y[sy]
    valido = (m > 0) & np.isfinite(hv) & np.isfinite(hh) & (hv > 0) & (hh > 0)
    hv = np.where(valido, hv, np.nan)
    hh = np.where(valido, hh, np.nan)
    XX, YY = np.meshgrid(xs, ys)
    dentro = contains_xy(pol_m, XX, YY) & valido
    print(f'{nombre}: {dentro.sum():,} píxeles de 10 m dentro del polígono ({dentro.sum() * 100 / 1e4:,.0f} ha), escena camino {camino}', flush=True)
    resumen.append({'sitio': nombre, 'camino': camino, 'pixeles_10m': int(dentro.sum()), 'HV_dB_mediana': round(db(np.nanmedian(hv[dentro])), 2),
                    'HV_dB_p5': round(db(np.nanpercentile(hv[dentro], 5)), 2), 'HV_dB_p95': round(db(np.nanpercentile(hv[dentro], 95)), 2),
                    'HH_dB_mediana': round(db(np.nanmedian(hh[dentro])), 2), 'HV/HH_dB': round(db(np.nanmedian(hv[dentro])) - db(np.nanmedian(hh[dentro])), 2)})

    # valor de NISAR en cada celda de 100 m con huellas GEDI (ventana de 10 x 10 píxeles, promedio en potencia)
    d = pares[pares.sitio == nombre].drop_duplicates(['longitude', 'latitude']).copy()
    cx, cy = a2m.transform(d.longitude.values, d.latitude.values)
    j = np.round((cx - xs[0]) / 10).astype(int)
    i = np.round((cy - ys[0]) / -10).astype(int)
    hv_c, hh_c = [], []
    for ii, jj in zip(i, j):
        w = (slice(max(ii - 5, 0), ii + 5), slice(max(jj - 5, 0), jj + 5))
        a, b = hv[w], hh[w]
        ok = np.isfinite(a).mean() > 0.8 if a.size else False
        hv_c.append(np.nanmean(a) if ok else np.nan)
        hh_c.append(np.nanmean(b) if ok else np.nan)
    d['hv_db'] = db(np.array(hv_c))
    d['hh_db'] = db(np.array(hh_c))
    celdas.append(d)

pd.DataFrame(resumen).to_csv(AQUI / 'resumen_nisar_hv.csv', index=False)
cel = pd.concat(celdas, ignore_index=True).dropna(subset=['hv_db'])
cel.to_csv(AQUI / 'celdas_nisar_hv.csv', index=False)

# bloques de ~1 km
cel = cel.copy()
lat0 = cel.latitude.mean()
cel['bx'] = np.floor(cel.longitude * 111.32 * np.cos(np.radians(lat0)) / 1.0)
cel['by'] = np.floor(cel.latitude * 110.57 / 1.0)
b = cel.groupby(['sitio', 'bx', 'by']).agg(celdas=('hv_db', 'size'), hv_db=('hv_db', 'mean'), hh_db=('hh_db', 'mean'), gedi=('gedi_agbd', 'mean'), cci=('cci_agb', 'mean')).reset_index()
b = b[b.celdas >= MIN_CELDAS]
filas = []
for nombre, d in b.groupby('sitio'):
    fila = {'sitio': nombre, 'bloques_1km': len(d)}
    for v in ('hv_db', 'hh_db'):
        fila[f'{v}_vs_GEDI_spearman'] = round(stats.spearmanr(d[v], d.gedi)[0], 2)
        fila[f'{v}_vs_CCI_spearman'] = round(stats.spearmanr(d[v], d.cci)[0], 2)
    fila['GEDI_vs_CCI_spearman'] = round(stats.spearmanr(d.gedi, d.cci)[0], 2)
    filas.append(fila)
res = pd.DataFrame(filas)
print(pd.DataFrame(resumen).to_string(index=False))
print(res.T.to_string(header=False))
res.to_csv(AQUI / 'resumen_nisar_vs_gedi_1km.csv', index=False)

fig, ax = plt.subplots(2, 2, figsize=(10.5, 8))
for k, (nombre, d) in enumerate(b.groupby('sitio')):
    for r, (col, et) in enumerate((('gedi', 'GEDI L4A, media del bloque (Mg/ha)'), ('cci', 'ESA CCI, media del bloque (Mg/ha)'))):
        a = ax[r, k]
        a.scatter(d[col], d.hv_db, s=d.celdas * 2, alpha=.5, color=COLORES[nombre])
        rho = stats.spearmanr(d[col], d.hv_db)[0]
        a.set_title(f'{nombre}: HV vs {col.upper()} (ρ = {rho:.2f}, n = {len(d)})', fontsize=10)
        a.set_xlabel(et)
        a.set_ylabel('NISAR HV (dB)')
plt.suptitle('NISAR banda L (HV, oct. 2026) frente a GEDI L4A y CCI — bloques de ~1 km')
plt.tight_layout()
plt.savefig(AQUI / 'nisar_hv_vs_gedi_1km.png', dpi=130)
