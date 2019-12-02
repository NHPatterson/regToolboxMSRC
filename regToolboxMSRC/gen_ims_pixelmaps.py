from regToolboxMSRC.utils.ims_utils import ImsPixelMaps
import SimpleITK as sitk
import os

if __name__ == "__main__":
    import yaml
    import sys

    with open(sys.argv[1]) as f:
        # use safe_load instead load
        dataMap = yaml.safe_load(f)

    ims_mapping = ImsPixelMaps(
        dataMap["IMS_data_fp"],
        dataMap["IMS_res"],
        dataMap["micro_res"],
        dataMap["image_padding"],
    )

    ims_mapping.generate_reg_mask(stamping=dataMap["stamping"])

    ims_mapping.generate_idx_mask()

    sitk.WriteImage(
        ims_mapping.IMS_reg_template,
        os.path.join(
            dataMap["wd"],
            dataMap["project_name"]
            + "_regTemplate_IMSres"
            + str(dataMap["IMS_res"])
            + "_MicroRes"
            + str(dataMap["micro_res"])
            + "_pad"
            + str(dataMap["image_padding"])
            + ".tif",
        ),
        True,
    )

    sitk.WriteImage(
        ims_mapping.IMS_indexed_mask,
        os.path.join(
            dataMap["wd"],
            dataMap["project_name"]
            + "_indexMask_IMSres"
            + str(dataMap["IMS_res"])
            + "_MicroRes"
            + str(dataMap["micro_res"])
            + "_pad"
            + str(dataMap["image_padding"])
            + ".mha",
        ),
        True,
    )

    ims_mapping.spots.to_csv(
        os.path.join(dataMap["wd"], dataMap["project_name"] + "_IMS_mapping_key.csv"),
        index=True,
        index_label="pixel_idx",
    )
