# Public Alert Context

PhoneBio can use recent public emergency alerts as context for field triage.
Alerts do not replace emergency services, SDS, a site supervisor, or incident
command.

## v1 Sources

| Source | Scope | Use |
|--------|-------|-----|
| NOAA/NWS `api.weather.gov` | U.S. active weather alerts by point | Nearby severe weather, flood, heat, fire-weather, marine, and related alerts. |
| GDACS | Global recent disaster events | Earthquakes, tropical cyclones, floods, volcanoes, and other sudden-onset disaster context. |

The tool is:

```text
get_public_alert_context
```

Inputs:

- `country`
- `latitude`
- `longitude`
- `radiusKm`
- `hazardHint`
- `offline`

Outputs:

- normalized alert summaries
- checked sources
- source errors if a feed is unavailable
- a read-aloud summary
- safety boundary text

## Voice Boundary

Use this phrasing:

```text
I can check public alert context, but if you are in immediate danger, move to
safety and contact emergency services or incident command if possible.
```

If voice-only service is the only working channel, the assistant should capture
relay facts first: location, hazard, injuries, callback/relay route, and whether
anyone nearby can call for help.

## Demo Line

```text
PhoneBio can fuse the call, phone signals, and public alerts like NWS or GDACS,
but it treats those feeds as context only.
```
