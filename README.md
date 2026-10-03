# Hermes ALT Update GUI (Windows)

**EN** — A graphical wrapper for `hermes update` with stages, a progress bar,
connection/download/error counters, a live log, and a green/red result banner.
It works around the release-channel 403 problem: `hermes-assets.nousresearch.com`
(Cloudflare/R2) returns `403 "Attention Required!"` to non-browser clients and
clients from Russia, so plain `hermes update` cannot read the release channel.
This wrapper runs the updater through the git branch `main` (GitHub git protocol
is not affected by the WAF) and shows you, step by step, what is happening.

**RU** — Графическая обёртка над `hermes update`: этапы, полоса прогресса,
счётчики соединений/загрузок/ошибок, живой лог, зелёный/красный баннер итога.
Обходит проблему 403 канала релизов: `hermes-assets.nousresearch.com`
(Cloudflare/R2) отдаёт `403 "Attention Required!"` не-браузерным клиентам и
клиентам из РФ, из-за чего обычное `hermes update` не может прочитать канал.
Обёртка запускает апдейтер по git-ветке `main` (git-протокол GitHub WAF не
затронут) и показывает по этапам, что происходит.

Interface languages: **English / Russian**, switchable with the **EN/RU** button
in the window header (the choice is remembered; `--lang en|ru` or
`HERMES_UPDATE_GUI_LANG` also work).

> **NOT an official Nous Research tool.** It does not modify Hermes code, does
> not require tokens, passwords or keys, and sends nothing anywhere except the
> Hermes update process itself.
> **Не официальный инструмент Nous Research.** Не меняет код Hermes, не требует
> токенов/паролей/ключей и ничего не отправляет наружу, кроме самого процесса
> обновления Hermes.

Related upstream threads: issue [#128295](https://github.com/NousResearch/hermes-agent/issues/128295),
PR [#128323](https://github.com/NousResearch/hermes-agent/pull/128323),
PR [#128305](https://github.com/NousResearch/hermes-agent/pull/128305),
PR [#128380](https://github.com/NousResearch/hermes-agent/pull/128380).

---

## ⚠️ Quick memo / Краткая памятка

| | EN | RU |
|---|---|---|
| **Do NOT launch from inside Hermes** | Do not start this installer from an agent session / the agent's own terminal — the updater force-kills gateway processes and would kill the installer mid-update. Launch it from the desktop / Explorer / a separate terminal window. | **Не запускайте этот установщик из-под Hermes** (из сессии агента или его терминала) — апдейтер принудительно останавливает процессы gateway и заодно снесёт сам установщик посреди обновления. Запускайте с рабочего стола, из проводника или из отдельного окна терминала. |
| Running agent is OK | A *running Hermes/agent* is fine: `hermes update` stops the gateway itself (drain → stop → cold-start after update). Do not pre-kill anything manually. | Запущенный Hermes/агент — не проблема: `hermes update` сам останавливает gateway (drain → stop → холодный старт после обновления). Выгружать его вручную заранее не нужно. |
| One copy at a time | A second copy shows a notice instead of starting a second updater. | Вторая копия покажет окно-предупреждение вместо второго апдейтера. |
| First run | An unsigned .exe may trigger SmartScreen: “More info → Run anyway”. | Неподписанный .exe может вызвать предупреждение SmartScreen: «Подробнее → Выполнить всё равно». |

## How it works / Механизм работы

1. **Find Hermes** — checks `HERMES_HOME`, `%LOCALAPPDATA%\hermes\hermes-agent`,
   `~\.hermes\hermes-agent`, `~\hermes-agent`, and the path behind `hermes.exe`
   in PATH. No disk scan. Not found → red banner with the checked path and a
   `--repo` hint.
   *Поиск Hermes по известным путям (без сканирования диска); не найден — красный баннер и подсказка `--repo`.*
2. **Launch the updater** — runs
   `<hermes venv>\Scripts\hermes.exe update --branch main --yes --keep-stash`
   with `HERMES_UPDATE_STEP_IDLE_SECONDS=1800` (watchdog for a hung step).
   `--branch main` bypasses the blocked release channel; `--keep-stash` preserves
   your local edits.
   *Запуск апдейтера по ветке `main` с watchdog 1800 с; `--keep-stash` сохраняет локальные правки.*
3. **Classify the stream** — every updater output line is matched against stage
   markers → 8 stages: Preparing Hermes → Connecting to repository → Downloading
   changes → Dependencies and binaries → Building web UI → Rebuilding the app →
   Skills and configuration → Finishing. The progress bar fills by stage weights
   (5/10/15/15/10/30/10/5) and only moves forward.
   *Каждая строка вывода сопоставляется с маркерами 8 этапов; полоса прогресса заполняется по весам этапов и движется только вперёд.*
4. **Counters & log** — connections/downloads/errors are counted from the stream;
   the full stream is written to `%LOCALAPPDATA%\hermes\logs\update-gui-<timestamp>.log`.
   *Счётчики пересчитываются из потока; полный лог пишется в файл.*
5. **Result** — green banner “UPDATE COMPLETE / ОБНОВЛЕНИЕ ЗАВЕРШЕНО” with the
   version transition (`old → new [branch @ commit]`) and a request to close the
   installer and restart Hermes; or a red banner with the last error lines.
   *Зелёный баннер с переходами версий и просьбой закрыть установщик, либо красный с последними ошибками.*

## Run / Запуск

### 1. Single .exe (recommended)

Download `HermesAltUpdateGUI.exe` from **Releases** and double-click it.
No Python needed — Tkinter is bundled inside.

### 2. .bat launcher (if Python is already installed)

`hermes-alt-update-gui.bat` — double click. It finds `hermes_update_gui.py`
(next to itself, then the Hermes tools dir), finds `pythonw.exe` (Hermes venv →
PATH → `py -3`), and offers `winget install Python.Python.3.12` if nothing was
found. `--dry-run` prints what it found without launching.

### 3. Directly from Python

```bat
pythonw hermes_update_gui.py
pythonw hermes_update_gui.py --check
pythonw hermes_update_gui.py --lang ru
pythonw hermes_update_gui.py --repo C:\Users\you\AppData\Local\hermes\hermes-agent
pythonw hermes_update_gui.py --version
```

Requires Python 3.10+ with Tkinter (the “tcl/tk and IDLE” option in the standard
Windows installer). The script has **no external dependencies** — stdlib only.

## Arguments / Аргументы

| Argument | Action |
|---|---|
| *(none)* | Full Hermes update |
| `--check` | Only check for updates, change nothing |
| `--lang en\|ru` | Interface language (also `HERMES_UPDATE_GUI_LANG` env; EN/RU button in the window) |
| `--repo <path>` | Explicit Hermes Agent checkout path |
| `--version` | Wrapper version |
| `--mock <file>` | Internal: replay a recorded log instead of a real update (UI tests) |

## Build the .exe yourself

```bat
py -3 -m venv .venv
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller build.spec
```

Output: `dist\HermesAltUpdateGUI.exe` (single-file, windowed, ~10 MB).

## Tests

```bat
python tests\test_classify.py
```

Replays a real successful update log plus two mock streams (success, and a
ffmpeg download failing with HTTP 404) through the same stage rules: stage
order, monotonic progress, counters, final status.

## Known limitations

- Does not bypass a blocked binary mirror (ffmpeg etc.) — if a GitHub release
  is unreachable, the updater reports the error and the red banner shows it.
- Works on the `main` branch only; `stable`/`canary` channels are not used.
- The exe is unsigned → SmartScreen warning on first run.
- One instance per user (mutex `Local\HermesAltUpdateGUI`).

## License

MIT.
