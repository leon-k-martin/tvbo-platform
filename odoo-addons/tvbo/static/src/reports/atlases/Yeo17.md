## Yeo17

> **openMINDS type:** `sands:BrainAtlas`  
> **Schema:** openMINDS SANDS — Spatial Anchoring of Neural Data Structures

### Properties

- **Atlas name:** Yeo17
- **Number of regions:** 17
- **Has coordinates:** Yes

### BIDS Provenance

- **Space:** MNI152
- **Atlas:** Yeo17
- **Resolution:** 1
- **Suffix:** dseg

### openMINDS SANDS Mapping

| TVBO Field | SANDS Type | SANDS Property |
|------------|------------|----------------|
| `name` | `sands:BrainAtlas` | `name` |
| `terminology` | `sands:ParcellationTerminology` | `hasEntity` |
| `terminology.entities[*]` | `sands:ParcellationEntity` | `name`, `lookupLabel` |
| `terminology.entities[*].center` | `sands:CoordinatePoint` | `x`, `y`, `z` |

### Parcellation Entities
*`sands:ParcellationEntity` — 17 regions*

| Index | Name | x | y | z |
|------|------|------|------|------|
| 1 | 1 | -28.2 | -82.3 | -1.8 |
| 2 | 2 | -11.8 | -70.5 | 10.6 |
| 3 | 3 | -21.5 | -25.4 | 61.0 |
| 4 | 4 | -51.0 | -15.5 | 15.8 |
| 5 | 5 | -35.9 | -64.1 | 15.4 |
| 6 | 6 | -35.0 | -41.1 | 52.9 |
| 7 | 7 | -42.4 | 1.4 | 1.7 |
| 8 | 8 | -31.6 | 43.3 | 27.3 |
| 9 | 9 | -36.0 | -4.2 | -33.7 |
| 10 | 10 | -13.6 | 39.0 | -17.8 |
| 11 | 11 | -6.6 | -61.7 | 44.3 |
| 12 | 12 | -43.0 | 21.8 | 22.5 |
| 13 | 13 | -33.8 | 54.0 | -2.5 |
| 14 | 14 | -56.7 | -31.0 | 4.4 |
| 15 | 15 | -25.9 | -31.5 | -18.9 |
| 16 | 16 | -8.3 | 50.5 | 6.4 |
| 17 | 17 | -56.0 | -12.5 | -18.8 |
