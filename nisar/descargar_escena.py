"""Descarga una escena NISAR GCOV (la más reciente con cobertura completa y HH+HV) por sitio.
Descarga con el token como Bearer (reanuda si se corta). Lee EARTHDATA_TOKEN de nisar/env.txt (no se imprime). Uso: python descargar_escena.py -> nisar/datos/*.h5"""
import sys
from pathlib import Path

import asf_search as asf
import pandas as pd

AQUI = Path(__file__).resolve().parent
DATOS = AQUI / 'datos'
DATOS.mkdir(exist_ok=True)

token = None
for linea in (AQUI / 'env.txt').read_text(encoding='utf-8').splitlines():
    if linea.startswith('EARTHDATA_TOKEN='):
        token = linea.split('=', 1)[1].strip().strip('"\'')
if not token:
    sys.exit('Falta EARTHDATA_TOKEN en env.txt')

df = pd.read_csv(AQUI / 'escenas_nisar_gcov.csv')
df = df[(df.cobertura_del_sitio >= 0.99) & (df.pol_principal == 'HH+HV')]

elegidas = df.sort_values('inicio').groupby('sitio').tail(1)
print(elegidas[['sitio', 'escena', 'inicio', 'direccion', 'camino', 'tamano_GB']].to_string(index=False), flush=True)

import requests

cab = {'Authorization': 'Bearer ' + token}
for _, f in elegidas.iterrows():
    destino = DATOS / f'{f.escena}.h5'
    parcial = destino.with_suffix('.h5.part')
    if destino.exists():
        print('ya existe', destino.name, flush=True)
        continue
    url = asf.granule_search([f.escena], asf.ASFSearchOptions(dataset=asf.DATASET.NISAR))[0].properties['url']
    ya = parcial.stat().st_size if parcial.exists() else 0
    with requests.get(url, headers={**cab, 'Range': f'bytes={ya}-'}, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(parcial, 'ab' if ya else 'wb') as out:
            for bloque in r.iter_content(1 << 22):
                out.write(bloque)
    parcial.rename(destino)
    print('descargado', destino.name, round(destino.stat().st_size / 1e9, 2), 'GB', flush=True)
