#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
PUMA Perf
author: Craig Warner
"""

import os
import platform
import sys
import random
from PyQt5 import QtCore, QtGui
import json
from pprint import pprint
import helpform
#import qrc_resources
from array import *
from time import sleep
from struct import pack
# import libc
from ctypes import CDLL


# Issue:
#
# Enhancements:

base_y = 60
base_x = 960
for y in range (0,960,120):
    for x in range(0,960,120):
        print("      { \"side_size\": 1,")
        print("        \"bg_x\": %d," % (x+base_x))
        print("        \"bg_y\": %d }," % (y+base_y))
