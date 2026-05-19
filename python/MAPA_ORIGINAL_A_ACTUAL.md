# Mapa del Watcher Original al Proyecto Actual

## Objetivo

Este documento sirve como marco de referencia para responder una pregunta crítica cuando aparezca una nueva versión del watcher original en `source/`:

- qué parte cambió en el original
- dónde vive hoy esa misma responsabilidad en `python/`
- qué zona del proyecto actual hay que revisar primero

La referencia base actual es:

- original: `source/SCMDB_LOG_WATCHER_v0.1.2/watcher.py`
- implementación activa: `python/`

## Regla de lectura

El original era un solo archivo monolítico. La implementación actual está separada por capas. Cuando llegue una actualización upstream, no hay que buscar por nombre de archivo, sino por responsabilidad.

## Mapa por responsabilidades

### 1. Versión y constantes públicas

Original:

- `__version__`
- `DEFAULT_PORT`
- `PROD_ORIGINS`
- `DEV_ORIGINS_DEFAULT`

Actual:

- `python/watcher.py`
- `python/scmdb_watcher/live_runtime_service.py`
- `python/scmdb_watcher/server.py`

Revisar si cambia:

- versión mínima esperada por la web
- puerto fijo `23456`
- whitelist de orígenes CORS

### 2. Patrones de parseo del Game.log

Original:

- `PATTERN_TIMESTAMP`
- `PATTERN_MARKER`
- `PATTERN_ACCEPTED`
- `PATTERN_END_MISSION`
- `PATTERN_BLUEPRINT`
- `parse_log_timestamp()`
- `process_line()`

Actual:

- `python/scmdb_watcher/domain.py`

Revisar si cambia:

- formato de timestamps
- texto exacto de líneas `CreateMarker`
- texto de `Contract Accepted`
- formato de `EndMission`
- formato de `Received Blueprint`

Impacto:

- si aquí falla, la app puede seguir viva pero dejar de detectar misiones o blueprints

### 3. Estado de misión y correlación

Original:

- `MissionEntry`
- `ActiveMission`
- `MissionLifecycleEvent`
- `WatcherState`

Actual:

- `python/scmdb_watcher/domain.py`

Revisar si cambia:

- estructura de estado activo
- correlación de blueprint con aceptación o completion
- ventana temporal de correlación

Impacto:

- puede romper datos sin romper `/ping`

### 4. Bus de eventos y SSE

Original:

- `EventBus`
- `build_app()`
- `/ping`
- `/state`
- `/events`

Actual:

- `python/scmdb_watcher/server.py`

Contrato crítico que no debe romperse:

- `GET /ping` devuelve `{"status":"ok","version":"x.y.z"}`
- `GET /state` devuelve snapshot JSON
- `GET /events` abre stream SSE
- el primer evento útil debe permitir a la web pasar a estado conectado

Si el original cambia aquí:

- comparar inmediatamente payloads, nombres de evento y shape JSON

### 5. Tail del archivo y rotación

Original:

- `LogTailer.run`

Actual:

- `python/watcher.py::LogTailer`

Revisar si cambia:

- lectura desde inicio o desde final
- detección de rotación
- política de `session_reset`
- comportamiento cuando el `Game.log` no existe todavía

Impacto:

- tirones al arrancar
- duplicados o pérdida de estado

### 6. Runtime live

Original:

- `run_live()`
- `build_allowed_origins()` implícito dentro del propio archivo
- bind del servidor local

Actual:

- `python/watcher.py::run_live`
- `python/scmdb_watcher/live_runtime_service.py`
- `python/scmdb_watcher/runtime_service.py`

Revisar si cambia:

- orden de arranque
- bind del servidor
- fallback de puerto
- secuencia de shutdown

Impacto:

- la web deja de detectar el watcher aunque el proceso exista

### 7. Import histórico

Original:

- `scan_file_for_export()`
- `run_import()`
- deduplicación y escritura de payload

Actual:

- `python/scmdb_watcher/import_service.py`
- `python/watcher.py::run_import`
- `python/scmdb_watcher/gui_controller.py::run_import_process`

Revisar si cambia:

- formato del payload exportado
- reglas de deduplicación
- criterios de qué misiones entran o no entran

Impacto:

- import correcto visualmente pero datos inconsistentes en SCMDB

### 8. CLI y parámetros

Original:

- `parse_live_args()`
- `parse_import_args()`
- `main()`

Actual:

- `python/watcher.py`
- `python/launcher.py`
- `python/scmdb_watcher/process_service.py`

Revisar si cambia:

- flags nuevas
- cambios en defaults
- nuevos subcomandos

Impacto:

- la GUI puede lanzar el watcher con un contrato viejo

### 9. Configuración y rutas

Original:

- path por defecto a `Game.log`
- runtime local sencillo en la carpeta del proyecto

Actual:

- `python/scmdb_watcher/config.py`
- `python/scmdb_watcher/paths.py`
- `python/scmdb_watcher/validators.py`
- `python/scmdb_watcher/gui_settings.py`

Revisar si cambia:

- resolución por canal `LIVE/HOTFIX`
- `watcher-config.json`
- composición de `log_path`

Impacto:

- proceso vivo pero sin observar el log correcto

### 10. GUI y capa de control

Original:

- no existía

Actual:

- `python/watcher_gui.py`
- `python/scmdb_watcher/gui_controller.py`
- `python/scmdb_watcher/gui_status.py`
- `python/scmdb_watcher/gui_view.py`
- `python/scmdb_watcher/gui_i18n.py`

Regla:

- si el upstream cambia la lógica del watcher, primero se adapta el runtime y solo después la GUI
- la GUI nunca debe inventar contratos distintos del watcher real

### 11. Instalador y distribución

Original:

- no existía esta capa empaquetada

Actual:

- `python/installer/INNO_SETUP_TEMPLATE.iss`
- `python/installer/build-app-exe.bat`
- `python/installer/build-installer-exe.bat`
- `lang/`

Revisar si cambia:

- archivos que deban acompañar al ejecutable
- nueva configuración requerida
- nuevos recursos de runtime

## Superficies críticas que deben pasar siempre

Si llega un update del original, estas cinco cosas se consideran bloqueantes:

1. `http://127.0.0.1:23456/ping` responde con `status=ok` y versión correcta.
2. `GET /events` sigue emitiendo snapshot y eventos entendibles por la web.
3. `process_line()` sigue detectando marker, accept, end mission y blueprint.
4. `run_import()` sigue generando JSON válido y deduplicado.
5. `watcher-config.json` y `log_path` siguen resolviendo correctamente el `Game.log` real.

## Cómo usar este mapa cuando llegue un update

1. Comparar el `watcher.py` nuevo del original contra `source/SCMDB_LOG_WATCHER_v0.1.2/watcher.py`.
2. Clasificar cada cambio según la responsabilidad de este documento.
3. Saltar directamente al archivo actual equivalente.
4. Actualizar primero la lógica base.
5. Solo después revisar GUI, instalador y documentación.

## Documento complementario

Para el procedimiento operativo completo, ver `python/PLAYBOOK_ACTUALIZACION_UPSTREAM.md`.
