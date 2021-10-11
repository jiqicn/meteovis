"""
GUIs of processing data, listing datasets, and visualizing data

Author: @jiqicn
"""
from .dataset import (DatasetGenerator, Dataset, DATASET_DIR)
from .view import View
from .control import AnimePlayer

import ipywidgets as widgets
from ipyfilechooser import FileChooser
import qgrid
import pandas as pd
import h5py
import json
import os


def process_data():
    """
    GUI of processing a collection of files as a dataset
    
    -returns-
    object of data-processing GUI
    """
    dg = DatasetGenerator()
    
    # define the GUI
    w_title = widgets.HTML(
        value="<b style='font-size: large'>Process files to dataset</b>"
    )
    w_path = FileChooser(
        title="<b>Select data folder</b>", 
        show_only_dirs=True
    )
    w_name = widgets.Text(
        description="<b>Name</b>"
    )
    w_desc = widgets.Text(
        description="<b>Description</b>"
    )
    w_src = widgets.Dropdown(
        description="<b>Data Source</b>", 
        options=[
            "", 
            "pvol", 
            "era5"
        ]
    )
    w_options = widgets.VBox()
    w_reset = widgets.Button(
        description="Reset"
    )
    w_process = widgets.Button(
        description="Process"
    )
    w_output = widgets.Output()
    process_gui = widgets.VBox([
        w_title, 
        w_path, 
        w_name, 
        w_desc, 
        w_src, 
        w_options,
        widgets.HBox([
            w_reset, 
            w_process
        ]), 
        w_output
    ])
    
    # define events of GUI widgets
    def source_on_change(e):
        """
        change w_options based on the selected data source
        """        
        for c in w_options.children:
            c.close()
        w_options.children = []
        if w_src.value == "": 
            return
        
        with w_output:
            print("* Set the data source to \"" + w_src.value + "\"")
            
            # get options and add widgets based on the return
            options = dg.get_options(
                w_src.value, 
                w_path.value
            )
            
            if options is None:
                w_src.value = w_src.options[0]
            else:
                if w_src.value == "pvol":
                    w_scan = widgets.Dropdown(
                        description="<b>Scan</b>", 
                        options=options["scans"]
                    )
                    w_qty = widgets.Dropdown(
                        description="<b>Quantity</b>", 
                        options=options["qtys"]
                    )
                    w_options.children += (
                        w_scan, 
                        w_qty, 
                    )
                elif w_src.value == "era5":
                    pass
    w_src.observe(
        source_on_change, 
        names="value"
    )
    
    def reset_on_click(b):
        """
        reset the whole gui
        """
        dg = DatasetGenerator()
        w_name.value = ""
        w_desc.value = ""
        w_path.reset()
        w_src.value = w_src.options[0]
        w_output.clear_output()
        for c in w_options.children:
            c.close()
        w_options.children = []
    w_reset.on_click(
        reset_on_click
    )
    
    def process_on_click(b):
        """
        start processing data files
        """
        meta = {
            "name": w_name.value, 
            "desc": w_desc.value, 
            "src": w_src.value
        }
        if w_src.value == "pvol":
            # w_scan and w_qty should be defined in this branch
            meta["scan"] = (
                w_options.children[0].label, 
                w_options.children[0].value
            )
            meta["qty"] = (
                w_options.children[1].label, 
                w_options.children[1].value
            )
        elif w_src.value == "era5":
            pass
        
        with w_output:
            try:
                if w_path.value == "" or w_path.value is None:
                    raise Exception("\033[91m! Please select your data folder\033[0m")
                for k in meta:
                    if meta[k] == "" or meta[k] is None or meta[k] == ("", ""):
                        raise Exception("\033[91m! Field %s is empty\033[0m" % k)
                dg.create_dataset(meta, w_path.value)
            except Exception as e:
                print("\033[91m! Error message: %s\033[0m" % e)
    w_process.on_click(
        process_on_click
    )
    
    return process_gui


def operate_datasets(dir_path=DATASET_DIR):
    """
    GUI of showing the existing datasets in a list
    
    -parameters-
    dir_path[str]: abs path to the folder of datasets, default to be 
    
    -returns-
    object of listing-datasets GUI
    """    
    # define the GUI
    w_title = widgets.HTML(
        value="<b style='font-size: large'>Dataset Operations</b>"
    )
    w_table = qgrid.show_grid(
        pd.DataFrame(), 
        show_toolbar=False
    )
    w_tabs = widgets.Tab()
    w_tabs.set_title(0, "General")
    w_tabs.set_title(1, "Visualization")
    
    # General tab
    w_refresh = widgets.Button(
        description="Refresh"
    )
    w_remove = widgets.Button(
        description="Remove"
    )
    w_tabs.children += (
        widgets.VBox([
            widgets.HTML('<b>Select ONE dataset for the operations below.</b>'), 
            widgets.HBox([
                w_refresh, 
                w_remove, 
            ]), 
        ]), 
    )
    
    # Visualization tab
    w_select_vis = widgets.Button(
        description="Confirm Selection"
    )
    w_vis_output = widgets.Output()
    w_view_box = widgets.HBox() # where to add views
    w_ctrl_box = widgets.VBox() # where to add controls like animation player
    w_tabs.children += (
        widgets.VBox([
            widgets.HTML(
                '<p><b>Select ONE or TWO dataset(s) for visualization.</b></p>' + 
                '<p>If you select two datasets, they will be presented side-by-side.</p>' +
                '<p>If you select more than two datasets, only the first two will be visualized.<p>' +
                '<p>Press the button below to confirm your selection.</p>'
            ), 
            w_select_vis, 
            w_vis_output, 
            w_view_box, 
            w_ctrl_box, 
        ]), 
    )
    
    oper_gui = widgets.VBox([
        w_title, 
        w_table, 
        w_tabs, 
    ])
    
    # define events of GUI widgets
    def refresh_on_click(b=None):
        """
        refresh dataset information
        """
        dataset_info = []
        for dn in os.listdir(dir_path):
            if not dn.startswith('.'):
                dp = os.path.join(dir_path, dn)
                ds = Dataset(dp)
                dataset_info.append([
                    ds.id, 
                    ds.name, 
                    ds.desc, 
                    ds.src,
                    ds.timeline[0],
                    ds.timeline[-1], 
                    json.dumps(ds.options)
                ])
        dataset_info = pd.DataFrame(
            dataset_info, 
            columns=[
                "ID", 
                "Name", 
                "Description", 
                "Data Source", 
                "Start Time", 
                "End Time", 
                "Metainfo"
            ]
        )
        dataset_info.set_index("ID", inplace=True) # set ID as index column
        w_table.df = dataset_info
    w_refresh.on_click(refresh_on_click)
    
    def remove_on_click(b=None):
        """
        remove dataset file
        """
        selection = w_table.get_selected_df()
        ids_to_remove = selection.index.values
        for dn in ids_to_remove:
            dn = dn + ".h5"
            dp = os.path.join(dir_path, dn)
            Dataset(dp).remove()
        refresh_on_click()
    w_remove.on_click(remove_on_click)
    
    def select_vis_on_click(b=None):
        """
        show views of the selected dataset(s)
        """
        views = []
        w_view_box.children = [] # clean view output
        w_ctrl_box.children = []
        selection = w_table.get_selected_df()
        ids_to_vis = selection.index.values
        for dn in ids_to_vis:
            dn = dn + ".h5"
            dp = os.path.join(dir_path, dn)
            ds = Dataset(dp)
            v = View(ds)
            views.append(v)
        
        # render datasets into cache
        w_vis_output.clear_output()
        for v in views:
            with w_vis_output:
                v.create_cache()
        
        # initialize controls and views
        ap = AnimePlayer(views)
        
        # display maps and controls
        for v in views:
            w_view_box.children += (v.view, )
        w_ctrl_box.children += (ap.player, )
        
    w_select_vis.on_click(select_vis_on_click)
    
    # init the dataset list and dataframe of dataset information
    refresh_on_click()
    
    return oper_gui