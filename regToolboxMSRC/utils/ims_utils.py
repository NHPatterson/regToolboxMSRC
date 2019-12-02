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
import tempfile


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
    if extension == ".imzml":

        elements = iterparse(filepath)

        coordinates = []
        for event, element in elements:
            # print(elem.tag)
            if element.tag == "{http://psi.hupo.org/ms/mzml}spectrum":
                scan_elem = element.find(
                    "%sscanList/%sscan"
                    % ("{http://psi.hupo.org/ms/mzml}", "{http://psi.hupo.org/ms/mzml}")
                )
                x = scan_elem.find(
                    '%scvParam[@accession="IMS:1000050"]'
                    % "{http://psi.hupo.org/ms/mzml}"
                ).attrib["value"]
                y = scan_elem.find(
                    '%scvParam[@accession="IMS:1000051"]'
                    % "{http://psi.hupo.org/ms/mzml}"
                ).attrib["value"]
                coordinates.append((int(x), int(y)))

        return np.array(coordinates)

    else:
        print(filepath + " is not an .izmml")
        return


# get sqlite coordinates
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
    coordinates = (
        sqlite_peaks.cursor()
        .execute("select XIndexPos, YIndexPos from Spectra")
        .fetchall()
    )
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

    if os.path.splitext(filepath)[-1].lower() == ".csv":
        spotlist = pd.read_csv(filepath, sep=",", header=1)
        bruker_coord_str = spotlist["spot-name"]

    if os.path.splitext(filepath)[-1].lower() == ".txt":
        spotlist = pd.read_csv(filepath, sep=" ", header=1)
        bruker_coord_str = spotlist["Y-pos"]

    bruker_coord_str = bruker_coord_str.str.split("X", 2, expand=True)
    bruker_coord_str = bruker_coord_str[1]
    bruker_coord_str = bruker_coord_str.str.split("Y", 2, expand=True)

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
    coordinate_df = pd.DataFrame(coordinates, columns=["x", "y"])

    coordinate_df["x_minimized"] = (
        coordinate_df["x"] - (int(np.min(coordinate_df["x"]))) + 1
    )
    coordinate_df["y_minimized"] = (
        coordinate_df["y"] - (int(np.min(coordinate_df["y"]))) + 1
    )

    coordinate_df = coordinate_df.sort_values(["y", "x"])

    coordinate_df.reset_index(drop=True, inplace=True)
    coordinate_df.index += 1

    return coordinate_df


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

    kernel = np.exp(-(xx ** 2 + yy ** 2) / (2.0 * nsig ** 2))
    kernel = kernel / np.sum(kernel)
    cmax = np.max(kernel)
    cmin = np.min(kernel)

    cscale = cmax - cmin
    scale = float(255 - 0) / cscale
    kernel = (kernel * 1.0 - cmin) * scale + 0.4999
    kernel[kernel > 255] = 255
    kernel[kernel < 0] = 0
    kernel = kernel.astype(np.uint8)

    return kernel


class ImsPixelMaps(object):
    def __init__(
        self,
        filepath,
        IMS_res,
        micro_res,
        padding=20,
        pad_x_left=0,
        pad_y_top=0,
        pad_x_right=0,
        pad_y_bot=0,
        x_offset=0,
        y_offset=0,
    ):
        self.type = "IMS pixel map"

        self.filepath = filepath
        self.micro_res = micro_res
        self.scale_factor = IMS_res / micro_res

        self.img_padding = int(padding * self.scale_factor)

        self.pad_x_left = int(pad_x_left / self.micro_res)
        self.pad_y_top = int(pad_y_top / self.micro_res)
        self.pad_x_right = int(pad_x_right / self.micro_res)
        self.pad_y_bot = int(pad_y_bot / self.micro_res)

        self.IMS_data_type = os.path.splitext(filepath)[-1]

        if self.IMS_data_type == ".csv" or self.IMS_data_type == ".txt":
            self.spots = parse_bruker_spotlist(self.filepath)
            # self.spots = self.spotToPandas()

        if self.IMS_data_type.lower() == ".imzml":
            self.spots = imzml_coord_parser(self.filepath)
            self.spots = self.spotToPandas()

        if self.IMS_data_type == ".sqlite":
            self.spots = parse_sqlite_coordinates(self.filepath)
            self.spots = self.spotToPandas()

        if self.IMS_data_type == ".npy":
            self.spots = np.load(self.filepath)
            if x_offset != 0 or y_offset != 0:
                self.spots[:, 0] = self.spots[:, 0] + x_offset
                self.spots[:, 1] = self.spots[:, 1] + y_offset

    def spotToPandas(self):
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
        IMS_mask = np.zeros(
            (max(self.spots["y_minimized"]), max(self.spots["x_minimized"])),
            dtype=np.uint8,
        )
        IMS_mask[
            np.array(self.spots["y_minimized"]) - 1,
            np.array(self.spots["x_minimized"]) - 1,
        ] = 1

        IMS_mask = sitk.GetImageFromArray(IMS_mask)

        self.IMS_binary_mask = IMS_mask * 255
        IMS_mask_upsampled = sitk.Expand(
            IMS_mask,
            (int(self.scale_factor), int(self.scale_factor)),
            sitk.sitkNearestNeighbor,
        )

        IMS_mask_upsampled.SetSpacing((self.micro_res, self.micro_res))

        if (
            self.pad_x_left > 0
            or self.pad_y_top > 0
            or self.pad_x_right > 0
            or self.pad_y_bot > 0
        ):

            IMS_mask_upsampled = sitk.ConstantPad(
                IMS_mask_upsampled,
                (self.pad_x_left, self.pad_y_top),
                (self.pad_x_right, self.pad_y_bot),
            )

        elif self.img_padding > 0:

            IMS_mask_upsampled = sitk.ConstantPad(
                IMS_mask_upsampled,
                (self.img_padding, self.img_padding),
                (self.img_padding, self.img_padding),
            )

        if self.scale_factor % 2 == 0:
            self.g_kernel = gkern(
                int(self.scale_factor - 1), nsig=(self.scale_factor - 1) / 5
            )
            self.g_kernel = cv2.resize(
                self.g_kernel, (int(self.scale_factor), int(self.scale_factor))
            )
        else:
            self.g_kernel = gkern(self.scale_factor, nsig=self.scale_factor / 5)

        if stamping is True:

            stamp_mat = np.tile(
                self.g_kernel,
                (max(self.spots["y_minimized"]), max(self.spots["x_minimized"])),
            )

            stamp_mat = sitk.GetImageFromArray(stamp_mat)
            print(stamp_mat.GetPixelIDTypeAsString())

            if (
                self.pad_x_left > 0
                or self.pad_y_top > 0
                or self.pad_x_right > 0
                or self.pad_y_bot > 0
            ):

                stamp_mat = sitk.ConstantPad(
                    stamp_mat,
                    (self.pad_x_left, self.pad_y_top),
                    (self.pad_x_right, self.pad_y_bot),
                )

            elif self.img_padding > 0:
                stamp_mat = sitk.ConstantPad(
                    stamp_mat,
                    (self.img_padding, self.img_padding),
                    (self.img_padding, self.img_padding),
                )

            npa = np.multiply(
                sitk.GetArrayFromImage(stamp_mat),
                sitk.GetArrayFromImage(IMS_mask_upsampled),
            )

            IMS_mask_upsampled = sitk.GetImageFromArray(npa)

            del stamp_mat
            self.IMS_reg_template = IMS_mask_upsampled
        else:
            self.IMS_reg_template = IMS_mask_upsampled

    def generate_idx_mask(self):
        IMS_mask_idx = np.zeros(
            (max(self.spots["y_minimized"]), max(self.spots["x_minimized"])),
            dtype=np.uint32,
        )
        IMS_mask_idx[
            np.array(self.spots["y_minimized"]) - 1,
            np.array(self.spots["x_minimized"]) - 1,
        ] = np.arange(1, len(np.array(self.spots["x_minimized"])) + 1, 1)
        IMS_mask_idx = sitk.GetImageFromArray(IMS_mask_idx)
        self.idx_map_ims_scale = IMS_mask_idx
        IMS_mask_idx_upsampled = sitk.Expand(
            IMS_mask_idx,
            (int(self.scale_factor), int(self.scale_factor)),
            sitk.sitkNearestNeighbor,
        )

        if (
            self.pad_x_left > 0
            or self.pad_y_top > 0
            or self.pad_x_right > 0
            or self.pad_y_bot > 0
        ):

            IMS_mask_idx_upsampled = sitk.ConstantPad(
                IMS_mask_idx_upsampled,
                (self.pad_x_left, self.pad_y_top),
                (self.pad_x_right, self.pad_y_bot),
            )

        elif self.img_padding > 0:
            IMS_mask_idx_upsampled = sitk.ConstantPad(
                IMS_mask_idx_upsampled,
                (self.img_padding, self.img_padding),
                (self.img_padding, self.img_padding),
            )

        self.IMS_indexed_mask = IMS_mask_idx_upsampled


class PointSetElx:
    def __init__(self, ptset_fp, pt_type, **kwargs):

        default_attr = dict(
            image_xy=(10000, 10000),
            image_spacing=(1, 1),
            ds_factor=1,
            micro_res=None,
            ims_res=None,
            padding=None,
        )
        default_attr.update(kwargs)

        self.__dict__.update((k, v) for k, v in default_attr.items())
        self.ptset_fp = ptset_fp
        self.pt_type = pt_type

        # instintaniate template transformations
        self.template_tforms()

        if self.pt_type == "PIMS":

            self.ptset_df = pd.read_csv(self.ptset_fp)
            ptset_df_cntrpts = self.ptset_df["Center"].str.split(",", n=1, expand=True)
            self.ptset_df["x_"] = ptset_df_cntrpts[0].astype(np.float32)
            self.ptset_df["y_"] = ptset_df_cntrpts[1].astype(np.float32)
            if self.ds_factor > 1 and isinstance(self.ds_factor, int):
                self.ptset_df["x_"] = self.ptset_df["x_"] / self.ds_factor
                self.ptset_df["y_"] = self.ptset_df["y_"] / self.ds_factor

            self.image_xy = self.image_xy
            self.image_xy_init = self.image_xy

        if self.pt_type == "IMS":

            pmap = ImsPixelMaps(
                self.ptset_fp, self.ims_res, self.micro_res, padding=self.padding
            )

            pmap.spots["x_micro"] = (pmap.spots["x_minimized"] - 1) * pmap.scale_factor
            pmap.spots["y_micro"] = (pmap.spots["y_minimized"] - 1) * pmap.scale_factor
            pmap.spots["x_micro"] = pmap.spots["x_micro"] + pmap.img_padding
            pmap.spots["y_micro"] = pmap.spots["y_micro"] + pmap.img_padding

            image_xy = (
                np.max(pmap.spots["x_micro"] + pmap.scale_factor) + pmap.img_padding,
                np.max(pmap.spots["y_micro"] + pmap.scale_factor) + pmap.img_padding,
            )

            ims_pixs_centroids = []
            for index, row in pmap.spots.iterrows():
                ims_pixs_centroids.append(
                    (
                        row["x_micro"] + 0.5 * pmap.scale_factor,
                        row["y_micro"] + 0.5 * pmap.scale_factor,
                    )
                )

            pmap.spots = pmap.spots.reset_index()

            self.xy_micro_centroids = pd.DataFrame(
                ims_pixs_centroids, columns=["x_", "y_"]
            )

            pmap.spots = pmap.spots.join(self.xy_micro_centroids)

            self.ptset_df = pmap.spots
            self.image_xy = image_xy
            self.image_xy_init = image_xy

        if self.pt_type == "QP":
            table = pd.read_table(self.ptset_fp, sep="#", header=None)

            newdata = table[2].str.split("_", expand=True)
            x = newdata[0]
            y = newdata[1]

            x = x.str.strip("[];")
            y = y.str.strip("[];")

            dfs = []
            for index, row in table.iterrows():

                xarray = np.array(x[index].split(","), dtype=np.float32)
                yarray = np.array(y[index].split(","), dtype=np.float32)
                pg_type = row[0]
                pg_name = row[1]
                dfs.append(
                    pd.DataFrame(
                        {
                            "pg_type": pg_type,
                            "pg_name": pg_name,
                            "x_": xarray,
                            "y_": yarray,
                        }
                    )
                )

            self.ptset_df = pd.concat(dfs)
            self.ptset_df.reset_index(inplace=True)
            self.image_xy = self.image_xy
            self.image_xy_init = self.image_xy

        if self.pt_type == "np":
            self.ptset_df = pd.DataFrame(
                {"x_": self.ptset_fp[:, 0], "y_": self.ptset_fp[:, 1]}
            )
            self.image_xy = self.image_xy
            self.image_xy_init = self.image_xy

        if self.pt_type == "df":
            self.ptset_df = pd.read_csv(self.ptset_fp, index_col=0)
            self.ptset_df = self.ptset_df.reset_index()
            self.image_xy = self.image_xy
            self.image_xy_init = self.image_xy

    def reset_points(self):

        self.__init__(
            self.ptset_fp,
            pt_type=self.pt_type,
            image_xy=self.image_xy_init,
            image_spacing=self.image_spacing,
            ds_factor=self.ds_factor,
            micro_res=self.micro_res,
            ims_res=self.ims_res,
            padding=self.padding,
        )

    def rot90(self, n_times=1):

        if n_times < 1 or n_times > 3:
            raise ValueError(
                (
                    "n_times must be equal to 1 (90 degrees clockwise),"
                    "2 (180 degrees clockwise), or 3 (270 degrees clockwise)"
                )
            )

        if n_times % 2 == 0:
            self.rig_tform["CenterOfRotationPoint"] = [
                str((self.image_xy[1] / 2)),
                str(self.image_xy[0] / 2),
            ]
            xydim = list(self.image_xy)
            self.rig_tform["Size"] = [str(i) for i in xydim]
            tform_params = [
                1.5708 * n_times,
                2 * ((xydim[0] - xydim[1]) / 2),
                2 * (xydim[1] - xydim[0]) / 2,
            ]

        else:
            self.rig_tform["CenterOfRotationPoint"] = [
                str(int(self.image_xy[0] / 2)),
                str(int(self.image_xy[1] / 2)),
            ]
            xydim = list(self.image_xy)

            self.rig_tform["Size"] = [str(i) for i in xydim]

            tform_params = [
                1.5708 * n_times,
                (xydim[1] - xydim[0]) / 2,
                (xydim[0] - xydim[1]) / 2,
            ]

            self.image_xy = self.image_xy[::-1]

        self.rig_tform["TransformParameters"] = [str(i) for i in tform_params]
        self.transform_pointset(self.rig_tform)

    def transform_pointset(self, tform):
        xscale = float(tform["Spacing"][0])
        yscale = float(tform["Spacing"][1])
        with tempfile.TemporaryDirectory() as dirpath:
            fp = os.path.join(dirpath, "elxpts.pts")

            npts = len(self.ptset_df)

            pts_f = open(fp, "w")
            pts_f.write("point\n")
            pts_f.write(str(npts) + "\n")
            if self.image_spacing[0] != 1:

                for index, row in self.ptset_df.iterrows():
                    pts_f.write(
                        "{} {}\n".format(row["x_"] * xscale, row["y_"] * yscale)
                    )

            else:
                for index, row in self.ptset_df.iterrows():
                    pts_f.write("{} {}\n".format(row["x_"], row["y_"]))
            pts_f.close()

            tfx = sitk.TransformixImageFilter()
            tfx.SetTransformParameterMap(tform)
            tfx.SetFixedPointSetFileName(fp)
            tfx.SetOutputDirectory(dirpath)
            tfx.LogToFileOff()
            tfx.Execute()

            output_dir = dirpath
            output_pts = pd.read_table(
                os.path.join(output_dir, "outputpoints.txt"),
                header=None,
                names=[
                    "point",
                    "index",
                    "InputIndex",
                    "InputPoint",
                    "OutputIndex",
                    "OutputPoint",
                    "Deformation",
                ],
            )
            self.output_pts = output_pts
            output_pts = output_pts["OutputPoint"].str.split(" ", expand=True)
            output_pts = output_pts.drop([0, 1, 2, 3, 6], axis=1)
            output_pts.columns = ["x_tformed", "y_tformed"]

            self.ptset_df["x_"] = output_pts["x_tformed"]
            self.ptset_df["y_"] = output_pts["y_tformed"]

            # reset points specified in physical coords to index coords
            self.ptset_df["x_"] = self.ptset_df["x_"].astype("float32") * (1 / xscale)
            self.ptset_df["y_"] = self.ptset_df["y_"].astype("float32") * (1 / xscale)

    def flip_points(self, direction="horizontal"):

        self.aff_tform["CenterOfRotationPoint"] = [
            str(int(self.image_xy[0] / 2)),
            str(int(self.image_xy[1] / 2)),
        ]
        xydim = list(self.image_xy)
        self.aff_tform["Size"] = [str(i) for i in xydim]

        if direction == "horizontal":
            tform_params = [-1, 0, 0, 1, 0, 0]
        if direction == "vertical":
            tform_params = [1, 0, 0, -1, 0, 0]

        self.aff_tform["TransformParameters"] = [str(i) for i in tform_params]
        self.transform_pointset(self.aff_tform)

    def use_elx_tform(self, elx_tform):
        self.transform_pointset(elx_tform)

    def use_elx_tform_mask(self, elx_tform):
        with tempfile.TemporaryDirectory() as dirpath:
            tfx = sitk.TransformixImageFilter()
            elx_tform["ResampleInterpolator"] = ["FinalNearestNeighborInterpolator"]
            tfx.SetMovingImage(self.ptset_mask)
            tfx.SetTransformParameterMap(elx_tform)
            tfx.SetOutputDirectory(dirpath)
            tfx.LogToFileOff()
            self.tformed_mask = tfx.Execute()
            self.mask_to_pts()

    def mask_to_pts(self):

        pmap = sitk.Cast(self.tformed_mask, sitk.sitkUInt32)
        pmap.SetSpacing((1, 1))

        lab_stats = sitk.LabelShapeStatisticsImageFilter()
        lab_stats.SetBackgroundValue(0)
        lab_stats.Execute(pmap)

        centroids = []
        for label in lab_stats.GetLabels():
            centroids.append(lab_stats.GetCentroid(label))

        centroids = np.asarray(centroids)

        mask_pt_centroids = pd.DataFrame(
            {
                "pix_idx": lab_stats.GetLabels(),
                "x_tformed": centroids[:, 0],
                "y_tformed": centroids[:, 1],
            }
        )

        self.ptset_df["x_"] = mask_pt_centroids["x_tformed"]
        self.ptset_df["y_"] = mask_pt_centroids["y_tformed"]

    def write_ij_csv(self, ij_csv_fp):
        out_pts_df = self.ptset_df[["x_", "y_"]]
        out_pts_df.to_csv(ij_csv_fp)

    def write_df_csv(self, csv_fp):
        self.ptset_df.to_csv(csv_fp, index=False)

    def ptset_to_mask(self, image_xy, pt_width=20, binary=False, spacing=1):

        if len(self.ptset_df) < 256:
            pt_dtype = sitk.sitkUInt8
        else:
            pt_dtype = sitk.sitkUInt32

        mask_template = sitk.Image(image_xy[0], image_xy[1], pt_dtype)

        for index, row in self.ptset_df.iterrows():
            xmin = int(row["x_"] - pt_width)
            xmax = int(row["x_"] + pt_width)
            ymin = int(row["y_"] - pt_width)
            ymax = int(row["y_"] + pt_width)
            for x in range(xmin, xmax):
                for y in range(ymin, ymax):
                    if binary is False:
                        mask_template[x, y] = index + 1
                    else:
                        mask_template[x, y] = 255

        self.ptset_mask = mask_template
        self.ptset_mask.SetSpacing((spacing, spacing))

    def write_qp_txt(self, qp_txt_fp):
        if self.pt_type == "QP":

            gb = self.ptset_df.groupby(self.ptset_df["pg_name"])

            pts_f = open(qp_txt_fp, "w")

            for name, group in gb:

                pg_type = group["pg_type"].iloc[0]
                pg_name = name

                xarray = group["x_"].astype(str).str.cat(sep=",")
                yarray = group["y_"].astype(str).str.cat(sep=",")

                string = "{}#{}#{}_{}\n".format(pg_type, pg_name, xarray, yarray)
                pts_f.write(string)
            pts_f.close()

        else:
            print("not a QP pts file")

    def template_tforms(self):
        aff_tform_params = dict(
            {
                "Transform": ["AffineTransform"],
                "NumberOfParameters": ["6"],
                "TransformParameters": ["1", "0", "0", "1", "0", "0"],
                "InitialTransformParametersFileName": ["NoInitialTransform"],
                "HowToCombineTransforms": ["Compose"],
                "FixedImageDimension": ["2"],
                "MovingImageDimension": ["2"],
                "FixedInternalImagePixelType": ["float"],
                "MovingInternalImagePixelType": ["float"],
                "Size": ["0", "0"],
                "Index": ["0", "0"],
                "Spacing": ["1.0000", "1.0000"],
                "Origin": ["0.0000", "0.0000"],
                "Direction": [
                    "1.0000000000",
                    "0.0000000000",
                    "0.0000000000",
                    "1.0000000000",
                ],
                "UseDirectionCosines": ["true"],
                "CenterOfRotationPoint": ["0", "0"],
                "ResampleInterpolator": ["FinalLinearInterpolator"],
                "Resampler": ["DefaultResampler"],
                "DefaultPixelValue": ["0.000000"],
                "ResultImageFormat": ["mha"],
                "ResultImagePixelType": ["float"],
                "CompressResultImage": ["true"],
            }
        )
        self.aff_tform = sitk.ParameterMap()

        for k, v in aff_tform_params.items():
            self.aff_tform[k] = v

        rig_tform_params = dict(
            {
                "Transform": ["EulerTransform"],
                "NumberOfParameters": ["3"],
                "TransformParameters": ["0", "0", "0"],
                "InitialTransformParametersFileName": ["NoInitialTransform"],
                "HowToCombineTransforms": ["Compose"],
                "FixedImageDimension": ["2"],
                "MovingImageDimension": ["2"],
                "FixedInternalImagePixelType": ["float"],
                "MovingInternalImagePixelType": ["float"],
                "Size": ["0", "0"],
                "Index": ["0", "0"],
                "Spacing": ["1.0000", "1.0000"],
                "Origin": ["0.0000", "0.0000"],
                "Direction": [
                    "1.0000000000",
                    "0.0000000000",
                    "0.0000000000",
                    "1.0000000000",
                ],
                "UseDirectionCosines": ["true"],
                "CenterOfRotationPoint": ["0", "0"],
                "ResampleInterpolator": ["FinalLinearInterpolator"],
                "Resampler": ["DefaultResampler"],
                "DefaultPixelValue": ["0.000000"],
                "ResultImageFormat": ["mha"],
                "ResultImagePixelType": ["float"],
                "CompressResultImage": ["true"],
            }
        )
        self.rig_tform = sitk.ParameterMap()

        for k, v in rig_tform_params.items():
            self.rig_tform[k] = v
