import numpy as np
import rasterio
import os

def gaussian_membership(array, c, sigma):
    """
    Apply Gaussian fuzzy membership function.
    """
    return np.exp(-((array - c) * 2) / (2 * sigma * 2))

def fuzzy_gamma_overlay(fuzzy_arrays, gamma_val):
    """
    Apply Fuzzy Gamma overlay operator.
    """
    fuzzy_and = np.minimum.reduce(fuzzy_arrays)
    fuzzy_or = np.maximum.reduce(fuzzy_arrays)
    return (fuzzy_and * (1 - gamma_val)) * (fuzzy_or * gamma_val)

def read_raster(filepath):
    """
    Read raster file and return array and metadata.
    """
    with rasterio.open(filepath) as src:
        arr = src.read(1).astype('float32')
        meta = src.meta
    return arr, meta

def save_raster(filepath, array, meta):
    """
    Save array as raster file.
    """
    meta.update(dtype=rasterio.float32, count=1)
    with rasterio.open(filepath, 'w', **meta) as dst:
        dst.write(array, 1)

# ----------------------------
# USER INPUTS
# ----------------------------

# Provide full paths to your raster files
raster_files = [
    r"path\to\raster1.tif",
    r"path\to\raster2.tif",
    r"path\to\raster3.tif"
]

# Define centers (c) and sigmas for each layer
centers = [50, 0.3, 300]    # ideal values
sigmas = [15, 0.1, 60]      # spread values

# Gamma value for overlay
gamma_value = 0.85

# Output raster path
output_raster = r"path\to\output\favorability_overlay.tif"

# ----------------------------
# PROCESSING
# ----------------------------

fuzzy_layers = []

# Loop through rasters and apply fuzzy membership
for i, raster_path in enumerate(raster_files):
    print(f"Processing: {os.path.basename(raster_path)}")
    arr, meta = read_raster(raster_path)
    
    # Handle nodata values safely (assuming nodata is masked as np.nan)
    arr = np.nan_to_num(arr, nan=0)
    
    fuzzy = gaussian_membership(arr, centers[i], sigmas[i])
    fuzzy_layers.append(fuzzy)

# Apply fuzzy gamma overlay
overlay = fuzzy_gamma_overlay(fuzzy_layers, gamma_value)

# Save result
save_raster(output_raster, overlay, meta)

print("✅ Fuzzy favorability map saved successfully:", output_raster)