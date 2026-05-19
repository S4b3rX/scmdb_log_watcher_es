# SCMDB Workspace Layout

Este workspace ahora queda organizado alrededor de tres repos distintos:

- scmdb_es: traduccion del sitio web scmdb.net
- scmdb_log_watcher_es: watcher, instalador y traducciones operativas de la app
- star-citizen-es-data: datos y traduccion en espanol del juego Star Citizen

La raiz de este workspace pasa a ser la base del repo del watcher.
El repo web sigue aislado en scmdb_tr/ y la traduccion del juego queda aislada en star-citizen-es-data/.

## Folder layout

- [python/README.md](python/README.md): active implementation, packaging and releases
- [lang/README.md](lang/README.md): editable UI translation files shared by the workspace
- [csharp/README.md](csharp/README.md): archived .NET prototype kept for reference only

## Related repositories in this workspace

- [scmdb_tr/README.md](scmdb_tr/README.md): repo separado para la traduccion del sitio web scmdb.net
- [star-citizen-es-data/README.md](star-citizen-es-data/README.md): repo separado para la traduccion y datos en espanol de Star Citizen
- [MAPA_PARTES_Y_ALCANCE.md](MAPA_PARTES_Y_ALCANCE.md): delimitacion operativa de cada repo y carpeta

## Working agreement

- Use `python/` for current feature work, fixes, packaging and day-to-day releases.
- Use `lang/` for user-editable translations shipped with the app.
- Treat this workspace root as the source base for the watcher repo, not for the web translation repo.
- Keep `scmdb_tr/` and `star-citizen-es-data/` isolated as independent repositories with their own history.
- Do not add new production features to `csharp/` unless the project is explicitly reactivated.
- Treat `csharp/` as reference material for future ideas such as an Avalonia shell, not as a maintained second watcher.

## Quick start

### Active app

Open [python/README.md](python/README.md) and run the scripts from inside `python/`.

### Archived prototype

Open [csharp/README.md](csharp/README.md) only if you need to inspect the archived .NET experiment.
