## 🗺️ Spatial Mapping Experiments

### Location: Passadís
| Log File | Environment State | Notes |
|---|---|---|
| `sensor_log_20251217_142216` | Background baseline | No active source |
| `sensor_log_20251217_164439` | Ethanol source active | - |
| `sensor_log_20251217_182052` | Post-ethanol | Ventilator running for 1 hour |

### Location: Rajoles
| Log File | Environment State | Robot Path | Notes |
|---|---|---|---|
| `sensor_log_20251218_165354` | Ethanol source active | Standard | - |
| `sensor_log_20251218_173718` | Ethanol source active | Standard | Ventilator running for 1 hour |
| `sensor_log_20251218_174453` | Ethanol source active | Inverted* | Ventilator running for 1 hour |
| `sensor_log_20251219_093522` | Ethanol source active | Inverted* | - |
| `sensor_log_20251219_095031` | Ethanol source active | Inverted* | Window open in the room |

*\*Inverted Path: The robot moves towards the ventilator.*

---

## 🎯 Directionality Tests

**Protocol:** Measurements were taken sequentially for each channel at distances of 20 cm, 15 cm, 10 cm, and 5 cm from the source.

| Log File | Channels Logged | Timestamp Interval (Approx.) | Notes |
|---|---|---|---|
| `sensor_log_20251219_113305` | Channels 0 to 3 | **Ch 0:** 0s - 900s<br>**Ch 1:** 900s - 1800s<br>**Ch 2:** 1800s - 3000s<br>**Ch 3:** 3000s - 4400s | Primary run |
| `sensor_log_20251219_125455` | Channel 4 | 0s - 1200s | New bringup (previous run cut off) |
| `sensor_log_20251219_132044` | Channel 5 | - | Final channel recording |