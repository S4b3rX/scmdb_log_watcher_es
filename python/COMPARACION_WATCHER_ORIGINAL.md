# Comparacion funcional: watcher original vs implementacion actual

## Objetivo

Comparar la version Python original en `source/SCMDB_LOG_WATCHER_v0.1.2/watcher.py` con la implementacion modular actual en `python/` para localizar divergencias que puedan explicar:

- arranque en estado `iniciando`
- no deteccion por parte de SCMDB
- congelamientos o tirones al iniciar
- residuos en `LocalAppData` tras desinstalar

## Resumen ejecutivo

La version original funciona como un watcher unico, con menos capas y menos estado auxiliar. La implementacion actual introduce una GUI, almacenamiento en `LocalAppData`, checklist de arranque, centricidad en `ping`, gestion de bandeja, instalador y proceso secundario. Esa arquitectura añade varios puntos de fallo que no existian en la version original.

Los problemas mas probables identificados son:

1. La GUI mantuvo durante varias iteraciones restos del fallback dinamico de puerto. Aunque el runtime ya se habia limitado, la GUI seguia conservando logica de `selected_port` y mensajes de fallback.
2. La ruta del log podia quedar mal compuesta si se elegia una carpeta que ya era `LIVE` o `HOTFIX`, generando casos como `LIVE/LIVE/Game.log`.
3. La version original releyendo el `Game.log` completo al primer arranque explica bien los tirones o bloqueos observados con logs grandes.
4. La persistencia en `LocalAppData` fue una decision de producto de la version actual; no es un fallo tecnico, pero contradice el comportamiento esperado por el usuario en desinstalacion limpia.

## Comparacion por areas

### 1. Arranque del watcher

Original:

- El script arranca directamente el tailer y el servidor HTTP/SSE.
- La logica de puerto esta concentrada en el propio proceso watcher.
- No hay una GUI intermediaria que interprete el estado.

Actual:

- La GUI lanza el watcher como subproceso.
- La GUI consulta el estado por `GET /ping` en bucle.
- Hay una capa extra (`gui_controller`, `process_service`, `live_runtime_service`) entre la UI y el watcher real.

Impacto:

- Si el watcher falla al arrancar o tarda en publicar `/ping`, la GUI puede quedar en `iniciando` o `esperando conexion` aunque el problema real este mas abajo.
- La GUI se convierte en un segundo sistema de estados, no solo en una ventana.

### 2. Puerto local

Original:

- El puerto esperado es `23456`.
- El objetivo real del sistema es que SCMDB encuentre el watcher en ese puerto fijo.

Actual:

- Se habia introducido busqueda de puerto alternativo en algunos puntos del codigo.
- Aunque el runtime ya se limito a usar solo el puerto solicitado, la GUI todavia conservaba restos del flujo de `selected_port`.

Impacto:

- Cualquier fallback silencioso rompe la deteccion desde SCMDB si la web sigue buscando `23456`.
- Incluso si el watcher "funciona", si lo hace en otro puerto la pagina no lo vera.

Estado actual tras correccion:

- Se elimina el residuo en GUI.
- El runtime queda forzado a usar el puerto configurado o fallar explicitamente.

### 3. Lectura inicial de Game.log

Original:

- Al primer `open`, el tailer lee el fichero desde el principio.
- Esto permite reconstruir misiones activas al iniciar tarde.

Actual inicial:

- Se mantenia ese mismo comportamiento.

Problema detectado:

- En logs de varios MB, leer y parsear todo el fichero al iniciar produce carga de CPU y disco justo al arrancar.
- Esto cuadra con los tirones del sistema reportados tanto en Sandbox como en el PC real.

Estado actual tras correccion:

- El primer arranque del watcher en vivo ahora se posiciona al final del `Game.log` actual.
- Las rotaciones posteriores siguen reiniciando estado como antes.

Tradeoff:

- Se reduce radicalmente el coste de arranque.
- Se pierde la reconstruccion automatica de misiones ya presentes en el log cuando el watcher arranca tarde.
- Dado el problema de rendimiento reportado, este cambio es razonable para el modo live.

### 4. Ruta del log

Original:

- La ruta por defecto es simple y fija.

Actual:

- La GUI y el instalador permiten deducir la ruta desde `game_install_dir` + `channel`.
- Si el usuario selecciona directamente una carpeta `LIVE`, el path podia quedar duplicado.

Impacto:

- Un `Game.log` mal resuelto deja al watcher vivo pero inutil.
- La GUI puede mostrar una ruta aparentemente correcta a nivel visual, pero internamente apuntar mal.

Estado actual tras correccion:

- `build_log_path()` detecta si la carpeta ya es un canal y evita duplicarlo.

### 5. Persistencia y desinstalacion

Original:

- No habia instalador ni almacenamiento separado por AppData en la misma forma.

Actual:

- La configuracion y runtime se guardan en `LocalAppData\SCMDB Log Watcher` cuando la app esta congelada.
- El instalador anterior no borraba esos datos al desinstalar.

Impacto:

- Reinstalar no forzaba una nueva configuracion.
- Quedaban residuos en el equipo del usuario.

Estado actual tras correccion:

- El script de Inno Setup ahora incluye borrado de `LocalAppData\SCMDB Log Watcher` en la desinstalacion.

### 6. Ventanas y UX

Original:

- No existia esta capa de UX.

Actual:

- La GUI agrega decisiones de estado, ventanas, centrado, bandeja y configuracion.

Hallazgos:

- Varias incidencias de UX no estaban en el watcher original porque no existia GUI.
- El centrado y el ajuste de alto son problemas exclusivos de esta capa nueva.

## Funciones / zonas a vigilar especialmente

### Version original

- `LogTailer.run`
- `process_line`
- `build_app`
- `run_live`

### Version actual

- `watcher.py::LogTailer.run`
- `scmdb_watcher/live_runtime_service.py::start_live_runtime`
- `scmdb_watcher/gui_controller.py::resolve_start_command`
- `watcher_gui.py::start_watcher`
- `watcher_gui.py::_poll_status`
- `scmdb_watcher/validators.py::build_log_path`
- `scmdb_watcher/config.py::resolve_data_dir`
- `installer/INNO_SETUP_TEMPLATE.iss`

## Hipotesis mas fuertes sobre el fallo actual de deteccion

1. El watcher no llega a publicar `/ping` aunque el proceso exista.
2. El watcher cae durante el arranque y la GUI solo se queda en estado transitorio.
3. La ruta del log apuntaba a una ubicacion invalida o no existente.
4. Un watcher anterior ocupaba el puerto y el nuevo no quedaba realmente operativo.

## Estado de correcciones ya aplicadas

- Se elimina el residuo del fallback dinamico de puerto en la GUI.
- Se fija el runtime al puerto solicitado sin alternativos silenciosos.
- Se corrige la construccion de la ruta `Game.log` cuando la carpeta ya es `LIVE/HOTFIX`.
- Se recorta el coste de arranque del tail en modo live comenzando desde el final del log actual.
- Se centra la ventana principal y las ventanas secundarias.
- La desinstalacion ahora limpia `LocalAppData\SCMDB Log Watcher`.

## Siguiente comprobacion recomendada

1. Arrancar la nueva build.
2. Verificar con `http://127.0.0.1:23456/ping` si realmente responde.
3. Si no responde, revisar el log de sesion del watcher generado en runtime.
4. Si responde pero SCMDB no lo ve, el fallo ya no estara en el watcher sino en el mecanismo de deteccion desde la web.
