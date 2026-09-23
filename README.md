# ES Heatpump Local

Experimental local Home Assistant integration for Energy Save (ES) heat pumps using a compatible RS232-to-TCP bridge. Unofficial community project, not affiliated with Energy Save.

**Early alpha: incomplete protocol mapping, tested on one installation only. The public build provides monitoring; DHW writes are disabled.** Contributions and compatibility reports are welcome.

## What works

- A local TCP listener receives data pushed by the heat pump bridge, without a cloud account.
- Decodes 45 live values and 136 settings from the observed protocol. Live values show their portal address (`portal_realdata_parameter`), a `label_confidence` and notes; unknown live values keep raw index names.
- Named sensors for selected temperatures, working mode, compressor speed and control level, refrigerant pressures and superheat, and other mapped values.
- Settings are named after the myheatpump.com portal labels: 72 verified against the reference installation, 56 unverified, 8 unknown. See the [field dictionary](docs/FIELDS.md). Settings sensors are disabled by default and can be enabled individually.
- Named main and reheating DHW temperature setpoints.
- Connection and frame diagnostics; UI setup and YAML import.

The source was extracted from a working Home Assistant installation using a **USR-W600** bridge in **Transparent / Socket B TCP-Client** mode. Reference installation: ES Nordic Plus 11 kW split, outdoor unit NP11-V7-S, refrigerant R410A, controller software V2.05. The supported model and firmware matrix has not yet been documented. Compatibility with other ES models or bridges is unverified.

## Upgrading from 0.1.0

- Unique IDs, entity IDs and raw states do not change. Friendly names change unless you renamed an entity yourself.
- Live 29 is now **Outdoor Coil Temp (Tp)**; it was mislabelled as suction temperature. Suction temperature is live 28, **Suction Temp (Ts)**.
- Units added to previously unitless live values: live 28 → °C, live 31 → rpm, live 41 and 42 → K (temperature difference). Home Assistant may raise statistics notices for these; history is not deleted and no unit conversion is applied.
- Live 40 is a dimensionless compressor control level, not a frequency. Live 24/25 pressures carry `pressure_reference: gauge (inferred)`.
- The reheating DHW target keeps its `..._daytime_target_temperature` entity ID but is named **Hot Water Reheating Target Temperature**.

## Installation

**Bridge setup:** [USR-W600 step-by-step guide](docs/USR-W600-setup.md) · [Пошаговая настройка на русском](docs/USR-W600-setup.ru.md). Includes the exact Socket B fields, first-time Wi-Fi setup, verification and cloud rollback.

1. Download this repository and copy `custom_components/es_heatpump_local` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.
3. Open **Settings → Devices & services → Add integration → ES Heatpump Local**.
4. Use bind address `0.0.0.0` and TCP port `18899`, or choose an available local address/port. This is the Home Assistant listener address, not the heat pump IP.
5. Configure the compatible bridge's TCP-client destination to your Home Assistant machine's LAN IP and the selected port. Preserve its existing serial settings and record its original destination first. Redirecting the cloud socket can interrupt vendor cloud access; this integration is not a cloud relay.
6. Check the connected-client and frame counters, then wait for telemetry.

For container installations, make the TCP port reachable from the bridge. Only expose it on a trusted LAN: the listener has no authentication or TLS.

The repository includes metadata for use as a HACS custom integration repository, but HACS installation has not been verified and it is not listed in the default HACS catalog. Manual installation is the documented path.

Optional YAML configuration (imported into a config entry):

```yaml
es_heatpump_local:
  host: 0.0.0.0
  port: 18899
```

## Current limitations

- No `climate` entity, operating-mode control, arbitrary parameter writes or heater control.
- One pump per listener is the intended setup. Multiple pumps on the same listener would mix telemetry; use only one. Multiple entries and their entity IDs are not fully supported.
- The telemetry parser checks framing and field counts but **does not validate CRC**. The retained experimental command code has separate CRC checks.
- Values remain available after a disconnect once received; check connection diagnostics and the last-frame timestamp before trusting them as current.
- Some sensor names and units are inferred from one controller (`label_confidence: inferred`), for example the P0-correlated signal, the compressor control level and the superheat values. Confirm their meaning for your installation.
- Settings labelled `unverified` still need checking. Portal ranges and options are reference metadata, not safe write limits.
- Malformed frames can close a connection. Parser hardening, stale-value handling and broader compatibility testing remain unfinished.
- No minimum supported Home Assistant version has been established. This public package has not been installed on a second Home Assistant instance.

## Experimental DHW command code

The original installation successfully used local writes to the main DHW target, with whole-degree limits of 45–55 °C, an expected-current-value check, fresh CRC-verified telemetry, a single verified connection and confirmation from a subsequent packet. This does not force compressor operation or change the reheating target. A timeout leaves the outcome unknown; there is no automatic retry or temperature restoration.

That implementation was pinned to the original device's eight-byte protocol identity. The private identity has been removed (`IDENTITY = None`), and both exposed DHW actions fail with a clear error in this public alpha. The code is retained for research, **not as ready-to-use control support for other pumps**. Generalized device identification and compatibility verification are still needed.

House-specific probe aliases, captures, logs, credentials, Home Assistant configuration and the separate DHW scheduling automation are not included.

## Related projects

[WombatFirst220/ha-es-heatpump](https://github.com/WombatFirst220/ha-es-heatpump) provides a HACS integration through the myheatpump.com cloud portal, including writable settings. [RoaldO/heatpump](https://github.com/RoaldO/heatpump) offers an AppDaemon cloud integration. This project instead receives the bridge's local TCP stream. No code from either project is included in this initial release.

The reference manual supplied with the original installation is titled **NPT-V7-S6/9/11/13**, document **NCSMS00282A00, Ver. B (2020-12-02)**. This identifies the manual's family, not a verified compatibility list or the exact installed model. The manufacturer's PDF is not redistributed here.

## Development

Run the offline checks with Python 3.11 or newer:

```sh
python -m unittest discover -s tests -v
python -m compileall -q custom_components tests
```

Tests use synthetic data and do not connect to hardware. They do not replace Home Assistant runtime testing.

When reporting compatibility, include the heat pump model, controller/bridge version and which readings match the controller display. Remove device identifiers and personal network details from diagnostics before sharing them.

## По-русски

Неофициальная незавершённая интеграция для локального чтения данных теплового насоса ES (Energy Save). Основана на работающей установке с USR-W600 (ES Nordic Plus 11 кВт, сплит, R410A). Совместимость с другими моделями пока не подтверждена.

В 0.2.0 настройки подписаны названиями полей портала myheatpump.com (72 проверены на эталонной установке, 56 ещё не проверены), исправлена подпись live 29 (это Tp, температура ламелей наружного блока; всасывание Ts — live 28), добавлены единицы и пометки достоверности. Идентификаторы сущностей не меняются.

Скопируйте `custom_components/es_heatpump_local` в каталог конфигурации Home Assistant, перезапустите HA и добавьте **ES Heatpump Local** через настройки. Насос через TCP-мост должен отправлять данные на локальный адрес HA, порт `18899`. Поле Bind address — адрес прослушивания HA, обычно `0.0.0.0`.

В публичной alpha доступны датчики; команды ГВС отключены, поскольку проверенная реализация была привязана к конкретному устройству. Часть параметров ещё не расшифрована. После потери связи старые показания сохраняются — проверяйте время последнего пакета. Планировщик нагрева по цене электричества в этот репозиторий не входит.
