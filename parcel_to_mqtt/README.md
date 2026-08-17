# Parcel to MQTT

Home Assistant app for publishing parcel tracking data through MQTT Discovery.

Adapted from and inspired by the original ioBroker adapter:
[TA2k/ioBroker.parcel](https://github.com/TA2k/ioBroker.parcel)

## Entities

- `Parcel Verbindung`
- `Parcel letzte Aktualisierung`
- `Parcel Sendungen`
- `Parcel Gesamt`
- `Parcel Unterwegs`
- `Parcel In Zustellung`
- `Parcel Zugestellt`
- `Parcel Problem`
- `Parcel Unbekannt`
- `Parcel 01` through configured parcel slots

Each parcel slot exposes tracking number, carrier, status, last event, last event time and raw status as attributes.

## Configuration

```yaml
track17_api_key: ""
tracking_numbers: "00340434123456789012,1Z999AA10123456784"
interval: 60
max_parcels: 6
log_response_details: false
```

`tracking_numbers` accepts a comma-separated list.
Notifications should be created as Home Assistant automations using the generated entities.
