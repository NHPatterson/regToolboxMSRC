# MSRC Registration Toolbox
This python toolbox performs registration between 2-D microscopy images from the same tissue section or serial sections in several ways to match imaging mass spectrometry experimental goals (IMS). Use cases are described near the bottom.

*N.B. As it stands this package is somewhat patchwork and can provide multipurpose outputs for downstream analysis in other software but does not do everything all in one (IMS data visualization & analysis).*

## Installation
We recommend using a virtual environment in the Anaconda distribution of Python 3.6.4.
```
conda create -n reg python=3.6 Anaconda
source activate reg #linux
activate reg #windows
## follow instructures below
```
1. Build [SimpleElastix](https://github.com/SuperElastix/SimpleElastix) from source. If using a virtual environment, make sure to compile against the Python binaries of your virtual environment. There are binaries available at [...](...) for windows that should be compatible with everything in the toolbox.
2. Conda install OpenCV (```conda install```)
3. Use git to clone this repository ```git clone ...```
4. Install the regToolboxMSRC package by navigating to the cloned repository in the terminal and running ```python setup.py install``` in the command line
5. If using Linux, you can run the GUI directly by running ```reg_tlbx_gui.py```
6. To run the GUI in windows, you can run ```....``` from the command line.
7.

## Use cases
* Registration of microscopy data from the same tissue sections
  * Easily manage images with different size of field of view, resolution, etc. All generated files are named and time-stamped.

* Generate of IMS registration masks for explicit laser ablation to IMS pixel registration.

  * Generates necessary data for explicit mapping of IMS pixels to their ablation mark, allowing highly confident and verifiable registration between microscopy and IMS data.

* Extraction of overlapping IMS pixels determined by registration of high-resolution microscopy images linked to IMS
  * Linkage of pixels in microscopy space allows very accurate registration to determine spatial relations between serial section IMS datasets

  * Relations can be mined for correlation of mass spectral signal without resampling and interpolation of mass spectral signal (example R Scripts and functions using [*Cardinal*](https://cardinalmsi.org) are provided)

* Next generation histology directed workflows for Bruker MALDI imaging platforms
  * Support for exporting ImageJ rectangular and polygonal ROIs to bruker .xml format following registration or after direct annotation on AF images.

## How to use
1. Use the GUI in ```reg_tlbx_gui.py```

2. Use .yaml configuration files to run any of the GUI routines from terminal
  * ```python /regtoolboxMSRC/register_MSM.py MSM_config.yaml```

3. As a library to design custom workflows
  * Provides functions to managing images, image masks, ROIs, registration outputs in ```utils.flx_utils, utils.ims_utils & utils.reg_utils```
