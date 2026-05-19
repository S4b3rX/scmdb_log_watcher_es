# Language Files

SCMDB Watcher loads UI translations from this folder.

Format:

- One JSON file per language.
- File name matches the language code, for example `es-es.json` or `fr-fr.json`.
- The `code` field should match the file name.
- `aliases` may include short forms such as `es` or `fr`.
- `strings` contains the translatable keys.

The applications look for a `lang` folder next to the executable first. During development they also search the repository root.

To add a custom language:

1. Copy the closest existing JSON file.
2. Rename it to your language code.
3. Update `code`, `display_name`, `native_name`, and `strings`.
4. Place the file in the installed `lang` folder.
