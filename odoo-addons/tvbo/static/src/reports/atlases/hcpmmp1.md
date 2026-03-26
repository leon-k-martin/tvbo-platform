## hcpmmp1

> **openMINDS type:** `sands:BrainAtlas`  
> **Schema:** openMINDS SANDS — Spatial Anchoring of Neural Data Structures

### Properties

- **Atlas name:** hcpmmp1
- **Terminology:** Glasser2016-MRTrix (`sands:ParcellationTerminology`)
- **Number of regions:** 379
- **Has coordinates:** Yes
- **Hemispheres:** 189 left, 189 right, 1 other

### BIDS Provenance

- **Template:** MNI152NLin2009b
- **Atlas:** hcpmmp1
- **Description:** ordered
- **Suffix:** dseg

### openMINDS SANDS Mapping

| TVBO Field | SANDS Type | SANDS Property |
|------------|------------|----------------|
| `name` | `sands:BrainAtlas` | `name` |
| `terminology` | `sands:ParcellationTerminology` | `hasEntity` |
| `terminology.entities[*]` | `sands:ParcellationEntity` | `name`, `lookupLabel` |
| `terminology.entities[*].center` | `sands:CoordinatePoint` | `x`, `y`, `z` |

### Parcellation Entities
*`sands:ParcellationEntity` — 379 regions*

| Index | Name | x | y | z |
|------|------|------|------|------|
| 1 | L_V1 | -10.4 | -84.1 | 1.6 |
| 2 | L_MST | -43.8 | -66.8 | 12.0 |
| 3 | L_V6 | -14.9 | -80.6 | 32.2 |
| 4 | L_V2 | -10.6 | -82.3 | 4.1 |
| 5 | L_V3 | -16.0 | -86.2 | 8.0 |
| 6 | L_V4 | -28.4 | -87.0 | -0.0 |
| 7 | L_V8 | -30.3 | -76.9 | -12.9 |
| 8 | L_4 | -28.4 | -20.4 | 54.6 |
| 9 | L_3b | -39.4 | -22.3 | 52.8 |
| 10 | L_FEF | -41.8 | -6.8 | 51.5 |
| 11 | L_PEF | -49.0 | -0.5 | 40.6 |
| 12 | L_55b | -49.0 | -1.5 | 50.2 |
| 13 | L_V3A | -15.0 | -91.6 | 28.2 |
| 14 | L_RSC | -4.9 | -36.6 | 21.1 |
| 15 | L_POS2 | -9.5 | -72.3 | 36.8 |
| 16 | L_V7 | -24.1 | -87.1 | 29.6 |
| 17 | L_IPS1 | -24.3 | -75.3 | 37.5 |
| 18 | L_FFC | -42.0 | -61.4 | -17.3 |
| 19 | L_V3B | -26.3 | -83.0 | 17.7 |
| 20 | L_LO1 | -39.8 | -83.9 | 8.2 |
| ... | *359 more regions* | | | |
