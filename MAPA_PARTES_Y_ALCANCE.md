# Mapa de Partes y Alcance

## Objetivo de este documento

Este archivo delimita que parte del workspace corresponde a cada producto o flujo de trabajo, para evitar mezclar:

- watcher Python
- traduccion operativa de la app watcher
- traduccion del juego Star Citizen
- repo publicable de traduccion del sitio web scmdb.net
- datos auxiliares, sandbox y referencias

## Repos adoptados

La separacion elegida para este workspace queda asi:

- Raiz del workspace: base local del repo scmdb_log_watcher_es
- [scmdb_tr](scmdb_tr): repo scmdb_es, dedicado solo al sitio web scmdb.net
- [star-citizen-es-data](star-citizen-es-data): repo separado para la traduccion y datos del juego Star Citizen

## Distincion critica entre tipos de traduccion

En este proyecto hay dos tipos de traduccion completamente distintos:

- Traduccion del sitio web scmdb.net:
    corresponde a textos del sitio, misiones, descripciones, nombres y contenido que carga SCMDB mediante un JSON web.
    su archivo principal es [scmdb_tr/scmdb-web-translation/lang/lang-es.json](scmdb_tr/scmdb-web-translation/lang/lang-es.json).
- Traduccion operativa del watcher:
    corresponde a textos de interfaz usados por la app watcher durante desarrollo, build y ejecucion.
    sus archivos estan en [lang](lang) dentro del workspace.
- Traduccion del juego Star Citizen:
    corresponde al paquete de idioma y datos publicados aparte para el juego.
    hoy su archivo en [star-citizen-es-data/lang/es-es.json](star-citizen-es-data/lang/es-es.json) debe entenderse como placeholder provisional.
    la copia operativa real que usa la app watcher sigue estando en [lang/es-es.json](lang/es-es.json).

No son la misma traduccion, no usan el mismo formato y no deben mezclarse en tareas, validaciones ni publicaciones.

## Vista rapida del workspace

### Parte activa del watcher

- [python](python): implementacion principal mantenida del watcher, GUI, runtime, import, build y empaquetado.
- [lang](lang): traducciones de interfaz del watcher usadas por la app durante desarrollo o en instalaciones.
- [release](release): artefactos y estructura de salida para builds publicables del watcher.
- [runtime](runtime): datos de ejecucion y configuracion local del watcher.
- [install.bat](install.bat): bootstrap del entorno principal.

### Material historico o de referencia tecnica

- [csharp](csharp): prototipo archivado, no es el objetivo de desarrollo actual.
- [source](source): copia o snapshot de referencia del watcher original o material base.
- [sources](sources): repositorios externos clonados como referencia de formato o investigacion.
- [sandbox](sandbox): pruebas, referencias externas y trabajo exploratorio fuera del set publicable.
- [tmp-scmdb-index.js](tmp-scmdb-index.js): artefacto auxiliar de inspeccion del sitio, no forma parte del repo publicable.

### Datos locales y apoyo

- [logs depuracion usuarios](logs%20depuracion%20usuarios): exportes y logs de usuarios para analisis local.
- [scmdb.html](scmdb.html): recurso suelto de apoyo local.
- [README.md](README.md): describe la orientacion general del workspace.

## Subrepo publicable separado

La parte web que se publica como repo independiente no es la raiz del workspace.

El repo publicable vive en:

- [scmdb_tr](scmdb_tr)

Ese subrepo esta pensado para GitHub y para compartir/publicar solo la traduccion web de SCMDB ES.

## Partes dentro de scmdb_tr

### 1. Traduccion web de SCMDB

- [scmdb_tr/scmdb-web-translation](scmdb_tr/scmdb-web-translation)
- Archivo principal: [scmdb_tr/scmdb-web-translation/lang/lang-es.json](scmdb_tr/scmdb-web-translation/lang/lang-es.json)

Funcion:

- Publicar la traduccion comunitaria del sitio web scmdb.net, cargada mediante el parametro lang.

Este es el archivo que hay que tocar cuando el trabajo sea:

- tono
- redaccion
- consistencia de misiones
- comparacion con el sitio
- revision de bloques como Foxwell, Covalex, Hockrow, Ling Family o Red Wind

### 2. Documentacion y landing publica

- [scmdb_tr/README.md](scmdb_tr/README.md)
- [scmdb_tr/PUBLICAR_GITHUB.md](scmdb_tr/PUBLICAR_GITHUB.md)
- [scmdb_tr/HANDOFF_AGENTE.md](scmdb_tr/HANDOFF_AGENTE.md)
- [scmdb_tr/index.html](scmdb_tr/index.html)

Funcion:

- Describir, publicar y documentar el repo del sitio web.

## Repo separado de Star Citizen

- [star-citizen-es-data](star-citizen-es-data)
- Traduccion del juego: [star-citizen-es-data/lang/es-es.json](star-citizen-es-data/lang/es-es.json)
- Export de blueprints: [star-citizen-es-data/blueprints/scmdb-import-2026-05-17_23-25-06.json](star-citizen-es-data/blueprints/scmdb-import-2026-05-17_23-25-06.json)

Funcion:

- Guardar la traduccion del juego Star Citizen y datos auxiliares asociados, sin mezclarlo con la traduccion web de SCMDB ni con el codigo del watcher.

No debe mezclarse con la traduccion web de SCMDB.

## Delimitacion del trabajo de traduccion actual

El trabajo activo de traduccion del sitio web scmdb.net corresponde solo a:

- [scmdb_tr/scmdb-web-translation/lang/lang-es.json](scmdb_tr/scmdb-web-translation/lang/lang-es.json)

No corresponde, salvo que el objetivo cambie expresamente, editar:

- [lang](lang)
- [python](python)
- [release](release)
- [runtime](runtime)
- [csharp](csharp)
- [source](source)
- [sources](sources)
- [sandbox](sandbox)
- [star-citizen-es-data](star-citizen-es-data)

## Delimitacion de pruebas locales

### Ruta antigua que induce confusion

Antes se estaba usando una URL local antigua como esta:

    http://localhost:8765/scmdb_tr/lang/lang-es.json

Esa ruta ya no corresponde a la estructura actual del repo publicable.

### Ruta local correcta para la traduccion web

La ruta correcta ahora es:

    http://localhost:8765/scmdb_tr/scmdb-web-translation/lang/lang-es.json

### URL publica correcta de SCMDB ES

[https://scmdb.net/?lang=https://raw.githubusercontent.com/S4b3rX/scmdb_es/main/scmdb-web-translation/lang/lang-es.json](https://scmdb.net/?lang=https://raw.githubusercontent.com/S4b3rX/scmdb_es/main/scmdb-web-translation/lang/lang-es.json)

## Documentos clave para retomar trabajo

- [PLAN_DIVISION_REPOS.md](PLAN_DIVISION_REPOS.md): propuesta de separacion en 3 repos, alternativa en 2 repos y plan de migracion.
- [scmdb_tr/HANDOFF_AGENTE.md](scmdb_tr/HANDOFF_AGENTE.md): relevo operativo completo.
- [scmdb_tr/ESTADO_TRADUCCION_SITIO.md](scmdb_tr/ESTADO_TRADUCCION_SITIO.md): estado corto de la traduccion web.
- [scmdb_tr/PUBLICAR_GITHUB.md](scmdb_tr/PUBLICAR_GITHUB.md): plantilla y pasos de publicacion.
- [scmdb_tr/README.md](scmdb_tr/README.md): descripcion publica del subrepo.

## Regla practica

Si la tarea habla de misiones, tono, descripciones, comparacion con scmdb.net o cobertura del sitio, el trabajo pertenece a:

- [scmdb_tr/scmdb-web-translation/lang/lang-es.json](scmdb_tr/scmdb-web-translation/lang/lang-es.json)

Si la tarea habla de GUI, watcher, Game.log, import, runtime, instalador o de la traduccion de la interfaz del juego Star Citizen y de la app, el trabajo pertenece al workspace principal, normalmente en:

- [python](python)
- [lang](lang)
- [release](release)

Si la tarea habla de exportes de misiones/blueprints o de la traduccion del juego Star Citizen en repo separado, el trabajo pertenece a:

- [star-citizen-es-data](star-citizen-es-data)
