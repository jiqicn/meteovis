"""
class of view, as well as other relevant classes

Author: @jiqicn
"""

import ipywidgets as widgets
import matplotlib.pyplot as plt
import multiprocessing as mp
import h5py
import os
from ipyleaflet import Map, basemaps, FullScreenControl


CACHE_DIR = os.getcwd() + "/cache"


class View(object):
    """
    interactive map view of dataset
    """
    def __init__(self, dataset):
        self.dataset = dataset
        self.id = dataset.id
        self.timeline = dataset.timeline
        self.view = Map(
            center=dataset.options["center"], 
            zoom=7, 
            scroll_wheel_zoom=True, 
            attribution_control=False, 
        )
        self.view.add_control(FullScreenControl())
        
    def update_view(self, img):
        """
        initialize the interactive map and put the raster layer
        
        -parameters-
        img[str]: image buffer encoded in base64
        """
        pass
        
        
    def create_cache(self, cache_dir=CACHE_DIR):
        """
        arrange rendering in parallel and keep the resulting images into cache
        
        -parameters-
        cache_dir[str]: path to the cache directory, default to be CACHE_DIR
        """
        dataset_id = self.id
        dataset_path = self.dataset.dataset_path
        cmap = self.dataset.cmap[0]
        vmin = self.dataset.cmap[1]
        vmax = self.dataset.cmap[2]
        raster_names = self.timeline
        pool = mp.Pool(mp.cpu_count() + 2)
        jobs = []
        
        print("Rendering and caching......", end="", flush=True)
        for rn in raster_names:
            job = pool.apply_async(
                self.render_image, 
                (dataset_id, dataset_path, cmap, vmin, vmax, cache_dir, rn)
            )
            jobs.append(job)
        for job in jobs:
            job.get()
        pool.close()
        pool.join()
        print("[Done]")
    
    @staticmethod
    def render_image(dataset_id, dataset_path, cmap, vmin, vmax,
                     cache_dir, raster_name):
        """
        render a raster into an image
        
        -parameters-
        dataset_id[str]
        dataset_path[str]
        cmap[str]: colormap name that is available in matplotlib
        vmin, vmax[int]: value range to be colored
        cache_dir[str]
        raster_name[str]
        """
        image_name = dataset_id + "_" + raster_name + ".png"
        image_path = os.path.join(cache_dir, image_name)
        
        with h5py.File(dataset_path, "r") as f:
            raster = f["data"][raster_name][...]
        
        fig_size = (raster.shape[1], raster.shape[0])
        fig = plt.figure(figsize=fig_size, dpi=1)
        fig.add_axes([0, 0, 1, 1])
        plt.imshow(
            raster, 
            cmap=cmap, 
            vmin=vmin, 
            vmax=vmax, 
        )
        plt.axis("off")
        fig.savefig(
            image_path, 
            transparent=True,
            bbox_inches="tight", 
            pad_inches=0, 
            dpi=1, 
        )
        plt.close()
        