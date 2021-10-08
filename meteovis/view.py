"""
class of view, as well as other relevant classes

Author: @jiqicn
"""

import ipywidgets as widgets


class View(object):
    """
    interactive map view of dataset
    """
    def __init__(self, dataset):
        self.view = widgets.HTML(dataset.id)
        
    def render(self):
        """
        render the dataset into images in cache
        """
        pass