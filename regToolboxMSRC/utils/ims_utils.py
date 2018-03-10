# -*- coding: utf-8 -*-
"""
Created on Thu Nov 23 13:14:46 2017

@author: pattenh1
"""

import SimpleITK as sitk
import numpy as np
import pandas as pd
import cv2
import os.path
import sys
import sqlite3

try:
    from lxml.etree import iterparse
except ImportError:
    try:
        from xml.etree.cElementTree import iterparse
    except ImportError:
        from xml.etree.ElementTree import iterparse


#this is a totally ripped and stripped version from : https://github.com/alexandrovteam/pyimzML
#gets coordinates from imzml
class ImzMLParser:
    """
    Parser for imzML 1.1.0 files (see specification here:
    http://imzml.org/download/imzml/specifications_imzML1.1.0_RC1.pdf).
    Iteratively reads the .imzML file into memory while pruning the per-spectrum metadata (everything in
    <spectrumList> elements) during initialization. Returns a spectrum upon calling getspectrum(i). The binary file
    is read in every call of getspectrum(i). Use enumerate(parser.coordinates) to get all coordinates with their
    respective index. Coordinates are always 3-dimensional. If the third spatial dimension is not present in
    the data, it will be set to zero.
    *pyimzML* has limited support for the metadata embedded in the imzML file. For some general metadata, you can use
    the parser's ``ìmzmldict`` attribute. You can find the exact list of supported metadata in the documentation of the
    ``__readimzmlmeta`` method.
    """

    def __init__(self, filename):
        """
        Opens the two files corresponding to the file name, reads the entire .imzML
        file and extracts required attributes. Does not read any binary data, yet.
        :param filename:
            name of the XML file. Must end with .imzML. Binary data file must be named equally but ending with .ibd
        """
        # custom map sizes are currently not supported, therefore mapsize is hardcoded.
        #mapsize = 0
        # ElementTree requires the schema location for finding tags (why?) but
        # fails to read it from the root element. As this should be identical
        # for all imzML files, it is hard-coded here and prepended before every tag
        self.sl = "{http://psi.hupo.org/ms/mzml}"
        # maps each imzML number format to its struct equivalent
        self.precisionDict = {
            "32-bit float": 'f',
            "64-bit float": 'd',
            "32-bit integer": 'i',
            "64-bit integer": 'l'
        }
        # maps each number format character to its amount of bytes used
        self.sizeDict = {'f': 4, 'd': 8, 'i': 4, 'l': 8}
        self.filename = filename
        #        self.mzOffsets = []
        #        self.intensityOffsets = []
        #        self.mzLengths = []
        #        self.intensityLengths = []
        # list of all (x,y,z) coordinates as tuples.
        self.coordinates = []
        self.root = None
        self.mzGroupId = self.intGroupId = self.mzPrecision = self.intensityPrecision = None
        self.__iter_read_spectrum_meta()
        # name of the binary file
        #bin_filename = self.filename[:-5] + "ibd"
        #self.m = open(bin_filename, "rb")

        # Dict for basic imzML metadata other than those required for reading
        # spectra. See method __readimzmlmeta()
        #self.imzmldict = self.__readimzmlmeta()
        #self.imzmldict['max count of pixels z'] = np.asarray(self.coordinates)[:,2].max()

    # system method for use of 'with ... as'
#    def __enter__(self):
#        return self

# system method for use of 'with ... as'
#    def __exit__(self, exc_t, exc_v, trace):
#        self.m.close()

    def __iter_read_spectrum_meta(self):
        """
        This method should only be called by __init__. Reads the data formats, coordinates and offsets from
        the .imzML file and initializes the respective attributes. While traversing the XML tree, the per-spectrum
        metadata is pruned, i.e. the <spectrumList> element(s) are left behind empty.
        Supported accession values for the number formats: "MS:1000521", "MS:1000523", "IMS:1000141" or
        "IMS:1000142". The string values are "32-bit float", "64-bit float", "32-bit integer", "64-bit integer".
        """
        mz_group = int_group = None
        slist = None
        elem_iterator = iterparse(self.filename, events=("start", "end"))

        if sys.version_info > (3, ):
            _, self.root = next(elem_iterator)
        else:
            _, self.root = elem_iterator.next()

        for event, elem in elem_iterator:
            if elem.tag == self.sl + "spectrumList" and event == "start":
                slist = elem
            elif elem.tag == self.sl + "spectrum" and event == "end":
                self.__process_spectrum(elem)
                slist.remove(elem)
            elif elem.tag == self.sl + "referenceableParamGroup" and event == "end":
                for param in elem:
                    if param.attrib["name"] == "m/z array":
                        self.mzGroupId = elem.attrib['id']
                        mz_group = elem
                    elif param.attrib["name"] == "intensity array":
                        self.intGroupId = elem.attrib['id']
                        int_group = elem
        #self.__assign_precision(int_group, mz_group)
        #self.__fix_offsets()


#    def __fix_offsets(self):
#        # clean up the mess after morons who use signed 32-bit where unsigned 64-bit is appropriate
#        def fix(array):
#            fixed = []
#            delta = 0
#            prev_value = float('nan')
#            for value in array:
#                if value < 0 and prev_value >= 0:
#                    delta += 2**32
#                fixed.append(value + delta)
#                prev_value = value
#            return fixed
#
#        self.mzOffsets = fix(self.mzOffsets)
#        self.intensityOffsets = fix(self.intensityOffsets)

#    def __assign_precision(self, int_group, mz_group):
#        valid_accession_strings = ("MS:1000521", "MS:1000523", "IMS:1000141", "IMS:1000142")
#        mz_precision = int_precision = None
#        for s in valid_accession_strings:
#            param = mz_group.find('%scvParam[@accession="%s"]' % (self.sl, s))
#            if param is not None:
#                mz_precision = self.precisionDict[param.attrib["name"]]
#                break
#        for s in valid_accession_strings:
#            param = int_group.find('%scvParam[@accession="%s"]' % (self.sl, s))
#            if param is not None:
#                int_precision = self.precisionDict[param.attrib["name"]]
#                break
#        if (mz_precision is None) or (int_precision is None):
#            raise RuntimeError("Unsupported number format: mz = %s, int = %s" % (mz_precision, int_precision))
#        self.mzPrecision, self.intensityPrecision = mz_precision, int_precision

    def __process_spectrum(self, elem):
        #        arrlistelem = elem.find('%sbinaryDataArrayList' % self.sl)
        #        elist = list(arrlistelem)
        #        elist_sorted = [None, None]
        #        for e in elist:
        #            ref = e.find('%sreferenceableParamGroupRef' % self.sl).attrib["ref"]
        #            if ref == self.mzGroupId:
        #                elist_sorted[0] = e
        #            elif ref == self.intGroupId:
        #                elist_sorted[1] = e
        #        mz_offset_elem = elist_sorted[0].find('%scvParam[@accession="IMS:1000102"]' % self.sl)
        #        self.mzOffsets.append(int(mz_offset_elem.attrib["value"]))
        #        mz_length_elem = elist_sorted[0].find('%scvParam[@accession="IMS:1000103"]' % self.sl)
        #        self.mzLengths.append(int(mz_length_elem.attrib["value"]))
        #        intensity_offset_elem = elist_sorted[1].find('%scvParam[@accession="IMS:1000102"]' % self.sl)
        #        self.intensityOffsets.append(int(intensity_offset_elem.attrib["value"]))
        #        intensity_length_elem = elist_sorted[1].find('%scvParam[@accession="IMS:1000103"]' % self.sl)
        #        self.intensityLengths.append(int(intensity_length_elem.attrib["value"]))
        scan_elem = elem.find('%sscanList/%sscan' % (self.sl, self.sl))
        x = scan_elem.find(
            '%scvParam[@accession="IMS:1000050"]' % self.sl).attrib["value"]
        y = scan_elem.find(
            '%scvParam[@accession="IMS:1000051"]' % self.sl).attrib["value"]
        try:
            #z = scan_elem.find('%scvParam[@accession="IMS:1000052"]' % self.sl).attrib["value"]
            self.coordinates.append((int(x), int(y)))
        except AttributeError:
            self.coordinates.append((int(x), int(y)))


def parse_imzml_coordinates(filepath):
    parsed = ImzMLParser(filepath)
    sname = pd.DataFrame(np.array(parsed.coordinates), columns=['x', 'y'])
    sname = sname.astype(int)
    sname['x'] = sname['x'] - (int(np.min(sname['x'])))
    sname['y'] = sname['y'] - (int(np.min(sname['y'])))
    sname = sname.sort_values(['y', 'x'])
    return sname


#get sqlite coordinates
def parse_sqlite_coordinates(filepath):
    sqlite_peaks = sqlite3.connect(filepath)
    coordinates = sqlite_peaks.cursor().execute(
        "select XIndexPos, YIndexPos from Spectra").fetchall()
    sname = pd.DataFrame(np.array(coordinates), columns=['x', 'y'])
    sname = sname.astype(int)
    #sname.rename(index=str, columns={'x':'original_x','y':'original_y'})
    sname['x'] = sname['x'] - (int(np.min(sname['x'])))
    sname['y'] = sname['y'] - (int(np.min(sname['y'])))
    sname = sname.sort_values(['y', 'x'])
    #sname['index'] = np.arange(1,len(np.array(sname['x']))+1,1)

    return sname


#def parse_sqlite_coordinates(filepath):
#        sqlite_peaks = sqlite3.connect(filepath)
#        coordinates = sqlite_peaks.cursor().execute("select XIndexPos, YIndexPos from Spectra").fetchall()
#        sname = pd.DataFrame(np.array(coordinates), columns = ['x','y'])
#        sname = sname.astype(int)
#        sname.rename(index=str, columns={'x':'original_x','y':'original_y'})
#        sname['x'] = sname['original_x'] - (int(np.min(sname['original_x'])))
#        sname['y'] = sname['original_y'] - (int(np.min(sname['original_y'])))
#        sname = sname.sort_values(['y','x'])
#        sname['index'] = np.arange(1,len(np.array(sname['x']))+1,1)
#
#        return sname


def parse_bruker_spotlist(spotlist_fp):
    if os.path.splitext(spotlist_fp)[1] == '.csv':
        spotlist = pd.read_csv(spotlist_fp, sep=",", header=1)
        sname = spotlist['spot-name']

    if os.path.splitext(spotlist_fp)[1] == '.txt':
        spotlist = pd.read_csv(spotlist_fp, sep=" ", header=1)
        sname = spotlist['Y-pos']

    #sname = spotlist['spot-name']
    sname = sname.str.split('X', 2, expand=True)
    sname = sname[1]
    sname = sname.str.split('Y', 2, expand=True)
    sname.rename(columns={0: 'x', 1: 'y'}, inplace=True)
    sname = sname.astype(int)

    sname['x'] = sname['x'] - (int(np.min(sname['x'])))
    sname['y'] = sname['y'] - (int(np.min(sname['y'])))
    sname = sname.sort_values(['y', 'x'])

    return sname


def gkern(kernlen, nsig):
    """
    creates gaussian kernel with side length of kernlen and a sigma of nsigma
    """

    ax = np.arange(-kernlen // 2 + 1, kernlen // 2 + 1)

    xx, yy = np.meshgrid(ax, ax)

    kernel = np.exp(-(xx**2 + yy**2) / (2. * nsig**2))

    return kernel / np.sum(kernel)


class ImsPixelMaps(object):
    def __init__(self, filepath, IMS_res, micro_res, padding=20):
        self.type = 'IMS pixel map'
        self.filepath = filepath

        self.scale_factor = IMS_res / micro_res
        self.img_padding = int(padding * self.scale_factor)

        self.ims_data_type = os.path.splitext(filepath)[1]

        if self.ims_data_type == '.csv' or self.ims_data_type == '.txt':
            self.spots = parse_bruker_spotlist(filepath)

        if self.ims_data_type.lower() == '.imzml':
            self.spots = parse_imzml_coordinates(filepath)

        if self.ims_data_type == '.sqlite':
            self.spots = parse_sqlite_coordinates(filepath)

    def IMS_reg_mask(self, stamping=True):
        IMS_mask = np.zeros((max(self.spots['y']) + 1,
                             max(self.spots['x']) + 1))
        IMS_mask[np.array(self.spots['y']), np.array(self.spots['x'])] = 255

        IMS_mask = sitk.GetImageFromArray(IMS_mask)
        self.ims_binary_mask = IMS_mask
        IMS_mask_upsampled = sitk.Expand(
            IMS_mask, (int(self.scale_factor), int(self.scale_factor)),
            sitk.sitkNearestNeighbor)
        IMS_mask_upsampled = sitk.ConstantPad(
            IMS_mask_upsampled, (self.img_padding, self.img_padding),
            (self.img_padding, self.img_padding))

        if self.scale_factor % 2 == 0:
            self.g_kernel = gkern(
                int(self.scale_factor - 1), nsig=(self.scale_factor - 1) / 5)
            self.g_kernel = cv2.resize(
                self.g_kernel,
                (int(self.scale_factor), int(self.scale_factor)))
        else:
            self.g_kernel = gkern(
                self.scale_factor, nsig=self.scale_factor / 5)

        if stamping == True:
            stamp_mat = np.tile(
                self.g_kernel,
                (max(self.spots['y']) + 1, max(self.spots['x']) + 1))
            stamp_mat = sitk.GetImageFromArray(stamp_mat)
            stamp_mat = sitk.ConstantPad(stamp_mat,
                                         (self.img_padding, self.img_padding),
                                         (self.img_padding, self.img_padding))
            IMS_mask_upsampled = sitk.GetImageFromArray(
                sitk.GetArrayFromImage(stamp_mat) *
                sitk.GetArrayFromImage(IMS_mask_upsampled))
            del stamp_mat
            IMS_mask_upsampled = sitk.RescaleIntensity(IMS_mask_upsampled, 0,
                                                       255)
            IMS_mask_upsampled = sitk.Cast(IMS_mask_upsampled, sitk.sitkUInt8)
            self.IMS_registration_mask = IMS_mask_upsampled
        else:
            IMS_mask_upsampled = sitk.Cast(IMS_mask_upsampled, sitk.sitkUInt8)
            self.IMS_registration_mask = IMS_mask_upsampled

    def IMS_idxed_mask(self):
        IMS_mask_idx = np.zeros((max(self.spots['y']) + 1,
                                 max(self.spots['x']) + 1))
        IMS_mask_idx[np.array(self.spots['y']),
                     np.array(self.spots['x'])] = np.arange(
                         1,
                         len(np.array(self.spots['x'])) + 1, 1)
        IMS_mask_idx = sitk.GetImageFromArray(IMS_mask_idx)
        IMS_mask_idx = sitk.Cast(IMS_mask_idx, sitk.sitkUInt32)
        self.ims_idxed_mask = IMS_mask_idx
        IMS_mask_idx_upsampled = sitk.Expand(
            IMS_mask_idx, (int(self.scale_factor), int(self.scale_factor)),
            sitk.sitkNearestNeighbor)
        IMS_mask_idx_upsampled = sitk.ConstantPad(
            IMS_mask_idx_upsampled, (self.img_padding, self.img_padding),
            (self.img_padding, self.img_padding))
        self.IMS_indexed_mask = IMS_mask_idx_upsampled


##testing:
#sl_pmap = ImsPixelMaps('D:/20171127_malaria_data/IMS_data/Imzmls/20171128_muLiv_malaria_HE_targ_lesions_FI.imzML', 20, 1, 20)
#sl_pmap.IMS_reg_mask(stamping=False)
#sitk.WriteImage(sl_pmap.IMS_registration_mask, "imzml_nostamptest.tif",True)
#sl_pmap.IMS_reg_mask(stamping=True)
#sitk.WriteImage(sl_pmap.IMS_registration_mask, "imzml_stamptest.tif",True)
#sl_pmap.IMS_idxed_mask()
#sitk.WriteImage(sl_pmap.IMS_indexed_mask, "imzml_idxedtest.mha",True)

#filepath = 'D:/rb_lip_repro.d/peaks.sqlite'
#parsed = parse_sqlite_coordinates(filepath)
#parsed.rename(index=str, columns={'x':'original_x','y':'original_y'})
#sl_pmap = ImsPixelMaps(filepath , 100, 2, 20)
#sl_pmap.IMS_reg_mask(stamping=False)
#sitk.WriteImage(sl_pmap.IMS_registration_mask, "sqlite_nostamptest.tif",True)
#sl_pmap.IMS_reg_mask(stamping=True)
#sitk.WriteImage(sl_pmap.IMS_registration_mask, "sqlite_stamptest.tif",True)
#sl_pmap.IMS_idxed_mask()
#sitk.WriteImage(sl_pmap.IMS_indexed_mask, "sqlite_idxedtest.mha",True)
