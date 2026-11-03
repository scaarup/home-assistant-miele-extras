# Miele Extras for Home Assistant

[![Validate](https://github.com/scaarup/home-assistant-miele-extras/actions/workflows/validate.yml/badge.svg)](https://github.com/scaarup/home-assistant-miele-extras/actions/workflows/validate.yml)
[![Release](https://img.shields.io/github/v/release/scaarup/home-assistant-miele-extras)](https://github.com/scaarup/home-assistant-miele-extras/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/github/license/scaarup/home-assistant-miele-extras)](LICENSE)

A custom integration that adds features from the Miele app that the official
[Miele integration](https://www.home-assistant.io/integrations/miele/) does not expose.
It runs **alongside** the official integration and does not change it.

> **Unofficial.** This integration uses the same private API as the Miele mobile app. It is not
> affiliated with or endorsed by Miele, it is not covered by Miele's public API terms, and it may
> stop working whenever Miele changes the app or its backend. Use it at your own risk.

## Features

One config entry covers your whole Miele account. Appliances are discovered automatically, and
entities are only created for appliances that actually support a feature.

| Platform | Entity | What it does |
|---|---|---|
| `camera` | Camera | Still image from an appliance with a built-in camera (for example an oven with a camera). |
| `binary_sensor` | Firmware update available | Whether the appliance has a remote firmware update waiting, plus an "update in progress" attribute. |
| `sensor` | Care status | Maintenance status per component (for example a dishwasher's appliance and seal/door care), with last and next required care time when Miele reports them. |

More features from the app can be added as new platforms.

### Notes on the camera

The camera serves the most recent image the appliance has stored. If the appliance is switched off,
that image can be old. Images are fetched at most every 20 seconds.

## How it relates to the official integration

Home Assistant lets a device belong to a single integration. Therefore each appliance gets its own
**"Extras" device** that is linked to the official Miele device with `via_device` (shown as
"Connected via ..."). The official integration's devices and entities are left untouched. If you
remove Miele Extras, nothing changes for the official integration.

## Requirements

- Home Assistant. Developed and tested on 2026.10; older versions are not tested.
- The official Miele integration set up (recommended, so the "Connected via" link has a target).
- A refresh token for your Miele app account (entered once in the setup form).
- [HACS](https://hacs.xyz) if you want to install through it (optional).

## Installation

### Option 1: HACS (recommended)

This repository is not in the default HACS store, so you add it as a **custom repository**.
The repository must be public for HACS to be able to read it.

1. Make sure HACS is installed and set up in Home Assistant (see the [HACS documentation](https://hacs.xyz/docs/use/)).
2. Click this button to open the repository in HACS, then click **Download**:

   [![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=scaarup&repository=home-assistant-miele-extras&category=integration)

   Or add it by hand:
   1. In Home Assistant, open **HACS**.
   2. Click the three-dot menu in the top right corner and choose **Custom repositories**.
   3. In **Repository**, enter `https://github.com/scaarup/home-assistant-miele-extras`.
   4. In **Type** (or **Category**), choose **Integration**, then click **Add**.
   5. Close the dialog, find **Miele Extras** in HACS, open it and click **Download**.
3. **Restart Home Assistant** (Settings > System > Restart).
4. Continue with [Setup](#setup).

HACS installs the latest release. When a new release is published, HACS shows an update for
Miele Extras; install it and restart Home Assistant. You can also enable HACS update notifications
under **Settings > Devices & services > HACS**.

### Option 2: Manual

1. Download `miele_extras.zip` from the [latest release](https://github.com/scaarup/home-assistant-miele-extras/releases/latest).
2. Unpack it into `config/custom_components/miele_extras/` in your Home Assistant configuration
   directory, so that `config/custom_components/miele_extras/manifest.json` exists.
3. Restart Home Assistant.

## Setup

1. Go to **Settings > Devices & services > Add integration** and choose **Miele Extras**.
2. Enter your refresh token.

The token is stored in the config entry. Home Assistant exchanges it for short-lived access tokens
automatically. Treat the token like a password: it gives access to your Miele account. If Miele
rejects it, the integration reports an authentication error and the token must be replaced.

## Entities

Entity names are generated from the appliance model, for example:

- `camera.<appliance>_extras_camera`
- `binary_sensor.<appliance>_extras_firmware_update_available`
- `sensor.<appliance>_extras_care_<component>`

You can rename entities and devices in Home Assistant as usual.

## Limitations

- Private, undocumented API: behaviour can change without notice.
- Data is polled every 15 minutes (the camera image is fetched on demand).
- New appliances or newly enabled services are picked up when the integration is reloaded.

## Troubleshooting

- **Authentication error / entities unavailable:** the token was rejected. Replace it by removing
  and re-adding the integration with a new token.
- **No camera entity:** the appliance does not report an active camera service.
- **Old camera image:** the appliance returns its last stored image when it is off.

Enable debug logging with:

```yaml
logger:
  logs:
    custom_components.miele_extras: debug
```

## Development and releases

Every pull request runs three checks: **hassfest** (Home Assistant's integration validator),
**HACS validation** and **lint** (ruff plus a compile check).

Releases are automatic. To publish one:

1. Open a pull request that raises `version` in `custom_components/miele_extras/manifest.json`
   (semantic versioning, for example `2.1.0`; a version with a suffix such as `2.1.0-beta.1` is
   published as a pre-release).
2. When the checks pass, merge it.
3. A workflow then creates the tag `v<version>` and a GitHub release with generated release notes
   and a `miele_extras.zip` asset. HACS and manual installs pick it up from there.

Pull requests labelled `enhancement`, `bug`, `maintenance` and so on are grouped in the release notes.

## License

[MIT](LICENSE)

## Disclaimer

Miele is a trademark of Miele & Cie. KG. This project is independent and not affiliated with Miele.
