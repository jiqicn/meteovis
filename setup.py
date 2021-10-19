from setuptools import setup

setup(
    name = 'meteovis',
    packages = ['meteovis'],
    version = '0.1.0',
    license='MIT',
    description = 'A jupyter-based tool for visualizing and exploring meteorological and bioecological data hosted at UvA-TCE.',
    author = '@jiqicn',
    author_email = 'qiji1988ben@gmail.com',
    url = 'https://github.com/jiqicn/meteovis',
    download_url = 'https://github.com/jiqicn/meteovis',
    keywords = ['Visualization', 'Jupyter', 'Widgets', "GIS"],
    install_requires=[
        'ipywidgets',
        'ipyfilechooser',
        'ipyleaflet'
        'qgrid', 
        'pandas', 
        'h5py', 
        'numpy', 
        'wradlib', 
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable', 
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
    ],
)