from distutils.core import setup

setup(
    name = 'MeteoVis',
    packages = ['MeteoVis'],
    version = '0.1.0',
    license='MIT',
    description = 'A jupyter-based tool for visualizing and exploring meteorological and bioecological data hosted at UvA-TCE.',
    author = '@jiqicn',
    author_email = 'qiji1988ben@gmail.com',
    url = 'https://github.com/user/reponame',
    download_url = 'https://github.com/jiqicn/meteovis',
    keywords = ['Visualization', 'Jupyter', 'Widgets', "GIS"],
    install_requires=[
        'ipywidgets>=7.6.0,<8',
        'ipyfilechooser>=0.6.0',
        'qgrid>=1.3.0', 
        'pandas>=1.3.0', 
        'h5py>=3.4.0', 
        'numpy>=1.21.0', 
        'wradlib>=1.11.0', 
    ],
    classifiers=[
        'Development Status :: 3 - Alpha', 
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)