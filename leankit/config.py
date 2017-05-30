#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import json

from . import log


def save():
    if not os.path.exists(config_folder):
        os.makedirs(config_folder)
    creds = {key: input(key.capitalize() + ': ') for key in credentials}
    with open(config_file, 'w') as conf:
        json.dump(creds, conf, indent=2)


def load():
    if os.path.exists(config_file):
        with open(config_file) as conf:
            try:
                return json.load(conf)
            except json.JSONDecodeError:
                log.warning("Failed to load configuration file")


config_folder = os.path.expanduser('~/.config/leankit')
config_file = os.path.join(config_folder, 'config.json')
credentials = {key: os.getenv('LEANKIT_' + key.upper()) for key in
               ['domain', 'username', 'password']}
credentials.update(load() or {})


if __name__ == "__main__":
    save()
