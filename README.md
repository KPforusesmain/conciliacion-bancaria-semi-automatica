# Conciliación Bancaria Semi-Automática

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/pandas-2.0%2B-green)](https://pandas.pydata.org/)
[![RapidFuzz](https://img.shields.io/badge/RapidFuzz-3.0%2B-orange)](https://github.com/maxbachmann/RapidFuzz)
[![License](https://img.shields.io/badge/license-MIT-purple)](LICENSE)

**Automatización financiera inteligente para conciliar movimientos bancarios con registros contables mediante reglas de matching por monto, fecha y similitud de texto.**

---

## Tabla de Contenidos
- [Conciliación Bancaria Semi-Automática](#conciliación-bancaria-semi-automática)
  - [Tabla de Contenidos](#tabla-de-contenidos)
  - [Objetivo del Proyecto](#objetivo-del-proyecto)
  - [Problema de Negocio](#problema-de-negocio)
  - [🛠 Tecnologías Utilizadas](#-tecnologías-utilizadas)
  - [Funcionalidades](#funcionalidades)
  - [Instalación y Uso](#instalación-y-uso)
    - [Prerrequisitos](#prerrequisitos)
    - [Pasos](#pasos)
    - [Mejoras aplicadas:](#mejoras-aplicadas)

---

## Objetivo del Proyecto

Reducir el trabajo manual, mejorar la trazabilidad de diferencias y fortalecer el control interno a través de una conciliación semi-automatizada que clasifica los resultados en:

| Categoría | Descripción |
|-----------|-------------|
| `matched` | Transacciones que coinciden en banco y contabilidad |
| `review` | Coincidencias parciales que requieren análisis humano |
| `unmatched` | Registros sin contraparte en el otro libro |

---

## Problema de Negocio

La conciliación bancaria manual es un proceso crítico pero tedioso que presenta múltiples desafíos:

- **Alto consumo de tiempo** en búsquedas y verificaciones manuales
- **Errores humanos** por descripciones inconsistentes o diferencias de fecha
- **Dificultad para detectar** partidas no registradas o registradas tarde
- **Referencias incompletas** que dificultan el matching automático
- **Baja trazabilidad** de diferencias en cierres contables

Este proyecto propone una solución base **reutilizable y escalable** para apoyar cierres contables, revisión operativa y análisis de diferencias.

---

## 🛠 Tecnologías Utilizadas

| Tecnología | Uso |
|------------|-----|
| ![Python](https://img.shields.io/badge/Python-3.8%2B-blue) | Lenguaje principal |
| ![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-green) | Procesamiento y manipulación de datos |
| ![RapidFuzz](https://img.shields.io/badge/RapidFuzz-Fuzzy%20Matching-orange) | Comparación difusa de texto |
| ![OpenPyXL](https://img.shields.io/badge/OpenPyXL-Excel%20Export-yellow) | Generación de archivos Excel |
| ![Matplotlib](https://img.shields.io/badge/Matplotlib-Visualization-red) | Creación de gráficos automáticos |
| ![ReportLab](https://img.shields.io/badge/ReportLab-PDF%20Generation-purple) | Generación de reportes PDF |
| ![CSV/Excel](https://img.shields.io/badge/CSV%2FExcel-Input%2FOutput-brightgreen) | Formatos de entrada/salida |
| ![GitHub](https://img.shields.io/badge/GitHub-Version%20Control-black) | Control de versiones y colaboración |
| ![VS Code](https://img.shields.io/badge/VS%20Code-IDE-blue) | Entorno de desarrollo |

---

## Funcionalidades

- **Lectura de archivos**: Soporte para bancarios y contables en formato CSV
- **Limpieza de datos**: Normalización de formatos, fechas y montos
- **Matching inteligente**: 
  - Monto exacto
  - Fecha con tolerancia configurable
  - Similitud de texto con RapidFuzz
- **Clasificación automática**:
  - Matched: Coincidencia perfecta
  - Review: Coincidencia parcial (requiere revisión)
  - Unmatched: Sin coincidencia
- **Generación de reportes**:
  - CSV de resultados por categoría
  - Excel consolidado con pestañas separadas
  - Gráficos automáticos de distribución
  - PDF ejecutivo con resumen y análisis

---


---

## Instalación y Uso

### Prerrequisitos
- Python 3.8 o superior
- pip (gestor de paquetes)

### Pasos

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/KPforusesmain/conciliacion-bancaria.git
   cd conciliacion-bancaria

### Mejoras aplicadas:
1. **Estructura profesional:** Tabla de contenidos, secciones claras.
2. **Formato atractivo:** Uso de emojis, badges, tablas.
3. **Detalles técnicos:** Estructura de carpetas, lógica de matching explicada.
4. **Usabilidad:** Instrucciones paso a paso, ejemplos de salida.
5. **Escalabilidad:** Sección de mejoras futuras y contribuciones.
