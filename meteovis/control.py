"""
class for controling views

Author: @jiqicn
"""

import ipywidgets as widgets
from .view import CACHE_DIR
from PIL import Image
from io import BytesIO
import os
import base64


IMAGE_BUFFER_SIZE = 100
EMPTY_IMAGE = "data:image/png;base64,R0lGODlhAQABAAAAACwAAAAAAQABAAA="


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
        self.player = widgets.HTML("Player")

    def init_views(self):
        """
        initialize the views by loading and overlaying the raster of the first timestamp
        """
        pass
    
        
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
            img_buf = EMPTY_IMAGE  # if image not exist, return empty image
        
        # add image to the queue
        self._queue.append(img_name)
        self[img_name] = img_buf
        
        return img_buf