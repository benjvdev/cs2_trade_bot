# Especificación de Diseño: CS2 Trade & Arbitrage Bot

## 1. Visión General
El objetivo de este proyecto es construir una herramienta avanzada de inteligencia de mercado para CS2 que combine la simulación de contratos (trade-ups) con la detección de oportunidades de arbitraje entre Buff163 (China), Steam y CSFloat.

## 2. Requisitos Clave
- **Scraping Multi-mercado:** Obtencion de precios en bloque de Buff163, Steam y CSFloat, mas daily dumps para Buff/Steam/Skinport cuando esten disponibles. Skinbaron queda pendiente de un endpoint JSON valido.
- **Detección de Arbitraje:** Identificación de diferencias de precio netas (post-comisiones).
- **Arbitraje de Delay:** Detección de tendencias en China antes de que lleguen a Occidente.
- **Hunter de Contratos Pro:** Combinaciones dinámicas (1x9, 5x5, etc.) con optimización de compra en Buff.
- **Gestion de Riesgo:** Objetivo de filtros de volumen, estabilidad y frescura para manejar el Trade Hold de 7 dias. En la estabilizacion actual, parte de esta conducta aun requiere validacion live y no debe considerarse completa.

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
│   │   ├── csfloat.py       # Scraper API para CSFloat
│   │   └── daily_dump.py    # Dumps CSGOTrader para Buff/Steam/Skinport/Skinbaron
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
- **Daily Dump Worker:** Carga dumps diarios de CSGOTrader para Buff, Steam y Skinport cuando el endpoint responde JSON valido. Skinbaron no tiene endpoint JSON activo actualmente.
- **Skinport/Skinbaron:** Actualmente no hay scrapers autenticados dedicados. Skinport se consume por daily dump cuando los datos existen; Skinbaron queda pendiente de fuente valida.

### 4.2. Motor de Análisis (The Brain)
- **Cálculo de Beneficio Neto:**
  `Profit = (Precio_Venta * (1 - Comisión)) - Precio_Compra`
  *Comisiones:* Steam (15%), CSFloat (2%), Buff (2.5%), Skinport (12%), Skinbaron (15%).
- **Fuentes confiables:** El motor de arbitraje filtra fuentes no confiables mediante una lista permitida y prioriza datos live sobre dumps para el mismo mercado.
- **Liquidez y frescura:** El filtro completo de liquidez/frescura es una meta de estabilizacion. La ruta completa/default ya rechaza analizar si todos los scrapers/dumps fallan, pero la marca automatica por edad de fuente (`max_price_age_hours`) aun esta en estabilizacion.

### 4.3. Hunter de Contratos
- Permitirá mezclas de hasta 5 colecciones diferentes.
- Calculará el ROI basándose en la compra de los 10 items en el mercado más barato disponible.

## 5. Reportes de Salida
Se generarán dos reportes principales:
1. `arbitraje_oportunidades.csv`: Lista de skins para compra directa y reventa.
2. `contratos_rentables.csv`: Guía de compra de inputs para trade-ups.

## 6. Estado Actual de Estabilizacion
1. Unit tests de matematicas/probabilidad, arbitraje basico, DB multi-source y scrapers principales cubren los caminos estabilizados.
2. La DB de precios usa clave compuesta `(market_hash_name, source)` y conserva `updated_at`, lo que permite almacenar fuentes live y dump para el mismo item.
3. CSFloat acepta payloads legacy de lista y payloads actuales con `data`/`cursor`.
4. Los scrapers principales devuelven estado observable para que `main` pueda detectar fallas agregadas.
5. El analisis de arbitraje filtra fuentes no confiables; la validacion por edad/frescura de fuente esta documentada como trabajo de estabilizacion, no como garantia completa.

## 7. Validacion Live Pendiente
1. Vigencia real de la cookie/sesion de Buff frente a Cloudflare y cambios de login.
2. Disponibilidad diaria de dumps CSGOTrader y formato JSON esperado.
3. Limites/rate limits de Steam en ejecuciones prolongadas.
