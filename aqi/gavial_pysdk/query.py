# -*- coding: utf-8 -*-
# Created by alan on 2016/10/28

import requests
from .exception import GavialException
from .eureka_app import EurekaApp

# __url_format__ = 'http://101.201.121.202:%d/mete/v1/%s/%s.json'
# __url_format__ = 'http://%s:%d/mete/v1/%s/%s.json'
__url_format__ = 'http://%s:%d/mete/v1/st/%s/%s.json'


class DataType(object):
    FORECAST = 'forecast'
    REALTIME = 'realtime'
    STDATA = 'stdata'


__type_dic__ = {
    # DataType.REALTIME: ['rnwst', 'rgwst', 'ghwst', 'rloct', 'rtempch', 'rtempglb'],
    # DataType.FORECAST: ['sevp'],
    DataType.STDATA: ['rnwst', 'rgwst', 'ghwst', 'rloct', 'rtempch', 'rtempglb', 'sevp']
}

__port_dic__ = {
    DataType.REALTIME: 8081,
    DataType.FORECAST: 8082,
    DataType.STDATA: 8100
}


class QueryType(object):
    """
    查询方式
    date:单时间点所有站点
    station:单站点时间序列
    nearby:临近点
    circle:圆形
    grid:矩形
    """
    # DATE = 'date'
    # STATION = 'station'
    # NEARBY = 'nearby'
    # CIRCLE = 'circle'
    # GRID = 'grid'

    SinglePoint = 'single/point'
    SinglePointZone = 'single/point/zone'

    NearestPoint = 'nearest/point'
    NearestLayerPoint = 'nearest/layer/point'

    BboxCover = 'bbox/cover'
    BboxLayerCover = 'bbox/layer/cover'




class ParamBuilder(object):
    """
    参数构造器
    """

    def __init__(self):
        self.__params__ = {}

    def typeCode(self, typeCode):
        self.__params__['typeCode'] = typeCode
        return self

    def date(self, date):
        self.__params__['date'] = date
        return self

    def base(self, base):
        self.__params__['base'] = base
        return self

    def timeRange(self, start, end):
        self.__params__['start'] = start
        self.__params__['end'] = end
        return self

    def point(self, point):
        self.__params__['lon'] = point.lon
        self.__params__['lat'] = point.lat
        return self

    def bbox(self, bbox):
        self.__params__['minLon'] = bbox.minLon
        self.__params__['minLat'] = bbox.minLat
        self.__params__['maxLon'] = bbox.maxLon
        self.__params__['maxLat'] = bbox.maxLat
        return self

    def vars(self, var_list):
        self.__params__['var'] = var_list
        return self

    def stCode(self,code):
        self.__params__['stCode'] = code
        return self

    def distance(self, distance):
        self.__params__['distance'] = distance
        return self

    def layer(self, layer):
        self.__params__['layer'] = layer
        return self



    def station(self, station):
        self.__params__['sta'] = station
        return self

    def dis(self, dis):
        self.__params__['dis'] = dis
        return self

    def circle(self, circle):
        self.__params__['lon'] = circle.lon
        self.__params__['lat'] = circle.lat
        self.__params__['dis'] = circle.dis
        return self

    def grid(self, grid):
        self.__params__['lonL'] = grid.lonLeft
        self.__params__['latL'] = grid.latLeft
        self.__params__['lonR'] = grid.lonRight
        self.__params__['latR'] = grid.latRight
        return self

    def build(self):
        return self.__params__


class QueryConfig(object):
    service_url = None
    retries = 3
    delay_time = 30
    proxies = None


class Query(object):
    def __init__(self, query_type, params):
        self.query_type = query_type
        self.params = params

    def query(self):
        try:

            typeCode = self.params.get('typeCode')
            typeName = getType(typeCode)
            self.__check__(typeName)
            port = getPort(typeName)
            if not port:
                raise GavialException('Type can not identify.')
            # url = __url_format__ % (port, typeName, self.querytype)
            url = self.__get_url__(typeName,typeCode ,delay_time=QueryConfig.delay_time, retries=QueryConfig.retries)
            req = requests.get(url, self.params, proxies=QueryConfig.proxies)
            # print req.url
            if req and req.status_code == requests.codes.ok:
                return req.text
            else:
                print(url, req.status_code)
                print(req.text)
                return {}
        except Exception as ex:
            raise GavialException(ex)

    def __get_url__(self, type_name, type_code,delay_time, retries):
        assert isinstance(delay_time, int)
        # assert isinstance(QueryConfig.service_url, basestring)
        app = EurekaApp()
        try:
            instance = app.get_instance_rr(type_name, QueryConfig.service_url, delay_time)[1]
            status_page_url = instance.status_page_url.replace(instance.host_name, instance.ip_address)
            req = requests.get(status_page_url, proxies=QueryConfig.proxies)
            if req.status_code != requests.codes.ok:
                raise GavialException('Instance Unable Service Return {0}'.format(req.status_code))
            url = __url_format__ % (instance.ip_address, int(instance.port), type_code, self.query_type)
            return url
        except  Exception as e:
            print(e)
            if retries > 0:
                self.is_updated = False
                app.get_applications(QueryConfig.service_url)
                return self.__get_url__(type_name, delay_time, retries - 1)
            else:
                raise GavialException('Instance Unable Try {0} Times'.format(retries))

    def __check__(self, typeName):
        if self.query_type == QueryType.SinglePoint:
            ret = self.__contains__(['typeCode', 'date','var', 'stCode'])
        elif self.query_type == QueryType.SinglePointZone:
            ret = self.__contains__(['typeCode', 'var', 'start', 'end' , 'stCode'])
        elif self.query_type == QueryType.NearestPoint:
            ret = self.__contains__(['typeCode', 'date', 'distance', 'var', 'lon', 'lat'])
        elif self.query_type == QueryType.NearestLayerPoint:
            ret = self.__contains__(['typeCode', 'date', 'distance', 'var', 'lon', 'lat','layer'])
        elif self.query_type == QueryType.BboxCover:
            if self.params.get('typeCode') == 'rloct':
                ret = self.__contains__(['typeCode', 'start','end', 'minLon', 'minLat', 'maxLon', 'maxLat', 'var'])
            else:
                ret = self.__contains__(['typeCode', 'date', 'minLon', 'minLat', 'maxLon', 'maxLat', 'var'])
        elif self.query_type == QueryType.BboxLayerCover:
            ret = self.__contains__(['typeCode', 'date', 'minLon', 'minLat', 'maxLon', 'maxLat', 'var', 'layer'])
        else:
            ret = False
        if ret:
            raise GavialException('Missing argument:' + str(ret) + '.')
        else:
            if typeName == 'sevp':
                ret = self.__contains__(['base'])
                if ret:
                    raise GavialException('Missing argument:base time.')

    def __contains__(self, key_list):
        ret = []
        for key in key_list:
            if not self.params.get(key, None):
                ret.append(key)
        return ret


def getType(typeCode):
    for k, v in __type_dic__.items():
        if typeCode in v:
            return k
    return None


def getPort(typeName):
    if typeName:
        return __port_dic__.get(typeName)
    return None
