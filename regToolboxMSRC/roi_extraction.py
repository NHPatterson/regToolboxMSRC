#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: pattenh1
"""
import os
from regToolboxMSRC.utils.flx_utils import ROIhandler


def extract_ROI_coordinates(index_image_fp,
                            annotation_fp,
                            IMS_key_fp,
                            project_name,
                            ims_res=50,
                            img_res=1,
                            wd=''):

    os.chdir(wd)
    ROIs = ROIhandler(index_image_fp, 1, is_mask=False)
    ROIs.get_polygons_ijroi(annotation_fp)
    ROIs.get_index_and_overlap(
        index_image_fp,
        ims_res,
        img_res,
        use_key=True,
        key_filepath=IMS_key_fp)
    try:
        ROIs.rois_ims_indexed.to_csv(project_name + '_ROI_key.csv', index=False)
    except:
        print('No ROIs found, none saved')
        return


if __name__ == '__main__':
    import yaml
    import sys
    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)

    extract_ROI_coordinates(dataMap['index_image_fp'],
                            dataMap['annotation_fp'], dataMap['IMS_key_fp'],
                            dataMap['project_name'], dataMap['ims_res'],
                            dataMap['img_res'])
