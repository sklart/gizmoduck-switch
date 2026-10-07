# Совместимость Godot 4.7.2 Android ARM64

Проверен официальный `godot-lib.4.7.2.stable.template_release.aar`.

| Артефакт | SHA-256 | ELF LOAD memory |
| --- | --- | --- |
| `libgodot_android.so` | `6b1cbfa830c7f6addec89bb5a4a444be53b3527472668fede03ca8637e040198` | `0x45e08d8` (~70 MiB) |
| `libc++_shared.so` | `c4c2fe5cbcb1fba0003a31fc7ab29a9bb12df6cc187ec45a806462540e83d93b` | `0x156b48` (~1.34 MiB) |

88 MiB резерв loader’а превышает сумму LOAD ranges с выравниванием. Runtime импортирует
OpenSLES, EGL/GLES3, Android asset/window/looper/camera/media, zlib, dl, libc++ и bionic.

Wrapper реализует ARM64 loader, bionic/newlib filesystem/thread/socket bridge, fake JNI,
AssetManager, EGL/GLES3 через switch-mesa, OpenSLES/Nimble audio, HID Joy-Con/Pro,
touch и `user://` в `/switch/gizmoduck/save`.

`scripts/audit_imports.py` проверен против этого AAR: все 572 `UND` symbols
разрешаются wrapper’ом или загруженным первым `libc++_shared.so`; отсутствующих
C/Android/GL imports нет.

Camera/media imports имеют безопасные error-return fallback; отсутствие import или JNI
на первом nxlink запуске должно исправляться по логу, не фиктивным success return. Запуск
на реальном Switch обязателен для EGL, audio, suspend/resume и полного прохождения.
