#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json

from . import log


config_path = os.path.expanduser('~/.config/leankit/config.json')
credentials = {'domain': 'domain', 'username': '', 'password': ''}
try:
    if os.path.exists(config_path):
        with open(config_path) as config_file:
            credentials = json.load(config_file)
except json.JSONDecodeError:
    log.warning("Failed to load configuration file")

for key in credentials:
    credentials[key] = os.getenv('LEANKIT_' + key.upper(), credentials[key])
