"""
classes related to dataset and its operations

Author: @jiqicn
"""
import os
import h5py
import numpy as np
import wradlib as wrl
import uuid
import multiprocessing as mp
import time
import json
import numpy as np
from scipy.interpolate import griddata
import wradlib.ipol as ipol


DATASET_DIR = os.getcwd() + "/dataset"
TEMP_DIR = os.getcwd() + "/temp"
MERGE_STEP = 1000  # step size of the merging result, in metres


class Colorbar(object):
    """
    define colormaps and value ranges for different radar products
    
    scheme: (matplotlib) cmap_name, v_min, v_max
    """
    
    PVOL_DEFAULT = ("turbo", -32, 60)
    PVOL = {
        "TH": ("turbo", -32, 60), 
        "VH": ("turbo", -32, 60), 
        "DBZH": ("turbo", -32, 60), 
        "DBZV": ("turbo", -32, 60), 
        "VRADH": ("coolwarm", -80, 80), 
        "VRADV": ("coolwarm", -80, 80), 
        "VRAD": ("coolwarm", -80, 80), 
        "KDP": ("coolwarm", -10, 10), 
        "ZDR": ("coolwarm", -10, 10), 
        "PHIDP": ("Greens", 0, 360), 
        "RHOHV": ("Greens", 0, 1.1)
    }

    
class DatasetGenerator(object):
    """
    Dataset generator that will talk with the data processing GUI
    """
    
    def __init__(self):
        self.dataset_path = "" # output dataset file
    
    def get_options(self, src, dir_path):
        """
        get options of data source
        
        -parameters-
        src[str]: data source name, e.g. "pvol", "era5"
        dir_path[str]: input files directory
        """
        
        # get the sample file that is the first file in the dir
        # assumption: files in the same dataset follow the same scheme
        try:
            for fn in os.listdir(dir_path):
                if not fn.startswith('.'):
                    file_name = fn
                    break
            file_path = os.path.join(
                dir_path, 
                file_name
            )
        except TypeError:
            print("\033[91m! Invalid path\033[0m")
            return
        except IndexError:
            print("\033[91m! No data file founded\033[0m")
            return
        
        if src == "pvol":
            return self.__get_options_pvol(
                file_path
            )
    
    def __get_options_pvol(self, file_path):
        """
        get scan and quantity list of pvol data
        
        -parameters-
        file_path[str]: sample file
        """
        
        scan_list = [("", "")]
        qty_list = [("", "")]
        
        with h5py.File(file_path, "r") as f:
            scan_names = []
            for s in f.keys():
                if 'dataset' in s:
                    scan_names.append(s)
            # sort scan names by the digits within
            scan_names = sorted(
                scan_names, 
                key=lambda x: int("".join([i for i in x if i.isdigit()]))
            )
            for i in range(len(scan_names)):
                sn = scan_names[i]
                elangle = f[sn]["where"].attrs["elangle"]
                t = (sn + " (Elev. = " + str(elangle) + ")", sn)
                scan_list.append(t)
            
            qty_names = [s for s in f["dataset1"].keys() if "data" in s]
            for i in range(len(qty_names)):
                qn = qty_names[i]
                qty = f["dataset1"][qn]["what"].attrs["quantity"].decode("utf-8")
                t = (qty, qn)
                qty_list.append(t)
            
        return {"scans": scan_list, "qtys": qty_list}
    
    def create_dataset(self, meta, dir_path):
        """
        create the dataset file
        
        -parameters-
        meta[dict]: name, desc, src, and opts
        dir_path[str]: input files directory
        """
        
        id = str(uuid.uuid4())
        name = meta["name"]
        desc = meta["desc"]
        src = meta["src"]
        crs = "epsg3857"
        timeline = []
        self.dataset_path = os.path.join(DATASET_DIR, id+".h5")
        with h5py.File(self.dataset_path, "w") as f:
            f.create_group("data")
            f.create_group("meta")
        
        # get meta information that may differ on data from different sources
        if meta["src"] == "pvol":
            options = {"scan": meta["scan"], "qty": meta["qty"]}
            if meta["qty"][0] in Colorbar.PVOL_DEFAULT:
                cmap = Colorbar.PVOL_DEFAULT[meta["qty"][0]]
            else:
                cmap = Colorbar.PVOL_DEFAULT
        
        # process input files in parallel and write to the dataset file
        print("* Processing input files")
        start_time = time.time()
        file_paths = [os.path.join(dir_path, fn) for fn in os.listdir(dir_path) if not fn.startswith('.')]
        q = mp.Manager().Queue()
        pool = mp.Pool(mp.cpu_count()+2)
        watcher = pool.apply_async(self.write_dataset_file, (q, ))
        jobs = []
        for fp in file_paths:
            job = pool.apply_async(self.process_pvol_file, (fp, options, q))
            jobs.append(job)

        # result = (dt, bbox, bbox_metre, data.shape, center, radar)
        for job in jobs:
            result = job.get()
            timeline.append(result[0])
            bbox = result[1]
            bbox_metre = result[2]
            res = result[3]  # resolution, rows * cols
            options["center"] = result[4]
            options["radar"] = result[5]
        timeline.sort()
        q.put("kill")
        pool.close()
        pool.join()
        print("* Finished in %.2f seconds" % (time.time() - start_time))
        
        # write meta information to the dataset file
        with h5py.File(self.dataset_path, "r+") as f:
            f["meta"].attrs.create("id", id)
            f["meta"].attrs.create("name", name)
            f["meta"].attrs.create("desc", desc)
            f["meta"].attrs.create("src", src)
            f["meta"].attrs.create("crs", crs)
            f["meta"].attrs.create("res", res)
            f["meta"].attrs.create("timeline", timeline)
            f["meta"].attrs.create("options", json.dumps(options))
            f["meta"].attrs.create("cmap", str(cmap))
            f["meta"].attrs.create("bbox", bbox)
            f["meta"].attrs.create("bbox_metre", bbox_metre)
    
    def process_pvol_file(self, file_path, options, q):
        """
        process pvol data file 
        
        -parameters-
        file_path[str]: input file
        q[multiprocessing.Manageer.Queue]: writing queue
        
        -returns-
        dt[str]: datetime stamp
        bbox[list]: [[lon_min, lat_min], [lon_max, lat_max]]
        center[list]: [lat, lon]
        radar[str]: radar station name and index
        """
        
        scan = options["scan"][1]
        qty = options["qty"][1]
        
        # get data and necessary attributes
        with h5py.File(file_path, "r") as f:
            data = f[scan][qty]["data"][...].astype("float64")
            elangle = float(f[scan]["where"].attrs["elangle"])
            rscale = float(f[scan]["where"].attrs["rscale"])
            nbins = int(f[scan]["where"].attrs["nbins"])
            nrays = int(f[scan]["where"].attrs["nrays"])
            gain = float(f[scan][qty]["what"].attrs["gain"])
            offset = float(f[scan][qty]["what"].attrs["offset"])
            nodata = float(f[scan][qty]["what"].attrs["nodata"])
            undetect = float(f[scan][qty]["what"].attrs["undetect"])
            lon = float(f["where"].attrs["lon"])
            lat = float(f["where"].attrs["lat"])
            height = float(f["where"].attrs["height"])
            date = str(f["what"].attrs["date"]).split("'")[1]
            time = str(f["what"].attrs["time"]).split("'")[1][:-2] # accurate to minutes
            radar = str(f["what"].attrs["source"]).split("'")[1]
            dt = date + "-" + time
            
        # mask nodata and undetect values
        data[data==nodata] = np.nan
        data[data==undetect] = np.nan
        
        # linear transformation to convert to physical unit
        data = data * gain + offset
            
        # compute polar grid
        polar_grid = np.empty((nrays, nbins, 3))  # azimuth, range, height
        polar_grid = wrl.georef.sweep_centroids(nrays=nrays, rscale=rscale, nbins=nbins, elangle=elangle)
        
        # compute cartisian grid of both projection epsg4326 (in degree) and epsg3857 (in metre)
        carti_grid_4326 = wrl.georef.polar.spherical_to_proj(
            polar_grid[..., 0], polar_grid[..., 1],                                                 
            polar_grid[..., 2], (lon, lat, height)
        )
        carti_grid_3857 = wrl.georef.polar.spherical_to_proj(
            polar_grid[..., 0], polar_grid[..., 1],                                                 
            polar_grid[..., 2], (lon, lat, height),                                                 
            proj=wrl.georef.projection.epsg_to_osr(3857)
        )
        # map data from polar grid to cartisian grid 3857
        x = carti_grid_3857[..., 0]
        y = carti_grid_3857[..., 1]
        xgrid = np.linspace(x.min(), x.max(), 2*nbins)
        ygrid = np.linspace(y.min(), y.max(), 2*nbins)
        grid_xy = np.meshgrid(xgrid, ygrid)
        grid_xy = np.vstack((grid_xy[0].ravel(), grid_xy[1].ravel())).transpose()
        xy=np.concatenate([x.ravel()[:,None],y.ravel()[:,None]], axis=1)
        data = wrl.comp.togrid(
            xy, grid_xy, nbins*rscale, np.array([x.mean(), y.mean()]), 
            data.ravel(), wrl.ipol.Nearest
        )
        data = np.ma.masked_invalid(data).reshape((len(xgrid), len(ygrid)))
        data = np.flip(data, 0)
        data = data.data # ignore the mask
        
        # bbox and coordinates of the radar station (in degree, i.e. epsg 4326)
        bbox = [
            [np.nanmin(carti_grid_4326[..., 1]), np.nanmin(carti_grid_4326[..., 0])],
            [np.nanmax(carti_grid_4326[..., 1]), np.nanmax(carti_grid_4326[..., 0])],
        ]
        bbox_metre = [
            [np.nanmin(carti_grid_3857[..., 1]), np.nanmin(carti_grid_3857[..., 0])],
            [np.nanmax(carti_grid_3857[..., 1]), np.nanmax(carti_grid_3857[..., 0])],
        ]
        center = (lat, lon)
        
        # put data to the queue
        q.put((dt, data))
            
        return (dt, bbox, bbox_metre, data.shape, center, radar)
    
    def write_dataset_file(self, q):
        """
        write data into the dataset file
        
        -parameters-
        q[multiprocessing.Manageer.Queue]: writing queue
        """
        with h5py.File(self.dataset_path, "r+") as f:
            while True:
                m = q.get()
                if m == "kill":
                    break
                f["data"].create_dataset(
                    m[0], 
                    data=m[1], 
                    compression="gzip", 
                    compression_opts=9
                )
                
class Dataset:
    """
    abstraction of dataset
    
    enable operations on datasets, including algebra, merging, etc.
    """
    def __init__(self, dataset_path=None):
        self.dataset_path = dataset_path

        # read dataset file if it's not an empty dataset object
        if dataset_path is not None:
            with h5py.File(dataset_path, "r") as f:
                self.id = f["meta"].attrs["id"]
                self.name = f["meta"].attrs["name"]
                self.desc = f["meta"].attrs["desc"]
                self.src = f["meta"].attrs["src"]
                self.crs = f["meta"].attrs["crs"]
                self.res = f["meta"].attrs["res"]
                self.options = json.loads(f["meta"].attrs["options"])
                self.cmap = eval(f["meta"].attrs["cmap"])
                self.timeline = f["meta"].attrs["timeline"].tolist()
                self.bbox = f["meta"].attrs["bbox"].tolist()
                self.bbox_metre = f["meta"].attrs["bbox_metre"].tolist()
            
    def remove(self):
        """
        remove dataset file from disk
        """
        os.remove(self.dataset_path)
        
    def merge(self, mode, *datasets):
        """
        merge two or more datasets into one

        -parameters-
        mode[str]: indicate in which way the datasets should be merged, options include "max", "min", "avg"
        datasets[arb]: arbitrary number of datasets
        """
        # initialize dataset
        self.id = str(uuid.uuid4())
        self.dataset_path = os.path.join(DATASET_DIR, self.id + ".h5")
        self.name = "COMB "
        for ds in datasets:
            self.name += ds.id + " "
        self.desc = self.name
        self.src = datasets[0].src  # we assume that only same product needs to be merged
        self.crs = datasets[0].crs
        self.cmap = datasets[0].cmap  # since same product, cmap would also be the same
        self.timeline = datasets[0].timeline  # we assume the two datasets having the same timeline
        self.options = {}
        with h5py.File(self.dataset_path, "w") as f:
            f.create_group("data")
            f.create_group("meta")

        # compute the new bbox
        self.bbox = datasets[0].bbox
        self.bbox_metre = datasets[0].bbox_metre
        for i in range(1, len(datasets)):
            self.bbox = [
                [
                    min(self.bbox[0][0], datasets[i].bbox[0][0]),  # lat_min
                    min(self.bbox[0][1], datasets[i].bbox[0][1])   # lon_min
                ], 
                [
                    max(self.bbox[1][0], datasets[i].bbox[1][0]),  # lat_max
                    max(self.bbox[1][1], datasets[i].bbox[1][1])   # lon_max
                ]
            ]
            self.bbox_metre = [
                [
                    min(self.bbox_metre[0][0], datasets[i].bbox_metre[0][0]),  # lat_min
                    min(self.bbox_metre[0][1], datasets[i].bbox_metre[0][1])   # lon_min
                ], 
                [
                    max(self.bbox_metre[1][0], datasets[i].bbox_metre[1][0]),  # lat_max
                    max(self.bbox_metre[1][1], datasets[i].bbox_metre[1][1])   # lon_max
                ]
            ]
        self.options["center"] = [
            (self.bbox[0][0] + self.bbox[1][0]) / 2,  # lat
            (self.bbox[0][1] + self.bbox[1][1]) / 2,  # lon
        ]

        # compute resolution of the new grid, with step size to be MERGE_STEP
        self.res = [
            int((self.bbox_metre[1][0] - self.bbox_metre[0][0]) / MERGE_STEP), 
            int((self.bbox_metre[1][1] - self.bbox_metre[0][1]) / MERGE_STEP), 
        ]
        
        # create the dataset file and write to the meta group
        with h5py.File(self.dataset_path, "r+") as f:
            f["meta"].attrs.create("id", self.id)
            f["meta"].attrs.create("name", self.name)
            f["meta"].attrs.create("desc", self.desc)
            f["meta"].attrs.create("src", self.src)
            f["meta"].attrs.create("crs", self.crs)
            f["meta"].attrs.create("res", self.res)
            f["meta"].attrs.create("timeline", self.timeline)
            f["meta"].attrs.create("options", json.dumps(self.options))
            f["meta"].attrs.create("cmap", str(self.cmap))
            f["meta"].attrs.create("bbox", self.bbox)
            f["meta"].attrs.create("bbox_metre", self.bbox_metre)

        # interpolate rasters, parallelize by (dataset, raster)
        print("Start interpolating......", end="", flush=True)
        pool = mp.Pool(mp.cpu_count()+2)
        jobs = []
        for ds in datasets:
            for t in self.timeline:
                job = pool.apply_async(
                    self.interpolate, 
                    (ds, t, self.bbox_metre, self.res)
                )
                jobs.append(job)
        for job in jobs:
            job.get()
        pool.close()
        pool.join()
        print("[Done]")
        
        # merge rasters, parallelize by raster, and write to the dataset file
        print("Start merging......", end="", flush=True)
        pool = mp.Pool(mp.cpu_count()+2)
        q = mp.Manager().Queue()
        watcher = pool.apply_async(self.write_merge_result, (q, ))
        jobs = []
        ids = []
        for ds in datasets:
            ids.append(ds.id) 
        for t in self.timeline:
            job = pool.apply_async(
                self.merge_rasters, 
                (ids, t, mode, q)
            )
            jobs.append(job)
        for job in jobs:
            job.get()
        q.put("kill")
        pool.close()
        pool.join()
        print("[Done]")
        
        # clean temps
        print("Cleaning temp files......", end="", flush=True)
        for f in os.listdir(TEMP_DIR):
            if not f.startswith('.'):
                os.remove(os.path.join(TEMP_DIR, f))
        print("[Done]")

        print("Merging completed!")
    
    @staticmethod
    def interpolate(dataset, raster_name, bbox_new, res_new):
        """
        interpolate data stored as (x, y, z) to the new grid with bbox and cell size indicated

        -parameters-
        raster_name[str]: indicate the raster to be interpolated
        bbox_new[list]: bbox of the target grid, [[lat_min, lon_min], [lat_max, lon_max]]
        lat_size, lon_size[float]: cell size of the target grid
        """
        # compute the coordinates and values of the original dataset
        x_step = (dataset.bbox_metre[1][1] - dataset.bbox_metre[0][1]) / dataset.res[1]
        y_step = (dataset.bbox_metre[1][0] - dataset.bbox_metre[0][0]) / dataset.res[0]
        x_min = dataset.bbox_metre[0][1] + 0.5 * x_step
        x_max = dataset.bbox_metre[1][1] - 0.5 * x_step
        y_min = dataset.bbox_metre[0][0] + 0.5 * y_step
        y_max = dataset.bbox_metre[1][0] - 0.5 * y_step
        x_range = np.linspace(x_min, x_max, dataset.res[1])
        y_range = np.linspace(y_min, y_max, dataset.res[0])
        y_range = np.flip(y_range)  # raster data stored upside down corresponding to the carte system
        x_grid, y_grid = np.meshgrid(x_range, y_range)
        with h5py.File(dataset.dataset_path, "r") as f:
            z = f["data"][raster_name][...]     
        values = z.flatten()
        coords = np.vstack((x_grid.ravel(), y_grid.ravel())).T

        # compute the x and y range of the target grid
        x_min_new = bbox_new[0][1]
        x_max_new = bbox_new[1][1]
        y_min_new = bbox_new[0][0]
        y_max_new = bbox_new[1][0]
        x_range_new = np.linspace(x_min_new, x_max_new, res_new[1])
        y_range_new = np.linspace(y_min_new, y_max_new, res_new[0])
        y_range_new = np.flip(y_range_new)
        x_grid_new, y_grid_new = np.meshgrid(x_range_new, y_range_new)

        # interpolate values to the new grid
        z_new = griddata(coords, values, (x_grid_new, y_grid_new), method="nearest")

        # write data to temp files
        temp_name = dataset.id + "_" + raster_name
        temp_path = os.path.join(TEMP_DIR, temp_name)
        np.savez_compressed(temp_path, data=z_new)

    @staticmethod
    def merge_rasters(ids, raster_name, mode, q):
        """
        merge the interpolated rasters into one
        
        -parameters-
        ids[list]: list of ids of input datasets
        raster_name[str]
        mode[str]: indicate method of merging
        q[mp.Manager.Queue]
        """
        temp_paths = []
        for ds_id in ids:
            temp_name = ds_id + "_" + raster_name + ".npz"
            temp_paths.append(
                os.path.join(TEMP_DIR, temp_name)
            )
        
        result = np.load(temp_paths[0])["data"]
        for i in range(1, len(temp_paths)):
            temp = np.load(temp_paths[i])["data"]
            if mode == "avg":
                result = np.nanmean([result, temp], axis=0)
            elif mode == "max":
                result = np.fmax(result, temp)
            elif mode == "min":
                result = np.fmin(result, temp)
        
        q.put((raster_name, result))

    def write_merge_result(self, q):
        """
        write merging result to dataset file
        """
        with h5py.File(self.dataset_path, "r+") as f:
            while True:
                m = q.get()
                if m == "kill":
                    break
                f["data"].create_dataset(
                    m[0], 
                    data=m[1], 
                    compression="gzip", 
                    compression_opts=9
                )