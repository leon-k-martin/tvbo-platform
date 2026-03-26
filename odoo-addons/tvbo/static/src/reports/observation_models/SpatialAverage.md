## SpatialAverage

Computes spatially averaged signals within regions defined by a spatial mask (node-to-region assignment). The mask assigns each node to a region index, and the output is the mean signal per region.

### Properties

- **Period:** 0.9765625 ms

### Parameters

| Name | Default | Unit | Description |
|------|---------|------|-------------|
| spatial_mask |  |  | Vector of length N_nodes mapping each node to a region index (0-indexed). Inferred from network topology if not provided. |

### Processing Pipeline

**1. spatial_average**
  Output: `region_averaged`
  ```
  spatial_mean @ X
  ```
  - spatial_mean =  (Region averaging matrix (n_regions, n_nodes). M[r, j] = 1/n_r if node j belongs to region r, else 0.)
