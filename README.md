# Miele Extras for Home Assistant

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

- Home Assistant 2025.x or newer
- The official Miele integration set up (recommended, so the "Connected via" link has a target)
- A refresh token for your Miele app account (entered once in the setup form)

## Installation

### HACS (custom repository)

1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/scaarup/home-assistant-miele-extras` with category **Integration**.
3. Install **Miele Extras** and restart Home Assistant.

### Manual

1. Copy the `custom_components/miele_extras` folder into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

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

## Disclaimer

Miele is a trademark of Miele & Cie. KG. This project is independent and not affiliated with Miele.
