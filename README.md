# MeteoVis
A jupyter-based tool for visualizing and exploring meteorological and bioecological data hosted at UvA-TCE.

## Usage
Process files to dataset:
![Process files screen](readme_gifs/process_files.gif)

Visualize datasets:
![Visualize datasets screen](readme_gifs/visualize_datasets.gif)

Merging datasets:
![Merge datasets screen](readme_gifs/merge_datasets.gif)

Update datasets:
![Update datasets screen](readme_gifs/update_datasets.gif)

## Installation
Using Anaconda:

```shell
conda config --add channels conda-forge
conda config --set channel_priority strict
conda create -n <name-of-your-env> python=3.8  # optional
conda activate <name-of-your-env>
conda install -c jiqi meteovis
```
When installing into JupyterLab 1 or 2, you need to also install the labextensions:

```shell
jupyter labextension install @jupyter-widgets/jupyterlab-manager jupyter-leaflet @j123npm/qgrid2@1.1.4
```
For now, MeteoVis is only available on AMD64 Linux systems, with Python@3.8.