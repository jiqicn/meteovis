"""
class of view, as well as other relevant classes

Author: @jiqicn
"""

import ipywidgets as widgets
import matplotlib.pyplot as plt
import multiprocessing as mp
import h5py
import os
from ipyleaflet import Map, basemaps, FullScreenControl, ImageOverlay, WidgetControl
import base64
import io
import numpy as np


CACHE_DIR = os.getcwd() + "/cache"
EMPTY_IMAGE = "data:image/png;base64,R0lGODlhAQABAAAAACwAAAAAAQABAAA="


class View(object):
    """
    interactive map view of dataset
    """
    def __init__(self, dataset):
        self.dataset = dataset
        self.id = dataset.id
        self.timeline = dataset.timeline
        
        # interactive map
        self.map = Map(
            center=dataset.options["center"], 
            zoom=7, 
            scroll_wheel_zoom=True, 
            attribution_control=False, 
        )
        self.map.add_control(FullScreenControl())
        
        # colorbar widget
        cbar_buf = io.BytesIO()
        cmap = dataset.cmap[0]
        vmin = dataset.cmap[1]
        vmax = dataset.cmap[2]
        plt.figure(figsize=(3, 0.5))
        plt.imshow(
            np.array([[vmin, vmax]]), 
            cmap=cmap
        )
        plt.gca().set_visible(False)
        plt.colorbar(
            cax=plt.axes([0.1, 0.2, 0.8, 0.3]), 
            orientation="horizontal", 
            extend="both"
        )
        plt.savefig(
            cbar_buf, 
            format="png", 
            transparent=True, 
            bbox_inches="tight", 
            pad_inches=0
        )
        plt.close()
        cbar_buf.seek(0)
        cbar_b64 = base64.b64encode(cbar_buf.read()).decode('ascii')
        img_str = '<div style="padding-left: 10px; padding-right: 10px">'
        img_str += '<p><b>Dataset: %s</b></p>' % dataset.name
        img_str += '<img src="data:image/png;base64, %s"/></div>' % cbar_b64
        w_cbar = widgets.HTML(
            img_str, 
            layout=widgets.Layout(padding='20 20 20 20')
        )
        self.map.add_control(
            WidgetControl(widget=w_cbar, position='topright')
        )
        
        # raster layer
        self.raster = ImageOverlay(
            url=EMPTY_IMAGE, 
            bounds=dataset.bbox, 
            opacity=1
        )
        self.map.add_layer(self.raster)
        
    def update_raster(self, img):
        """
        initialize the interactive map and put the raster layer
        
        -parameters-
        img[str]: image buffer encoded in base64
        """
        self.raster.url = img
        
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
        
        print("[" + dataset_id + "]" + "Rendering and caching......", end="", flush=True)
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
        if os.path.isfile(image_path): 
            return
        
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
        