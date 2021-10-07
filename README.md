# meteovis
A jupyter-based tool for visualizing and exploring meteorological and bioecological data hosted at UvA-TCE.

## Install
It's highly recommand to use anaconda/miniconda to install meteovis and manage dependencies. Especially, anaconda provides a quite convenient way of installing wradlib with GDAL and libgdal, which is usually difficult to do with pypi. 

First, you need to create a new conda environment and install python 3.8:

```console
conda create -n <name-of-your-env> python=3.8
```

Replace ```<name-of-your-env>``` with any name you want. After that, activate your environment:

```console
conda activate <name-of-your-env>
```

Install meteovis with the following command:

```console
conda install -c jiqi meteovis
```