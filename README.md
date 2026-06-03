# CS2 Trade & Arbitrage Bot

Herramienta avanzada para la simulacion de contratos (trade-ups) y deteccion de oportunidades de arbitraje entre Buff163, Steam y CSFloat. Skinport se consume actualmente mediante daily dump cuando esta disponible; Skinbaron queda reservado para daily dump futuro si vuelve a existir un endpoint JSON valido. No existen scrapers autenticados dedicados para Skinport/Skinbaron.

## Características

- **Scraping Multi-mercado:** Obtiene precios live de Buff163 (via Playwright), Steam y CSFloat (con soporte API Key). Buff, Steam y Skinport tambien se consumen desde daily dumps CSGOTrader cuando estan disponibles; Skinbaron no tiene endpoint JSON activo actualmente.
- **Arbitrage Engine:** Encuentra diferencias de precio netas considerando comisiones de distintos mercados.
- **Contract Hunter Pro:** Optimiza combinaciones de contratos (10x, 9x+1x, etc.) buscando los insumos más baratos globalmente.
- **Daily Dump:** Extracción masiva diaria de datos de mercado para análisis a largo plazo.
- **Continuous Intelligence Loop:** Bucle continuo que monitorea precios, extrae información en tiempo real, analiza oportunidades en lotes (batching) y notifica de hallazgos.
- **Estado de datos:** En la ruta completa/default, si todos los scrapers y dumps fallan, el bot se niega a analizar para evitar reportes obsoletos. La marca por ventana de frescura (`max_price_age_hours`) esta planificada/en estabilizacion.
- **Gestion de Riesgo:** Incluye parametros de ROI, presupuesto y frescura; los filtros completos de volumen/liquidez y estabilidad siguen en estabilizacion y no deben tratarse como validacion live completa.

## Estructura del Proyecto

```text
cs2_trade_bot/
├── app/
│   ├── core/           # Motores de análisis (Arbitraje, Contratos, Probabilidades, Continuous Loop)
│   ├── database/       # Gestión de base de datos SQLite
│   ├── scrapers/       # Workers de obtención de datos (Python & Node.js, Daily Dump)
│   └── main.py         # Orquestador principal
├── data/               # Bases de datos y archivos de respaldo
├── docs/               # Documentación y especificaciones de diseño
├── reports/            # Reportes generados en CSV
└── config.json         # Configuración personal (Ignorado por Git)
```

## Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/tu-usuario/cs2_trade_bot.git
   cd cs2_trade_bot
   ```

2. **Entorno de Python:**
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\activate
   # Linux/Mac
   source .venv/bin/activate
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

3. **Entorno de Node.js (Scraper de Buff):**
   ```bash
   cd app/scrapers/buff
   npm install
   cd ../../../
   ```

## Configuración

Copia el archivo de ejemplo y rellena tus datos (incluyendo la cookie de sesión de Buff, API Keys y opciones de batching):
```bash
cp config.example.json config.json
```

**Nuevos campos de configuración:**

`config.json` contiene configuracion personal y permanece ignorado por Git. No subas cookies ni API keys al repositorio. Tambien puedes suministrar secretos mediante variables de entorno; si existen, reemplazan los valores del archivo:

- `BUFF_SESSION`
- `CSFLOAT_API_KEY`
- `SKINPORT_API_KEY`
- `SKINBARON_API_KEY`

Nota: las variables de Skinport y Skinbaron se aceptan como overrides de configuracion, pero la ingesta actual de Skinport usa daily dump cuando esta disponible. Skinbaron no tiene endpoint JSON activo actualmente. Los scrapers autenticados dedicados para Skinport/Skinbaron aun no estan implementados.

- `csfloat_api_key`: Tu clave de API para CSFloat.
- `batch_size`: Tamaño del lote de peticiones para operaciones continuas y scraping.
- `batch_sleep`: Tiempo de espera (en segundos) entre lotes para evitar bloqueos por rate-limit.
- `skinport_api_key`: Reservado para una futura integracion autenticada de Skinport; actualmente Skinport llega por daily dump cuando esta disponible.
- `skinbaron_api_key`: Reservado para una futura integracion autenticada de Skinbaron; actualmente Skinbaron no tiene endpoint JSON activo en daily dump.

## Uso

El bot se maneja mediante argumentos de línea de comandos:

- **Ejecutar todo (Scraping + Análisis):**
  ```bash
  python -m app.main --all
  ```

- **Solo actualizar precios:**
  ```bash
  python -m app.main --scrape
  ```

- **Solo realizar análisis y generar reportes:**
  ```bash
  python -m app.main --analyze
  ```

- **Ejecutar el Continuous Intelligence Loop:**
  Inicia el bucle continuo que realiza el monitoreo automatico de precios y analisis, combinando live scrapers de Buff/Steam/CSFloat con los datos de daily dump disponibles.
  ```bash
  python -m app.main --loop
  ```

Los resultados de los analisis apareceran en la carpeta `reports/`. En la ruta completa/default, si ningun scraper o dump reporta exito, el proceso se detiene antes de analizar datos viejos. La marca automatica de reportes por edad de fuente aun se esta estabilizando alrededor de `max_price_age_hours`.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un Issue o un Pull Request para discutir cualquier cambio.

## Licencia

[MIT](LICENSE)
