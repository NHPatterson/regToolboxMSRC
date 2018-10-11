# -*- coding: utf-8 -*-
"""
@author: pattenh1
"""

import os
import numpy as np
import pandas as pd
import SimpleITK as sitk
import cv2
import sqlite3
from lxml.etree import iterparse


def imzml_coord_parser(filepath):
    """Extracts x y coordinates from imzml coordinates.
    It is a stripped out version from
    https://github.com/alexandrovteam/pyimzML
    Parameters
    ----------
    filepath : str
        .imzML filepath, must have .imzML extension.

    Returns
    -------
    numpy array
        numpy array of the coordinates for further processing

    """
    extension = os.path.splitext(filepath)[-1].lower()
    if extension == '.imzml':

        elements = iterparse(filepath)

        coordinates = []
        for event, element in elements:
            #print(elem.tag)
            if element.tag == '{http://psi.hupo.org/ms/mzml}spectrum':
                scan_elem = element.find('%sscanList/%sscan' %
                                         ('{http://psi.hupo.org/ms/mzml}',
                                          '{http://psi.hupo.org/ms/mzml}'))
                x = scan_elem.find(
                    '%scvParam[@accession="IMS:1000050"]' %
                    '{http://psi.hupo.org/ms/mzml}').attrib["value"]
                y = scan_elem.find(
                    '%scvParam[@accession="IMS:1000051"]' %
                    '{http://psi.hupo.org/ms/mzml}').attrib["value"]
                coordinates.append((int(x), int(y)))

        return np.array(coordinates)

    else:
        print(filepath + ' is not an .izmml')
        return


#get sqlite coordinates
def parse_sqlite_coordinates(filepath):
    """Short summary.

    Parameters
    ----------
    filepath : type
        Description of parameter `filepath`.

    Returns
    -------
    type
        Description of returned object.

    """
    sqlite_peaks = sqlite3.connect(filepath)
    coordinates = sqlite_peaks.cursor().execute(
        "select XIndexPos, YIndexPos from Spectra").fetchall()
    return np.array(coordinates)


def parse_bruker_spotlist(filepath):
    """Short summary.

    Parameters
    ----------
    filepath : type
        Description of parameter `filepath`.

    Returns
    -------
    type
        Description of returned object.

    """

    if os.path.splitext(filepath)[-1].lower() == '.csv':
        spotlist = pd.read_csv(filepath, sep=",", header=1)
        bruker_coord_str = spotlist['spot-name']

    if os.path.splitext(filepath)[-1].lower() == '.txt':
        spotlist = pd.read_csv(filepath, sep=" ", header=1)
        bruker_coord_str = spotlist['Y-pos']

    bruker_coord_str = bruker_coord_str.str.split('X', 2, expand=True)
    bruker_coord_str = bruker_coord_str[1]
    bruker_coord_str = bruker_coord_str.str.split('Y', 2, expand=True)

    return np.array(bruker_coord_str, dtype=np.int64)


def coordinates_to_pd(coordinates):
    """Short summary.

    Parameters
    ----------
    coordinates : type
        Description of parameter `coordinates`.

    Returns
    -------
    type
        Description of returned object.

    """
    coordinate_df = pd.DataFrame(coordinates, columns=['x', 'y'])

    coordinate_df['x_minimized'] = coordinate_df['x'] - (int(
        np.min(coordinate_df['x']))) + 1
    coordinate_df['y_minimized'] = coordinate_df['y'] - (int(
        np.min(coordinate_df['y']))) + 1

    coordinate_df = coordinate_df.sort_values(['y', 'x'])

    coordinate_df.reset_index(drop=True, inplace=True)
    coordinate_df.index += 1

    return (coordinate_df)


def gkern(kernlen, nsig):
    """Short summary.

    Parameters
    ----------
    kernlen : type
        Description of parameter `kernlen`.
    nsig : type
        Description of parameter `nsig`.

    Returns
    -------
    type
        Description of returned object.

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

        self.IMS_data_type = os.path.splitext(filepath)[-1]

        if self.IMS_data_type == '.csv' or self.IMS_data_type == '.txt':
            self.spots = parse_bruker_spotlist(self.filepath)

        if self.IMS_data_type.lower() == '.imzml':
            self.spots = imzml_coord_parser(self.filepath)

        if self.IMS_data_type == '.sqlite':
            self.spots = parse_sqlite_coordinates(self.filepath)

        self.spots = coordinates_to_pd(self.spots)

    def generate_reg_mask(self, stamping=True):
        """Short summary.

        Parameters
        ----------
        stamping : type
            Description of parameter `stamping`.

        Returns
        -------
        type
            Description of returned object.

        """
        IMS_mask = np.zeros((max(self.spots['y_minimized']),
                             max(self.spots['x_minimized'])))
        IMS_mask[np.array(self.spots['y_minimized']) - 1,
                 np.array(self.spots['x_minimized']) - 1] = 255

        IMS_mask = sitk.GetImageFromArray(IMS_mask)
        self.IMS_binary_mask = IMS_mask
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
            stamp_mat = np.tile(self.g_kernel,
                                (max(self.spots['y_minimized']),
                                 max(self.spots['x_minimized'])))
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
            self.IMS_reg_template = IMS_mask_upsampled
        else:
            IMS_mask_upsampled = sitk.Cast(IMS_mask_upsampled, sitk.sitkUInt8)
            self.IMS_reg_template = IMS_mask_upsampled

    def generate_idx_mask(self):
        IMS_mask_idx = np.zeros((max(self.spots['y_minimized']),
                                 max(self.spots['x_minimized'])),dtype=np.uint32)
        IMS_mask_idx[np.array(self.spots['y_minimized']) - 1,
                     np.array(self.spots['x_minimized']) - 1] = np.arange(
                         1,
                         len(np.array(self.spots['x_minimized'])) + 1, 1)
        IMS_mask_idx = sitk.GetImageFromArray(IMS_mask_idx)
        self.idx_map_ims_scale = IMS_mask_idx
        IMS_mask_idx_upsampled = sitk.Expand(
            IMS_mask_idx, (int(self.scale_factor), int(self.scale_factor)),
            sitk.sitkNearestNeighbor)
        IMS_mask_idx_upsampled = sitk.ConstantPad(
            IMS_mask_idx_upsampled, (self.img_padding, self.img_padding),
            (self.img_padding, self.img_padding))
        self.IMS_indexed_mask = IMS_mask_idx_upsampled
