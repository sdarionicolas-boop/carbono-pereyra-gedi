# Correcciones propuestas — Estimación de carbono aéreo, Reserva de Biosfera Pereyra Iraola

**Para:** Darío N. Sánchez Leguizamón · **Alcance:** paper (CAI 2026 — 55 JAIIO) y repositorio `carbono-pereyra-gedi`
**Origen:** auditoría de los archivos de `PEREYRA/`, del notebook original (`Altura+COIraola (1).ipynb`) y del repo publicado.
**Cómo leerlo:** cada hallazgo indica su **estado** — *Verificado* (reproducido con tus archivos), *Inferido* (deducción razonable, falta confirmar) o *Condicional* (depende de un dato que no pude comprobar).

---

## 1. Resumen ejecutivo

1. **La cadena de cálculo real no coincide con la descrita.** Los resultados salen de la altura de dosel de **Meta/WRI** (1 m), convertida a carbono con una ecuación propia, y de un Random Forest con Sentinel-2. **GEDI no interviene** en ninguna celda que genere los resultados, y la fórmula del repo no es la usada.
2. **El stock publicado (4,6 kt) es incorrecto.** Se calculó con área de píxel errónea (1 m² en lugar de ~20 m²) y sobre una caja que cubre solo el 59 % de la reserva. Con el mismo método bien calculado: **63 ktC**.
3. **Las "zonas" Núcleo / Amortiguamiento / Transición no son zonas de la reserva:** son tres franjas norte–sur de la caja, y las superficies oficiales (4.998 / 791 / 4.459 ha) quedaron asignadas a los nombres equivocados (§3.4).
4. **Los R² (0,71; 0,93; 1,00) no validan carbono:** miden qué tan bien se reproduce una transformación de la altura de Meta.
5. **La altura de Meta subestima frente a GEDI** (desfase medio ≈ −2,8 m dentro de la reserva y ≈ −3,9 m donde ambos productos detectan vegetación). Calibrada contra GEDI con la ecuación del trabajo, el stock sube a **~146–177 ktC**; pero esa ecuación sobreestima 2 a 3 veces la biomasa de GEDI L4A en alturas bajas, y con L4A como referencia el valor es **≈ 95–130 ktC** (§3.10).
6. **Pereyra e Iguazú solo son comparables con un método común** (huellas GEDI → ecuación). Así, Iguazú tiene **~3 a 4 veces más carbono por hectárea** que Pereyra (3,6 con GEDI L4A en ambos sitios); el nivel absoluto de cada sitio depende de la ecuación o producto usado (§3.9).

---

## 2. Cifras: publicado vs. corregido

| Concepto | Publicado | Corregido | Estado |
|---|---|---|---|
| Stock total | 4,6 ktC (README) / 4.665 t (notebook) | **63,3 ktC** (método del paper, reserva completa) | Verificado |
| Stock de la caja de los rasters (≈15.300 ha) | — | 77,2 ktC (idéntico en dos rasters) | Verificado |
| Área analizada | "~10.248 ha" | Caja ≈ 15.300 ha, de las cuales **5.943 ha (59 %)** son reserva | Verificado (polígono OSM) |
| Stock con altura calibrada contra GEDI (ecuación del trabajo) | — | 146–177 ktC | Verificado (ver límites, §3.7 y §3.10) |
| Stock con altura calibrada contra GEDI L4A | — | **≈ 95 ktC** [84–102] (L4A directo: 116–131) | Verificado, con reservas (§3.10) |
| Zonas (3,79 kt en total) | `Carbono_Zonas.csv` | No utilizable (§3.4) | Verificado |

Los escenarios completos (`Stock_Pereyra_reserva.csv`, polígono OSM, 10.054 ha):

| Escenario | ktC | tC/ha | vs. paper |
|---|---|---|---|
| 1. Paper: altura media a 5 m | 63,3 | 6,3 | 1,00 |
| 2. Meta p95 a 25 m, sin calibrar | 95,6 | 9,5 | 1,51 |
| 3. Calibrado contra GEDI | 176,7 [161,7 – 187,4] | 17,6 | 2,79 |
| 4. Calibrado, 0 donde Meta = 0 | 146,1 [131,8 – 156,1] | 14,5 | 2,31 |

Los intervalos reflejan solo la calibración (bootstrap por bloques de 2 km). **No** incluyen el error de la ecuación de carbono ni el de la altura de Meta.

---

## 3. Hallazgos, con evidencia

### 3.1 La cadena real no incluye GEDI — *Verificado*
- El notebook original genera `Altura_Dosel_Pereyra.tif` desde el asset de Meta (`projects/meta-forest-monitoring-okw37/assets/CanopyHeight`, banda `cover_code`), lo promedia a ~5 m (`Resampling.average`, salida `uint8`), aplica la fórmula y obtiene `Carbono_Pereyra.tif`.
- Reproducción: aplicar la fórmula a esa altura reproduce `Carbono_Pereyra.tif` con diferencia máxima de 7,5 × 10⁻⁶ tC/ha.
- El notebook del repo (`Carbono_Pereyra_GEDI_Sentinel2_RF.ipynb`) exporta RH95 de GEDI a 25 m, pero ese raster (`GEDI_RH95_Pereyra.tif`) no existe entre tus archivos ni se usa en los resultados. Tampoco el repo contiene el código que genera `Altura_Dosel_Pereyra*.tif`.

### 3.2 La fórmula del repo no es la utilizada — *Verificado*
- **Usada:** `C = 0,0673 · (0,6·h)^1,23 · 100 · 0,47` (tC/ha, *h* en m).
- **En el repo:** Chave (2014) con diámetro estimado `D = 2,5·h^0,63`.
- La del repo (Chave 2014) es una ecuación **por árbol**; el origen de la usada en los datos no está documentado (§3.10). Ninguna se validó contra carbono medido.

### 3.3 Error de área y de dominio en el stock — *Verificado*
- `Resumen_Altura_Pereyra.csv` y `Carbono_Zonas.csv` cuentan cada píxel como 1 m² (753,8 ha en total). Los píxeles son de ~20,4 m² (5 m) y ~81,5 m² (10 m).
- Por eso la tabla por clases suma 4.665 t (origen del 4,6 kt del README), y las zonas suman 3,79 kt.
- Con el área real, `Carbono_Pereyra.tif` (5 m) y `Carbono_Pereyra_10m.tif` dan el mismo stock: 77,2 ktC en la caja.
- La caja (lon −58,233 a −58,043; lat −34,89 a −34,81) cubre solo el 59 % del polígono de la reserva (OSM, 10.053 ha). Faltan ~4.100 ha al norte y al este, con mucho menos carbono (GEDI: 7,5 vs 27,8 tC/ha). Además, ~9.500 ha de la caja no pertenecen a la reserva.
- Polígono: OpenStreetMap, relación 10968584 (ODbL). Coincide con el de WDPA (92 % de solapamiento, contorno a ≤ 825 m) y con el área oficial (10.248 ha) dentro de ~2 %. No sé si ambos derivan de la misma fuente.

### 3.4 Las zonas UNESCO eran franjas de la caja, con superficies asignadas al nombre equivocado — *Verificado*
**Qué hizo el notebook.** Dividió la caja en tres franjas norte–sur (cortes en 7,7 % y 51,2 % del alto) con las proporciones de un «documento UNESCO» (791, 4.459 y 4.998 ha) y les puso los nombres Núcleo, Amortiguamiento y Transición, en ese orden.

**Qué dice el documento oficial** (proyecto de Reserva de Biosfera, formulario MAB-UNESCO, abril de 2007, enviado por el Parque; apartado 7):

| Zona | Superficie oficial | En el notebook se la llamó |
|---|---|---|
| A · Núcleo (Reserva Natural Punta Lara) | **4.998,05 ha** (48,8 %) | «Transición» |
| B · Amortiguamiento (tampón) | **791,14 ha** (7,7 %) | «Núcleo» |
| C · Transición | **4.458,81 ha** (43,5 %) | «Amortiguamiento» |
| Total | 10.248,00 ha | — |

Las tres superficies son las del documento, pero **quedaron asignadas a los nombres equivocados** (el orden estaba invertido). Además, la geometría real no son franjas: según el mapa «Zonificación y área de influencia» (Ministerio de Ambiente de la Provincia, agosto de 2022), el **núcleo es el bloque grande del norte-noreste, sobre la costa del Río de la Plata** (entre la autopista La Plata–Buenos Aires y el río); el amortiguamiento es una franja menor al este; y la **transición** ocupa el sur y se subdivide en C1 (uso productivo), C2 (uso público) y C3 (uso mixto).

**Consecuencias.**
- La tabla por zonas del trabajo publicado **no es utilizable** (ni los nombres, ni la geometría, ni las áreas por el error de unidades de §3.3).
- Los extremos geográficos oficiales (N 34°45′54″ S; S 34°53′15″ S; E 57°59′46″ O; O 58°11′19″ O) **coinciden con el polígono de OpenStreetMap** usado en este trabajo, lo que respalda ese límite. El área del polígono (10.053 ha) difiere un 2 % del área oficial (10.248 ha).
- La **caja de los rasters originales cubre sobre todo la zona de transición** (la parte sur, el Parque Provincial propiamente dicho) y deja afuera casi todo el núcleo, que está al norte-noreste. Esto explica por qué solo el 59 % del polígono estaba dentro de la caja y por qué esa parte tenía más carbono (GEDI: 27,8 vs. 7,5 tC/ha fuera de la caja).

**Qué falta.** El Parque envió los mapas como imágenes: para calcular carbono por zona hace falta la zonificación en formato vectorial (shapefile o GeoJSON).

**Aproximación con OpenStreetMap (provisoria).** Mientras no llegue la cartografía vectorial, se aproximó la zonificación así: *núcleo + amortiguamiento* ≈ Reserva Natural Punta Lara (OSM, relación 10968583; el proyecto oficial dice 4.998,05 + 791,14 = 5.789 ha) y *transición* ≈ el resto de la reserva. Las áreas resultantes son cercanas a las oficiales (5.617 ha, −3 %; 4.437 ha, −0,5 %). **No se puede separar el amortiguamiento del núcleo** con estos datos.

| | Núcleo + amortiguamiento (≈ Punta Lara) | Transición (resto) |
|---|---|---|
| Área en este cálculo | 5.617 ha | 4.437 ha |
| Huellas GEDI / bloques de 2 km | 1.960 / 22 | 1.320 / 19 |
| RH95 medio · % de huellas ≥ 5 m | 2,9 m · 10 % | 11,7 m · 69 % |
| Carbono, GEDI L4A (tC/ha) | **3,0** [1,5 – 4,9] | **25,7** [18,5 – 31,2] |
| Carbono, ecuación sobre RH95 (tC/ha) | 6,8 [5,4 – 8,5] | 37,1 [28,5 – 44,6] |
| Stock, método original (altura de Meta) | 9,2 ktC | 54,0 ktC |
| Stock con la altura calibrada contra GEDI | 27,5 – 50,2 ktC | 118,6 – 126,5 ktC |
| Stock, L4A × área | 17,0 ktC | 113,9 ktC |

**Lectura.**
- **Entre el 72 y el 87 % del carbono aéreo está en la zona de transición**, según el método (85 % con el método original, 87 % con L4A). El núcleo, que es la parte de mayor valor de conservación, tiene poco carbono aéreo por hectárea porque es sobre todo pajonal y bañado, con la selva marginal en una franja angosta junto al río (el 81 % de sus huellas tiene altura 0 según Meta).
- Esto **no** quiere decir que el núcleo valga poco: el carbono del suelo, de los humedales y la biodiversidad no se miden aquí.
- **Es coherente con la caja de los rasters originales:** el stock de la transición con el método original (54,0 ktC) casi coincide con los 54,3 ktC que se habían obtenido dentro de la caja (§3.3), porque esa caja cubría sobre todo esta zona.

**Salvedades.** Es una aproximación con pocos bloques (22 y 19), por lo que los intervalos son anchos. En vegetación herbácea el piso de ruido de GEDI pesa mucho: la ecuación sobre RH95 asigna ~4,5 tC/ha a un RH95 de 2,2 m, y L4A (3,0 tC/ha en el núcleo) parece más razonable. Todos los valores dependen de ecuaciones o productos sin validación de campo.

### 3.5 Interpretación de los R² — *Verificado*
- `R² = 1,000` (log–log altura–carbono): identidad, el carbono es función exacta de la altura.
- `R² = 0,928` (RF altura → carbono): el modelo aprende esa misma función.
- `R² = 0,71` (RF Sentinel-2 → carbono): mide qué tanto Sentinel-2 reproduce un producto derivado de Meta. En una réplica con submuestra de 200.000 píxeles y 100 árboles obtuve 0,67 con división aleatoria y 0,63 / 0,58 con bloques espaciales de 2 y 5 km. **No hay inflado por autocorrelación**, pero tampoco es validación de carbono. No reproduje exactamente el 0,71.
- El carbono de Iguazú muestra qué pasa cuando el objetivo es una medición independiente (GEDI L4A): el R² espacial cae a ~0,08.

### 3.6 Altura de Meta vs. GEDI — *Verificado*
Dentro de la reserva (3.280 huellas GEDI, filtros: calidad, sensibilidad ≥ 0,95, noche, pendiente ≤ 20°, 2019–2023):
- r = 0,88; sesgo de Meta = −2,8 m; RMSE 4,4 m.
- **Cómo varía con la altura:** al clasificar las huellas por la altura de GEDI, el desfase parece crecer (−1,7 m con RH95 < 5 m hasta −9,2 m con ≥ 20 m), pero eso es en buena parte un **artefacto estadístico** (regresión a la media: se clasifica por la variable más ruidosa). Al clasificar por la altura de Meta, el desfase GEDI − Meta es casi constante (+2,9; +3,3; +4,1 y +3,3 m en las clases 0,5–5; 5–10; 10–15 y ≥ 15 m). Lo defendible es un **desfase de ~3–4 m, aproximadamente constante**; la pendiente Meta ~ GEDI es 0,55 (MCO) o 0,68 (regresión de Deming, λ = 1).
- El 60 % de las huellas tiene Meta = 0; en ese grupo GEDI marca una mediana de ~2,2 m (probable piso de ruido).
- Carbono medio por huella: GEDI 19,0 vs. Meta 10,8 tC/ha (cociente 0,57).

- **Chequeo de superficie arbolada (independiente de GEDI).** Dentro del polígono, el mapa de Meta da **2.924 ha con altura ≥ 5 m y 3.432 ha con altura ≥ 3 m**, frente a las «aproximadamente 3.200 hectáreas» de masa vegetal arbolada que cita el proyecto de Reserva de Biosfera (2007). No valida el carbono, pero indica que el mapa de cobertura arbórea es razonable; lo que subestima es la altura.

### 3.7 Calibración contra GEDI: límites — *Verificado, con reservas*
- Se ajusta una regresión isotónica del carbono-GEDI sobre la altura de Meta; con validación cruzada espacial el R² por huella sube de 0,62 a 0,73.
- GEDI también tiene error (geolocalización ~10 m, piso de ruido en vegetación baja); **no es una verdad de campo**. Por eso se dan dos variantes (3 y 4) y no un único valor.
- La estimación directa por huellas (sin Meta) da 159–191 ktC (IC95 91–264), coherente pero no independiente.

### 3.8 Etiquetas de variables en la importancia del RF — *Verificado*
En la celda del Random Forest del notebook original, `feature_names` tiene **9** nombres (`B2, B3, B4, B8, B11, B12, NDVI, NDWI, NBR`) pero el stack exportado tiene **8** bandas (`B2, B3, B4, B8, B11, NDVI, NDWI, NBR`; no se exportó B12). La función `zip(feature_names, importances)` corta en 8, de modo que las últimas tres etiquetas quedaron corridas:

| Etiqueta impresa | Banda real | Importancia |
|---|---|---|
| B12 | **NDVI** | 0,043 |
| NDVI | **NDWI** | 0,032 |
| NDWI | **NBR** | 0,062 |

- **B11 = 0,591 (59,1 %) no cambia**: ocupa la misma posición en ambas listas. Las bandas B2, B3, B4 y B8 tampoco cambian.
- Hay que corregir el texto que dice «NDVI aporta 3,2 %»: **el NDVI aporta 4,3 %** (3,2 % es el NDWI). La conclusión cualitativa (el NDVI aporta poco frente a B11) se mantiene.
- **B12 no forma parte del modelo.** Aparece en la figura `Importancia_Variables_RF_Mejorada.png`, que además se generó con valores escritos a mano (`importance = [0.049, 0.132, ...]`) y con la misma lista de 8 etiquetas errónea.
- El mismo notebook confirma las métricas del README: R² 0,712 · RMSE 7,62 · MAE 5,14 tC/ha · 873.668 muestras (división aleatoria 70/30).
- **El stack de Sentinel-2 se generó con** mediana anual de **2024**, `CLOUDY_PIXEL_PERCENTAGE < 20`, sin máscara de nubes por píxel (el notebook del repo decía 2023 y < 10 %).

### 3.9 Comparación Pereyra–Iguazú con el mismo método — *Verificado, con reservas*
Los resultados de ambos sitios **no se pueden comparar tal como salieron**: en Pereyra el objetivo es un carbono derivado de la altura de Meta (R² ≈ 0,6) y en Iguazú es la biomasa de GEDI L4A (R² espacial ≈ 0,08). Esos R² no dicen cuál sitio se predice mejor. Para comparar sí hay un método común: **huellas GEDI L2A RH95** (mismos filtros: calidad, sensibilidad ≥ 0,95, noche, pendiente ≤ 20°, 2019–2023) → ecuación → media por hectárea con IC95 por bootstrap de bloques de 2 km.

| | Pereyra (polígono OSM) | Iguazú (polígono WDPA) |
|---|---|---|
| Huellas | 3.280 | 20.283 |
| RH95 media / mediana | 6,4 / 2,2 m | 18,0 / 18,3 m |
| Huellas con RH95 ≥ 5 m / ≥ 20 m | 34 % / 6 % | 99 % / 34 % |

| Ecuación y variante | Pereyra (tC/ha) | Iguazú (tC/ha) | Iguazú ÷ Pereyra |
|---|---|---|---|
| Del trabajo (exp. 1,23), todas las huellas | 19,0 [12,7 ; 26,2] | 59,7 [58,6 ; 60,8] | 3,2 |
| Del trabajo, 0 si RH95 < 3 m | 16,5 [9,6 ; 24,3] | 59,7 [58,5 ; 60,8] | 3,6 |
| Del trabajo, 0 si RH95 < 5 m | 15,8 [9,0 ; 23,6] | 59,6 [58,5 ; 60,7] | 3,8 |
| Chave 2014 con D estimado, todas | 19,0 [10,1 ; 29,5] | 73,5 [71,3 ; 75,8] | 3,9 |
| **GEDI L4A (AGBD × 0,47), mismo producto** | **11,5 [6,6 ; 17,3]** (N = 2.927) | **41,5 [40,2 ; 42,7]** (N = 24.603) | **3,6** |

**Lectura:**
- **Iguazú tiene ~3 a 4 veces más carbono por hectárea que Pereyra.** Es robusto a la ecuación (dos probadas) y al tratamiento del piso de ruido de GEDI.
- **El valor absoluto depende del método**: la misma selva de Iguazú da 41,5 (L4A), 59,7 (ecuación del trabajo) o 73,5 tC/ha (Chave), un factor de 1,4 a 1,8. Sin parcelas no se puede decir cuál es mejor. Que 59,7 coincida con la media regional del INBN2 (59,7) es una **coincidencia numérica**, no una validación.
- **Los IC no son comparables en ancho**: Pereyra tiene 37 bloques de 2 km (IC amplio); Iguazú tiene muchos más y un bosque homogéneo. El IC de Iguazú tampoco incluye la incertidumbre del límite del Parque: con el polígono de OpenStreetMap (58.178 ha) y con el de WDPA (59.100 ha) la media es la misma (41,5 tC/ha); el área declarada (≈ 67.600 ha) es mayor que ambos y no sé cuál es la geometría legal.
- **Los stocks totales** (≈ 190 ktC Pereyra; ≈ 3.500 ktC Iguazú, con la ecuación del trabajo) son solo orden de magnitud: dependen del área y del polígono.
- **L4A confirma el cociente:** con el mismo producto en los dos sitios, Iguazú ÷ Pereyra = 3,6, dentro del rango obtenido con RH95 (3,2 a 3,9). Para Pereyra, L4A da 11,5 tC/ha, menos que la ecuación sobre RH95 (19,0 o 15,8 con piso). Una razón probable: L4A asigna ~1 a 1,5 Mg/ha en campo abierto (62 % de las huellas con AGBD < 5 Mg/ha), mientras que la ecuación del trabajo asigna ~4,5 tC/ha a un RH95 de 2,2 m; eso apunta a que las variantes con piso (0 si RH95 < 3 o 5 m) son más sensatas que "todas las huellas". Es una interpretación, no una prueba.
- **Stock de Pereyra por distintos caminos** (10.053 ha; solo orden de magnitud y todos con ecuaciones no validadas): método original bien calculado 63 ktC; L4A × área ≈ 116 ktC [IC95 ≈ 66–174]; ecuación del trabajo sobre RH95 ≈ 159–191 ktC; Meta calibrado contra GEDI ≈ 146–177 ktC.
- **Salvedades de L4A en Pereyra:** 353 de las 3.280 huellas (11 %) no tienen dato L4A y quedan fuera. Verificado: son huellas de vegetación baja (RH95 medio 2,3 m, 87 % con Meta = 0, 1 % con RH95 ≥ 5 m), así que la media L4A de 11,5 tC/ha está algo sobreestimada: si esas huellas valieran 0, o lo que predice su RH95, la media sería ≈ 10,3–10,4 tC/ha (−10 %, dentro del IC95 [6,6 ; 17,3]) y el cociente Iguazú ÷ Pereyra subiría de 3,6 a ≈ 4,0. Además, r(RH95, AGBD) = 0,87 en Pereyra pero 0,61 en Iguazú: en selva densa L4A depende de más que la altura.

### 3.10 La ecuación de carbono frente a GEDI L4A — *Verificado, con reservas*
**Origen.** El notebook original la rotula «t/ha aproximado» y no cita fuente. Comparte el coeficiente 0,0673 con la ecuación pantropical de Chave et al. (2014), pero tiene otra forma (exponente 1,23, sin diámetro, factor ×100). **Su origen y su validez no están documentados.**

**Comparación en las mismas huellas.** Cociente entre la biomasa que da la ecuación sobre RH95 y la biomasa de GEDI L4A (modelo calibrado a escala global con parcelas de campo), por clase de altura:

| RH95 de GEDI | < 3 m | 3–6 | 6–10 | 10–15 | 15–20 | 20–25 | 25–30 | ≥ 30 m |
|---|---|---|---|---|---|---|---|---|
| Pereyra (2.927 huellas) | 6,3 | 2,9 | 2,6 | 2,3 | 1,6 | 1,4 | 1,3 | 1,1 |
| Iguazú (20.000 huellas) | — | 2,5 | 2,5 | 2,0 | 1,6 | 1,3 | 1,1 | 1,0 |

- **La ecuación sobreestima 2 a 3 veces frente a L4A en alturas menores de 15 m** (la mayor parte de Pereyra) y converge con L4A en dosel alto. El patrón es el mismo en los dos sitios.
- Ajustando una potencia a L4A, el exponente implícito es de ≈ 2,4 (Pereyra) a 2,8 (Iguazú), contra 1,23 de la ecuación del trabajo.
- Las medias sobre todas las huellas: Pereyra, ecuación 44,0 vs. L4A 24,5 Mg/ha; Iguazú, 128,0 vs. 87,7 Mg/ha.

**Consecuencia: dos errores que se compensan en parte.** La altura de Meta es ~4 m menor que la de GEDI (§3.6, resta carbono) y la ecuación sobreestima a alturas bajas (suma carbono). Por eso el stock del método original (63 ktC) cae en medio de los demás. Stock de la reserva completa según el camino:

| Camino | Stock (ktC) |
|---|---|
| Método original, bien calculado (altura de Meta + ecuación) | 63,3 |
| Altura de Meta calibrada **directamente contra L4A** (regresión isotónica) | **94,8** [84,2 – 102,1] (núcleo + amortiguamiento 18,2; transición 76,5) |
| Media L4A × área (ponderada por zona: 131) | 116 |
| Altura de Meta con la ecuación, sin calibrar (p95 a 25 m) | 95,6 |
| Ecuación calibrada contra RH95 de GEDI | 146 – 177 |

**Lectura.** Ningún valor está validado en campo. Dado que la ecuación infla las alturas bajas respecto de L4A, **los 146–177 ktC (que usan la ecuación) probablemente sobreestiman**, y el rango más consistente con un producto calibrado con parcelas es **≈ 95–130 ktC**. L4A es a su vez un modelo global con error propio, sobre todo en vegetación baja y herbácea; no es verdad de campo.

**Qué hacer.** Si se quiere un valor central, usar la calibración de la altura contra L4A (o contra parcelas, si llegan) y no la ecuación; si se conserva la ecuación, presentarla como una hipótesis no validada.

**Qué dicen los documentos del proyecto sobre la ecuación** (extracción con NotebookLM de los PDF del trabajo; las citas **no se verificaron contra los PDF**):

1. **El paper se contradice a sí mismo.** La §2.3 (p. 3) de `Carbono_Pereyra_JAIIO2026_v2.pdf` describe la ecuación completa de Chave et al. (2014), `AGB = 0,0673·(ρ·D²·H)^0,976`, con el diámetro D estimado por un modelo H:D a partir de RH95. El Apéndice A2 (p. 8) da otra: `AGB = 0,0673·(ρ·H)^1,23·100; C = 0,47·AGB`, «exportado como Carbono_Pereyra.tif». **La segunda es la que generó los datos**; la primera coincide con la descripción del notebook del repositorio anterior.
2. **El exponente 1,23 se presenta como un resultado y es circular.** Los textos informan una regresión log-log altura–carbono con pendiente 1,23 y R² = 0,98 (`Pereyra.pdf`, §3.3), R² = 0,93 «exploratoria» (apéndice) y R² = 1,000 (notebook). Esa pendiente es el exponente de la propia ecuación, así que no puede respaldarla. No hay una derivación documentada del 1,23. El «Informe Crítico de Validación» ya lo marcó («relación tautológica (circular)»).
3. **La densidad de madera no era específica del sitio.** El texto dice que se asigna «por tipo de hábitat según el mapa UNESCO» (§2.3) y «por clase de cobertura» (§4.3); el código usa **ρ = 0,6 constante**, que coincide con el supuesto del ejemplo de las guías de Winrock («Wood Density is assumed to be 0.6 g/cm3 for all trees»).
4. **La fracción de carbono cambia entre versiones:** 0,47 en la v2 (Winrock, que cita IPCC 2006, Tabla 4.3) y 50 % en `Pereyra.pdf`.
5. **Ni Chave (2014) ni Winrock proponen estimar la biomasa de árboles vivos solo con la altura del dosel.** La Ec. (4) de Chave usa D, H y ρ por árbol (en kg); su Ec. (7) prescinde de la altura. Las guías de Winrock usan el diámetro.
6. **Los informes de validación** recomiendan incorporar la densidad de la madera por tipo funcional de vegetación y señalan la simplificación; evaluaron un texto que describía GEDI como fuente de la altura.

**Conclusión.** La ecuación es una **simplificación propia de Chave (2014)**, sin derivación ni calibración documentadas, con un exponente que no tiene respaldo. La §2.3 y la §4.3 del paper publicado deben corregirse para que describan lo que se hizo (Apéndice A2, ρ constante).

### 3.11 Texto del paper vs. apéndice vs. archivos — *Verificado contra archivos donde se indica; el resto, extracción con NotebookLM sin verificar contra los PDF*
El apéndice A2 de `Carbono_Pereyra_JAIIO2026_v2.pdf` describe el flujo real (altura de Meta, ecuación simplificada, Sentinel-2 de 2024, NBR). El cuerpo del texto describe otro.

| Aspecto | Cuerpo del paper (v2) | Apéndice A2 y archivos |
|---|---|---|
| Fuente de la altura de dosel | GEDI L2A RH95 (§2.2.1, p. 3) | **Meta/WRI de 1 m** (A2, p. 8; `Pereyra.pdf` §3.1; raster `Altura_Dosel_Pereyra.tif`) |
| Sentinel-2 | 2023; nubes < 10 % con QA60 (§2.2.2) | **2024**; nubosidad de escena < 20 %, sin máscara por píxel (notebook y archivos) |
| Bandas | B2, B3, B4, B8, B11, **B12**, NDVI, NDWI (Tabla 2) | B2, B3, B4, B8, B11, NDVI, NDWI y **NBR**; sin B12 (stack exportado) |
| Resolución de `Carbono_Pereyra.tif` | 10 m (§2.3) | ~5 m; la de 10 m es un remuestreo bilineal (archivos) |
| Las 873.668 muestras | «cobertura completa de la reserva tras filtrado GEDI» (Tabla 3) | Píxeles de 10 m con carbono > 0 del raster remuestreado; **no hay filtrado GEDI** en los datos |
| Partición 70/30 | «aleatoria por clase de altura» (Tabla 3) | Aleatoria simple, sin estratificar (código) |
| Ecuación y ρ | Chave completa con D; ρ por hábitat (§2.3, §4.3) | Ecuación simplificada con ρ = 0,6 constante (§3.10) |
| Fracción de carbono | 0,47 (v2) | 0,47 en el código; 50 % en `Pereyra.pdf` |
| Fecha del proyecto MAB-UNESCO | «2008» | El formulario está fechado en **abril de 2007** (documento del Parque) |
| Métricas (R² 0,712; RMSE 7,62; MAE 5,14; B11 59,1 %) y Tabla 6 de error por clase | Las mismas | **Coinciden** con las salidas del notebook (las etiquetas de NDVI, NDWI y NBR están desplazadas, §3.8) |

**Tabla de stock por clase de altura de `Pereyra.pdf` (§4.1).** Informa superficies de 3.000 / 2.500 / 2.000 / 1.500 / 1.000 / 248 ha (suma 10.248 ha) y 15 / 125 / 460 / 900 / 1.350 / 1.750 t C (suma 4.600 t). **No coincide con las salidas del notebook** (541,43 / 89,01 / 70,01 / 42,27 / 8,11 / 2,96 ha; 4.665 t) y las superficies son números redondos que suman exactamente el área de la reserva. No se conoce cómo se obtuvieron esos valores; **no deben citarse** hasta aclararlo.

**Tabla por zonas.** El apéndice A2 menciona el análisis por zonas y su exportación a `Carbono_Zonas.csv`, pero según la extracción la tabla con valores **no figura** en el texto de la v2. Verificar si se publicó en algún lado antes de pedir su retiro.

**Informes de validación.** Ni el «Informe Crítico de Validación» ni «Validación GEDI» identifican autor, herramienta ni fecha; ambos dan una valoración global de «Ajustable» y recomiendan, entre otras cosas, aclarar la fuente del mapa de 1 m, detallar los filtros GEDI, cuantificar la incertidumbre y validar con parcelas de campo.

**Uso de IA declarado.** El apéndice C de la v2 declara el uso de ChatGPT para la redacción y para la «revisión y documentación de los scripts de Python en Google Colab». Es una **hipótesis** (no una conclusión) que ese proceso explique por qué el notebook del repositorio anterior describía un flujo distinto del que generó los datos.

---

## 4. Qué cambiar

### Paper
| # | Cambio |
|---|---|
| 1 | Describir el método real: *altura de dosel Meta/WRI (1 m) → ecuación alométrica → RF con Sentinel-2*. GEDI, si se mantiene, como **chequeo independiente** de la altura |
| 2 | Reemplazar 4,6 kt por el stock recalculado y presentarlo **como rango** (§2), con la advertencia de que la ecuación no está validada |
| 3 | Aclarar el dominio: área real analizada y qué parte de la reserva cubre |
| 4 | Quitar o rehacer la tabla por zonas |
| 5 | Presentar R² como consistencia del modelo con la altura de Meta, no como validación de carbono |
| 6 | Agregar el chequeo Meta vs. GEDI y el sesgo de altura a Limitaciones |
| 7 | Corregir el hallazgo de importancia de variables según §3.8: NDVI = 4,3 % (no 3,2 %); B11 = 59,1 % se mantiene |
| 8 | Si el trabajo se presenta junto con Iguazú, comparar **con el mismo método** (§3.9) y no los R² ni los mapas del RF |
| 9 | Corregir la §2.3 (ecuación de Chave completa con D estimado) y la §4.3 (ρ por hábitat) según el Apéndice A2: ecuación simplificada con ρ = 0,6 constante; no presentar la pendiente log-log 1,23 ni su R² como respaldo (§3.10) |
| 10 | Reescribir §2.2, §2.3, las Tablas 2 y 3 y la §4.3 según el apéndice A2 y los archivos (fuente de la altura, año y bandas de Sentinel-2, resolución, origen de las muestras, partición); no citar la tabla de stock por clase de `Pereyra.pdf` hasta aclarar su origen (§3.11) |

### Repositorio
- Subir el código real que genera `Altura_Dosel_Pereyra*.tif` y `Carbono_Pereyra.tif`, con la fórmula usada.
- Corregir README: stock, área, descripción del pipeline (hoy dice GEDI RH95), lista de archivos.
- Quitar o corregir `Carbono_Zonas.csv` y `Resumen_Altura_Pereyra.csv`, o regenerarlos con área real.
- Verificar que las bandas del stack coincidan con las etiquetas del notebook.

### Texto sugerido (Métodos y Limitaciones)
> *Métodos.* La altura del dosel se obtuvo del mapa global de altura de dosel de 1 m (Meta/WRI; Tolan et al., 2024), promediada a ~5 m. El carbono aéreo se estimó mediante la ecuación alométrica C = 0,0673·(ρh)^1,23 × 100 × 0,47 (ρ = 0,6), sin calibración local. Se entrenó un Random Forest para predecir ese carbono a partir de un mosaico anual Sentinel-2. El stock se calculó con el área real del píxel dentro del polígono de la reserva (10.053 ha).
>
> *Limitaciones.* El R² del modelo mide la capacidad de Sentinel-2 para reproducir un producto derivado de altura de dosel y no constituye validación frente a carbono medido en campo. La altura de Meta resultó, frente a 3.280 huellas GEDI (filtradas por calidad, noche y pendiente), en promedio 2,8 m menor (r = 0,88; ≈ 3,9 m donde ambos detectan vegetación). Corregir ese sesgo eleva la estimación de stock en un factor de ~2,3 a 2,8. La ecuación alométrica, desarrollada para árboles individuales, no se validó contra parcelas.

---

## 5. Pendiente / sin verificar
- Obtener la zonificación oficial **en formato vectorial** (el Parque envió documentos y mapas en imagen, ver §3.4) para calcular carbono por zona.
- Si hay parcelas de campo en Pereyra, validar la ecuación de carbono: es el factor que más pesa y el menos conocido.
- Validar con parcelas de campo en Iguazú (los pedidos están redactados en `PEDIDOS_DATOS.md`): es lo único que permite decidir entre 41,5, 59,7 y 73,5 tC/ha.

## 6. Archivos de soporte (carpeta `carbono-iguazu-gedi/`)
`pereyra_osm.geojson` · `pares_meta_gedi_reserva.csv` · `Meta_H5m_mean.tif` · `Meta_H25m.tif` · `Stock_Pereyra_reserva.csv` · `stock_pereyra_reserva_completa.py` · `calibracion_meta_gedi_pereyra.py` · `comparacion_pereyra_iguazu.py` · `Comparacion_Pereyra_Iguazu.csv` · `Comparacion_estructura_Pereyra_Iguazu.csv` · `repo_pereyra_actualizado/` (script único `pereyra_carbono.py` y README para el repo) · `PEREYRA_poligono_vs_caja.png` (esta imagen se hizo antes de contrastar con OSM; su lectura de "desalineación" quedó descartada)
