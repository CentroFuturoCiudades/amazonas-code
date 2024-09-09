import numpy as np
import rasterio as rio

from pathlib import Path


def load_rasters(ghsl_path, year):
    pop_path = Path(ghsl_path / "POP" / f"{year}.tif")
    smod_path = Path(ghsl_path / "SMOD" / f"{year}.tif")

    with rio.open(smod_path, nodata=-200) as ds:
        smod_orig = ds.read(1).astype(float)
        transform = ds.transform

    with rio.open(pop_path, nodata=-200) as ds:
        pop_orig = ds.read(1).astype(float)

    pop_orig[pop_orig == -200] = np.nan
    smod_orig[smod_orig == -200] = np.nan

    return pop_orig, smod_orig, transform