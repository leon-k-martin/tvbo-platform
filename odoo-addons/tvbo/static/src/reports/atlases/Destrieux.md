## Destrieux

> **openMINDS type:** `sands:BrainAtlas`  
> **Schema:** openMINDS SANDS — Spatial Anchoring of Neural Data Structures

### Properties

- **Atlas name:** Destrieux
- **Coordinate space:** MNI152Nlin2009c (`sands:CommonCoordinateSpace`)
- **Number of regions:** 167
- **Has coordinates:** No
- **Source label mapping:** Yes (e.g., FreeSurfer lookup labels)
- **Hemispheres:** 9 left, 9 right, 149 other

### BIDS Provenance

- **Template:** MNI152Nlin2009c
- **Atlas:** Destrieux
- **Description:** ranked
- **Suffix:** dseg

### openMINDS SANDS Mapping

| TVBO Field | SANDS Type | SANDS Property |
|------------|------------|----------------|
| `name` | `sands:BrainAtlas` | `name` |
| `coordinateSpace` | `sands:CommonCoordinateSpace` | `abbreviation` |
| `terminology` | `sands:ParcellationTerminology` | `hasEntity` |
| `terminology.entities[*]` | `sands:ParcellationEntity` | `name`, `lookupLabel` |
| `terminology.entities[*].originalLookupLabel` | `sands:ParcellationEntity` | `lookupLabel` (source) |

### Parcellation Entities
*`sands:ParcellationEntity` — 167 regions*

| Index | Name | Source Label |
|------|------|------|
| 1 | left-cerebellum-cortex | 8 |
| 2 | left-thalamus | 10 |
| 3 | left-caudate | 11 |
| 4 | left-putamen | 12 |
| 5 | left-pallidum | 13 |
| 6 | brain-stem | 16 |
| 7 | left-hippocampus | 17 |
| 8 | left-amygdala | 18 |
| 9 | left-accumbens-area | 26 |
| 10 | left-ventraldc | 28 |
| 11 | right-cerebellum-cortex | 47 |
| 12 | right-thalamus | 49 |
| 13 | right-caudate | 50 |
| 14 | right-putamen | 51 |
| 15 | right-pallidum | 52 |
| 16 | right-hippocampus | 53 |
| 17 | right-amygdala | 54 |
| 18 | right-accumbens-area | 58 |
| 19 | right-ventraldc | 60 |
| 20 | ctx_lh_g_and_s_frontomargin | 11101 |
| ... | *147 more regions* | |
