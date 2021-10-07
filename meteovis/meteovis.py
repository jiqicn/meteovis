"""
GUIs of processing data, listing datasets, and visualizing data

Author: @jiqicn
"""
from .dataset import (DatasetGenerator, Dataset, DATASET_DIR)

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
    w_title = widgets.HTML(value="<b style='font-size: large'>Process files to dataset</b>")
    w_path = FileChooser(title="<b>Select data folder</b>", show_only_dirs=True)
    w_name = widgets.Text(description="<b>Name</b>")
    w_desc = widgets.Text(description="<b>Description</b>")
    w_src = widgets.Dropdown(description="<b>Data Source</b>", options=["", "pvol", "era5"])
    w_options = widgets.VBox()
    w_reset = widgets.Button(description="Reset")
    w_process = widgets.Button(description="Process")
    w_output = widgets.Output()
    process_gui = widgets.VBox([w_title, w_path, w_name, w_desc, w_src, w_options,
                                widgets.HBox([w_reset, w_process]), w_output])
    
    # define events of GUI widgets
    def source_on_change(e):
        """
        change w_options based on the selected data source
        """        
        for c in w_options.children:
            c.close()
        w_options.children = []
        if w_src.value == "": return
        
        with w_output:
            print("* Set the data source to \"" + w_src.value + "\"")
            
            # get options and add widgets based on the return
            options = dg.get_options(w_src.value, w_path.value)
            
            if options is None:
                w_src.value = w_src.options[0]
            else:
                if w_src.value == "pvol":
                    w_scan = widgets.Dropdown(description="<b>Scan</b>", options=options["scans"])
                    w_qty = widgets.Dropdown(description="<b>Quantity</b>", options=options["qtys"])
                    w_options.children += (w_scan, w_qty, )
                elif w_src.value == "era5":
                    pass
    w_src.observe(source_on_change, names="value")
    
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
    w_reset.on_click(reset_on_click)
    
    def process_on_click(b):
        """
        start processing data files
        """
        meta = {"name": w_name.value, "desc": w_desc.value, "src": w_src.value}
        if w_src.value == "pvol":
            meta["scan"] = (w_options.children[0].label, w_options.children[0].value) # w_scan
            meta["qty"] = (w_options.children[1].label, w_options.children[1].value) # w_qty
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
    w_process.on_click(process_on_click)
    
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
    dataset_info = pd.DataFrame([])
    w_title = widgets.HTML(value="<b style='font-size: large'>Dataset Operations</b>")
    w_table = qgrid.show_grid(dataset_info, show_toolbar=False)
    w_refresh = widgets.Button(description="Refresh")
    w_remove = widgets.Button(description="Remove")
    w_copy = widgets.Button(description="Copy")
    oper_gui = widgets.VBox([w_title, w_table, widgets.HBox([w_refresh, w_remove, w_copy])])
    
    # define events of GUI widgets
    def refresh_on_click(b=None):
        """
        refresh dataset information
        
        -returns-
        pandas data frame that keeps all the dataset information
        """
        file_paths = [os.path.join(dir_path, fn) for fn in os.listdir(dir_path) if not fn.startswith('.')]
        dataset_info = []
        for fp in file_paths:
            ds = Dataset(fp)
            dataset_info.append([ds.id, ds.name, ds.desc, ds.src, ds.timeline[0], ds.timeline[-1], 
                                json.dumps(ds.options)])
        dataset_info = pd.DataFrame(dataset_info, columns=["ID", "Name", "Description", 
                                                                      "Data Source", "Start Time", 
                                                                      "End Time", "Metainfo"])
        dataset_info.set_index("ID", inplace=True)
        w_table.df = dataset_info
    w_refresh.on_click(refresh_on_click)
    
    refresh_on_click() # refresh before rendering the GUI
    return oper_gui