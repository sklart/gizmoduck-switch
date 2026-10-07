# Gizmoduck для Nintendo Switch

Неофициальный homebrew-порт Gizmoduck для Nintendo Switch. Репозиторий содержит
только исходный код Switch-обёртки, сценарии сборки и инструменты подготовки.
Игра, её PCK/ассеты, `.exe`, `.so`, NRO, иконка, шрифт, runtime и готовые
архивы намеренно не публикуются.

Для работы нужна легально полученная Windows-версия Gizmoduck. Единый сценарий
извлекает из пользовательского `Gizmoduck.exe` игровые данные и иконку, а затем
готовит полностью локальную папку для SD-карты.

В devkitPro MSYS2 установите `switch-mesa`, `switch-libdrm_nouveau`, `switch-zlib`:

```sh
python scripts/prepare_port.py "C:/Games/Gizmoduck/Gizmoduck.exe" --replace
```

Команду запускайте из devkitPro MSYS2 после установки devkitA64, `libnx`,
`switch-mesa`, `switch-libdrm_nouveau`, `switch-zlib`, Python, PowerShell и
`make`. Она извлекает PCK и распакованные ассеты из указанного `.exe`,
скачивает официальный Godot Android runtime и Noto Sans CJK, извлекает
JPEG-иконку, собирает NRO, готовит `release/switch/gizmoduck/` и проверяет
результат.

Параметры: `--work-dir ПАПКА`, `--output ПАПКА`, `--replace`, `--aar ФАЙЛ`,
`--runtime-sha256 ХЕШ`, `--cjk-font ФАЙЛ`, `--font-url URL` и `--skip-build`.
`--replace` удаляет только указанные сгенерированные рабочую и выходную папки.

На SD-карту скопируйте содержимое `release/switch/gizmoduck/` в
`sdmc:/switch/gizmoduck/`. Нужны `gizmoduck.nro`, обе `.so`, `game.pck`,
`assets/project.binary`, `android_root/` и `save/`. Даже при наличии `game.pck`
папку `assets/` не удаляйте: стартовая проверка обёртки использует
`assets/project.binary`, а PCK подключается Godot как основной пакет. При
обновлении сохраняйте `save/`.

Запускать через title override: удерживайте `R`, откройте обычную установленную
игру и в hbmenu выберите Gizmoduck. Режим Album/applet не даёт нужного объёма
памяти.

Локальная devkitA64-сборка NRO прошла. Реальная графика, звук, ввод, lifecycle и
прохождение требуют Switch; см. `docs/`.

`make` по умолчанию собирает диагностическую версию и создаёт
`/switch/gizmoduck/gizmoduck_debug.log`. После аварийного запуска сохраните этот
файл вместе с `boot_stats.txt`. Иконка NRO извлекается из принадлежащего пользователю
оригинального `Gizmoduck.exe` в `assets/icon.jpg` и поэтому не хранится в репозитории.

Общий loader основан на MIT-совместимой работе delsonazevedo и fgsfds/NaGaa95/elliencode;
игровые патчи и ресурсы другого проекта не переносились. Лицензия wrapper — MIT.

## Управление

Порт передаёт A/B/X/Y, L/R, ZL/ZR, D-pad, оба стика, `+` (Start) и `-` (Back)
как стандартный контроллер Godot. Назначение действий определяется настройками
самой Gizmoduck. Один отсоединённый Joy-Con автоматически поворачивается; для
левого его ориентацию задаёт `joycon_turn`.

Сенсорное управление Android намеренно не передаётся: оно не соответствует
раскладке Switch и не нужно при физических контроллерах. Игровой кадр сохраняет
исходные пропорции, поэтому чёрные боковые поля ожидаемы. CRT-фильтры зависят
от версии игры и драйвера Mesa; при белом/чёрном перекрытии отключите фильтр в
настройках игры.

## `config.txt`

После первого запуска рядом с NRO создаётся `config.txt`. Формат строки:
`ключ значение`; пустые строки и строки с `#` в начале игнорируются.

| Ключ | По умолчанию | Назначение |
| --- | --- | --- |
| `screen_width`, `screen_height` | `-1` | Автоматический размер экрана; менять только для диагностики. |
| `boost` | `0` | `0` — частота CPU повышается на загрузках и долгих кадрах; `1` — повышенный режим постоянно. |
| `split_joycons` | `0` | `1` делает каждую половину Joy-Con отдельным игроком. |
| `joycon_turn` | `3` | Поворот левого одиночного Joy-Con на 0–3 четверти по часовой стрелке. |
| `controller_menu` | `0` | От `1` до `4` показывает системное распределение контроллеров при старте. |

`data_root` и `save_root` предназначены для диагностики нестандартной установки;
не меняйте их без необходимости.

## Ручное обновление

Для новой версии снова выполните `prepare_port.py` с новым `Gizmoduck.exe`.
Либо по отдельности используйте `prepare_game.py`, `make_pck.py`,
`prepare_runtime.py`, `extract_original_icon.ps1`, затем `make`,
`package_sd.py` и `verify_sd_layout.py`. Не переносите в Git результат этих
команд: `.work/`, `assets/`, `release/`, PCK, runtime и игровые файлы уже
исключены `.gitignore`.

## Проверки и диагностика

```sh
make
make clean && make DEBUG=1
python -m unittest discover -s tests -v
python scripts/verify_sd_layout.py release/switch/gizmoduck
```

При аварийном завершении приложите `gizmoduck_debug.log` и `boot_stats.txt`.
`VERBOSE_IO=1` включает очень подробный и заметно замедляющий файловый журнал.
Noto Sans CJK загружается локально из официального проекта Noto и распространяется
по SIL Open Font License 1.1.
