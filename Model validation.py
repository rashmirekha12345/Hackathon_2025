import geopandas as gpd
import rasterio
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score
import os

# === USER INPUT ===
raster_path = "fuzzy_overlay.tif"
shapefile_dir = "min_Au_shapefile"
shapefile_name = "min_Au.shp"
crs_epsg = 32643  # UTM Zone 43N

# === LOAD SHAPEFILE ===
shapefile_path = os.path.join(shapefile_dir, shapefile_name)
points_gdf = gpd.read_file(shapefile_path)

# === LOAD RASTER ===
with rasterio.open(raster_path) as src:
    raster_data = src.read(1)
    transform = src.transform
    raster_crs = src.crs
    raster_height = src.height
    raster_width = src.width
    nodata = src.nodata

# Handle missing CRS
if raster_crs is None:
    raster_crs = rasterio.crs.CRS.from_epsg(crs_epsg)

# === CRS ALIGNMENT ===
if points_gdf.crs is None:
    raise ValueError("Shapefile missing CRS definition")
points_gdf = points_gdf.to_crs(raster_crs)

# === VALUE EXTRACTION ===
def extract_values(gdf, raster, transform, height, width):
    values = []
    for point in gdf.geometry:
        # Get column/row indices
        col, row = ~transform * (point.x, point.y)
        col = int(col)
        row = int(row)
        
        # Check bounds
        if 0 <= row < height and 0 <= col < width:
            val = raster[row, col]
            # Validate against NoData
            if (np.isnan(nodata) and not np.isnan(val)) or \
               (not np.isnan(nodata) and val != nodata):
                values.append(val)
    return np.array(values)

occurrence_values = extract_values(points_gdf, raster_data, transform, 
                                  raster_height, raster_width)

# === RANDOM SAMPLING ===
# Create valid pixel mask
if np.isnan(nodata):
    valid_mask = ~np.isnan(raster_data)
else:
    valid_mask = raster_data != nodata
rows, cols = np.where(valid_mask)

# Safe sampling
sample_size = min(len(rows), len(occurrence_values))
if sample_size == 0:
    raise ValueError("No valid pixels for random sampling")
rand_idx = np.random.choice(len(rows), size=sample_size, replace=False)
random_values = raster_data[rows[rand_idx], cols[rand_idx]]

# === STATISTICAL ANALYSIS ===
y_true = np.concatenate([np.ones_like(occurrence_values), 
                        np.zeros_like(random_values)])
y_score = np.concatenate([occurrence_values, random_values])
auc_score = roc_auc_score(y_true, y_score)

# === OUTPUT ===
print("\nValidation Summary:")
print(f"Number of known occurrences: {len(occurrence_values)}")
print(f"Number of random points: {len(random_values)}")
print(f"Mean favorability (occurrences): {np.mean(occurrence_values):.3f}")
print(f"Mean favorability (random): {np.mean(random_values):.3f}")
print(f"ROC-AUC Score: {auc_score:.3f}")

# === VISUALIZATION ===
plt.figure(figsize=(8, 5))
plt.hist(occurrence_values, bins=20, alpha=0.7, label="Known Occurrences")
plt.hist(random_values, bins=20, alpha=0.7, label="Random Points")
plt.xlabel("Fuzzy Favorability Value")
plt.ylabel("Frequency")
plt.title("Fuzzy Favorability Distribution")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()