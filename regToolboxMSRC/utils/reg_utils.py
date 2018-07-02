# -*- coding: utf-8 -*-
"""
@author: pattenh1
"""

import numpy as np
import cv2
import os
import SimpleITK as sitk
#import pandas as pd
import time
import datetime
import xml.etree.ElementTree as ET
import xml.dom.minidom
import pkg_resources


class RegImage(object):
    '''
        Container class for image meta data and processing between ITK and cv2

    '''

    def __init__(self, filepath, im_format, img_res=1, load_image=True):
        '''
        Container class for image meta data and processing between ITK and cv2
            :param filepath: filepath to the image
            :type filepath: str

            :param im_format: 'sitk' - SimpleITK format or 'np' - numpy (cv2)
            :type im_format: str

            :param im_res: pixel spacing of image
            :type im_res: float

        '''
        self.type = 'Registration Image Container'
        self.filepath = filepath
        self.im_format = im_format
        self.spacing = float(img_res)

        if load_image == True:
            try:
                image = sitk.ReadImage(self.filepath)
                self.image_xy_dim = image.GetSize()[0:2]
            except:
                print('Error: image type not recognized')
                return

            self.image = self.set_img_type(image, self.im_format)

    def get_image_from_memory(self, image):
        if isinstance(image, sitk.Image):
            self.image = image
            self.image_xy_dim = self.image.GetSize()[0:2]
            self.image = self.set_img_type(self.image, 'sitk')
        else:
            print('use SimpleITK images to load from memory')

    def set_img_type(self, image, im_format):
        """Short summary.

        Parameters
        ----------
        image : numpy array or SimpleITK.Image()
            Loaded image for registration
        im_format : str
            'sitk' or 'np' for SimpleITK or Numpy as type.

        Returns
        -------
        self.image or self.mask
            image or mask for registration in desired format in memory

        """
        if im_format == 'np':
            image = sitk.GetArrayFromImage(image)
            return image
        if im_format == 'sitk':
            if len(image.GetSpacing()) == 3:
                image.SetSpacing((self.spacing, self.spacing, float(1)))
            else:
                image.SetSpacing((self.spacing, self.spacing))
            return image

    def load_mask(self, filepath, im_format):
        """
        Loads binary mask for registration.
        Parameters
        ----------
        filepath : str
            filepath to 8-bit mask with one ROI
        im_format : str
            'sitk' or 'np' for SimpleITK or Numpy as type.

        Returns
        -------
        self.mask
            mask for registration in desired format in memory

        """
        self.mask_filepath = filepath
        self.mask_im_format = im_format

        try:
            image = sitk.ReadImage(self.mask_filepath)
            self.mask_xy_dim = image.GetSize()[0:2]
            self.mask = self.set_img_type(image, self.mask_im_format)
        except:
            print('Error: image type not recognized')

    def get_mask_bounding_box(self):
        """Calculates bounding box of the mask and returns a python dictionary
        with the minimum x and y point as well as box width and height for
        later slicing.
        Returns
        -------
        dict
            returns mask bounding box as dict

        """
        try:
            self.mask
            if self.mask_xy_dim == self.image_xy_dim:
                x, y, w, h = self.calculate_bounding_box()
                self.mask_bounding_box = {}
                self.mask_bounding_box.update({
                    'min_x': x,
                    'min_y': y,
                    'bb_width': w,
                    'bb_height': h,
                })
            else:
                print('Error: Mask and image dimensions do not match')
        except AttributeError:
            print('Error: no mask has been loaded')

    def crop_to_bounding_box(self):
        try:
            self.mask_bounding_box
            self.image = self.image[
                self.mask_bounding_box['min_x']:self.mask_bounding_box['min_x']
                + self.mask_bounding_box['bb_width'], self.mask_bounding_box[
                    'min_y']:self.mask_bounding_box['min_y'] +
                self.mask_bounding_box['bb_height']]
            self.mask = self.mask[
                self.mask_bounding_box['min_x']:self.mask_bounding_box['min_x']
                + self.mask_bounding_box['bb_width'], self.mask_bounding_box[
                    'min_y']:self.mask_bounding_box['min_y'] +
                self.mask_bounding_box['bb_height']]

            self.image.SetOrigin((0, 0))
            self.mask.SetOrigin((0, 0))
            self.type = self.type + '-Bounding Box Cropped'

        except AttributeError:
            print('Error: no bounding box extents found')

    def calculate_bounding_box(self):
        '''
            Uses sitk to get bounding box, assumes image is an uint8 mask with only 1 polygonal label.
            Returns top-left x,y pixel coordinates and the width and height of bounding box.
        '''
        #in case the image is np array
        if isinstance(self.mask, sitk.Image) == False:
            mask = sitk.GetImageFromArray(self.mask)
        else:
            mask = self.mask
        cc = sitk.ConnectedComponent(mask)
        lab_stats = sitk.LabelStatisticsImageFilter()
        lab_stats.Execute(cc, cc)
        bb = lab_stats.GetBoundingBox(1)
        x, y, w, h = bb[0], bb[2], bb[1] - bb[0], bb[3] - bb[2]
        print('bounding box:', x, y, w, h)
        return x, y, w, h

    def to_greyscale(self):
        '''
        Converts RGB registration image to greyscale using cv2. (sitk images will eventually be converted using ITK...)
        '''
        if self.im_format == 'sitk':
            if self.image.GetNumberOfComponentsPerPixel() == 3:
                spacing = self.image.GetSpacing()
                image = sitk.GetArrayFromImage(self.image)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                image = sitk.GetImageFromArray(image)
                image.SetSpacing(spacing)
            else:
                raise ValueError('Channel depth != 3, image is not RGB type')

        if self.im_format == 'np':
            if self.image.shape == 3 and self.image.shape[2] == 3:
                image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            else:
                raise ValueError('Channel depth != 3, image is not RGB type')

        self.image = image
        self.type = self.type + '-Greyscaled'

    def compress_AF_channels(self, compression):
        '''
        This converts multi 2D layer images like multichannel fluorescence images to a single layer by summing, taking the mean or max of the layer.
        The final image will be rescaled to unsigned 8-bit.

        :param compression: 'sum', 'mean', or 'max'.
        '''
        if self.im_format == 'sitk':
            if self.image.GetDepth() > 1:
                image = sitk.GetArrayFromImage(self.image)

                if compression == 'sum':
                    image = np.sum(image, 0)
                    #print(image.dtype)
                    #image = cast_8bit_np(image)

                if compression == 'mean':
                    image = np.mean(image, 0)
                    #print(image.dtype)

                if compression == 'max':
                    image = np.max(image, 0)
                    #print(image.dtype)
                    #image = cast_8bit_np(image)

                self.image = sitk.GetImageFromArray(image)
                self.image = sitk.RescaleIntensity(self.image, 0, 255)
                self.image = sitk.Cast(self.image, sitk.sitkUInt8)
                #self.image.SetSpacing(self.spacing)
                self.image.SetSpacing((self.spacing, self.spacing))

                self.type = self.type + '-AF channels compressed'
            else:
                raise ValueError('Only one layer, image is not multichannel')

        if self.im_format == 'np':
            if len(self.image.shape) == 3 and self.image.shape[0] > 1:
                image = self.image

                if compression == 'sum':
                    image = image.sum(axis=0)
                if compression == 'mean':
                    image = image.mean(axis=0)
                if compression == 'max':
                    image = image.max(axis=0)

                #image = cast_8bit_np(image)
                self.image = image
                self.type = self.type + '-AF channels compressed'
            else:
                raise ValueError('Only one layer, image is not multichannel')

    def invert_intensity(self):
        '''
        This will invert the intensity scale of a greyscale registration image.
        This is useful with histological images where the background is 'whitish.'

        '''
        if self.im_format == 'sitk':
            #use sitk filters instead of CV2 conversion
            image = sitk.InvertIntensity(self.image)

            #img_bu = self.image
            #image = sitk.GetArrayFromImage(self.image)
            #image = cv2.bitwise_not(image)
            #image = sitk.GetImageFromArray(image)

            # image.CopyInformation(img_bu)

        if self.im_format == 'np':
            image = cv2.bitwise_not(self.image)

        self.image = image
        self.type = self.type + '-image intensity inverted'

    def flip_type(self):
        '''
        This is a convenience function that flips an image between cv2 and SimpleITK formats.
        '''
        if self.im_format == 'sitk':
            self.image = sitk.GetArrayFromImage(self.image)
            self.im_format = 'np'

        else:
            self.image = sitk.GetImageFromArray(self.image)
            self.im_format = 'sitk'
            self.image.SetSpacing((self.spacing, self.spacing))


class parameter_files(object):
    '''
        Class to load SimpleITK parameters from file
    '''

    def __init__(self):
        resource_package = 'regToolboxMSRC'

        self.testing = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'testing.txt'))))
        self.rigid = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'rigid.txt'))))
        self.scaled_rigid = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'scaled_rigid.txt'))))
        self.affine = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'affine.txt'))))
        self.nl = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'nl.txt'))))
        self.correction = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'fi_correction.txt'))))
        self.affine_test = sitk.ReadParameterFile(
            pkg_resources.resource_filename(resource_package, '/'.join(
                ('parameter_files', 'affine_test.txt'))))


def get_mask_bb(mask_fp):
    '''
        Uses sitk to get bounding box after reading image from file, assumes image is an uint8 mask.
        Returns top-left x,y pixel coordinates and the width and height of bounding box.

        :param mask_fp: File path to the mask image
    '''
    mask = sitk.ReadImage(mask_fp)
    mask = sitk.ConnectedComponent(mask)
    lab_stats = sitk.LabelStatisticsImageFilter()
    lab_stats.Execute(mask, mask)
    bb = lab_stats.GetBoundingBox(1)
    x, y, w, h = bb[0], bb[2], bb[1] - bb[0], bb[3] - bb[2]
    print('bounding box:', x, y, w, h)
    return x, y, w, h


def register_elx_(source,
                  target,
                  param,
                  source_mask=None,
                  target_mask=None,
                  output_dir="transformations",
                  output_fn="myreg.txt",
                  return_image=False,
                  logging=True):
    '''
    Utility function to register 2D images and save their results in a user named subfolder and transformation text file.

    :param source: SimpleITK image set as source image. Can optionally pass sitk.ReadImage(source_img_fp) to load image from file. Warning that usually this function is accompanied using the 'RegImage' class where image spacing is set

    :param target: SimpleITK image set as target image. Can optionally pass sitk.ReadImage(target_img_fp) to load image from file. Warning that usually this function is accompanied using the 'RegImage' class where image spacing is set

    :param param: Elastix paramter file loaded into SWIG. Can optionally pass sitk.ReadParameterFile(parameter_fp) to load text parameter from file. See http://elastix.isi.uu.nl/ for example parameter files

    :param source_mask: Filepath to source image (a binary mask) or the source image itself. Function will type check the image.

    :param target_mask:
        Filepath to target mask image (a binary mask) or the SimpleITK target mask image itself.
        Function will type check the image.

    :param source_mask:
        Filepath to target mask image (a binary mask) or the SimpleITK target mask image itself.
        Function will type check the image.

    :param output_dir:
        String used to create a folder in the current working directory to store registration outputs (iteration information and transformation parameter file)

    :param output_fn:
        String used to name transformation file in the output_fn directory

    :param logging:
        Boolean, whether SimpleElastix should log to console. Note that this logging doesn't work in IPython notebooks

    :param bounding_box:
        Currently experimental that addresses masking in SimpleElastix by cropping images to the bounding box of their mask

    :return: Transformation file and optionally the registered source image
    :return type: SimpleITK parameter map and SimpleITK image

    '''
    try:
        selx = sitk.SimpleElastix()
    except:
        selx = sitk.ElastixImageFilter()

    if logging == True:
        selx.LogToConsoleOn()

    param_selx = param

    #turns off returning the image in the paramter file
    if return_image == False:
        param_selx['WriteResultImage'] = ('false', )

    selx.SetParameterMap(param_selx)

    #set masks if used
    if source_mask == None:
        pass
    else:
        if isinstance(source_mask, sitk.Image) == True:
            selx.SetMovingMask(source_mask)

        else:
            source_mask = sitk.ReadImage(source_mask)
            source_mask.SetSpacing(source.GetSpacing())
            selx.SetsourceMask(source_mask)

    if target_mask == None:
        pass
    else:
        if isinstance(target_mask, sitk.Image) == True:
            selx.SetTargetMask(target_mask)

        else:
            target_mask = sitk.ReadImage(target_mask)
            target_mask.SetSpacing(target.GetSpacing())
            selx.SetsourceMask(target_mask)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    selx.SetOutputDirectory(os.path.join(os.getcwd(), output_dir))

    selx.SetMovingImage(source)
    selx.SetFixedImage(target)

    selx.LogToFileOn()

    #execute registration:
    if return_image == True:
        transformed_image = selx.Execute()
    else:
        selx.Execute()

    os.rename(
        os.path.join(os.getcwd(), output_dir, 'TransformParameters.0.txt'),
        os.path.join(os.getcwd(), output_dir, output_fn))

    transformationMap = selx.GetTransformParameterMap()

    if return_image == True:
        return transformationMap, transformed_image

    else:
        return transformationMap


def register_elx_n(source,
                   target,
                   param,
                   output_dir="transformations",
                   output_fn="myreg.txt",
                   return_image=False,
                   intermediate_transform=False,
                   logging=True):
    '''
    Utility function to register 2D images and save their results in a user named subfolder and transformation text file.

    :param source: SimpleITK image set as source image. Can optionally pass sitk.ReadImage(source_img_fp) to load image from file. Warning that usually this function is accompanied using the 'RegImage' class where image spacing is set

    :param target: SimpleITK image set as target image. Can optionally pass sitk.ReadImage(target_img_fp) to load image from file. Warning that usually this function is accompanied using the 'RegImage' class where image spacing is set

    :param param: Elastix paramter file loaded into SWIG. Can optionally pass sitk.ReadParameterFile(parameter_fp) to load text parameter from file. See http://elastix.isi.uu.nl/ for example parameter files

    :param source_mask: Filepath to source image (a binary mask) or the source image itself. Function will type check the image.

    :param target_mask:
        Filepath to target mask image (a binary mask) or the SimpleITK target mask image itself.
        Function will type check the image.

    :param source_mask:
        Filepath to target mask image (a binary mask) or the SimpleITK target mask image itself.
        Function will type check the image.

    :param output_dir:
        String used to create a folder in the current working directory to store registration outputs (iteration information and transformation parameter file)

    :param output_fn:
        String used to name transformation file in the output_fn directory

    :param logging:
        Boolean, whether SimpleElastix should log to console. Note that this logging doesn't work in IPython notebooks

    :param bounding_box:
        Currently experimental that addresses masking in SimpleElastix by cropping images to the bounding box of their mask

    :return: Transformation file and optionally the registered source image
    :return type: SimpleITK parameter map and SimpleITK image

    '''
    try:
        selx = sitk.SimpleElastix()
    except:
        selx = sitk.ElastixImageFilter()

    #gotta fix this element
    if str(type(source)) != str(
            '<class \'regToolboxMSRC.utils.reg_utils.RegImage\'>'):
        print('Error: source is not of an object of type RegImage')
        return

    if str(type(target)) != str(
            '<class \'regToolboxMSRC.utils.reg_utils.RegImage\'>'):
        print('Error: source is not of an object of type RegImage')
        return

    if logging == True:
        selx.LogToConsoleOn()

    param_selx = param

    #turns off returning the image in the paramter file
    if return_image == False:
        param_selx['WriteResultImage'] = ('false', )

    selx.SetParameterMap(param_selx)

    #set masks if used
    try:
        source.mask
        if isinstance(source.mask, sitk.Image) == True:
            selx.SetMovingMask(source.mask)

        else:
            print('Error: Source mask could not be set')
    except AttributeError:
        print('No moving mask found')

    try:
        target.mask
        if isinstance(target.mask, sitk.Image) == True:
            selx.SetFixedMask(target.mask)

        else:
            print('Error: Target mask could not be set')
    except AttributeError:
        print('No fixed mask found')

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    selx.SetOutputDirectory(os.path.join(os.getcwd(), output_dir))

    selx.SetMovingImage(source.image)
    selx.SetFixedImage(target.image)

    selx.LogToFileOn()

    #execute registration:
    if return_image == True:
        transformed_image = selx.Execute()
    else:
        selx.Execute()

    #os.rename(
    #    os.path.join(os.getcwd(), output_dir, 'TransformParameters.0.txt'),
    #    os.path.join(os.getcwd(), output_dir, output_fn + '.txt'))

    transformationMap = selx.GetTransformParameterMap()[0]
    transformationMap['OriginalSizeMoving'] = [
        str(source.image_xy_dim[0]),
        str(source.image_xy_dim[1])
    ]
    transformationMap['OriginalSizeFixed'] = [
        str(target.image_xy_dim[0]),
        str(target.image_xy_dim[1])
    ]

    transformationMap['BoundingBoxMoving'] = ['0', '0', '0', '0']
    transformationMap['BoundingBoxFixed'] = ['0', '0', '0', '0']

    if hasattr(source, 'mask_bounding_box'):
        transformationMap['BoundingBoxMoving'] = [
            str(source.mask_bounding_box['min_x']),
            str(source.mask_bounding_box['min_y']),
            str(source.mask_bounding_box['bb_width']),
            str(source.mask_bounding_box['bb_height'])
        ]

    if hasattr(target, 'mask_bounding_box'):
        transformationMap['BoundingBoxFixed'] = [
            str(target.mask_bounding_box['min_x']),
            str(target.mask_bounding_box['min_y']),
            str(target.mask_bounding_box['bb_width']),
            str(target.mask_bounding_box['bb_height'])
        ]

    if intermediate_transform == True:
        transformationMap['IntermediateTransform'] = ['true']
    else:
        transformationMap['IntermediateTransform'] = ['false']

    sitk.WriteParameterFile(transformationMap,
                            os.path.join(os.getcwd(), output_dir,
                                         output_fn + '.txt'))

    if return_image == True:
        return transformationMap, transformed_image

    else:
        return transformationMap


def paste_to_original_dim(transformed_image, target_x, target_y,
                          final_size_2D):
    '''
        Experimental support function to used 'crops' of singular masks rather than using Elastix masking (which seems not to work...)
        Returns image in coordinate original coordinate space

        :param target_x:
            top-left x coordinate of mask's bounding box

        :param target_y:
            top-left y coordinate of mask's bounding box

        :param final_size_2D:
            m x n dimensions of target image from registration


    '''

    if transformed_image.GetNumberOfComponentsPerPixel() == 3:
        print('RGB_image')
        placeholder = sitk.Image([final_size_2D[0], final_size_2D[1]],
                                 transformed_image.GetPixelIDValue(), 3)
        placeholder.GetSize()
        transformed_image = sitk.Paste(
            placeholder,
            transformed_image,
            transformed_image.GetSize(),
            destinationIndex=[target_x, target_y])

    elif transformed_image.GetDepth() > 1:
        print('multichannel_image')

        placeholder = sitk.Image(
            [final_size_2D[0], final_size_2D[1],
             transformed_image.GetDepth()],
            transformed_image.GetPixelIDValue())
        #print('image made')
        #print(str(placeholder.GetSize()))
        #print(str(transformed_image.GetSize()))
        transformed_image = sitk.Paste(
            placeholder,
            transformed_image,
            transformed_image.GetSize(),
            destinationIndex=[target_x, target_y, 0])

    elif transformed_image.GetDepth(
    ) < 1 and transformed_image.GetNumberOfComponentsPerPixel() == 1:
        print('singlechannel_image')
        placeholder = sitk.Image([final_size_2D[0], final_size_2D[1]],
                                 transformed_image.GetPixelIDValue())
        placeholder.GetSize()
        transformed_image = sitk.Paste(
            placeholder,
            transformed_image,
            transformed_image.GetSize(),
            destinationIndex=[target_x, target_y])

    return transformed_image


def check_im_size_fiji(image):
    '''
        Checks to see if image size is too large to be loaded into FIJI as a .tiff

        :param image:
            SimpleITK image
    '''
    impixels = image.GetSize()[0] * image.GetSize()[1]

    if len(image.GetSize()) > 2:
        impixels = impixels * image.GetSize()[2]

    impixels = impixels * image.GetNumberOfComponentsPerPixel()

    return impixels > 10**9


def transform_image(source, transformationMap, override_tform=False):
    """Transforms an image using SimpleTransformix.

    Parameters
    ----------
    source : SimpleITK.Image
        SimpleITK image that will be registered.
    transformationMap : SimpleITK parameterMap
        SimpleITK parameterMap that defines transformation

    Returns
    -------
    SimpleITK image
        Transformed image

    """

    try:
        transformix = sitk.SimpleTransformix()
    except:
        transformix = sitk.TransformixImageFilter()

    overriden_flag = False

    if 'BoundingBoxMoving' in transformationMap:
        bb_source = list(transformationMap['BoundingBoxMoving'])
        bb_source = [int(float(x)) for x in bb_source]
        if sum(bb_source) > 0:
            source = source[bb_source[0]:bb_source[0] + bb_source[2],
                            bb_source[1]:bb_source[1] + bb_source[3]]

    transformix.SetMovingImage(source)
    transformix.SetTransformParameterMap(transformationMap)
    transformix.LogToConsoleOn()
    source_tformed = transformix.Execute()

    if source_tformed.GetSize(
    ) != transformationMap['OriginalSizeFixed'] and override_tform == True:

        bb = list(transformationMap['BoundingBoxFixed'])
        bb = [int(float(x)) for x in bb]

        img_size = list(transformationMap['OriginalSizeFixed'])
        img_size = [int(float(x)) for x in img_size]

        source_tformed = paste_to_original_dim(source_tformed, bb[0], bb[1],
                                               (img_size[0], img_size[1]))
        overriden_flag = True

    if source_tformed.GetSize(
    ) != transformationMap['OriginalSizeFixed'] and transformationMap['IntermediateTransform'] == (
            'false', ) and overriden_flag == False:

        bb_target = list(transformationMap['BoundingBoxFixed'])
        bb_target = [int(float(x)) for x in bb_target]
        img_size = list(transformationMap['OriginalSizeFixed'])
        img_size = [int(float(x)) for x in img_size]

        source_tformed = paste_to_original_dim(source_tformed, bb_target[0],
                                               bb_target[1],
                                               (img_size[0], img_size[1]))

    img_spacing = [float(x) for x in transformationMap['Spacing']]
    source_tformed.SetSpacing(img_spacing)

    return (source_tformed)


def transform_mc_image_sitk(image_fp,
                            transformationMap,
                            img_res,
                            from_file=True,
                            is_binary_mask=False,
                            override_tform=False):

    if from_file == True:
        print('image loaded from file')
        image = sitk.ReadImage(image_fp)
        if len(image.GetSpacing()) == 3:
            image.SetSpacing((float(img_res), float(img_res), float(1)))
        else:
            image.SetSpacing((float(img_res), float(img_res)))

    if from_file == False:
        print('image loaded from memory')
        image = image_fp

    # grayscale image transformation
    if image.GetNumberOfComponentsPerPixel() == 1 and image.GetDepth() == 0:
        print('transforming grayscale image')
        tformed_image = transform_image(
            image, transformationMap, override_tform=override_tform)
        print('casting grayscale image')
        if is_binary_mask == True:
            tformed_image = sitk.Cast(tformed_image, sitk.sitkUInt8)
            return tformed_image
        else:
            tformed_image = sitk.RescaleIntensity(tformed_image, 0, 255)
            tformed_image = sitk.Cast(tformed_image, sitk.sitkUInt8)
            return tformed_image

    # RGB image
    if image.GetNumberOfComponentsPerPixel() > 1:
        tformed_image = []
        for chan in range(image.GetNumberOfComponentsPerPixel()):
            print('getting image ' + str(chan) + ' of RGB')
            channel = sitk.VectorIndexSelectionCast(image, chan)
            print('transforming image ' + str(chan) + ' of RGB')
            channel = transform_image(
                channel, transformationMap, override_tform=override_tform)
            print('rescaling image ' + str(chan) + ' of RGB')
            channel = sitk.RescaleIntensity(channel, 0, 255)
            tformed_image.append(channel)
        print('composing RGB')
        tformed_image = sitk.Compose(tformed_image)
        tformed_image = sitk.Cast(tformed_image, sitk.sitkVectorUInt8)
        return tformed_image

    #multilayer 2D image, i.e. multichannel fluorescence
    if image.GetDepth() > 0:
        tformed_image = []
        for chan in range(image.GetDepth()):
            print('getting image ' + str(chan) + ' of multi-layer image')
            channel = image[:, :, chan]
            print('transforming image ' + str(chan) + ' of multi-layer image')
            channel = transform_image(
                channel, transformationMap, override_tform=override_tform)
            print('rescaling image ' + str(chan) + ' of multi-layer image')
            channel = sitk.RescaleIntensity(channel, 0, 255)
            tformed_image.append(channel)

        print('adding images to sequence')
        tformed_image = sitk.JoinSeries(tformed_image)
        print('casting to 8-bit')
        tformed_image = sitk.Cast(tformed_image, sitk.sitkUInt8)
        return tformed_image

    return tformed_image


def transform_from_gui(source_fp, transforms, TFM_wd, src_reso, project_name):
    """Deprecated function for gui transform. This will read a python list of
    transforms and apply them in chain.

    Parameters
    ----------
    source_fp : str
        Filepath string to image to be transformed
    transforms : list
        Python list of transform filepaths
    TFM_wd : str
        String of directory where image will be saved
    src_reso : float
        pixel resolution of image
    project_name : str
        Name that will be appended onto saved image.

    Returns
    -------
    None
        Only writes image

    """
    for i in range(len(transforms)):
        if i == 0:
            source = transform_mc_image_sitk(
                source_fp,
                transforms[i],
                src_reso,
                from_file=True,
                is_binary_mask=False)
        if i > 0:
            source = transform_mc_image_sitk(
                source,
                transforms[i],
                source.GetSpacing()[0],
                from_file=False,
                is_binary_mask=False)
    os.chdir(TFM_wd)
    sitk.WriteImage(source, project_name + ".tif", True)


def write_param_xml(xml_params, opdir, ts, project_name):
    """Deprecated xml parameter save function. changed to .yaml

    """
    stringed = ET.tostring(xml_params)
    reparsed = xml.dom.minidom.parseString(stringed)

    myfile = open(opdir + ts + project_name + '_parameters.xml', "w")
    myfile.write(reparsed.toprettyxml(indent="\t"))
    myfile.close()
    return


def prepare_output(wd, project_name, xml_params):
    """Deprecaed xml parameter function.
    """
    #prepare folder name

    ts = datetime.datetime.fromtimestamp(
        time.time()).strftime('%Y%m%d_%H_%M_%S_')
    os.chdir(wd)
    os.makedirs(ts + project_name + "_images")
    opdir = ts + project_name + "_images\\"

    #output parameters to XML file
    #output parameters to XML file
    write_param_xml(xml_params, opdir, ts, project_name)


def RegImage_load(image, source_img_res, load_image=True):
    if isinstance(image, sitk.Image) == True:
        image.SetSpacing((source_img_res, source_img_res))
        return image
    elif os.path.exists(image):
        try:
            image = RegImage(image, 'sitk', source_img_res, load_image)
            return image
        except:
            print('invalid image file')


def parameterFile_load(parameterFile):
    """Convenience function to load parameter file. Detects whether parameterFile
    is already loaded into memory or needs to be loaded from file.

    Parameters
    ----------
    parameterFile : str or SimpleITK parameterMap
        filepath to a SimpleITK parameterMap or a SimpleITK parameterMap loaded into memory

    Returns
    -------
    SimpleITK parameterMap


    """
    if isinstance(parameterFile, sitk.ParameterMap) == True:
        return parameterFile
    elif os.path.exists(parameterFile):
        try:
            parameterFile = sitk.ReadParameterFile(parameterFile)
            return parameterFile
        except:
            print('invalid parameter file')
    else:
        print('parameter input is not valid')


def reg_image_preprocess(image_fp,
                         img_res,
                         img_type='RGB_l',
                         mask_fp=None,
                         bounding_box=False):

    if img_type in ['RGB_l', 'AF', 'in_memory', 'none']:
        if img_type == "RGB_l":
            out_image = RegImage(image_fp, 'sitk', img_res)
            out_image.to_greyscale()
            out_image.invert_intensity()
        elif img_type == 'AF':
            out_image = RegImage(image_fp, 'sitk', img_res)
            if out_image.image.GetDepth() > 1:
                out_image.compress_AF_channels('max')
            if out_image.image.GetNumberOfComponentsPerPixel() == 3:
                out_image.to_greyscale()
        elif img_type == 'in_memory':
            out_image = RegImage(
                'from_file', 'sitk', img_res, load_image=False)
            out_image.get_image_from_memory(image_fp)
        else:
            out_image = RegImage(image_fp, 'sitk', img_res)

        if mask_fp != None:
            if isinstance(mask_fp, sitk.Image) == True:
                if out_image.image.GetSize() != mask_fp.GetSize():
                    print(
                        'Warning: reg image and mask do not have the same dimension'
                    )
                out_image.mask = mask_fp

            else:
                out_image.load_mask(mask_fp, 'sitk')

            if bounding_box == True:
                out_image.get_mask_bounding_box()
                out_image.crop_to_bounding_box()
    else:
        print(img_type + ' is an invalid image type (valid: RGB_l & AF)')

    return out_image


def parameter_load(reg_model):
    """Load a default regtoolboxMSRC registration parameter or one from file.

    Parameters
    ----------
    reg_model : str
        a string of the default parameterMap name. If reg_model is not in the default list
        it should be a filepath to a SimpleITK parameterMap

    Returns
    -------
    SimpleITK parameterMap


    """
    if isinstance(reg_model, str):
        if reg_model in [
                'affine', 'affine_test', 'fi_correction', 'nl', 'rigid',
                'scaled_rigid', 'testing'
        ]:
            reg_param = getattr(parameter_files(), reg_model)
            return reg_param

        else:
            try:
                reg_param = sitk.ReadParameterFile(reg_model)
                return reg_param
            except:
                print('invalid parameter file')
    else:
        print(
            'parameter input is not a filepath or default parameter file str')
