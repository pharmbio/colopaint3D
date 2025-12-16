# 3D Spheroid Analysis - Harmony Batch Correction

## Goal
Use Harmony batch correction on 3D spheroid single-cell data to remove technical z-depth artifacts while preserving biological radial distance variation.

## Key Context

### Technical vs Biological Variation
- **Technical issue:** Imaging depth (z-plane) creates artifacts that overshadow biological variation
- **Biological signal:** Radial distance from spheroid center (outer→inner layers)
- **Key insight:** In center z-planes, you can see radial biology within a single plane

### Data Structure
- 12 z-planes per spheroid (partial spheroid coverage in Z)
- 12 imaging sites (XY positions)
- `Metadata_Site` = imaging field position (NOT z-plane)
- Z-plane information encoded in filenames (e.g., `Well-D12-z0-CONC.ome.tiff`)

## Implementation in `1_SC_Harmony.ipynb`

### Workflow Overview (AnnData-First Approach)
1. **Load data** → pandas DataFrame
2. **Convert to AnnData** → structured format with .obs, .var, .obsm, .uns
3. **Add spatial metadata** → calculate and store in adata.obs
4. **Visualize** → 3D plots using adata
5. **Quality checks** → validate data structure

### AnnData Structure
- **`.X`** - Feature matrix (cells × morphological features)
- **`.obs`** - Cell metadata (Metadata_*, identifiers, spatial annotations)
- **`.var`** - Feature metadata (measurement_type, compartment, channel, metric)
- **`.obsm`** - Multi-dimensional annotations (spatial_2d, spatial_3d coordinates)
- **`.uns`** - Global parameters (pixel_size_um, z_step_um, spheroid_centers)

### Radial Distance Calculation (Completed)
1. **Extract z-plane from filename** → `Metadata_Z` (added to adata.obs)
2. **Create spheroid ID** → `Metadata_Spheroid_ID` (added to adata.obs)
3. **Calculate 3D radial distance** → `Metadata_Radial_Distance_3D` (added to adata.obs)
   - **Method (Hybrid 3D):** Find z-plane with largest radial extent (equatorial plane)
   - For each spheroid, identify the z-plane with maximum radial extent
   - Use that plane's centroid as the reference center (XY and Z)
   - Calculate 3D distance: `sqrt((X - center_X)² + (Y - center_Y)² + (Z - center_Z)²)` in microns

## Radial Distance Methods Comparison

| Aspect | 3_PCAUMAP_loc Method | Our 2D Method | **Hybrid 3D Method (CHOSEN)** |
|--------|---------------------|---------------|-------------------------------|
| **Center** | Fixed (512, 512, 0) | Dynamic (equatorial centroid) | **Dynamic (equatorial centroid)** |
| **Distance** | 3D spherical | 2D radial | **3D radial** |
| **Units** | Microns | Pixels | **Microns (0.227 µm/pixel)** |
| **X,Y center** | Fixed at image center | Calculated from equatorial plane | **Calculated from equatorial plane** |
| **Z center** | NOT centered (starts at 0) | Not used in distance | **Equatorial plane Z position** |
| **Assumptions** | Spheroid centered in image | Finds actual center from data | **Finds actual center from data** |
| **Z handling** | Uses Metadata_Site × 5µm | Ignores Z | **Uses Metadata_Z × 5µm** |
| **Speed** | Fast (per-row calc) | Slower (groupby) | **Fast (vectorized after center calc)** |
| **Biological meaning** | Distance from XY-center at z=0 | Distance from equatorial axis | **Distance from equatorial plane center** |

### Hybrid 3D Method Details
- Finds equatorial plane (largest radial extent) for each spheroid
- Uses that plane's centroid as XY center
- Uses that plane's Z position as Z center
- Calculates 3D distance: `sqrt((X-Cx)² + (Y-Cy)² + (Z-Cz)²)` in microns
- Biological interpretation: true 3D distance from the equatorial plane's center point

## Current Status

### Data Loading (Resolved)
- ✅ Loading from `FeaturesImages_291025_none/SingleCell/HCT116.parquet`
- ✅ Contains all z-planes 0-12 (13 total planes)
- ✅ 873,550 cells with 2,167 columns (2,081 features + 86 metadata)

### Notebook Organization (Completed)
- ✅ Streamlined from 12 to 9 cells
- ✅ AnnData-first workflow implemented
- ✅ Functions separated from execution
- ✅ Dead code removed (unused helper functions, old commented snippets)
- ✅ Analysis plan converted to markdown
- ✅ Backup saved as `1_SC_Harmony.ipynb.backup`

## Next Steps - Harmony Integration (Plan A)

1. **Preprocessing (scanpy workflow)**
   - Filter cells/features (quality control)
   - Normalize data (e.g., log-transform)
   - Identify highly variable features
2. **Filter to DMSO controls** for initial testing
3. **Apply Harmony batch correction**
   - Use `adata.obs['Metadata_Z']` as batch covariate
   - Remove technical z-depth artifacts
   - Store corrected embeddings in `adata.obsm['X_harmony']`
4. **Validate on DMSO controls:**
   - PCA/UMAP on harmonized data
   - Plot colored by `Metadata_Radial_Distance_3D`
   - Check if radial biology becomes visible after correction
5. **If successful:** Apply to full dataset
6. **Continue with clustering:**
   - Leiden clustering on harmonized data (stored in `adata.obs['leiden']`)
   - Check if clusters correspond to spheroid layers (radial distance bins)
7. **Layer aggregation:**
   - Aggregate to spheroid layer level
   - Continue analysis at pseudo-bulk level

## Plan B (Fallback)
If Harmony removes too much biological signal:
- Focus analysis only on central z-planes
- Where technical and biological signals are less confounded
- Avoids issue at top/bottom planes where radial distance ≈ z-plane position

## Files Modified
- `spher_colo52_v1/1_Data/1_SC_Harmony.ipynb` - Streamlined notebook with AnnData-first workflow
- `spher_colo52_v1/1_Data/1_SC_Harmony.ipynb.backup` - Backup of original notebook
- `/share/data/analyses/christa/colopaint3D/claude.md` - Updated documentation

## Key AnnData Components

### `adata.obs` columns (cell metadata)
- `Metadata_Z` - z-plane index (0-12)
- `Metadata_Spheroid_ID` - unique spheroid identifier (Barcode_Well)
- `Metadata_Radial_Distance_3D` - 3D distance from equatorial plane center (microns)
- `Metadata_Equatorial_Z` - equatorial plane Z index for each spheroid
- `Metadata_Well`, `Metadata_Barcode`, `Metadata_Site` - experimental identifiers
- `ImageNumber_cytoplasm`, `ObjectNumber_cytoplasm` - cell tracking IDs
- Plus all `FileName_*` and `PathName_*` columns for traceability

### `adata.var` columns (feature metadata)
- `measurement_type` - Category of measurement (Intensity, AreaShape, Texture, etc.)
- `compartment` - Cellular compartment (cytoplasm, nucleus)
- `channel` - Imaging channel (HOECHST, MITO, SYTO, PHAandWGA, CONC)
- `metric` - Specific metric (MeanIntensity, Area, etc.)

### `adata.obsm` arrays (multi-dimensional annotations)
- `spatial_2d` - XY coordinates (pixels), shape (n_cells, 2)
- `spatial_3d` - XYZ coordinates (pixels), shape (n_cells, 3)

### `adata.uns` dictionary (global metadata)
- `pixel_size_um` - 0.227 µm/pixel
- `z_step_um` - 5.0 µm between z-planes
- `dataset` - 'HCT116'
- `n_spheroids` - Number of unique spheroids
- `n_z_planes` - Number of z-planes (13)
- `spheroid_centers` - Dict mapping spheroid_id → {center_x, center_y, center_z}

## Implementation Details

### AnnData Conversion
```python
def convert_to_anndata(df, pixel_size=0.227, z_step=5.0):
    # Separates columns into:
    #   - Features → adata.X
    #   - Metadata → adata.obs
    #   - Feature info → adata.var (parsed from column names)
    #   - Spatial coords → adata.obsm['spatial_2d']
    #   - Global params → adata.uns
```

### Hybrid 3D Radial Distance Calculation (AnnData-based)
```python
def calc_radial_distance_3d(adata, pixel_size=0.227, z_step=5.0):
    # For each spheroid:
    #   1. Find equatorial plane (max radial extent in XY)
    #   2. Store that plane's XY centroid and Z position as center
    # For all cells:
    #   3. Convert XY to microns: (X - center_X) * 0.227
    #   4. Convert Z to microns: (Z - center_Z) * 5.0
    #   5. Calculate: sqrt(x_um² + y_um² + z_um²)
    # Results stored in:
    #   - adata.obs['Metadata_Radial_Distance_3D']
    #   - adata.obs['Metadata_Equatorial_Z']
    #   - adata.obsm['spatial_3d']
    #   - adata.uns['spheroid_centers']
```

**Parameters:**
- `pixel_size = 0.227` µm/pixel (XY resolution)
- `z_step = 5.0` µm (Z-plane spacing)

### Usage Example
```python
# Load and convert
DataSingleCell = pd.read_parquet("HCT116.parquet")
adata = convert_to_anndata(DataSingleCell, pixel_size=0.227, z_step=5.0)

# Add spatial metadata
adata.obs['Metadata_Z'] = adata.obs['FileName_CONC_cytoplasm'].str.extract(r'-z(\d+)-')[0].astype(int)
adata.obs['Metadata_Spheroid_ID'] = adata.obs['Metadata_Barcode'].astype(str) + '_' + adata.obs['Metadata_Well'].astype(str)
adata = calc_radial_distance_3d(adata, pixel_size=0.227, z_step=5.0)

# Access data
spheroid_cells = adata[adata.obs['Metadata_Spheroid_ID'] == 'PB000137_B02']
xyz_coords = adata.obsm['spatial_3d']
radial_dist = adata.obs['Metadata_Radial_Distance_3D']
```
