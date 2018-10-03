# MSRC Registration Toolbox
This python toolbox performs registration between 2-D microscopy images from the same tissue section or serial sections in several ways to achieve imaging mass spectrometry (IMS) experimental goals.

This code supports the following works and enables others to perform the workflows outlined in the following works, please cite them if you use this toolbox:
* *Advanced Registration and Analysis of MALDI Imaging Mass Spectrometry Measurements through Autofluorescence Microscopy*, [10.1021/acs.analchem.8b02884](10.1021/acs.analchem.8b02884)

* *Next Generation Histology-directed Imaging Mass Spectrometry Driven by Autofluorescence Microscopy*, [10.1021/acs.analchem.8b02885](10.1021/acs.analchem.8b02885)

*N.B. As it stands this package is somewhat patchwork and can provide multipurpose outputs for downstream analysis in other software but does not do everything all in one (IMS data visualization & analysis).*


## Installation
We recommend using a virtual environment in the [Anaconda distribution of Python 3.6](https://www.anaconda.com/download/). We developed and tested using Python 3.6 but other versions of Python 3 may work as well.
```
conda create -n reg python=3.6 Anaconda
source activate reg #linux
activate reg #windows
## follow instructures below
```
1. Build [SimpleElastix](https://github.com/SuperElastix/SimpleElastix) from source. If using a virtual environment, make sure to compile against the Python binaries of your virtual environment. There are binaries available [here](https://sourceforge.net/projects/simpleelastix/) for Windows that should be compatible with everything in the toolbox but are not tested!
2. Conda install OpenCV (```conda install -c menpo opencv3 ```)
3. Use git to clone this repository ```git clone https://github.com/nhpatterson/regToolboxMSRC```
4. Install the regToolboxMSRC package by navigating to the directory of cloned repository in the terminal/command line and running ```python setup.py install```
5. If using Linux, you can run the GUI directly by running ```reg_tlbx_gui.py```
6. To run the GUI in windows, you can run ```python /path_to_gui/reg_tlbx_gui.py``` from the command line.


## Use cases
For a major overview of data formats, how to use the GUI, and other considerations please see [this manual.](https://github.com/nhpatterson/regToolboxMSRC/)

* Registration of microscopy data from the same tissue sections
  * Easily manage images with different size of field of view, resolution, etc. All generated files are named and time-stamped.

* Generate of IMS registration masks for explicit laser ablation to IMS pixel registration.

  * Generates necessary data for explicit mapping of IMS pixels to their ablation mark, allowing highly confident and verifiable registration between microscopy and IMS data.

* Extraction of overlapping IMS pixels determined by registration of high-resolution microscopy images linked to IMS
  * Linkage of pixels in microscopy space allows very accurate registration to determine spatial relations between serial section IMS datasets

  * Relations can be mined for correlation of mass spectral signal without resampling and interpolation of mass spectral signal ([example R Script](https://github.com/nhpatterson/regToolboxMSRC/) and functions using [*Cardinal*](https://cardinalmsi.org) are provided)

* Next generation histology directed workflows for Bruker MALDI imaging platforms
  * Support for exporting ImageJ rectangular and polygonal ROIs to bruker .xml format following registration or after direct annotation on AF images.

## How to use
1. Use the GUI in ```reg_tlbx_gui.py```

2. Use .yaml configuration files to run any of the GUI registration routines from terminal
  * ```python /regtoolboxMSRC/register_MSM.py MSM_config.yaml```

3. As a library to design custom workflows
  * Provides functions to managing images, image masks, ROIs, registration outputs in ```utils.flx_utils, utils.ims_utils & utils.reg_utils```
