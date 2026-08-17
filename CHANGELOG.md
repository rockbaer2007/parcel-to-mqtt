# Changelog

## 0.1.4

- Added optional DHL account login through a `dhllogin://` browser redirect URL.
- Stored the DHL refresh token in the app data folder and reused it on restart.
- Added DHL account parcel-list polling in addition to manual tracking numbers.

## 0.1.3

- Fixed local Home Assistant app builds by using the same Home Assistant base Python image layout as the other UGSo apps.

## 0.1.2

- Added direct Hermes Germany parcel tracking.
- Added shared parcel status groups for registered, pickup point and returning.
- Prepared GLS configuration fields while keeping GLS polling disabled until the required guest bearer session is implemented.
- Added attribution for the ha-parcel-integrations status model inspiration.

## 0.1.1

- Removed 17TRACK API support because the API key can be paid.
- Switched the MVP to direct DHL parcel tracking by configured DHL tracking numbers.

## 0.1.0

- Initial Home Assistant Supervisor app.
- Added MQTT Discovery sensors for parcel tracking.
- Added manual tracking number configuration, counters, JSON lists and six parcel slot entities.
- Added app icon and logo assets.
