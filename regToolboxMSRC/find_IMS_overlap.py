import os
import time
import datetime
from regToolboxMSRC.utils.reg_utils import (
    transform_image,
    RegImage_load,
    parameterFile_load,
)
import SimpleITK as sitk
import pandas as pd
import numpy as np


def IMS_ablation_overlap(
    source_ims_fp,
    target_ims_fp,
    source_ims_res,
    target_ims_res,
    source_key_fp,
    target_key_fp,
    init_tform_fp,
    nl_tform_fp=None,
    ims_res=20,
    img_res=2,
    project_name="",
    wd="",
):

    # timestamp and output dir
    ts = datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d_%H_%M_%S_")
    os.chdir(wd)

    source_ims = RegImage_load(source_ims_fp, source_ims_res)
    if source_ims.image.GetPixelIDTypeAsString() != "32-bit unsigned integer":
        print("Error: source image should have PixelType : 32-bit unsigned integer")
        return

    init_tform = parameterFile_load(init_tform_fp)
    # make sure the appropriate resampling order is used to avoid interpolation artifacts as pixel indices
    init_tform["FinalBSplineInterpolationOrder"] = ("0",)
    source_ims.image = transform_image(source_ims.image, init_tform)

    if nl_tform_fp is not None:
        nl_tform = parameterFile_load(nl_tform_fp)
        # make sure the appropriate resampling order is used to avoid interpolation artifacts as pixel indices
        nl_tform["FinalBSplineInterpolationOrder"] = ("0",)

        source_ims.image = transform_image(source_ims.image, nl_tform)

    source_ims.image = sitk.Cast(source_ims.image, sitk.sitkUInt32)

    source_ims.image = sitk.GetArrayFromImage(source_ims.image)

    target_ims = RegImage_load(target_ims_fp, target_ims_res)
    if target_ims.image.GetPixelIDTypeAsString() != "32-bit unsigned integer":
        print("Error: target image should have PixelType : 32-bit unsigned integer")
        return

    target_ims.image = sitk.GetArrayFromImage(target_ims.image)

    # determine denominator to convert integer index to fraction
    denominator = 10 ** len(str(np.max(target_ims.image).astype(int)))
    # convert one array to fraction

    target_ims.image = target_ims.image / denominator

    # sum array where fractional component is index from one and integer component is index of other
    source_target_ims = source_ims.image + target_ims.image

    # find uniques
    unique, counts = np.unique(source_target_ims, return_counts=True)

    # return the integer indices after fractioning
    unique_source = np.floor(unique).astype(int)
    unique_target = unique - np.floor(unique)
    unique_target = np.round(unique_target * denominator, 0).astype(int)

    # pixel-size
    pixel_size = (np.array(ims_res) / np.array(img_res)) ** 2

    # get matches as dataframe
    # use key to search indices against x,y coordinates
    source_key = pd.read_csv(source_key_fp)
    target_key = pd.read_csv(target_key_fp)

    df = pd.DataFrame(
        {"source_idx": unique_source, "target_idx": unique_target, "percentage": counts}
    )

    # counts for each overlap / number of imaging pixels in one ablation point
    df["percentage"] = df["percentage"] / pixel_size.astype(int)

    # remove garbage from df
    df = df.loc[~(df == 0).any(axis=1)]

    df = pd.merge(df, source_key, left_on="source_idx", right_on="pixel_idx")
    df = df.drop(columns=["pixel_idx"])
    df = df.rename(
        index=str,
        columns={
            "x": "x_source",
            "y": "y_source",
            "x_minimized": "x_minimized_source",
            "y_minimized": "y_minimized_source",
        },
    )

    df = pd.merge(df, target_key, left_on="target_idx", right_on="pixel_idx")
    df = df.drop(columns=["pixel_idx"])

    df = df.rename(
        index=str,
        columns={
            "x": "x_target",
            "y": "y_target",
            "x_minimized": "x_minimized_target",
            "y_minimized": "y_minimized_target",
        },
    )

    df.to_csv(ts + project_name + "overlaps.csv")

    return df


if __name__ == "__main__":
    import yaml
    import sys

    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)

    IMS_ablation_overlap(
        dataMap["source_ims_fp"],
        dataMap["target_ims_fp"],
        dataMap["source_ims_res"],
        dataMap["target_ims_res"],
        dataMap["source_key_fp"],
        dataMap["target_key_fp"],
        dataMap["init_tform_fp"],
        dataMap["nl_tform_fp"],
        dataMap["ims_res"],
        dataMap["img_res"],
        dataMap["project_name"],
        dataMap["wd"],
    )
