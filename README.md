# Carbono aéreo — Reserva de Biosfera Pereyra Iraola (Buenos Aires, Argentina)

**Autor:** Darío Nicolás Sánchez Leguizamón · Universidad Nacional Arturo Jauretche (UNAJ) · sdarionicolas@gmail.com
**Trabajo:** *Estimación del carbono aéreo en la Reserva de Biósfera Pereyra Iraola (Buenos Aires, Argentina) mediante integración de datos GEDI, Sentinel-2 e inteligencia artificial* — CAI 2026, 55 JAIIO.

> **Nota de revisión.** Este repositorio fue auditado y corregido. La versión anterior describía un flujo con GEDI RH95 y Chave (2014) que **no** es el que produjo los resultados; además, el stock informado (4,6 kt) estaba mal calculado. Ver `docs/CORRECCIONES_PEREYRA.md`.

## Qué hace el pipeline

```
altura de dosel Meta/WRI (1 m) → altura media ~5 m (entero) → ecuación alométrica → carbono (tC/ha)
                                                                    ↘ Random Forest con Sentinel-2
Chequeo independiente: altura de Meta vs. huellas GEDI L2A (RH95) → escenarios de stock calibrados
```

Todo está en un solo archivo, `pereyra_carbono.py`, con cinco subcomandos:

| Subcomando | Qué hace | Requiere |
|---|---|---|
| `export` | Exporta a Drive la altura de Meta (5 y 25 m) y un stack Sentinel-2 | GEE |
| `gedi` | Huellas GEDI + altura de Meta con coordenadas → CSV | GEE |
| `stock` | Carbono y stock con el **área real del píxel**, recortado por el polígono | local |
| `rf` | Random Forest Sentinel-2 → carbono (validación aleatoria y espacial) | local |
| `calibrar` | Escenarios de stock: Meta tal cual vs. calibrado contra GEDI | local |

## Uso

```bash
pip install rasterio numpy pandas scikit-learn shapely earthengine-api
python pereyra_carbono.py export  --proyecto TU_PROYECTO_GEE          # luego bajá los .tif de Drive
python pereyra_carbono.py gedi    --proyecto TU_PROYECTO_GEE
python pereyra_carbono.py stock
python pereyra_carbono.py rf
python pereyra_carbono.py calibrar
```
Los nombres por defecto de los archivos coinciden con los que genera `export` y `gedi`. `export` usa por defecto los parámetros del cálculo original de Sentinel-2 (año 2024, nubosidad de escena < 20 %, sin máscara por píxel; `--mascara-scl` la activa). `--help` muestra todas las opciones.
`stock`, `rf` y `calibrar` se probaron con los datos reales; `export` y `gedi` (Earth Engine) **no** se pudieron probar en esta revisión.

## Resultados corregidos (polígono OSM, 10.054 ha)

| Escenario | Stock (ktC) | tC/ha |
|---|---|---|
| 1. Método original (altura media a 5 m) | **63,3** | 6,3 |
| 2. Meta p95 a 25 m, sin calibrar | 95,6 | 9,5 |
| 3. Calibrado contra GEDI | 176,7 (IC95 161,7–187,4) | 17,6 |
| 4. Calibrado, 0 donde Meta = 0 | 146,1 (IC95 131,8–156,1) | 14,5 |

Los intervalos reflejan solo la calibración. **No** incluyen el error de la ecuación de carbono ni el de la altura de Meta.

## Limitaciones
- La ecuación de carbono, `C = 0,0673·(0,6·h)^1,23·100·0,47`, es por árbol y se aplica a la altura del dosel de un píxel. **No está validada con parcelas.**
- El R² del Random Forest mide cuánto Sentinel-2 reproduce un carbono derivado de la altura de Meta. No valida carbono.
- La altura de Meta subestima frente a GEDI: sesgo medio ≈ −2,8 m (r = 0,88; 3.280 huellas), creciente con la altura. GEDI tampoco es verdad de campo.
- Las zonas Núcleo / Amortiguamiento / Transición del trabajo anterior eran franjas norte–sur de una caja y **se eliminaron**.

## Datos y licencias
- Código: MIT (ver `LICENSE`).
- Polígono de la reserva: © colaboradores de OpenStreetMap, [ODbL](https://opendatacommons.org/licenses/odbl/) — relación 10968584.
- Altura de dosel: Meta y World Resources Institute (Tolan et al., 2024). Sentinel-2: Copernicus/ESA. GEDI: NASA/UMD.

## Cómo citar
Ver `CITATION.cff`.
