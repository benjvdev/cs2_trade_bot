# Especificación de Diseño: CS2 Trade & Arbitrage Bot

## 1. Visión General
El objetivo de este proyecto es construir una herramienta avanzada de inteligencia de mercado para CS2 que combine la simulación de contratos (trade-ups) con la detección de oportunidades de arbitraje entre Buff163 (China), Steam y CSFloat.

## 2. Requisitos Clave
- **Scraping Multi-mercado:** Obtención de precios en bloque de Buff163, Steam y CSFloat.
- **Detección de Arbitraje:** Identificación de diferencias de precio netas (post-comisiones).
- **Arbitraje de Delay:** Detección de tendencias en China antes de que lleguen a Occidente.
- **Hunter de Contratos Pro:** Combinaciones dinámicas (1x9, 5x5, etc.) con optimización de compra en Buff.
- **Gestión de Riesgo:** Filtros de volumen y estabilidad para manejar el Trade Hold de 7 días.

## 3. Arquitectura Propuesta (Refactor)

Para mejorar el orden y mantenimiento, reestructuraremos el proyecto de la siguiente manera:

```text
cs2_trade_bot/
├── app/
│   ├── core/                # Lógica de negocio (Motores)
│   │   ├── arbitrage.py     # Lógica de comparación
│   │   ├── contracts.py     # Hunter de contratos (v6)
│   │   ├── math_engine.py   # Cálculos de floats (existente)
│   │   └── probability.py   # Motor de probabilidades (existente)
│   ├── database/            # Gestión de SQLite
│   │   └── db_manager.py    
│   ├── scrapers/            # Workers de obtención de datos
│   │   ├── buff/            # Scraper Node/Playwright para Buff
│   │   ├── steam.py         # Scraper API para Steam
│   │   └── csfloat.py       # Scraper API para CSFloat
│   ├── utils/               # Utilidades generales
│   │   ├── currency.py      # Conversor RMB -> USD
│   │   └── logger.py        # Registro de actividades
│   └── main.py              # Punto de entrada principal
├── data/                    # DB, JSONs y Archivos de respaldo
├── docs/                    # Documentación y especificaciones
├── reports/                 # Carpeta de salida para CSVs/Excel
├── config.json              # Configuración de límites y filtros
└── requirements.txt         # Dependencias del proyecto
```

## 4. Componentes Detallados

### 4.1. Workers (Scrapers)
- **Buff Worker:** Utilizará Playwright (Node.js) para evadir Cloudflare y extraer precios de las listas de mercado mediante cookies de sesión.
- **Steam Worker:** Consultas a `market/search/render` en bloques de 100 items.
- **CSFloat Worker:** Uso de la API pública para obtener los listados más económicos.

### 4.2. Motor de Análisis (The Brain)
- **Cálculo de Beneficio Neto:**
  `Profit = (Precio_Venta * (1 - Comisión)) - Precio_Compra`
  *Comisiones:* Steam (15%), CSFloat (2%).
- **Filtro de Liquidez:** Solo recomendará items con un volumen diario superior al umbral configurado.

### 4.3. Hunter de Contratos
- Permitirá mezclas de hasta 5 colecciones diferentes.
- Calculará el ROI basándose en la compra de los 10 items en el mercado más barato disponible.

## 5. Reportes de Salida
Se generarán dos reportes principales:
1. `arbitraje_oportunidades.csv`: Lista de skins para compra directa y reventa.
2. `contratos_rentables.csv`: Guía de compra de inputs para trade-ups.

## 6. Siguientes Pasos
1. Refactorización de la estructura de carpetas.
2. Implementación del Worker de Buff (Fase Crítica).
3. Integración de la lógica de comparación multi-mercado.
4. Generación automatizada de reportes.
