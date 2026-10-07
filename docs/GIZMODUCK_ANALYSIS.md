# Gizmoduck 1.1.2 — анализ исходной сборки

Проверка выполнена на предоставленных Windows и Linux 1.1.2. Ресурсы игры не добавлены в репозиторий.

| Свойство | Результат |
| --- | --- |
| Движок | Godot 4.7.2 Stable |
| PCK | format 4, встроен в оба исполняемых файла |
| Флаг PCK | `0x2` (`PACK_REL_FILEBASE`); каталог не зашифрован |
| Файлы | 3 469 в каждой сборке |
| Скрипты | 353 `.gdc`, исходных `.gd` нет |
| Native extensions | `.gdextension`, `.dll`, `.so` отсутствуют |
| Mono/C# | отсутствуют |
| `project.binary` | SHA-256 `4EAB86E1D252CEB146E3A75487DE3673CE609079AEED0EB4F0996364AE4EFD9E` в обеих сборках |

`scripts/prepare_game.py` находит PCK по trailer `GDPC`, валидирует MD5 каждой
записи и извлекает все 3 469 файлов. Следовательно каталог и файлы этой поставки
не зашифрованы.

## `project.binary`

- название `Gizmoduck`, версия `1.1.2`;
- renderer `gl_compatibility` (также mobile);
- viewport `256×144`, override `1024×768`, stretch `canvas_items`;
- стартовая сцена: UID `uid://gkn2glytq5f1`;
- есть `InputEventJoypadButton`/`InputEventJoypadMotion`;
- autoload включает Storage, AudioManager, CrtFilter, Leaderboard и UpdateChecker;
- подтверждены `global/leaderboard.gdc`, `global/update_checker.gdc` и
  `user://save/pending_run.json`.

Состав: 959 `.import`, 796 `.ctex`, 708 `.remap`, 353 `.gdc`, 321 `.scn`,
157 `.oggvorbisstr`, 112 `.json`, 34 `.res`, 6 `.gdshader`.

Точный путь сцены по UID требует UID cache/runtime и не должен быть подменён.
