# Plan de Division de Repos

## Objetivo

Este documento fija tres cosas:

- propuesta exacta de 3 repos separados
- alternativa reducida de 2 repos
- plan de migracion desde el estado actual

## Decision adoptada

La division finalmente elegida para este workspace es esta:

1. scmdb_es
  repo exclusivo de la traduccion del sitio web scmdb.net
2. scmdb_log_watcher_es
  repo del watcher, su instalador y las traducciones operativas de la app
3. star-citizen-es-data
  repo de la traduccion y datos en espanol del juego Star Citizen

Esta decision sustituye la variante anterior en la que el instalador podia salir a un repo aparte.
Desde ahora, el instalador queda unido al watcher y solo la traduccion web y la traduccion del juego se mantienen fuera de ese repo.

## Estado de ejecucion actual

- scmdb_es ya existe y sigue siendo el repo web publicado
- scmdb_log_watcher_es ya fue creado en GitHub para convertir la raiz del workspace en su base local
- star-citizen-es-data ya fue creado en GitHub y tambien en carpeta local dentro del workspace

La motivacion principal es evitar que se sigan mezclando trabajos que no son intercambiables y no usan el mismo flujo:

- traduccion del sitio web scmdb.net
- traduccion de la interfaz del juego Star Citizen y del watcher
- instalador y distribucion

## Recomendacion principal: 3 repos

Esta es la opcion mas limpia a medio plazo.

### Repo 1: traduccion del sitio web scmdb.net

Nombre recomendado:

- scmdb_es

Motivo:

- ya existe
- ya esta enlazado a GitHub
- ya contiene la URL publica esperada para scmdb.net

Responsabilidad:

- alojar solo la traduccion del sitio web scmdb.net
- alojar documentacion publica del proyecto web
- servir el JSON raw que consume SCMDB

Archivo canonico:

- scmdb-web-translation/lang/lang-es.json

Debe incluir:

- traduccion web
- README publico del proyecto web
- documentacion de handoff del trabajo de tono
- landing publica si quieres mantener GitHub Pages

No deberia incluir a largo plazo:

- traduccion de la interfaz del juego Star Citizen
- exportes de blueprints si no son necesarios para el sitio
- instaladores del watcher

URL canonica esperada:

- [https://scmdb.net/?lang=https://raw.githubusercontent.com/S4b3rX/scmdb_es/main/scmdb-web-translation/lang/lang-es.json](https://scmdb.net/?lang=https://raw.githubusercontent.com/S4b3rX/scmdb_es/main/scmdb-web-translation/lang/lang-es.json)

### Repo 2: traduccion de la interfaz del juego Star Citizen y del watcher

Nombre recomendado:

- scmdb_starcitizen_es

Responsabilidad:

- alojar los archivos de idioma del watcher y del entorno asociado
- definir el idioma espanol de interfaz del producto local
- centralizar el origen canonico de los JSON como es-es.json

Archivo canonico recomendado:

- lang/es-es.json

Debe incluir:

- el paquete de idioma espanol del watcher
- documentacion especifica de instalacion o edicion de idiomas
- si hace falta, otros idiomas empaquetados o la estructura base de lang/

No deberia incluir:

- traduccion del sitio web scmdb.net
- instaladores
- datos de marketing o landing del proyecto web

Nota importante:

- a largo plazo, este repo deberia convertirse en el origen canonico de la traduccion de interfaz que hoy existe en el workspace principal en lang/ y tambien en la copia de scmdb_tr/star-citizen-es-data/lang/es-es.json

### Repo 3: instalador y distribucion

Nombre recomendado:

- scmdb_watcher_installer

Responsabilidad:

- publicar artefactos de instalacion y distribucion
- documentar versiones de instalador, empaquetado y entrega
- separar claramente binarios de las traducciones

Contenido esperado:

- instaladores publicados
- notas de version del instalador
- documentacion de instalacion o despliegue
- opcionalmente checksums, changelog y release notes

No deberia incluir:

- traduccion del sitio web
- traduccion de la interfaz del juego como contenido canonico

## Opcion alternativa: 2 repos

Si quieres menos mantenimiento, esta es la version equilibrada.

### Repo A: sitio web scmdb.net

Nombre recomendado:

- scmdb_es

Responsabilidad:

- solo traduccion del sitio web
- handoff, estado de tono, documentacion publica y landing

### Repo B: watcher, interfaz del juego e instalador

Nombre recomendado:

- scmdb_watcher_es

Responsabilidad:

- traduccion de interfaz del watcher y del juego
- instaladores
- documentacion tecnica del watcher

Ventajas:

- menos repos que mantener
- suficiente separacion entre sitio y app local

Desventajas:

- la traduccion del juego y el instalador siguen compartiendo historia
- los lanzamientos de idioma y los de instalador no quedan completamente desacoplados

## Recomendacion practica final

Mi recomendacion real, por orden, es esta:

1. minimo separar sitio web y juego en repos distintos
2. mantener el watcher y el instalador en el mismo repo para no romper el contexto tecnico
3. mantener scmdb_es como repo del sitio web para no romper la URL ya publicada

## Estado actual desde el que migrar

Hoy el estado relevante es este:

- repo actual publicado: scmdb_es
- dentro del repo actual hay tres bloques:
  - installer/
  - scmdb-web-translation/
  - star-citizen-es-data/

Eso significa que el repo actual ya esta organizado logicamente, pero aun no esta separado fisicamente por producto.

## Plan de migracion propuesto

### Fase 0: congelar el criterio

Antes de mover nada:

- dejar asentado que no son intercambiables
- dejar asentado cual es el archivo canonico de cada flujo
- no volver a mezclar sitio web con juego en tareas nuevas

Esto ya esta bastante cubierto por:

- MAPA_PARTES_Y_ALCANCE.md
- scmdb_tr/HANDOFF_AGENTE.md
- scmdb_tr/README.md

### Fase 1: definir que repo se queda con cada canonico

Decision recomendada:

- scmdb_es se queda con el canonico del sitio web
- scmdb_starcitizen_es se queda con el canonico del juego y watcher
- scmdb_watcher_installer se queda con el canonico del instalador

### Fase 2: separar sin romper el sitio

Primero no romper la URL del sitio.

Orden recomendado:

1. mantener en scmdb_es el archivo web actual
2. crear el repo del juego y copiar ahi la traduccion de interfaz
3. crear el repo del instalador y copiar ahi el instalador
4. una vez validado todo, limpiar scmdb_es para que quede solo lo del sitio

### Fase 3: mover contenidos exactos

#### Lo que deberia quedarse en scmdb_es

- scmdb-web-translation/
- README y documentacion especifica del sitio
- handoff y estado de traduccion web
- landing publica si sigue siendo util

#### Lo que deberia salir de scmdb_es hacia el repo del juego

- star-citizen-es-data/lang/es-es.json

Adicionalmente, el repo del juego deberia absorber o reflejar la fuente del workspace principal:

- lang/es-es.json

#### Lo que deberia salir de scmdb_es hacia el repo del instalador

- installer/SCMDB-Log-Watcher-Setup.exe

#### Lo que deberia revisarse antes de mover exportes de blueprints

- star-citizen-es-data/blueprints/scmdb-import-2026-05-17_23-25-06.json

Este archivo puede quedarse en el repo del juego si lo vas a usar como dato auxiliar de ese ecosistema. Si no tiene valor publico continuo, tambien puede quedarse fuera de GitHub o ir a un repo de datos separado.

## Canonicos recomendados despues de la migracion

### Canonico del sitio web

- repo: scmdb_es
- archivo: scmdb-web-translation/lang/lang-es.json

### Canonico de interfaz del juego

- repo: scmdb_starcitizen_es
- archivo: lang/es-es.json

### Canonico del instalador

- repo: scmdb_watcher_installer
- artefacto: SCMDB-Log-Watcher-Setup.exe

## Reglas para no volver a mezclar trabajo

Si una tarea habla de:

- misiones
- tono
- descripciones
- comparacion con scmdb.net
- carga del parametro lang en la web

Entonces pertenece al repo del sitio web.

Si una tarea habla de:

- interfaz del watcher
- archivos de idioma es-es.json
- UI local
- traduccion del juego Star Citizen

Entonces pertenece al repo del juego.

Si una tarea habla de:

- instalador
- releases
- binarios
- distribucion

Entonces pertenece al repo del instalador.

## Secuencia recomendada de ejecucion real

Si quieres hacerlo con el menor riesgo posible, el orden seria:

1. mantener scmdb_es como repo del sitio web
2. crear scmdb_starcitizen_es y mover ahi el canonico de interfaz
3. crear scmdb_watcher_installer y mover ahi el instalador
4. actualizar documentacion cruzada entre repos
5. retomar la traduccion del sitio solo sobre el repo web

## Resultado esperado

Al final deberias tener:

- un repo para el sitio web, centrado en tono y contenido de SCMDB
- un repo para la interfaz del juego y del watcher, centrado en idioma local
- un repo para distribucion, centrado en instaladores y releases

Ese estado reduce la confusion estructural y hace mucho mas dificil volver a tratar como equivalentes dos traducciones que en realidad pertenecen a productos distintos.
