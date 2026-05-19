# Playbook de Actualización del Watcher Upstream

## Objetivo

Reducir el tiempo muerto si aparece una nueva versión del watcher original y hay que absorber cambios rápido sin dejar la app inservible.

Este documento define:

- qué comparar
- en qué orden tocar el proyecto
- qué validar antes de dar por buena la actualización

## Principio operativo

Cuando llegue un update, el riesgo no es "cambiar muchas cosas".
El riesgo real es cambiar en el sitio equivocado o tocar GUI/instalador antes de restaurar el contrato del watcher.

La secuencia correcta es siempre:

1. original nuevo
2. lógica runtime actual
3. integración web
4. import
5. GUI
6. instalador y documentación

## Punto de partida fijo

Baseline conocida:

- original congelado de referencia: `source/SCMDB_LOG_WATCHER_v0.1.2/watcher.py`
- implementación activa: `python/`
- mapa funcional: `python/MAPA_ORIGINAL_A_ACTUAL.md`

## Procedimiento de actualización

### Fase 1. Captura y diff

1. Guardar la nueva versión upstream dentro de `source/` con su número de versión.
2. Compararla contra la baseline anterior.
3. Anotar cambios por categoría:
   - parseo de log
   - estado
   - SSE/API localhost
   - import
   - CLI
   - defaults y constantes

Salida esperada:

- lista breve de cambios clasificados por superficie

### Fase 2. Restaurar el contrato mínimo

Antes de tocar GUI, asegurar estas rutas:

1. `process_line()` absorbe los patrones nuevos.
2. `/ping` sigue vivo en `127.0.0.1:23456`.
3. `/events` sigue siendo compatible con la web.
4. `run_import()` no rompe el payload.

Archivos probables:

- `python/scmdb_watcher/domain.py`
- `python/scmdb_watcher/server.py`
- `python/watcher.py`
- `python/scmdb_watcher/import_service.py`
- `python/scmdb_watcher/live_runtime_service.py`
- `python/scmdb_watcher/runtime_service.py`

### Fase 3. Adaptación de configuración y rutas

Revisar si el update upstream cambia:

- ruta por defecto del log
- canal esperado
- argumentos CLI
- shape del output importado

Archivos probables:

- `python/scmdb_watcher/paths.py`
- `python/scmdb_watcher/config.py`
- `python/scmdb_watcher/validators.py`
- `python/scmdb_watcher/gui_settings.py`
- `python/scmdb_watcher/process_service.py`

### Fase 4. Adaptación de GUI

Solo cuando el runtime vuelva a ser correcto:

- actualizar textos o estados nuevos
- exponer nuevos parámetros si hacen falta
- evitar lógica duplicada que contradiga el watcher

Archivos probables:

- `python/watcher_gui.py`
- `python/scmdb_watcher/gui_controller.py`
- `python/scmdb_watcher/gui_status.py`
- `python/scmdb_watcher/gui_view.py`
- `python/scmdb_watcher/gui_i18n.py`
- `lang/*.json`

### Fase 5. Instalador y distribución

Revisar si la actualización exige:

- archivos adicionales en Program Files
- configuración nueva en primera ejecución
- cambios de release tree

Archivos probables:

- `python/installer/INNO_SETUP_TEMPLATE.iss`
- `python/installer/build-app-exe.bat`
- `python/installer/build-installer-exe.bat`
- `python/installer/README.md`

## Validación mínima obligatoria

Una actualización no se considera absorbida hasta que pase esto:

### Validación 1. API local

1. `GET /ping` devuelve `status=ok`.
2. la versión expuesta coincide con la esperada.
3. `GET /state` responde.
4. `GET /events` abre stream SSE.

### Validación 2. Parseo

1. aceptar contrato genera `mission_start`.
2. completar contrato genera `mission_complete`.
3. abandonar/fallar/desconectar genera `mission_ended`.
4. blueprint sigue correlacionando correctamente.

### Validación 3. Import

1. escanea backups sin romperse.
2. deduplica por GUID.
3. genera JSON compatible.

### Validación 4. GUI

1. puede iniciar y detener el watcher.
2. refleja estados correctos.
3. no introduce fallback de puerto silencioso.
4. sigue usando `log_path` válido.

### Validación 5. Instalador

1. instala exe, README y `lang/`.
2. el build instalada arranca.
3. `Program Files\SCMDB Log Watcher\lang` existe.

## Política de severidad

### Cambio crítico

Se trata como crítico si toca cualquiera de estos puntos:

- patrones del `Game.log`
- endpoint `/ping`
- stream `/events`
- versión mínima requerida por la web
- output del import

Acción:

- congelar cualquier otra mejora y atender solo compatibilidad

### Cambio medio

- flags CLI nuevos
- cambios de defaults
- ajustes de rutas
- cambios de logging

Acción:

- adaptar runtime y luego GUI

### Cambio bajo

- textos
- documentación
- layout visual

Acción:

- no bloquear release técnica por esto

## Estrategia para no quedarnos inservibles

Si llega un update y no se puede absorber completo en el momento:

1. restaurar primero `process_line()` y `/ping`.
2. confirmar que la web vuelve a detectar el watcher.
3. dejar import, GUI avanzada y empaquetado como segunda ola si hace falta.

La prioridad operativa es:

1. detección por SCMDB
2. tracking live de misiones
3. import histórico
4. UX fina

## Recomendación práctica de proceso

Cada vez que llegue un update upstream:

1. crear carpeta nueva en `source/` con la versión recibida.
2. actualizar el documento `python/MAPA_ORIGINAL_A_ACTUAL.md` si cambia la responsabilidad de alguna pieza.
3. abrir una nota corta de cambios con este formato:
   - versión upstream
   - superficies tocadas
   - archivos actuales impactados
   - validaciones hechas
   - riesgos pendientes

## Plantilla de nota rápida para updates

```md
# Update upstream vX.Y.Z

## Cambios detectados

-

## Archivos actuales tocados

-

## Validaciones ejecutadas

-

## Riesgos pendientes

-
```
