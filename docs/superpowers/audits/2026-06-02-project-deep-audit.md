# CS2 Trade Bot Deep Audit - 2026-06-02

## Alcance

Auditoria realizada sobre el proyecto en `C:\Users\Duoc\Downloads\cs2_trade_bot`.

Revisado:
- Codigo propio en `app/`, `scripts/legacy/`, `tests/` y `check_data.py`.
- Documentacion propia en `README.md`, `docs/design_spec.md`, `docs/superpowers/specs/` y `docs/superpowers/plans/`.
- Configuracion disponible, sin copiar secretos.
- Estado de Git, `.gitignore`, dependencias Python/Node, DB local, logs y reportes generados.

Excluido como codigo de proyecto:
- `.venv/`
- `app/scrapers/buff/node_modules/`
- `__pycache__/`
- `.pytest_cache/`

## Objetivo declarado del proyecto

La documentacion define el proyecto como una herramienta de inteligencia de mercado para CS2 que debe:
- Obtener precios multi-mercado: Buff163, Steam, CSFloat, Skinport y Skinbaron.
- Detectar arbitraje neto despues de comisiones.
- Simular y rankear contratos trade-up rentables.
- Usar daily dumps para cobertura amplia y scrapers live para verificacion.
- Aplicar gestion de riesgo, liquidez, frescura de datos y medidas anti-bloqueo.
- Generar reportes accionables.

## Hallazgos criticos

### 1. CSFloat no funciona por cambio/formato real del endpoint

Evidencia:
- `app/scrapers/csfloat.py:55-58` exige que `response.json()` sea una lista en la raiz.
- La llamada live del 2026-06-02 a `https://csfloat.com/api/v1/listings?limit=1` devolvio HTTP 200 con JSON tipo `dict` y claves `data` y `cursor`.
- `fetch_csfloat_prices(1)` retorno `False` con el log `CSFloat API unexpected response format (not a list)`.
- La DB local no contiene fuente `csfloat`.

Causa raiz:
- El parser esta acoplado a un contrato antiguo/incompleto. El endpoint actual entrega los listings en `payload["data"]` y usa `payload["cursor"]` para paginacion.

Impacto:
- CSFloat nunca actualiza precios.
- El motor de arbitraje y contratos trabaja sin una de las fuentes principales.
- `main.py` ignora el retorno del scraper y sigue generando analisis con datos incompletos.

Riesgos adicionales en CSFloat:
- `app/scrapers/csfloat.py:21` no usa `type=buy_now`; la muestra live incluyo `type: auction`, que no necesariamente representa una compra inmediata.
- No hay paginacion con `cursor`.
- No hay manejo especifico para `401`, `403`, `429`, HTML/no JSON o respuesta parcial.
- No existe test para este scraper.

### 2. El orquestador continua aunque fallen scrapers

Evidencia:
- `app/main.py:31-35` llama Steam y CSFloat, pero no valida sus retornos.
- `app/main.py:42-46` usa `subprocess.run(..., check=True)` para Buff, pero el script Node captura errores y no fuerza exit code distinto de cero.
- `app/scrapers/csfloat.py` retorna `False`, pero `run_scrapers()` no lo propaga.

Impacto:
- El usuario puede recibir reportes aparentemente validos aunque los datos live hayan fallado.
- Los reportes actuales incluyen oportunidades extremas basadas en datos stale/no confiables.

### 3. Daily dumps de CSGOTrader no son confiables en el entorno actual

Evidencia:
- `app/scrapers/daily_dump.py:17-19` y `:33-35` usan `requests.get(...).json()` sin validar content-type ni HTML.
- El log historico muestra `Error loading V6 dump: Expecting value: line 1 column 1`.
- Verificacion live del 2026-06-02:
  - `requests` con verificacion TLS normal fallo con `CERTIFICATE_VERIFY_FAILED`.
  - Aislando TLS con `verify=False`, ambos endpoints respondieron `403` y `text/html`.

Causa probable:
- El proveedor bloquea/filtra la descarga directa o hay un problema local de certificados; el codigo actual no distingue entre SSL, 403, HTML y JSON invalido.

Impacto:
- La cobertura masiva prometida por el proyecto puede quedar congelada.
- El bot no marca fuentes como stale ni detiene reportes si el dump falla.

### 4. La base local mezcla fuentes viejas y produce falsos positivos graves

Estado de DB local (`cs2_skins.db`):
- `skins`: 2053 filas.
- `prices`: 64044 filas.
- Fuentes:
  - `buff`: 90
  - `csgobackpack`: 30448
  - `dump_buff`: 33489
  - `steam`: 17
  - sin `csfloat`
  - sin `dump_steam`, `dump_skinport`, `dump_skinbaron` persistentes actuales
- Timestamps:
  - `csgobackpack`: 2026-02-11
  - `buff`, `dump_buff`, `steam`: 2026-05-27 a 2026-05-28

Evidencia funcional:
- `find_arbitrage_opportunities()` devolvio 29250 oportunidades.
- La primera oportunidad fue `Sticker | Titan (Holo) | Katowice 2014`, comprando en `csgobackpack` y vendiendo en `dump_buff`, con ROI mayor a 21000%.
- `reports/arbitrage_report.csv` contiene oportunidades de ese tipo.

Causa raiz:
- `app/core/arbitrage.py` no filtra por frescura, liquidez, confianza de fuente, volumen, tipo de item, ni umbral `min_roi`.
- `csgobackpack` actua como fuente de mercado vigente aunque es historica/stale.

Impacto:
- Reportes no accionables.
- Riesgo alto de decisiones comerciales incorrectas.

### 5. `ContractEngine.hunt_contracts()` es demasiado lento y no termina en tiempo razonable

Evidencia:
- Ejecutar arbitraje fue rapido.
- Ejecutar contratos junto al analisis supero 120 segundos y fue terminado por timeout.
- El conteo de candidatos no es enorme: alrededor de 1054 contratos candidatos con la configuracion actual.
- Una sola evaluacion de contrato tardo alrededor de 0.36s con 36 outcomes.

Causa raiz probable:
- `DBManager.get_price()` abre y cierra una conexion SQLite por cada consulta.
- `ContractEngine.calculate_contract_profitability()` consulta precios por cada input y cada outcome/fuente.
- `probability.simulate_contract_probabilities()` usa un `DB_PATH` global y consulta SQLite en cada simulacion.

Errores de correctness:
- `ContractEngine.calculate_contract_profitability()` solo consulta ventas live (`steam`, `csfloat`, `buff`, `skinport`, `skinbaron`, `csgobackpack`), no `dump_*`, aunque `hunt_contracts()` dice usar dump data como filtro.
- `hunt_contracts()` evalua `10x target` dentro de un loop de fillers aunque `n_f=0`; genera duplicados para el mismo target.
- Usa float fijo `0.08` sin verificar si ese float es posible para cada skin.
- El reporte de contratos no incluye receta/input composition suficiente para ejecutar la operacion.

### 6. El continuous loop no verifica realmente los items del batch

Evidencia:
- `app/core/intelligence_loop.py:37-49` toma `top_arb` y arma batches.
- `:59` llama Steam con un `limit` generico.
- `:64` llama CSFloat con un `limit` generico.
- `:76` llama Buff siempre con `weapon_ak47`.
- `contracts_results` se calcula en `:32-35`, pero no se usa.

Causa raiz:
- El loop no pasa los nombres de oportunidades a los scrapers. Por lo tanto, no refresca los items que esta intentando verificar.

Impacto:
- La "live verification" descrita en docs no ocurre.
- El loop puede dormir y repetir ciclos sin acercarse a datos frescos de las oportunidades reales.

### 7. Inconsistencia de ubicacion de DB y datos versionados

Evidencia:
- `docs/superpowers/specs/2026-05-28-db-manager-design.md` dice que DBManager apunta a `data/cs2_skins.db`.
- `app/database/db_manager.py:8-10`, `app/core/probability.py:8`, `app/scrapers/buff/index.js:6` y scripts legacy apuntan a `cs2_skins.db` en la raiz.
- `data/cs2_skins.db` existe pero no tiene tablas.
- `.gitignore` ignora `cs2_skins.db` y `prices.json`, pero ambos ya estan en `git ls-files`.

Impacto:
- Riesgo de usar una DB distinta a la esperada.
- Datos grandes y cambiantes quedan versionados.
- Los scripts legacy pueden escribir esquemas antiguos si se ejecutan.

### 8. Configuracion y secretos

Evidencia:
- `config.json` local contiene valores que parecen credenciales reales. No se copian aqui.
- `config.json` esta ignorado por Git, pero los secretos siguen existiendo en disco.
- `app/core/config.py` importa `SecretStr` pero no lo usa.
- `config.example.json` incluye `skinport_api_key` y `skinbaron_api_key`, pero `Settings` no define esos campos; Pydantic los ignora silenciosamente.
- `requirements.txt` solo contiene `cloudscraper`, `requests`, `playwright`; faltan `pydantic` y `pytest`, aunque el codigo/tests dependen de ellos.

Impacto:
- Instalacion limpia falla.
- El README promete campos que el codigo no consume.
- Riesgo de exposicion accidental de credenciales.

### 9. Buff y Steam tienen problemas de robustez

Buff:
- `app/scrapers/buff/index.js` captura errores criticos pero no termina con exit code distinto de cero; Python puede registrar "Buff scraper finished" aunque haya fallado.
- `page.waitForResponse()` filtra solo status 200; un 401/403 puede terminar como timeout opaco.
- `main.py` solo ejecuta categoria `weapon_ak47`, insuficiente para cobertura de mercado.

Steam:
- `app/scrapers/steam.py` solo maneja retry para 429; otros errores o excepciones terminan la ejecucion.
- No hay paginacion ni targeting por items concretos.
- En el log historico una llamada con `limit=50` actualizo solo 10 items.

### 10. Cobertura de tests insuficiente

Estado:
- `pytest -q`: 5 tests pasan.
- Cubierto: calculos basicos de arbitraje, lowest price basico, daily dump con mocks, math engine.
- No cubierto: CSFloat, Steam, Buff, DBManager, config, probability, CLI/main, continuous loop, freshness, stale data, report generation, performance de contratos.

Riesgos:
- La falla actual de CSFloat habria sido detectada con un test simple de payload `{"data": [...], "cursor": "..."}`.
- Tests escriben en `logs/bot.log` porque usan el logger real.

### 11. Documentacion no representa el estado real

Ejemplos:
- README dice soporte de Skinport/Skinbaron con API keys, pero solo hay dumps parciales y `Settings` ignora esas keys.
- Docs prometen gestion de riesgo por volumen/estabilidad, pero no existe en motores.
- Docs prometen live verification y trend-lag, pero el loop no targetea items ni genera alertas.
- Varios planes previos quedan parcialmente implementados sin seccion de estado.

## Verificaciones ejecutadas

- `git status --short`: limpio antes de documentar.
- `python -m pytest -q`: `5 passed`.
- `pip show pydantic pytest cloudscraper requests playwright`: dependencias instaladas en `.venv`.
- `node --version`: `v24.16.0`.
- `npm --version`: `11.13.0`.
- `npm ls --depth=0`: `playwright@1.60.0`, `sqlite3@5.1.7`.
- Live CSFloat shape: HTTP 200, JSON `dict`, claves `data` y `cursor`.
- `fetch_csfloat_prices(1)`: `False`, error por formato no lista.
- Daily dump direct check: TLS normal fallo; con TLS aislado respondio 403 HTML.
- DB inventory: conteos y timestamps por fuente.
- Arbitraje: 29250 oportunidades; top result es falso positivo por fuente stale.
- Contratos: timeout a 120s en ejecucion completa.

## Prioridad recomendada

1. Corregir CSFloat con tests y paginacion.
2. Hacer que scrapers devuelvan resultados estructurados y que `main.py` falle/degrade explicitamente.
3. Bloquear reportes con datos stale/no confiables.
4. Arreglar daily dumps o reemplazar fuente.
5. Optimizar `ContractEngine` con price index en memoria y corregir outputs/recetas.
6. Hacer que continuous loop verifique items concretos.
7. Completar dependencias, config segura y limpieza de datos versionados.
8. Actualizar README/docs al estado real.
