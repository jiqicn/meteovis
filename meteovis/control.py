"""
class for controling views

Author: @jiqicn
"""

import ipywidgets as widgets


class AnimePlayer(object):
    """
    play interactive map as animation
    """
    def __init__(self, views):
        self.player = widgets.HTML("Player")
        
        
class ImageBuffer(dict):
    """
    queneing of image buffers.
    
    only images missing from the queue will be loaded
    old buffers will be removed when the queue is full
    """
    def __init__(self):
        pass