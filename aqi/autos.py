#coding:utf-8
from gavial_pysdk.query import *
from gavial_pysdk.model import *
import pandas as pd
import datetime
import numpy as np
import json

QueryConfig.service_url = "http://123.56.237.5:8080/eureka/v2/apps"
QueryConfig.proxies = {
    "http": "http://123.56.100.41:8000"
}
QueryConfig.delay_time = 30
QueryConfig.retries = 3

_default_var = [u'sta',u'dt', u'gst', u'lgst', u'lonlat',
                 u'p', u'p_24h_change', u'p_3h_change', u'prec_12h', u'prec_1h',
                 u'prec_24h', u'prec_3h', u'prec_6h', u'rh', u'rh_min', u'slp',
                  u't', u't_24h_change', u't_max', u't_max_24h',
                 u't_min', u't_min_24h', u'vap', u'vis_10min_avg', u'vis_1min_avg', u'vis_atf', u'vis_min', u'wp',
                 u'ws_10mi_avg', u'ws_2mi_avg', u'ws_extm', u'ws_max']


def point_zone(stCode, start, end, var=None,typecode="rnwst"):
    '''
     单点时间区间多要素查询
    :param stCode: 站号
    :param start: 起始时间-%Y%m%d%H
    :param end: 终止时间-%Y%m%d%H
    :param var: 变量类型
    :return: 气象数据dataframe. index：时间 . columns：变量类型
    '''
    if var == None:
        var = _default_var

    params = ParamBuilder().typeCode(typecode).vars(var).stCode(stCode).timeRange(start, end).build()
    response = Query(QueryType.SinglePointZone, params).query()
    return to_dataframe(response)

def point(stCode,date,var=None,typecode="rnwst"):
    '''
    单点单时次多要素查询
    :param stCode: 站号
    :param date: 查询时间-%Y%m%d%H
    :param var: 变量类型
    :return: 气象数据dataframe. index：时间 . columns：变量类型
    '''
    if var == None:
        var = _default_var

    params = ParamBuilder().typeCode(typecode).vars(var).stCode(stCode).date(date).build()
    response = Query(QueryType.SinglePoint, params).query()
    return to_dataframe(response)

def bbox(date,bbox,var=None,typecode="rnwst"):
    '''
    矩形区域范围内查询
    :param stCode:
    :param date:
    :param bbox: (west,south,east,north)
    :param var:
    :return:
    '''
    if var == None:
        var = _default_var

    if not "sta" in var:var.append("sta")
    params = ParamBuilder().typeCode(typecode).vars(var).bbox(Bbox(*bbox)).date(date).build()
    response = Query(QueryType.BboxCover, params).query()
    return to_dataframe(response,index_col="sta")

def rloct(start,end,bbox,var=None):
    '''
    矩形区域范围雷电查询
    '''
    if var==None:
        var=["layer", "lci", "lms", "loc_city", "loc_cnty", "loc_prov", "poi_err", "poi_type"]

    params = ParamBuilder().typeCode("rloct").timeRange(start, end).bbox(Bbox(*bbox)).vars(var).build()
    response = Query(QueryType.BboxCover, params).query()
    return to_dataframe(response)

def to_dataframe(msg,index_col="datetime"):
    _json = json.loads(msg)
    if len(_json)==0:
        return None
    df = pd.DataFrame(_json)
    df["datetime"] = pd.to_datetime(df["dataTime"], unit="ms") + datetime.timedelta(hours=8)
    df = df.set_index(index_col)
    df['lon'] = [loc[0] for loc in df['lonlat']]
    df['lat'] = [loc[1] for loc in df['lonlat']]
    df.drop(['lonlat', 'dataTime'], axis=1, inplace=True)
    df.replace(999999,np.nan,inplace=True)
    df.sort_index(inplace=True)
    return df
