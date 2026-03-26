## DesikanKilliany

> **openMINDS type:** `sands:BrainAtlas`  
> **Schema:** openMINDS SANDS — Spatial Anchoring of Neural Data Structures

### Properties

- **Atlas name:** DesikanKilliany
- **Coordinate space:** MNI152NLin2009c (`sands:CommonCoordinateSpace`)
- **Number of regions:** 87
- **Has coordinates:** Yes
- **Source label mapping:** Yes (e.g., FreeSurfer lookup labels)
- **Hemispheres:** 9 left, 9 right, 69 other

### BIDS Provenance

- **Template:** MNI152NLin2009c
- **Atlas:** DesikanKilliany
- **Description:** ranked
- **Suffix:** dseg

### openMINDS SANDS Mapping

| TVBO Field | SANDS Type | SANDS Property |
|------------|------------|----------------|
| `name` | `sands:BrainAtlas` | `name` |
| `coordinateSpace` | `sands:CommonCoordinateSpace` | `abbreviation` |
| `terminology` | `sands:ParcellationTerminology` | `hasEntity` |
| `terminology.entities[*]` | `sands:ParcellationEntity` | `name`, `lookupLabel` |
| `terminology.entities[*].center` | `sands:CoordinatePoint` | `x`, `y`, `z` |
| `terminology.entities[*].originalLookupLabel` | `sands:ParcellationEntity` | `lookupLabel` (source) |

### Parcellation Entities
*`sands:ParcellationEntity` — 87 regions*

| Index | Name | Source Label | x | y | z |
|------|------|------|------|------|------|
| 1 | left-cerebellum-cortex | 8 | -24.4 | -61.9 | -36.6 |
| 2 | left-thalamus | 10 | -11.5 | -18.5 | 7.1 |
| 3 | left-caudate | 11 | -12.7 | 10.4 | 9.8 |
| 4 | left-putamen | 12 | -26.0 | 1.4 | 0.2 |
| 5 | left-pallidum | 13 | -20.5 | -4.5 | -0.8 |
| 6 | brain-stem | 16 | -6.1 | -30.4 | -33.2 |
| 7 | left-hippocampus | 17 | -25.2 | -21.8 | -13.6 |
| 8 | left-amygdala | 18 | -22.9 | -4.5 | -19.3 |
| 9 | left-accumbens-area | 26 | -8.3 | 11.5 | -7.8 |
| 10 | left-ventraldc | 28 | -10.2 | -14.8 | -10.1 |
| 11 | right-cerebellum-cortex | 47 | 24.8 | -61.5 | -36.7 |
| 12 | right-thalamus | 49 | 11.6 | -16.9 | 7.1 |
| 13 | right-caudate | 50 | 13.3 | 11.8 | 9.7 |
| 14 | right-putamen | 51 | 26.6 | 3.2 | -0.4 |
| 15 | right-pallidum | 52 | 21.3 | -2.8 | -0.9 |
| 16 | right-hippocampus | 53 | 26.5 | -20.7 | -13.8 |
| 17 | right-amygdala | 54 | 23.3 | -3.0 | -19.6 |
| 18 | right-accumbens-area | 58 | 8.5 | 12.6 | -7.2 |
| 19 | right-ventraldc | 60 | 10.6 | -14.2 | -10.2 |
| 20 | ctx-lh-bankssts | 1001 | -53.4 | -45.8 | 8.5 |
| ... | *67 more regions* | | | | |
