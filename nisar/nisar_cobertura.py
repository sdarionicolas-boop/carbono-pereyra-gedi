"""Cobertura NISAR (banda L, productos GCOV) sobre Iguazú y Pereyra Iraola.
Solo consulta el catálogo de ASF (metadatos): no descarga ni requiere cuenta.
Uso: python nisar_cobertura.py  ->  escenas_nisar_gcov.csv, resumen_nisar.csv, cobertura_nisar.png"""
import json
import sys
from pathlib import Path

import asf_search as asf
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import shape

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
SITIOS = {
    'Iguazú': RAIZ / 'iguazu' / 'iguazu_osm.geojson',
    'Pereyra Iraola': RAIZ / 'pereyra_osm.geojson',
}
COLORES = {'Iguazú': '#eb6834', 'Pereyra Iraola': '#2a78d6'}


def poligono(ruta):
    return shape(json.loads(ruta.read_text(encoding='utf-8'))['features'][0]['geometry'])


def fraccion_cubierta(huella, sitio):
    """Fracción del polígono del sitio que cae dentro de la huella (proyección equirrectangular local)."""
    k = np.cos(np.radians(sitio.centroid.y))
    from shapely import affinity
    f = lambda g: affinity.scale(g, xfact=k, yfact=1, origin=(0, 0))
    return f(sitio).intersection(f(huella)).area / f(sitio).area


def buscar(sitio):
    # el catálogo devuelve también productos auxiliares de NISAR: se filtra por nivel GCOV
    return asf.geo_search(intersectsWith=sitio.simplify(0.002).wkt, dataset=asf.DATASET.NISAR, processingLevel='GCOV', maxResults=2000)


filas = []
huellas = {}
for nombre, ruta in SITIOS.items():
    if not ruta.exists():
        sys.exit(f'No encuentro {ruta}')
    sitio = poligono(ruta)
    escenas = buscar(sitio)
    huellas[nombre] = (sitio, [])
    for e in escenas:
        p = e.properties
        h = shape(e.geometry)
        cub = fraccion_cubierta(h, sitio)
        huellas[nombre][1].append(h)
        gb = max((v['bytes'] for k, v in p['bytes'].items() if k.endswith('.h5') and 'QA' not in k), default=np.nan) / 1e9
        filas.append({'sitio': nombre, 'escena': p['sceneName'], 'inicio': p['startTime'], 'direccion': p['flightDirection'], 'camino': p['pathNumber'],
                      'frame': p['frameNumber'], 'pol_principal': '+'.join(p.get('mainBandPolarization') or []), 'cobertura_del_sitio': round(cub, 3),
                      'frame_completo': p.get('frameCoverage'), 'coleccion': p.get('collectionName'), 'tamano_GB': round(gb, 1)})

df = pd.DataFrame(filas).sort_values(['sitio', 'inicio'])
df.to_csv(AQUI / 'escenas_nisar_gcov.csv', index=False)

res = []
for nombre, d in df.groupby('sitio'):
    comp = d[d.cobertura_del_sitio >= 0.99]
    res.append({'sitio': nombre, 'escenas': len(d), 'escenas_que_cubren_todo_el_sitio': len(comp), 'primera': d.inicio.min()[:10], 'ultima': d.inicio.max()[:10],
                'caminos_distintos': d.camino.nunique(), 'direcciones': '/'.join(sorted(d.direccion.unique())), 'polarizaciones': ', '.join(sorted(d.pol_principal.unique())),
                'colecciones': ', '.join(sorted(d.coleccion.dropna().unique())), 'tamano_medio_GB': round(d.tamano_GB.mean(), 1)})
res = pd.DataFrame(res)
res.to_csv(AQUI / 'resumen_nisar.csv', index=False)
print(res.T.to_string(header=False))

fig, ax = plt.subplots(1, len(SITIOS), figsize=(11, 5))
for a, (nombre, (sitio, hs)) in zip(ax, huellas.items()):
    for h in hs:
        x, y = h.exterior.xy
        a.plot(x, y, color=COLORES[nombre], lw=0.6, alpha=0.5)
    sx, sy = (sitio.geoms[0] if sitio.geom_type == 'MultiPolygon' else sitio).exterior.xy
    a.fill(sx, sy, color=COLORES[nombre], alpha=0.35)
    b = sitio.bounds
    a.set_xlim(b[0] - 0.3, b[2] + 0.3)
    a.set_ylim(b[1] - 0.3, b[3] + 0.3)
    a.set_title(f'{nombre}: {len(hs)} escenas GCOV')
    a.set_aspect(1 / np.cos(np.radians(sitio.centroid.y)))
plt.suptitle('NISAR banda L (GCOV): huellas de las escenas que tocan el sitio')
plt.tight_layout()
plt.savefig(AQUI / 'cobertura_nisar.png', dpi=130)
