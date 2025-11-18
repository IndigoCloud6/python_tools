import logging
import os

import geopandas as gpd
import numpy as np
import rasterio
from shapely.geometry import Point
from tqdm import tqdm


class PointElevationUpdater:
    """
    A powerful utility for assigning DEM elevation (Z-values) to point datasets.

    Features:
        - Batch process multiple shapefiles
        - Automatically handle CRS mismatch
        - Export 3D Shapefile / GeoJSON
        - Logging system
        - High-speed raster sampling (rasterio.sample)
        - Progress bars (tqdm)
    """

    def __init__(self, dem_path: str, log_level=logging.INFO):
        self.dem_path = dem_path
        self.dem = rasterio.open(dem_path)

        # Configure logging
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )
        logging.info(f"Loaded DEM: {dem_path}")

    def _ensure_same_crs(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Reproject points to DEM CRS if needed."""
        if gdf.crs != self.dem.crs:
            logging.info("CRS mismatch detected → Reprojecting points to DEM CRS...")
            return gdf.to_crs(self.dem.crs)
        return gdf

    def _sample_elevations(self, gdf: gpd.GeoDataFrame) -> np.ndarray:
        """Fast elevation sampling with tqdm progress bar."""
        coords = [(geom.x, geom.y) for geom in gdf.geometry]

        elevations = []
        for val in tqdm(
            self.dem.sample(coords),
            total=len(coords),
            desc="Sampling elevations",
            ncols=80
        ):
            elevations.append(val)

        return np.array(elevations).flatten()

    def update_z_values(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Update point Z coordinates using DEM."""
        gdf = self._ensure_same_crs(gdf)

        # Progress bar for elevation sampling
        elevations = self._sample_elevations(gdf)

        new_geoms = []
        for geom, z in zip(gdf.geometry, elevations):
            if np.isfinite(z):
                new_geoms.append(Point(geom.x, geom.y, float(z)))
            else:
                new_geoms.append(geom)

        updated = gdf.copy()
        updated.geometry = new_geoms

        return updated

    def export_shp(self, gdf: gpd.GeoDataFrame, output_path: str):
        """Export as 3D Shapefile."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        gdf.to_file(output_path, driver="ESRI Shapefile", encoding="utf-8")
        logging.info(f"3D Shapefile exported → {output_path}")

    def export_geojson(self, gdf: gpd.GeoDataFrame, output_path: str):
        """Export GeoJSON."""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        gdf = gdf.to_crs(epsg=4326)
        gdf.to_file(output_path, driver="GeoJSON", encoding="utf-8")
        logging.info(f"GeoJSON exported → {output_path}")

    def process_shapefile(self, shp_path: str, out_dir: str):
        """Process a single shapefile."""
        logging.info(f"Processing: {shp_path}")
        gdf = gpd.read_file(shp_path)

        updated = self.update_z_values(gdf)

        base = os.path.splitext(os.path.basename(shp_path))[0]
        shp_out = os.path.join(out_dir, f"{base}_Z.shp")
        json_out = os.path.join(out_dir, f"{base}_Z.geojson")

        self.export_shp(updated, shp_out)
        self.export_geojson(updated, json_out)

    def process_folder(self, folder: str, out_dir: str):
        """Batch process all shapefiles in a folder with tqdm progress bar."""
        files = [f for f in os.listdir(folder) if f.lower().endswith(".shp")]
        logging.info(f"Found {len(files)} shapefiles.")

        for f in tqdm(files, desc="Processing shapefiles", ncols=80):
            self.process_shapefile(os.path.join(folder, f), out_dir)


# ---------------- Example Usage ----------------
if __name__ == "__main__":
    dem_path = "example.tif"
    input_folder = "test_shapefiles"
    output_folder = "output_z"

    updater = PointElevationUpdater(dem_path)
    updater.process_folder(input_folder, output_folder)

    logging.info("All processing completed.")
