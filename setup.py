# -*- coding: utf-8 -*-
"""
Created on Thu Feb 22 18:45:41 2018

@author: nhpatterson
"""

from setuptools import setup, find_packages

setup(name='regToolboxMSRC',
      version='0.1.1',
      description='Registration toolbox for serial section data for imaging mass spectrometry to microscopy',
      long_description='Registration toolbox for serial section data for imaging mass spectrometry experiments developed at the Mass Spectrometry Research Center at Vanderbilt University, Nashville, TN, USA',
      url='tbd',
      author='Nathan Heath Patterson',
      author_email='nathan.h.patterson@vanderbilt.edu',
      license='MIT',
      keywords='imaging mass spectrometry microscopy registration',
      packages=['regToolboxMSRC','regToolboxMSRC.utils','regToolboxMSRC.GUI'],
      scripts=['regToolboxMSRC/GUI/reg_tlbx_gui.py'],
include_package_data=True,
      zip_safe=False)
