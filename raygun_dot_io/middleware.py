import json
import logging

import datetime
import multiprocessing
import traceback
from django.conf import settings
import psutil
import requests
import sys
import socket
import platform

__author__ = 'bopfermann'

logger = logging.getLogger(__name__)

class RaygunDotIOMiddleware(object):
    """
    This will not return a response object to defer to the default
    Django behavior.
    """
    def __init__(self):
        self.RAYGUN_API_URL     = getattr(settings, 'RAYGUN_API_URL',     "https://api.raygun.io/entries")
        self.RAYGUN_API_KEY     = getattr(settings, 'RAYGUN_API_KEY',     None)
        self.RAYGUN_API_ENABLED = getattr(settings, 'RAYGUN_API_ENABLED', False)

    def process_exception(self, request, exception):
        if self.RAYGUN_API_ENABLED and self.RAYGUN_API_KEY:
            rgException = RaygunException(request, exception)
            self.handle_transport(rgException)

    def handle_transport(self, rgException):
        headers = {'X-ApiKey': self.RAYGUN_API_KEY}
        requests.post(self.RAYGUN_API_URL, data=rgException.toJson(), headers=headers, timeout=2)


class RaygunException(object):

    def __init__(self, request, exception, when=datetime.datetime.now(), customData={}):
        self.exception  = exception
        self.request    = request
        self.when       = when
        self.customData = customData

        self.data = {
            'occurredOn' : self.when.isoformat(),
            'details' : {
                'machineName' : socket.gethostname(),
                'client' : self._getClientData(),
                'error' : self._getErrorData(),
                'environment' : self._getSystemInformation(),
                'tags' : [],
                'userCustomData' : self.customData,
                'request' : self._getRequestData()
            }
        }

    def _getRequestData(self):
        headers = self.request.META.items()
        _headers = dict()
        for k,v in headers:
            if not k.startswith('wsgi'):
                _headers[k] = v

        return {
            'hostName' : self.request.get_host(),
            'url' : self.request.path,
            'httpMethod' : self.request.method,
            'ipAddress' : self.request.META.get('REMOTE_ADDR', '?'),
            'queryString' : self.request.GET.dict(),
            'form' : self.request.POST.dict(),
            'headers' : _headers,
            'rawData' : self.request.body,
        }

    def _getClientData(self):
        return {
            'name' : 'Raygun.IO Django API',
            'version' : '1.0.0',
            'clientUrl' : 'http://wanttt.com'
        }

    def _getErrorData(self):
        (e_type, e_value, e_tb) = sys.exc_info()

        return {
            'message' : self.exception.message,
            'data' : {
                'type' : e_type.__name__,
            },
            'stackTrace' : self._getStackTraceData(),
        }

    def _getStackTraceData(self, e_tb=None):
        if not e_tb:
            (e_type, e_value, e_tb) = sys.exc_info()

        frames = traceback.extract_tb(e_tb)
        return [{
            'lineNumber' : f[1],
            'className' : '',
            'fileName' : f[0],
            'methodName' : f[2],
        } for f in frames ]

    def _getSystemInformation(self):
        return {
            'processorCount' : multiprocessing.cpu_count(),
            'osVersion' : sys.platform,
            'cpu' : platform.processor(),
            'architecture' : platform.architecture()[0],
            'totalPhysicalMemory' : psutil.virtual_memory().total,
        }

    def toJson(self):
        return json.dumps(self.data, indent=4)
