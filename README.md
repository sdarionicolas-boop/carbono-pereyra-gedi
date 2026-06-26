# Carbono Aéreo — Reserva de Biósfera Pereyra Iraola
## Pipeline: GEDI L2A + Sentinel-2 L2A + Random Forest

[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://python.org)
[![Google Colab](https://img.shields.io/badge/Google%20Colab-ready-orange)](https://colab.research.google.com)
[![Licencia](https://img.shields.io/badge/Licencia-MIT-green)](LICENSE)

**Autor:** Darío Nicolás Sánchez Leguizamón  
**Institución:** Universidad Nacional Arturo Jauretche (UNAJ), Argentina  
**Contacto:** sdarionicolas@gmail.com

**Paper:** *Estimación del carbono aéreo en la Reserva de Biósfera Pereyra Iraola (Buenos Aires, Argentina) mediante integración de datos GEDI, Sentinel-2 e inteligencia artificial*  
**Congreso:** CAI 2026 — 55 JAIIO, La Plata, Argentina, 2026

---

## Descripción

Pipeline computacional **modular y reproducible** para la estimación y cartografía de carbono aéreo
en la Reserva de Biósfera Pereyra Iraola (~10.248 ha, Buenos Aires, Argentina).

Integra tres capas tecnológicas:
- **GEDI L2A** (NASA): altura del dosel mediante LiDAR orbital (métrica RH95)
- **Sentinel-2 L2A** (ESA/Copernicus): imágenes multiespectrales de 10 m procesadas en GEE
- **Random Forest** (scikit-learn): regresión multibanda para predicción espacial del carbono

### Métricas del modelo principal

| Métrica | Valor |
|---------|-------|
| R²      | 0.71  |
| RMSE    | 7.62 tC/ha |
| MAE     | 5.14 tC/ha |
| Muestras | 873.668 píxeles |
| Stock total estimado | 4.6 ktoneladas de C |

### Hallazgo principal

La banda **SWIR1 (B11)** concentra el **59.1% de la importancia del modelo**, superando ampliamente al NDVI (3.2%), que se satura en ecosistemas de alta cobertura boscosa.

---

## Estructura del repositorio

```
carbono-pereyra-gedi/
├── Carbono_Pereyra_GEDI_Sentinel2_RF.ipynb   # Pipeline principal (Google Colab)
├── README.md                                  # Este archivo
└── LICENSE                                    # Licencia MIT
```

### Módulos del notebook

| Módulo | Descripción |
|--------|-------------|
| 0 | Configuración, instalación de dependencias y autenticación GEE |
| 1 | Adquisición y exportación GEDI L2A desde GEE |
| 2 | Adquisición y exportación Sentinel-2 L2A desde GEE |
| 3 | Estimación de biomasa y carbono aéreo (alometría Chave et al., 2014) |
| 4 | Random Forest univariado altura → carbono (referencia intermedia) |
| 5 | Random Forest multibanda Sentinel-2 → carbono (modelo principal) |
| 6 | Validación visual: scatter plot, mapa de carbono y residuos |
| 7 | Análisis estratificado del error por clase de altura del dosel |
| 8 | Importancia de variables espectrales (Feature Importance Gini) |

---

## Requisitos previos

1. Cuenta de Google con acceso a [Google Earth Engine](https://earthengine.google.com/)
2. Proyecto GEE activo (gratuito para investigación)
3. Google Drive con al menos 2 GB libres
4. No se requieren instalaciones locales — todo corre en **Google Colab**

---

## Cómo usar este pipeline

### Paso 1 — Clonar o descargar

```bash
git clone https://github.com/sdarionicolas-boop/carbono-pereyra-gedi.git
```

O descargá directamente el archivo `.ipynb` y subílo a Google Colab.

### Paso 2 — Configurar parámetros

Editá **solo la celda de parámetros globales** (Módulo 0):

```python
# Reemplazá con tu proyecto GEE
GEE_PROJECT = 'TU_PROYECTO_GEE'

# Ajustá si querés analizar otra área
COORDS_RESERVA = [...]

# Año del mosaico Sentinel-2
S2_YEAR = '2023'
```

### Paso 3 — Ejecutar en orden

Ejecutá los módulos de 0 a 8 secuencialmente.

> ⚠️ **Módulos 1 y 2** exportan datos a Google Drive mediante GEE (tarea asincrónica).  
> Esperá a que finalicen las tareas en el panel **Tasks** de GEE antes de continuar con el Módulo 3.

### Archivos generados

El pipeline crea los siguientes archivos en tu carpeta `PEREYRA/` de Google Drive:

| Archivo | Descripción |
|---------|-------------|
| `GEDI_RH95_Pereyra.tif` | Altura del dosel (m), resolución ~25 m |
| `Sentinel2_Pereyra_Stack.tif` | Stack multibanda de 8 capas, 10 m |
| `Carbono_Pereyra.tif` | Carbono alométrico observado (tC/ha) |
| `Carbono_Pereyra_10m.tif` | Carbono remuestreado a 10 m |
| `Carbono_Predicho_RF.tif` | Carbono predicho por Random Forest |
| `Carbono_Residuos_RF.tif` | Residuos espaciales del modelo |
| `Scatter_Validacion_RF.png` | Gráfico observado vs. predicho (Figura 1 del paper) |
| `Mapa_Carbono_RF.png` | Mapa final de distribución de carbono (Figura 2 del paper) |
| `Mapa_Residuos_RF.png` | Mapa y distribución de residuos |
| `Importancia_Variables_RF.png` | Feature importance de las 8 bandas |
| `Error_Por_Clase_Altura.csv` | Error estratificado por clase de dosel |

---

## Dependencias

Todas se instalan automáticamente en Colab con el Módulo 0:

```
geemap
geopandas
rasterio
matplotlib
pandas
scikit-learn
```

---

## Transferibilidad

Para adaptar el pipeline a otra área de estudio:

1. Redefinir `COORDS_RESERVA` con las coordenadas del nuevo sitio
2. Ajustar `DRIVE_FOLDER` si querés otra carpeta de salida
3. Los módulos 1–8 corren sin modificaciones adicionales

El único paso que requiere reentrenamiento es el Módulo 5 (Random Forest multibanda),
ya que los pesos aprendidos son específicos del ecosistema de entrenamiento.

---

## Citar este trabajo

Si usás este pipeline en tu investigación, por favor citá:

> Leguizamón, D. N. S. (2026). Estimación del carbono aéreo en la Reserva de Biósfera Pereyra Iraola (Buenos Aires, Argentina) mediante integración de datos GEDI, Sentinel-2 e inteligencia artificial. *CAI 2026 — 55 JAIIO*, La Plata, Argentina.

---

## Licencia

Este proyecto está bajo la [Licencia MIT](LICENSE).  
Podés usar, modificar y redistribuir el código con atribución al autor.

---

## Referencias principales

- Belgiu, M. y Drăguț, L. (2016). Random forest in remote sensing. *ISPRS Journal*, 114, 24–31.
- Chave, J., et al. (2014). Improved allometric models. *Global Change Biology, 20*(10), 3177–3190.
- Dubayah, R., et al. (2020). The Global Ecosystem Dynamics Investigation. *Science of Remote Sensing, 1*, 100002.
- Lei, Y., et al. (2024). Estimating forest canopy height based on GEDI. *ISPRS Archives, XLVIII-1*, 297–303.
- Sione, S. M., et al. (2021). Estimación del contenido y captura potencial de carbono en el Espinal. *FAVE, 20*(1), 331–349.
- Winrock International. (2018). *Calculating carbon stocks: A guidance module*.
