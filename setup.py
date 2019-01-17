#!/usr/bin/python3
# Copyright (c) 2013-2018 Hanson Robotics, Ltd. 

from setuptools import setup, find_packages
setup(
    name = "roscom-blender-api",
    version = "0.3.0",
    package_dir = {'': 'src',},
    packages = find_packages('src'),
    entry_points = {
        'blender_api.command_source.build': 'ros = roscom:build'
    }
)
