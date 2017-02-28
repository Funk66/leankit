# -*- coding: utf-8 -*-

import requests
import logging


log = logging.getLogger(__name__)


class Connector(object):
    session = requests.Session()

    def authenticate(self, domain, username, password):
        self.session.auth = (username, password)
        self.base = 'https://' + domain + '.leankit.com/kanban/api'

    def get(self, url):
        log.debug('GET {}'.format(url))
        assert self.session.auth, "No credentials provided"
        try:
            request = self.session.get(self.base + url, verify=True)
        except Exception as error:
            raise IOError("Unable to make HTTP request: {}".format(error))
        if request.ok:
            try:
                response = request.json()
                if response['ReplyCode'] == 200:
                    return response['ReplyData'][0]
                else:
                    raise ConnectionError("Error {ReplyCode}: {ReplyText}".format(**response))

            except ValueError:
                raise IOError("Invalid response")
        else:
            raise ConnectionError('Server responded with code {}'.format(request.status_code))


api = Connector()

