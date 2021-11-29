"""
class for controling views

Author: @jiqicn
"""

import ipywidgets as widgets
from .view import CACHE_DIR, EMPTY_IMAGE
from PIL import Image
from io import BytesIO
import os
import base64


IMAGE_BUFFER_SIZE = 500
ANIME_SPEED = 400  # speed control, miliseconds between every two frames


class AnimePlayer(object):
    """
    play interactive map as animation
    """
    def __init__(self, views):
        """
        -parameters-
        views[list]: list of View objects
        """
        self.views = views
        self.buffer = ImageBuffer(IMAGE_BUFFER_SIZE)
        
        # merge the timelines of input views into one
        self.timeline = []
        for v in views:
            self.timeline += v.timeline
        self.timeline = list(set(self.timeline))
        self.timeline.sort()
        
        # initialize the player widget
        self.player = widgets.Play(
            value=0, 
            min=0, 
            max=len(self.timeline) - 1, 
            interval=ANIME_SPEED,  
        )
        self.slider = widgets.SelectionSlider(
            value=self.timeline[0], 
            options=self.timeline, 
        )
        
        # event of player and slider
        def change_player(e):
            i = e["new"]
            raster_name = self.timeline[i]
            self.slider.value = raster_name
            self.update_views(raster_name)
        self.player.observe(change_player, names="value")
        
        def change_slider(e):
            raster_name = e["new"]
            i = self.timeline.index(raster_name)
            self.player.value = i
            self.update_views(raster_name)
        self.slider.observe(change_slider, names="value")
        
    def get_player(self):
        """
        return the player and the slider as a whole
        """
        return widgets.HBox([
            widgets.HTML("<b>Timeline&nbsp<b>"), 
            self.player, 
            self.slider, 
        ])
    
    def update_views(self, raster_name):
        """
        update both views
        """
        for v in self.views:
            vid = v.id
            img_name = vid + "_" + raster_name + ".png"
            img = self.buffer[img_name]
            v.update_raster(img)

    def init_views(self):
        """
        initialize the views by loading and overlaying the raster of the first timestamp
        """
        raster_name = self.timeline[0]
        self.update_views(raster_name)
    
        
class ImageBuffer(dict):
    """
    queneing of image buffers.
    
    only images missing from the queue will be loaded
    old buffers will be removed when the queue is full
    """
    def __init__(self, buffer_size=100):
        if not hasattr(self, '_queue'):
            self._queue = []  # queue of image buffers, where keys (image names) stored
        self.buffer_size = buffer_size
    
    def __missing__(self, img_name):
        """
        reload of the missing function of dict.
        
        -parameters-
        img_name[str]
        
        -return-
        the image buffer in b64
        """
        img = self.load(img_name)
        self[img_name] = img
        return img
        
    def load(self, img_name):
        """
        load image to buffer
        
        -parameters-
        img_name[str]
        
        -return-
        the image buffer in b64
        """
        if len(self._queue) >= self.buffer_size:
            self.pop(self._queue.pop(0))
        
        # create image buffer
        img_path = os.path.join(CACHE_DIR, img_name)
        try:
            img = Image.open(img_path)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_buf = buffered.getvalue()
            img_buf = base64.b64encode(img_buf).decode('ascii')
            img_buf = "data:image/png;base64," + img_buf
        except FileNotFoundError:  
            # img_buf = EMPTY_IMAGE  # if image not exist, return empty image
            img_buf = None
        
        # add image to the queue
        self._queue.append(img_name)
        self[img_name] = img_buf
        
        return img_buf
    

class OpacityController(object):
    def __init__(self, views):
        """
        Opacity control widget
        """
        self.opactl = widgets.FloatSlider(
            value=1, 
            min=0, 
            max=1, 
        )
        
        def change_opactl(e=None):
            for v in views:
                v.raster.opacity = e["new"]
        self.opactl.observe(change_opactl, names="value")
    
    def get_controler(self):
        return widgets.HBox([
            widgets.HTML('<b>Opacity&nbsp</b>'), 
            self.opactl
        ])