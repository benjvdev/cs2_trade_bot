# CS2 Trade & Arbitrage Bot

Herramienta avanzada para la simulación de contratos (trade-ups) y detección de oportunidades de arbitraje entre múltiples mercados (Buff163, Steam, CSFloat, Skinport, Skinbaron).

## Características

- **Scraping Multi-mercado:** Obtiene precios en tiempo real de Buff163 (vía Playwright), Steam, CSFloat (con soporte API Key), Skinport y Skinbaron.
- **Arbitrage Engine:** Encuentra diferencias de precio netas considerando comisiones de distintos mercados.
- **Contract Hunter Pro:** Optimiza combinaciones de contratos (10x, 9x+1x, etc.) buscando los insumos más baratos globalmente.
- **Daily Dump:** Extracción masiva diaria de datos de mercado para análisis a largo plazo.
- **Continuous Intelligence Loop:** Bucle continuo que monitorea precios, extrae información en tiempo real, analiza oportunidades en lotes (batching) y notifica de hallazgos.
- **Gestión de Riesgo:** Filtra items por volumen de venta y estabilidad de precio para mitigar el Trade Hold de 7 días.

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
- `csfloat_api_key`: Tu clave de API para CSFloat.
- `batch_size`: Tamaño del lote de peticiones para operaciones continuas y scraping.
- `batch_sleep`: Tiempo de espera (en segundos) entre lotes para evitar bloqueos por rate-limit.
- `skinport_api_key`: Clave para Skinport (opcional).
- `skinbaron_api_key`: Clave para Skinbaron (opcional).

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
  Inicia el bucle continuo que realiza el monitoreo automático de precios y análisis, integrando los datos de todos los mercados soportados.
  ```bash
  python -m app.main --loop
  ```

Los resultados de los análisis aparecerán en la carpeta `reports/`.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un Issue o un Pull Request para discutir cualquier cambio.

## Licencia

[MIT](LICENSE)