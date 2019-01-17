blender_api_msgs
================
The Hanson Robotics humanoids are controlled by animations performed
on Blender ([the 3D software animation platform](https://www.blender.org/)),
and then converted into motor movements. The animations that should be
played at any given moment are controlled by a ROS node.

This repo defines the ROS messages used to control that animation.  It 
is distinct from the ROS node itself, (XXX FIXME, where the heck is the
ROS node? I cannot find it anywhere! !!???!!?? ) This allows
other ROS nodes to get access to the message defintions.

This repo is also distinct from the blender rig and animations, which 
are in the [blender_api](https://github.com/hansonrobotics/blender_api)
repo.

The [cookbook.md]() file provides lots of examples on how to use this.

## Design goals
* Avoids adding ROS code to the `blender_api` python module
* Eliminates the need for other ROS nodes from having to import
  the `blender_api` python module.

## Installation
```
$ cd your_catkin_workspace/src
$ git clone https://github.com/hansonrobotics/blender_api_msgs.git
$ pip3 install -t ../devel/lib/python2.7/dist-packages/ ./blender_api_msgs
$ cd ../
$ catkin build
```
The the above uses several hacks which may be painful to discover and
diagnose. These are:

* Neither `catkin_make` nor `catkin build` currently support
  `entry_points` in `setup.py`. To be more precise, it is actually
  `catkin_pkg.python_setup` that does not support `entry_points`, and
  thus ordinary python setup is used, instead of the catkinized version.

* Next, `pip3 install` defaults to an install path in the root file
  system.  To work around this, an explicit install path must be
  specified with the `-t` flag.

* You might think that the correct catkin install path would be
  in python3.4 not python2.7 but you would be wrong: when sourcing
  `devel/setup.sh`, only the 2.7 path is added to `PYTHONPATH`.

## Usage
Start blender from the `/blender_api` project.  If this package was
installed with pip or setuptools, `blender_api` should discover it
automatically.

Blender can be started with the **autostart script**:
```
blender -y Sophia.blend -P autostart.py
```
or it can be started manually, by pressing the **Start Command
Listener** button.

Review the [cookbook.md]() for lots of example usages.

## Copyright

Copyright (c) 2014,2015,2106,2017 Hanson Robotics, Ltd.
