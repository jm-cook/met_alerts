# Home Assistant Alert Integrations - Design Notes

**Date:** December 13, 2025  
**Author:** Jeremy Cook

## Summary

Investigation into Met.no weather alerts and NVE/Varsom.no landslide warnings for Home Assistant integration.

### Key Findings

1. **Met.no API** provides meteorological warnings (wind, ice, snow, rain, storm surge, etc.)
2. **NVE/Varsom.no API** provides landslide and flood warnings (separate from Met.no)
3. The debris avalanche warning visible on Yr.no comes from NVE, not Met.no
4. Current `met_alerts` integration uses outdated multi-sensor pattern (_2, _3, _4)

---

## Issues Fixed in met_alerts Integration

### Changes Made

1. ✅ **SSL Certificate Handling** - Added certifi for Windows SSL verification
2. ✅ **User-Agent Headers** - Added required identification headers
3. ✅ **Coordinate Rounding** - Round lat/lon to 4 decimals as per API requirements
4. ✅ **API Endpoint** - Changed from `/current` to `/all` to include future alerts

### Modified Files

- `sensor.py` - Updated API calls, SSL context, coordinate rounding
- `config_flow.py` - Updated validation API calls
- `.gitignore` - Added venv and common exclusions

### Current Endpoint

```
https://aa015h6buqvih86i1.api.met.no/weatherapi/metalerts/2.0/all.json?lat={lat}&lon={lon}&lang={lang}
```

Note: Uses Home Assistant-specific endpoint (`aa015h6buqvih86i1.api.met.no`)

---

## New Varsom.no Integration Plan

### Why Separate Integration?

- Different data source (NVE vs Met.no)
- Different alert types (landslide/flood vs weather)
- Different geographic scope (municipality-based vs coordinates)
- Different use cases

### API Details

**Base URL:** `https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api`

**Key Endpoints:**
```
GET /Warning/County/{countyId}/{lang}        # Get all warnings for a county
GET /Warning/All/{lang}                       # Get all warnings in Norway
GET /Warning/{id}                             # Get specific warning by ID
GET /Warning/MasterId/{masterId}              # Get warning by master ID
```

**Languages:** `en`, `no`

**County Codes:**
- Vestland: `46`
- Rogaland: `11`
- [See full list in API docs]

### Response Structure

```json
{
  "Id": "584731",                              // Forecast ID
  "ActivityLevel": "2",                        // 1=Green, 2=Yellow, 3=Orange, 4=Red
  "DangerTypeName": "Jord- og flomskredfare",  // Danger type
  "ValidFrom": "2025-12-14T07:00:00",
  "ValidTo": "2025-12-15T06:59:00",
  "DangerIncreaseDateTime": "2025-12-14T16:00:00",
  "DangerDecreaseDateTime": "2025-12-15T19:00:00",
  "MainText": "Warning text...",
  "WarningText": "Detailed warning...",
  "AdviceText": "What to do...",
  "ConsequenceText": "What might happen...",
  "MunicipalityList": [
    {
      "Id": "4616",
      "Name": "Tysnes"
    }
  ],
  "CountyList": [...],
  "ImageUrlList": []                           // Always empty - maps not exposed via API
}
```

### Varsom.no URLs

Construct URL with forecast ID to get page with interactive map:
```
https://www.varsom.no/en/flood-and-landslide-warning-service/forecastid/{Id}
```

Example: https://www.varsom.no/en/flood-and-landslide-warning-service/forecastid/584731

---

## Recommended Sensor Design Pattern

### ❌ OLD APPROACH (Current met_alerts)

**Problems:**
- Creates 4 sensors even when only 1 alert exists
- Entities named `sensor.met_alerts_2`, `sensor.met_alerts_3`, etc.
- Confusing for users
- Wastes entity registry space

```yaml
sensor.met_alerts:    state: "ice"
sensor.met_alerts_2:  state: "wind"
sensor.met_alerts_3:  state: "No Alert"
sensor.met_alerts_4:  state: "No Alert"
```

### ✅ NEW APPROACH (Recommended)

**Single sensor with all alerts in attributes**

```yaml
sensor.varsom_landslide_vestland:
  state: "2"  # Highest activity level
  attributes:
    active_alerts: 2
    highest_level: "yellow"
    highest_level_numeric: 2
    alerts:
      - id: "584731"
        level: 2
        level_name: "yellow"
        danger_type: "Jord- og flomskredfare"
        municipalities: ["Tysnes", "Bergen", "Stord"]
        valid_from: "2025-12-14T07:00:00"
        valid_to: "2025-12-15T06:59:00"
        danger_increases: "2025-12-14T16:00:00"
        danger_decreases: "2025-12-15T19:00:00"
        main_text: "Varsel om jord- og flomskredfare..."
        warning_text: "Det ventes opp mot 150 mm nedbør..."
        advice_text: "Hold deg oppdatert..."
        consequence_text: "Skredhendelser kan forekomme..."
        url: "https://www.varsom.no/en/flood-and-landslide-warning-service/forecastid/584731"
      - id: "584732"
        level: 2
        ...
```

### Benefits

1. **Single Entity** - Clean entity list
2. **Scalable** - Works with 1 or 100 alerts
3. **Flexible** - Can create template sensors if needed
4. **Modern Pattern** - Matches current HA best practices
5. **State Triggers** - State changes when highest level changes
6. **All Data Available** - Everything accessible via attributes

### Template Sensor Examples

Users can create custom views if needed:

```yaml
# Get specific municipality alerts
template:
  - sensor:
      - name: "Tysnes Landslide Alert"
        state: >
          {% set alerts = state_attr('sensor.varsom_landslide_vestland', 'alerts') | selectattr('municipalities', 'search', 'Tysnes') | list %}
          {{ alerts[0].level_name if alerts else 'none' }}
        attributes:
          alert: >
            {% set alerts = state_attr('sensor.varsom_landslide_vestland', 'alerts') | selectattr('municipalities', 'search', 'Tysnes') | list %}
            {{ alerts[0] if alerts else none }}
```

---

## Implementation Recommendations

### For New Varsom Integration

**Entity Structure:**

1. **One sensor per county** - `sensor.varsom_landslide_{county_name}`
2. **State** = Highest activity level (1-4 or green/yellow/orange/red)
3. **All warnings in attributes** as structured list
4. Optional: Separate sensors for flood vs landslide warnings

**Configuration Options:**

```yaml
# config_flow.py
- County selection (dropdown)
- Warning type (landslide, flood, or both)
- Language (English/Norwegian)
- Update interval (default 30 minutes)
```

**Sensor Attributes:**

Essential:
- `active_alerts` (count)
- `highest_level` (text: green/yellow/orange/red)
- `highest_level_numeric` (1-4)
- `alerts` (array of alert objects)
- `last_update` (timestamp)
- `county_name`
- `county_id`

Per Alert:
- `id` (forecast ID)
- `level` (1-4)
- `level_name` (green/yellow/orange/red)
- `danger_type`
- `municipalities` (array)
- `valid_from` / `valid_to`
- `danger_increases` / `danger_decreases`
- `main_text`
- `warning_text`
- `advice_text`
- `consequence_text`
- `url` (varsom.no link with map)

### For Updated met_alerts Integration

Consider refactoring to same pattern:
- Single sensor per location
- State = highest severity alert event
- All alerts in attributes array
- Breaking change, would need major version bump

---

## Code References

### Test Scripts Created

- `test_api.py` - Met.no API testing (with SSL fixes)
- `test_nve_api.py` - NVE/Varsom API testing
- `check_all_events.py` - Check all event types in Norway
- `check_nve_fields.py` - Examine NVE response structure
- `check_image_urls.py` - Test for image URL availability

### API Examples

**Met.no (current):**
```python
url = f"https://aa015h6buqvih86i1.api.met.no/weatherapi/metalerts/2.0/all.json"
params = {"lat": round(lat, 4), "lon": round(lon, 4), "lang": "no"}
headers = {"User-Agent": "met_alerts/3.0.0 https://github.com/kurtern84/met_alerts"}
ssl_context = ssl.create_default_context(cafile=certifi.where())
```

**NVE/Varsom:**
```python
url = f"https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/api/Warning/County/46/en"
headers = {"Accept": "application/json", "User-Agent": "varsom_alerts/1.0.0 email@example.com"}
# No special SSL handling needed
```

---

## Next Steps

### Monday Tasks

1. **Decide on met_alerts changes**
   - Leave as-is for backward compatibility?
   - Add new single-sensor option alongside existing?
   - Breaking change to new pattern?

2. **Create varsom integration skeleton**
   - Use `hacs/integration` template
   - Copy structure from met_alerts as starting point
   - Implement single-sensor pattern from start

3. **Config flow design**
   - County selection (fetch from `/Region` endpoint)
   - Warning type selection
   - Language preference

4. **Sensor implementation**
   - Coordinator pattern for API calls
   - Single sensor with attributes
   - Proper state handling

5. **Testing**
   - Verify all alert levels work
   - Check state changes trigger automations
   - Test template sensor access to attributes

### Questions to Answer

- Should varsom integration support multiple counties (multiple sensors)?
- Include both landslide AND flood warnings in same sensor?
- Offer filtering by municipality in config?
- Add diagnostic sensors (API call count, last success time, etc.)?

---

## Resources

### API Documentation

- Met.no: https://api.met.no/weatherapi/metalerts/2.0/documentation
- NVE Landslide: https://api.nve.no/doc/jordskredvarsling/
- NVE Flood: https://api.nve.no/doc/flomvarsling/
- NVE Swagger: https://api01.nve.no/hydrology/forecast/landslide/v1.0.10/swagger/ui/index

### Example Alert

- Live Tysnes warning: https://www.varsom.no/en/flood-and-landslide-warning-service/forecastid/584731
- Forecast ID: 584731
- Level: Yellow (2)
- Valid: 2025-12-14 to 2025-12-15

### Useful Links

- Home Assistant Dev Docs: https://developers.home-assistant.io/
- Coordinator Pattern: https://developers.home-assistant.io/docs/integration_fetching_data
- Config Flow: https://developers.home-assistant.io/docs/config_entries_config_flow_handler

---

## Notes

### Coordinate Precision
- Met.no API works better with 4 decimal places
- Your location: 59.9405, 5.4835 (Tysnes/Neshamnen area)

### SSL Issues on Windows
- Python on Windows doesn't find system certificates
- Solution: `pip install certifi` + `ssl.create_default_context(cafile=certifi.where())`

### Event Types
Met.no events: blowingSnow, forestFire, gale, ice, icing, lightning, polarLow, rain, rainFlood, snow, stormSurge, wind

NVE danger types: Jord- og flomskredfare (debris/landslide), Flomfare (flood), various subtypes

### Update Frequency
- Met.no: 30 minutes (to catch new alerts quickly)
- NVE: 30-60 minutes (warnings updated less frequently, usually 1-2 times per day)

---

## Contact

**Integration Repos:**
- met_alerts: https://github.com/kurtern84/met_alerts
- Future varsom integration: TBD

**Email:** jeremy.m.cook@gmail.com
