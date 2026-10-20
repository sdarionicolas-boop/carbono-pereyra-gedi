#!/usr/bin/env python3
"""
Carbono aéreo — Reserva de Biosfera Pereyra Iraola (Buenos Aires, Argentina)
=============================================================================
Pipeline reproducible en un solo archivo. Cadena de cálculo (la que generó los resultados del trabajo):

    altura de dosel Meta/WRI (1 m)  →  altura media a ~5 m (entero)  →  ecuación alométrica  →  carbono (tC/ha)
                                                                          ↘  Random Forest con Sentinel-2
    Chequeo independiente: altura de Meta frente a huellas GEDI L2A (RH95) y escenarios de stock calibrados.

Subcomandos
-----------
  export   (GEE)  Exporta a Drive: altura de Meta a 5 y 25 m (polígono completo) y un stack Sentinel-2.
  gedi     (GEE)  Muestrea huellas GEDI RH95 + altura de Meta dentro de la reserva → CSV con coordenadas.
  stock           Carbono y stock con el ÁREA REAL del píxel, recortado por el polígono de la reserva.
  rf              Random Forest Sentinel-2 → carbono, con validación aleatoria y espacial por bloques.
  calibrar        Escenarios de stock: Meta tal cual vs. calibrado contra GEDI (regresión isotónica).

Advertencias (ver CORRECCIONES_PEREYRA.md)
------------------------------------------
* La ecuación de carbono es por árbol y se aplica a la altura del dosel de un píxel; NO está validada con parcelas.
* El R² del Random Forest mide qué tanto Sentinel-2 reproduce un carbono derivado de la altura de Meta; no valida carbono.
* La altura de Meta subestima frente a GEDI (sesgo ≈ −2,8 m dentro de la reserva).

Polígono: OpenStreetMap, relación 10968584 (© colaboradores de OpenStreetMap, ODbL).
"""
import argparse, json, os, sys
import numpy as np

# ── Parámetros de la ecuación (tal como en el cálculo original) ──────────────────────────────────
RHO, CF, COEF_A, EXP_B = 0.6, 0.47, 0.0673, 1.23       # C = A·(ρ·h)^B · 100 · CF
CLASES_M = [1, 5, 10, 15, 20]                           # límites de clase de altura (m)
ETIQ_CLASES = ['<1', '1–5', '5–10', '10–15', '15–20', '>20']
GEDI_INICIO, GEDI_FIN = '2019-04-18', '2023-12-31'      # huellas GEDI usadas en el chequeo
BLOQUE_M = 2000                                         # lado de los bloques de validación espacial (m)


def carbono(h):
    """Carbono aéreo (tC/ha) desde la altura h (m). ⚠ Ecuación por árbol usada como de rodal; sin calibración local."""
    h = np.maximum(np.asarray(h, dtype='float64'), 0)
    return COEF_A * (RHO * h) ** EXP_B * 100 * CF


def ha_por_fila(T, H):
    """Área (ha) de un píxel en cada fila de una grilla geográfica (el área varía con la latitud)."""
    lat = T.f + T.e * (np.arange(H) + .5)
    return abs(T.a) * 111320 * np.cos(np.radians(lat)) * abs(T.e) * 110540 / 1e4


def leer_poligono(path):
    return [f['geometry'] for f in json.load(open(path, encoding='utf-8'))['features']]


def mascara_poligono(geoms, shape, T):
    from rasterio.features import geometry_mask
    return geometry_mask(geoms, out_shape=shape, transform=T, invert=True)


def bloques(lon, lat, lado=BLOQUE_M):
    lon, lat = np.asarray(lon), np.asarray(lat)
    dx = lado / (111320 * np.cos(np.radians(lat.mean()))); dy = lado / 110540
    return (np.floor((lon - lon.min()) / dx) * 100000 + np.floor((lat - lat.min()) / dy)).astype(int)


def metricas(y, p):
    return dict(R2=1 - ((y - p) ** 2).sum() / ((y - y.mean()) ** 2).sum(), RMSE=float(np.sqrt(np.mean((y - p) ** 2))),
                MAE=float(np.mean(np.abs(y - p))))


# ═══════════════════════════ GEE ═══════════════════════════
def _ee(proyecto, geojson):
    import ee
    ee.Authenticate(); ee.Initialize(project=proyecto)
    geom = leer_poligono(geojson)[0]
    return ee, ee.Geometry(geom)


def _meta(ee):
    col = ee.ImageCollection('projects/meta-forest-monitoring-okw37/assets/CanopyHeight')
    base = col.mosaic().select('cover_code').unmask(0)          # sin árbol = 0 m, como en el cálculo original
    return base.setDefaultProjection(col.first().select('cover_code').projection())


def cmd_export(a):
    ee, roi = _ee(a.proyecto, a.poligono); base = _meta(ee)
    h5 = (base.reduceResolution(ee.Reducer.mean(), maxPixels=1024).reproject(crs='EPSG:4326', scale=5)
          .round().toUint8().rename('H5M_MEAN'))
    red = ee.Reducer.mean().combine(ee.Reducer.percentile([95]), sharedInputs=True)
    h25 = (base.reduceResolution(red, maxPixels=1024).reproject(crs='EPSG:4326', scale=25)
           .select(['cover_code_mean', 'cover_code_p95'], ['H_MEAN', 'H_P95']).toFloat())

    # Sentinel-2 L2A: mediana anual (por defecto 2024, nubosidad < 20 %, igual que el cálculo original). Bandas: B2,B3,B4,B8,B11,NDVI,NDWI,NBR
    def mascara(img):
        s = img.select('SCL'); return img.updateMask(s.neq(3).And(s.neq(8)).And(s.neq(9)).And(s.neq(10)).And(s.neq(11)))
    col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED').filterBounds(roi)
           .filterDate(f'{a.anio}-01-01', f'{a.anio}-12-31').filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', a.nubes)))
    s2 = (col.map(mascara) if a.mascara_scl else col).median()      # por defecto SIN máscara por píxel, como el cálculo original
    stack = (s2.select(['B2', 'B3', 'B4', 'B8', 'B11'])
             .addBands(s2.normalizedDifference(['B8', 'B4']).rename('NDVI'))
             .addBands(s2.normalizedDifference(['B3', 'B11']).rename('NDWI'))
             .addBands(s2.normalizedDifference(['B8', 'B12']).rename('NBR')).toFloat())
    for img, nombre, escala in [(h5, 'Meta_H5m_mean', 5), (h25, 'Meta_H25m', 25), (stack, 'Sentinel2_Stack_10m', 10)]:
        ee.batch.Export.image.toDrive(image=img, description=nombre, folder=a.carpeta, fileNamePrefix=nombre,
                                      region=roi.bounds(), scale=escala, crs='EPSG:4326', maxPixels=1e13).start()
        print('🚀 exportando', nombre, '→ Drive/' + a.carpeta)
    print('Esperá a que terminen en https://code.earthengine.google.com/tasks y bajá los .tif a la carpeta de trabajo.')


def cmd_gedi(a):
    import pandas as pd
    ee, roi = _ee(a.proyecto, a.poligono); base = _meta(ee)
    srtm = ee.Image('USGS/SRTMGL1_003').select('elevation'); pend = ee.Terrain.slope(srtm)

    def filtrar(img):
        m = (img.select('quality_flag').eq(1).And(img.select('degrade_flag').eq(0)).And(img.select('sensitivity').gte(0.95))
             .And(img.select('solar_elevation').lt(0)).And(img.select('elev_lowestmode').subtract(srtm).abs().lte(50))
             .And(pend.lte(20)))
        return img.updateMask(m)
    rh95 = (ee.ImageCollection('LARSE/GEDI/GEDI02_A_002_MONTHLY').filterBounds(roi).filterDate(GEDI_INICIO, GEDI_FIN)
            .map(filtrar).select('rh95').median().rename('RH95'))
    # GEDI L4A (biomasa aérea AGBD, Mg/ha) con los mismos filtros; permite comparar con otros sitios usando el mismo producto
    def filtrar_l4a(img):
        m = (img.select('l4_quality_flag').eq(1).And(img.select('degrade_flag').eq(0)).And(img.select('sensitivity').gte(0.95))
             .And(img.select('solar_elevation').lt(0)).And(pend.lte(20)))
        return img.updateMask(m)
    agbd = (ee.ImageCollection('LARSE/GEDI/GEDI04_A_002_MONTHLY').filterBounds(roi).filterDate(GEDI_INICIO, GEDI_FIN)
            .map(filtrar_l4a).select('agbd').median().rename('AGBD').unmask(-9999))   # -9999 = sin L4A en esa huella
    red = ee.Reducer.mean().combine(ee.Reducer.percentile([95]), sharedInputs=True)
    h25 = (base.reduceResolution(red, maxPixels=1024).reproject(crs='EPSG:4326', scale=25)
           .select(['cover_code_mean', 'cover_code_p95'], ['H_MEAN', 'H_P95']))
    h25 = h25.addBands(h25.select('H_P95').focalMean(1, 'square', 'pixels').rename('H_P95_3x3'))
    comb = rh95.addBands(h25).addBands(agbd).updateMask(rh95.mask()).clip(roi).toFloat()

    (x0, y0), (x1, y1) = [roi.bounds().coordinates().getInfo()[0][i] for i in (0, 2)]
    filas, NX, NY = [], 4, 3                                      # teselas: cada getInfo admite ≤ 5.000 elementos
    for i in range(NX):
        for j in range(NY):
            caja = ee.Geometry.Rectangle([x0+(x1-x0)*i/NX, y0+(y1-y0)*j/NY, x0+(x1-x0)*(i+1)/NX, y0+(y1-y0)*(j+1)/NY])
            fc = comb.sample(region=caja.intersection(roi, 1), scale=25, projection='EPSG:4326', dropNulls=True, geometries=True)
            for f in fc.getInfo()['features']:
                p = dict(f['properties']); p['lon'], p['lat'] = f['geometry']['coordinates']; filas.append(p)
    df = pd.DataFrame(filas); df = df[(df.RH95 > 0) & (df.RH95 <= 50)]
    df['AGBD'] = df.AGBD.where(df.AGBD > 0)                    # vacío donde L4A no tiene dato
    df[['lon', 'lat', 'RH95', 'H_P95', 'H_P95_3x3', 'H_MEAN', 'AGBD']].round(5).to_csv(a.salida, index=False)
    print(f'{len(df)} huellas GEDI utilizables ({df.AGBD.notna().sum()} con L4A) → {a.salida}')


# ═══════════════════════════ Análisis local ═══════════════════════════
def cmd_stock(a):
    import pandas as pd, rasterio
    geoms = leer_poligono(a.poligono)
    with rasterio.open(a.altura) as r:
        h = r.read(1).astype('float64'); T = r.transform; H, W = r.shape; perfil = r.profile.copy()
    c = carbono(h); dentro = mascara_poligono(geoms, (H, W), T)
    ha = np.repeat(ha_por_fila(T, H)[:, None], W, axis=1)
    A = ha[dentro].sum(); stock = (c * ha)[dentro].sum() / 1e3
    print(f'Área de la reserva en el raster: {A:,.0f} ha | stock: {stock:,.1f} ktC | media: {stock*1e3/A:.2f} tC/ha | '
          f'píxeles con altura > 0: {(h[dentro] > 0).mean():.1%}')
    try:                                                          # ¿el raster cubre todo el polígono?
        from shapely.geometry import shape; from shapely.affinity import scale
        g = shape(geoms[0]); k = 111320 * np.cos(np.radians(g.centroid.y))
        tot = scale(g, xfact=k, yfact=110540, origin=(0, 0)).area / 1e4
        print(f'Área del polígono: {tot:,.0f} ha → el raster cubre {A/tot:.1%}' + ('  ⚠ cobertura incompleta' if A / tot < .98 else ''))
    except ImportError:
        pass
    # Tabla por clase de altura con ÁREA REAL (reemplaza a Resumen_Altura_Pereyra.csv)
    cls = np.digitize(h[dentro], CLASES_M); hh, cc, aa = h[dentro], c[dentro], ha[dentro]
    filas = [dict(Clase_m=ETIQ_CLASES[k], Hectareas=aa[cls == k].sum(),
                  Carbono_medio_tC_ha=(cc[cls == k] * aa[cls == k]).sum() / max(aa[cls == k].sum(), 1e-9),
                  Carbono_total_t=(cc[cls == k] * aa[cls == k]).sum()) for k in range(6)]
    tab = pd.DataFrame(filas).round(2); print('\n' + tab.to_string(index=False)); tab.to_csv(os.path.join(a.salida, 'Carbono_por_clase_altura.csv'), index=False)
    perfil.update(dtype='float32', count=1, nodata=None)
    with rasterio.open(os.path.join(a.salida, 'Carbono_5m.tif'), 'w', **perfil) as d:
        d.write(c.astype('float32'), 1)
    print(f'\nGuardado: {a.salida}/Carbono_5m.tif y Carbono_por_clase_altura.csv')


def cmd_rf(a):
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.warp import reproject
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.model_selection import GroupKFold, cross_val_predict, train_test_split
    geoms = leer_poligono(a.poligono)
    with rasterio.open(a.stack) as s:
        S = s.read().astype('float32'); T = s.transform; H, W = s.height, s.width
        nombres = [d or f'banda{i+1}' for i, d in enumerate(s.descriptions)]     # nombres tomados del propio archivo
        gcrs = s.crs
    c = np.full((H, W), np.nan, dtype='float32')
    with rasterio.open(a.carbono) as r:
        reproject(source=rasterio.band(r, 1), destination=c, dst_transform=T, dst_crs=gcrs, resampling=Resampling.average)
    ok = mascara_poligono(geoms, (H, W), T) & np.all(np.isfinite(S), axis=0) & np.isfinite(c)
    if not a.incluir_ceros:
        ok &= c > 0
    cols, rows = np.meshgrid(np.arange(W), np.arange(H)); lon = T.c + T.a * (cols + .5); lat = T.f + T.e * (rows + .5)
    X, y, lo, la = S[:, ok].T, c[ok], lon[ok], lat[ok]
    if len(y) > a.max_muestras:
        i = np.random.default_rng(0).choice(len(y), a.max_muestras, replace=False); X, y, lo, la = X[i], y[i], lo[i], la[i]
    print(f'Variables: {nombres}\nMuestras: {len(y):,}')
    rf = lambda: RandomForestRegressor(n_estimators=a.arboles, max_depth=20, n_jobs=-1, random_state=42)
    Xa, Xb, ya, yb = train_test_split(X, y, test_size=.3, random_state=42)
    m = metricas(yb, rf().fit(Xa, ya).predict(Xb)); print(f"División aleatoria 70/30     R²={m['R2']:.3f}  RMSE={m['RMSE']:.2f} tC/ha")
    for lado in (BLOQUE_M, 5000):
        p = cross_val_predict(rf(), X, y, groups=bloques(lo, la, lado), cv=GroupKFold(5)); m = metricas(y, p)
        print(f"Validación espacial {lado:>5} m   R²={m['R2']:.3f}  RMSE={m['RMSE']:.2f} tC/ha")
    imp = sorted(zip(nombres, rf().fit(X, y).feature_importances_), key=lambda t: -t[1])
    print('Importancia (Gini):', ', '.join(f'{n} {v:.3f}' for n, v in imp))
    print('\n⚠ El R² mide cuánto Sentinel-2 reproduce un carbono derivado de la altura de Meta; no es una validación de carbono.')


def cmd_calibrar(a):
    import pandas as pd
    from sklearn.isotonic import IsotonicRegression
    from sklearn.model_selection import GroupKFold
    geoms = leer_poligono(a.poligono); par = pd.read_csv(a.pares)
    x, y = par.H_P95.values, par.RH95.values; cg = carbono(y); grp = bloques(par.lon, par.lat)
    fit = lambda xx, cc: IsotonicRegression(out_of_bounds='clip').fit(xx, cc)

    def en_poligono(path, banda=1):
        import rasterio
        with rasterio.open(path) as r:
            v = r.read(banda).astype('float64'); T = r.transform; H, W = r.shape
        d = mascara_poligono(geoms, (H, W), T); ha = np.repeat(ha_por_fila(T, H)[:, None], W, axis=1)
        return v[d], ha[d]
    h5, ha5 = en_poligono(a.h5m); hp, ha25 = en_poligono(a.h25m, banda=2)             # banda 2 = H_P95
    A = ha5.sum(); s_paper = (carbono(h5) * ha5).sum() / 1e3

    pred = np.zeros_like(cg)
    for tr, te in GroupKFold(5).split(x, groups=grp):
        pred[te] = fit(x[tr], cg[tr]).predict(x[te])
    r2 = lambda u, v: 1 - ((u - v) ** 2).sum() / ((u - u.mean()) ** 2).sum()
    print(f'Huellas: {len(par):,} en {len(np.unique(grp))} bloques | sesgo Meta−GEDI {np.mean(x-y):+.2f} m | r={np.corrcoef(x, y)[0,1]:.3f} | '
          f'carbono GEDI {cg.mean():.2f} vs Meta {carbono(x).mean():.2f} tC/ha | R² por huella: sin calibrar {r2(cg, carbono(x)):.3f}, calibrado (CV espacial) {r2(cg, pred):.3f}')
    iso = fit(x, cg); pc = iso.predict(hp); pz = np.where(hp == 0, 0, pc)
    idx = {b: np.flatnonzero(grp == b) for b in np.unique(grp)}; ks = list(idx); rng = np.random.default_rng(1); bt = []
    for _ in range(a.bootstrap):
        sel = np.concatenate([idx[b] for b in rng.choice(ks, len(ks))]); m_ = fit(x[sel], cg[sel]).predict(hp)
        bt.append(((m_ * ha25).sum() / 1e3, (np.where(hp == 0, 0, m_) * ha25).sum() / 1e3))
    bt = np.array(bt)
    filas = [('1. Paper: altura media a 5 m', s_paper, np.nan, np.nan),
             ('2. Meta p95 a 25 m, sin calibrar', (carbono(hp) * ha25).sum() / 1e3, np.nan, np.nan),
             ('3. Calibrado contra GEDI', (pc * ha25).sum() / 1e3, *np.percentile(bt[:, 0], [2.5, 97.5])),
             ('4. Calibrado, 0 donde Meta = 0', (pz * ha25).sum() / 1e3, *np.percentile(bt[:, 1], [2.5, 97.5]))]
    tab = pd.DataFrame(filas, columns=['Escenario', 'Stock_ktC', 'IC95_inf', 'IC95_sup'])
    tab['tC_ha'] = tab.Stock_ktC * 1e3 / A; tab['Cociente_vs_paper'] = tab.Stock_ktC / s_paper
    print(f'\nÁrea de la reserva: {A:,.0f} ha\n' + tab.round(2).to_string(index=False))
    print('\nEl IC refleja solo la calibración (bootstrap por bloques); no incluye el error de la ecuación de carbono ni el de Meta.')
    tab.round(3).to_csv(a.salida, index=False); print('Guardado:', a.salida)


def main():
    try:                                   # consolas de Windows (cp1252): evitar errores con tildes y símbolos
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    def p(nombre, f, ayuda):
        sp = sub.add_parser(nombre, help=ayuda); sp.set_defaults(f=f); sp.add_argument('--poligono', default='pereyra_osm.geojson'); return sp
    sp = p('export', cmd_export, 'exporta altura de Meta y Sentinel-2 desde GEE')
    sp.add_argument('--proyecto', required=True, help='proyecto de GEE'); sp.add_argument('--carpeta', default='PEREYRA_RESERVA')
    sp.add_argument('--anio', default='2024'); sp.add_argument('--nubes', type=float, default=20)
    sp.add_argument('--mascara-scl', dest='mascara_scl', action='store_true', help='enmascarar nubes por píxel con SCL (el cálculo original no lo hacía)')
    sp = p('gedi', cmd_gedi, 'huellas GEDI + altura de Meta con coordenadas')
    sp.add_argument('--proyecto', required=True); sp.add_argument('--salida', default='pares_meta_gedi_reserva.csv')
    sp = p('stock', cmd_stock, 'carbono y stock con área real del píxel')
    sp.add_argument('--altura', default='Meta_H5m_mean.tif'); sp.add_argument('--salida', default='.')
    sp = p('rf', cmd_rf, 'Random Forest Sentinel-2 → carbono')
    sp.add_argument('--stack', default='Sentinel2_Stack_10m.tif'); sp.add_argument('--carbono', default='Carbono_5m.tif')
    sp.add_argument('--max-muestras', dest='max_muestras', type=int, default=200000); sp.add_argument('--arboles', type=int, default=100)
    sp.add_argument('--incluir-ceros', dest='incluir_ceros', action='store_true', help='incluir píxeles con carbono 0 (el cálculo original los excluía)')
    sp = p('calibrar', cmd_calibrar, 'escenarios de stock calibrados contra GEDI')
    sp.add_argument('--pares', default='pares_meta_gedi_reserva.csv'); sp.add_argument('--h5m', default='Meta_H5m_mean.tif')
    sp.add_argument('--h25m', default='Meta_H25m.tif'); sp.add_argument('--bootstrap', type=int, default=300); sp.add_argument('--salida', default='Stock_reserva.csv')
    a = ap.parse_args(); a.f(a)


if __name__ == '__main__':
    main()
