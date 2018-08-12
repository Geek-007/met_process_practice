# -*- coding:utf-8 -*-
# Created by jixin on 2016/10/31

import requests
import time
import threading
from .exception import GavialException

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


def singleton(cls, *args, **kw):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


class DataType(object):
    FORECAST = 'FORECASTDATASERVICE_V1'
    REALTIME = 'REALTIMEDATASERVICE_V1'
    STDATA = 'STDATASERVICE_V1'

    @staticmethod
    def get_instance_type(type_name):
        if type_name == 'forecast':
            return DataType.FORECAST
        if type_name == 'realtime':
            return DataType.REALTIME
        if type_name == 'stdata':
            return DataType.STDATA


class Instance(object):
    def __init__(self, instance_id, host_name, app, ip_addr, status, overridden_status, port, port_enable, secure_port,
                 secure_port_enable, vip_address, action_type, status_page_url):
        self.instance_id = instance_id
        self.host_name = host_name
        self.app = app
        self.ip_address = ip_addr
        self.status = status
        self.overridden_status = overridden_status
        self.port = port
        self.port_enable = port_enable
        self.secure_port = secure_port
        self.secure_port_enable = secure_port_enable
        self.vip_address = vip_address
        self.action_type = action_type
        self.status_page_url = status_page_url


class Application(object):
    def __init__(self, name):
        self.name = name
        self.instance = []
        self.instance_rr = self.get_item()

    def cycle(self, iterable):
        saved = []
        for element in iterable:
            yield element
            saved.append(element)
        while saved:
            for element in iterable:
                yield element

    def get_item(self):
        count = 0
        for item in self.cycle(self.instance):
            count += 1
            yield (count, item)

    def add_instance(self, instance):
        self.instance.append(instance)

    def get_instance(self):
        assert len(self.instance) > 0
        return next(self.instance_rr)


@singleton
class EurekaApp(object):
    def __init__(self):
        self.Applications = []
        self.__data_expires_at = 0
        self.is_updated = False
        self.service_url = None
        self.lock = threading.Lock()

    def get_applications(self, service_url):
        self.lock.acquire()
        if not self.is_updated:
            self.Applications = []
            req = requests.get(service_url)
            tree = ET.fromstring(req.text)
            for child_of_applications in tree.findall('application'):
                name = child_of_applications.find('name').text
                application = Application(name)
                for child_of_application in child_of_applications.findall('instance'):
                    instance_id = child_of_application.find('instanceId').text
                    host_name = child_of_application.find('hostName').text
                    app = child_of_application.find('app').text
                    ip_addr = child_of_application.find('ipAddr').text
                    status = child_of_application.find('status').text
                    overridden_status = child_of_application.find('overriddenstatus').text
                    port = child_of_application.find('port').text
                    port_element = child_of_application.find('port')
                    port_enable = port_element.get('enabled')
                    secure_port = child_of_application.find('securePort').text
                    secure_port_element = child_of_application.find('securePort')
                    secure_port_enable = secure_port_element.get('enabled')
                    # countryId = child_of_application.find('countryId')
                    vip_address = child_of_application.find('vipAddress').text
                    action_type = child_of_application.find('actionType').text
                    status_page_url = child_of_application.find('statusPageUrl').text
                    instance = Instance(instance_id, host_name, app, ip_addr, status, overridden_status, port,
                                        port_enable,
                                        secure_port, secure_port_enable, vip_address, action_type, status_page_url)
                    application.instance.append(instance)
                self.Applications.append(application)
            self.is_updated = True
            self.__data_expires_at = time.time()
            self.service_url = service_url
        self.lock.release()

    def get_instance_rr(self, type_name, service_url, delay_time):
        now = time.time()
        if now - self.__data_expires_at > delay_time:
            self.is_updated = False
            self.get_applications(service_url)
        for item in self.Applications:
            if item.name == DataType.get_instance_type(type_name):
                instance = item.get_instance()
                return instance
        raise GavialException('Can Not Found Instance')
