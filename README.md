# Comfee Dehumidifier via AppDaemon (Cloud Control)

Home Assistant integration for Comfee/Midea dehumidifiers whose **local token/key
cannot be retrieved** from the Midea cloud API — a known, unresolved issue for
some devices (see [georgezhao2010/midea_ac_lan#48](https://github.com/georgezhao2010/midea_ac_lan/issues/48)
and similar reports across Midea-based Home Assistant integrations).

If you've hit an error like:

```
Can't get available token from Midea server for device <id>
```

...in the standard Midea/Comfee integrations, and none of the usual fixes
(different app/server selection, HACS alternatives) work, this project is a
workaround: it talks to the device **entirely through the Midea cloud API**
using the [`midea-beautiful-air`](https://github.com/nbogojevic/midea-beautiful-air)
Python library, instead of requiring a local token/key.

## How it works

An [AppDaemon](https://appdaemon.readthedocs.io/) app polls the device status
every few minutes via the cloud and publishes it as Home Assistant sensors. A
handful of Home Assistant helpers (`input_boolean`, `input_number`,
`input_select`) let you control the device; changing them triggers a cloud
"set" call.

The `set` subcommand in `midea-beautiful-air-cli` has a bug (as of 0.10.7)
that makes every cloud `set` call fail with an "unused arguments" error. This
project works around it by calling the library's Python API directly
(`midea_set.py`) instead of the broken CLI `set` subcommand.

## What you get

- `sensor.comfee_luefter_luftfeuchte` — current humidity
- `sensor.comfee_luefter_zielfeuchte_ist` — target humidity (as reported by device)
- `sensor.comfee_luefter_stufe_ist` — fan speed (as reported by device)
- `sensor.comfee_luefter_modus_ist` — raw mode value (as reported by device)
- `binary_sensor.comfee_luefter_laeuft` — running state
- `binary_sensor.comfee_luefter_tank_voll` — tank full
- Control via `input_boolean.comfee_lufter_betrieb` (on/off),
  `input_number.comfee_lufter_zielfeuchte` (target humidity),
  `input_number.comfee_lufter_stufe` (fan speed), and
  `input_select.comfee_lufter_modus` (operating mode)

## Requirements

- Home Assistant with the [AppDaemon add-on](https://github.com/hassio-addons/addon-appdaemon)
  installed
- A Midea/Comfee/NetHome Plus cloud account with the device already paired in
  the vendor app
- Your device's numeric **device ID** (see below)

## Installation

1. Install the AppDaemon add-on in Home Assistant if you haven't already.
2. In the AppDaemon add-on configuration, add `midea-beautiful-air` to
   `python_packages`, then restart the add-on.
3. Copy `apps/comfee_dehumidifier.py` and `apps/midea_set.py` into your
   AppDaemon `apps/` directory (typically
   `/addon_configs/a0d7b954_appdaemon/apps/` on Home Assistant OS — the
   hash prefix depends on your installation).
4. Copy `apps/apps.yaml.example` to `apps/apps.yaml` (merge with any
   existing `apps.yaml` content) and fill in your `device_id`.
5. Copy `secrets.yaml.example` to `secrets.yaml` in the AppDaemon config
   root and fill in your real Midea cloud account/password. **Never commit
   this file** — it's already in `.gitignore`.
6. In Home Assistant, create the helpers referenced in `apps.yaml`:
   - `input_boolean.comfee_lufter_betrieb`
   - `input_number.comfee_lufter_zielfeuchte` (e.g. min 30, max 80, step 5, unit %)
   - `input_number.comfee_lufter_stufe` (e.g. min 0, max 100, step 20)
   - `input_select.comfee_lufter_modus` with options matching your device's
     modes (see "Finding your mode mapping" below)
7. Restart the AppDaemon add-on.

### Finding your device ID

If the standard integration's discovery step got far enough to show a
device (even if it then failed on token retrieval), the device ID is
usually visible in that error message or in the integration's discovery
dialog. Otherwise, run:

```bash
pip install midea-beautiful-air
midea-beautiful-air-cli discover --account YOUR_EMAIL --password 'YOUR_PASSWORD' --credentials
```

This lists devices on your account along with their numeric `id`.

### Finding your mode mapping

The `mode` value is an integer (0–15) whose meaning is device/firmware
specific and undocumented. Add a few placeholder options to
`input_select.comfee_lufter_modus`, select one at a time, and check what the
vendor app shows. Then edit the `mapping` dict in `on_mode_change()` inside
`comfee_dehumidifier.py` to match your device's actual modes.

For reference, on the device this was built against, values `1`–`4`
corresponded to Manual, Continuous, Smart, and Dryer respectively — but this
is **not guaranteed** to be the same on your device.

## Known limitations

- Cloud-only control means a small delay (a few seconds) between changing a
  helper and the device responding, and status only refreshes on the
  `poll_interval` (default 5 minutes) unless triggered by a control change.
- Relies on undocumented behavior of the Midea cloud API via a third-party
  library; if Midea changes their API, this may break.
- The `set` CLI bug this project works around may be fixed in a future
  release of `midea-beautiful-air` — check before assuming the workaround is
  still necessary.

## License

MIT — use, modify, and share freely.
