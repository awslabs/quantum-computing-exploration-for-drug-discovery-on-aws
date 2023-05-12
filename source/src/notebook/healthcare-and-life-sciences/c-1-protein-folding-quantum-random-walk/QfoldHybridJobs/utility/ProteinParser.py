# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

########################################################################################################################
#   The following class is the parser for different types of molecule files
########################################################################################################################

import pandas as pd
import numpy as np
import re

import logging
import pickle  # nosec
import os

log = logging.getLogger()
log.setLevel('INFO')

class ProteinData():

    def __init__(self, data_folder):
        # split folder
        logging.info("prepare protein data")
