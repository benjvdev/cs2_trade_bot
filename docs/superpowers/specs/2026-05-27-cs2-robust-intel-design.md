# Diseño de Especificación: CS2 Robust Intelligence Bot (v2.0)

## 1. Objetivo
Transformar el bot actual en una herramienta de grado profesional capaz de monitorear el mercado global de CS2 sin riesgo de baneo, utilizando un modelo de datos híbrido (Volcado Diario + Verificación en Vivo).

## 2. Componentes de Datos (The Data Layer)

### 2.1. Base Update (Daily Dump)
- **Fuente:** JSONs de CSGOTrader (`prices.csgotrader.app`).
- **Función:** Descarga y carga masiva de precios de Buff163, Steam, Skinport y Skinbaron (20,000+ items).
- **Frecuencia:** Una vez cada 24 horas.

### 2.2. Smart Scrapers (Live Layer)
- **Buff Worker (Navegador):** Rotación de 1 categoría cada 180 segundos para evitar detección.
- **Steam Worker (API):** Límite estricto de 15 peticiones/minuto.
- **CSFloat Worker (API Key):** Implementación de autenticación por cabecera `Authorization` para eliminar el error 403.

## 3. Lógica de Inteligencia (The Brain)

### 3.1. Arbitrage Engine v2
- **Comparación Global:** Buff Live vs [Steam Live, CSFloat Live, Skinport Dump, Skinbaron Dump].
- **Detección de Trend-Lag:** Compara el precio actual de Buff contra la media del Daily Dump. Si el precio sube en Buff pero no en el Dump, se genera una señal de compra en mercados occidentales.
- **Matriz de Comisiones:**
  - Steam: 15%
  - CSFloat: 2%
  - Skinport: 12%
  - Skinbaron: 15%

### 3.2. Hunter Engine "Smart-Verify"
- **Fase A:** Simulación de contratos en segundo plano usando los precios del Daily Dump (Cobertura total del mercado).
- **Fase B:** El sistema genera un ranking global de los mejores ~500 contratos teóricos.
- **Fase C (Continuous Intelligence Loop):**
  - El bot procesa el ranking en bloques (batches) de 50 items.
  - Para cada bloque, lanza los scrapers Live, valida la rentabilidad y actualiza el reporte.
  - Entre bloques, aplica pausas de enfriamiento para resetear los límites de los servidores.
  - El proceso puede ejecutarse en bucle infinito para mantener una vigilancia constante del mercado.

## 4. Medidas Anti-Ban
- **Jitter aleatorio:** Retrasos variables entre 5% y 15% en cada petición.
- **User-Agent Masquerade:** Rotación de cabeceras de navegador real.
- **Sequential Execution:** Nunca lanzar dos scrapers al mismo tiempo sobre el mismo mercado.
- **Cool-down periods:** Pausas obligatorias entre ciclos de análisis masivo.

## 5. Reportes y Documentación
- `arbitraje_inteligente.csv`: Oportunidades con "Nivel de Confianza" basado en la frescura de los datos.
- `contratos_validados.csv`: Contratos que han pasado la Fase C de verificación Live.
- `alertas_mercado.txt`: Notificaciones de subidas de precio en China (Trend-Lag).
- **README Update:** Al finalizar la implementación, se actualizará el manual de usuario para reflejar los nuevos modos de uso y la configuración de la API Key de CSFloat.
