# Pollen.lu

This component adds actual pollen count from [pollen.lu](https://www.chl.lu/fr/app-pollen) mobile app to Home Assistant.

A current count is provided every 3 hours for the following grass and tree pollen:

 Latin      | English       | Deutsch           | Français
------------|---------------|-------------------|----------
Rumex       | Sorrel        | Ampfer            | Oseille
Artemisia   | Mugwort       | Beifuß            | Armoise
Betula      | Birch         | Birke             | Bouleau
Fagus       | Beech         | Buche             | Hêtre
Quercus     | Oak           | Eiche             | Chêne
Alnus       | Alder         | Erle              | Aulne
Fraxinus    | Ash           | Esche             | Frêne
Chenopodium | Goosefoot     | Gänsefuß          | Chénopode
Poacea      | Grasses       | Gräser            | Graminées
Corylus     | Hazel Shrub   | Haselnussstrauch  | Noisetier
Plantago    | Plantain      | Wegerich          | Plantain


This component fetches data every hour from the pollen.lu API. The remote data is, as of this writing, updated every 3 hours.

If you like this component, please give it a star on [github](https://github.com/Foxi352/hacs_pollen_lu).

## Installation

1. Ensure that [HACS](https://hacs.xyz) is installed.
2. Install **Pollen.lu** integration via HACS.
3. Add **Pollen.lu** integration to Home Assistant:

   [![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=pollen_lu)

In case you would like to install manually:

1. Copy the folder `custom_components/pollen_lu` to `custom_components` in your Home Assistant `config` folder.
2. Add **Pollen.lu** integration to Home Assistant:

   [![](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=pollen_lu)

## Configuration

After adding the integration, you can configure the polling interval via the integration options.

## Sensors

This integration provides one sensor per pollen type. The sensor is named according to the pollen type (latin name).

### Sensor State

 The sensor state represents an index of the last pollen count.

### Sensor Attributes

Each sensor provides the following attributes (not including default attributes):

Attribute           | Example             | Description
--------------------|---------------------|-----------------------------
level               | high                | Actual level (undetected, low, medium, high)
last_update         | 2024-03-29 12:00:12 | When the pollen was last counted
last_poll           | 2024-07-03 16:10:29 | When the API was last queried
next_poll           | 2024-07-03 17:10:29 | When the API will be queried next
description         | Die Erle gehört ... | A localized description of the plant / tree
moderate_threshold  | 11                  | Threshold from which the concentration is considered moderate
high_threshold      | 51                  | Threshold from which the concentration is considered high
entity_picture      | https://pollen-api.chl.lu/pictures/aulne.svg  | URL 
friendly_name       | Pollen Erle         | Localized friendly name

The friendly name and the description are both localized to the Home Assistant system language. Available are english, german and french.

## Services

### `pollen_lu.force_poll`

This service forces the integration to poll the Pollen.lu API immediately.

**Example usage:**

1. Go to Developer Tools -> Services.
2. Select `pollen_lu.force_poll` from the dropdown.
3. Click "Call Service" to force a poll.

### Example Automation

You can create an automation to call the `force_poll` service, for example, every day at a specific time:

```yaml
automation:
  - alias: Daily Force Poll Pollen Data
    trigger:
      platform: time
      at: '08:00:00'
    action:
      service: pollen_lu.force_poll
```