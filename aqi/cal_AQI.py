#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date    : 2016-03-16 10:15:23
# @Author  : wormone (renyuuu@gmail.com)
# @Link    : http://github.com/wormone
# @Version : $Id$

from __future__ import unicode_literals, division
import numpy as np


ELE_LIMITS = {
    'pm25': [0, 35, 75, 115, 150, 250, 350, 500],
    'pm10': [0, 50, 150, 250, 350, 420, 500, 600],
    'so2': [0, 150, 500, 650, 800, 1600, 2100, 2620],
    'no2': [0, 100, 200, 700, 1200, 2340, 3090, 3840],
    'co': [0, 5, 10, 35, 60, 90, 120, 150],
    'o3': [0, 160, 200, 300, 400, 800, 1000, 1200],
}

ELE_LIMITS_daily = {
    'pm25': [0, 35, 75, 115, 150, 250, 350, 500],
    'pm10': [0, 50, 150, 250, 350, 420, 500, 600],
    'so2': [0, 50, 150, 475, 800, 1600, 2100, 2620],
    'no2': [0, 40, 80, 180, 280, 565, 750, 940],
    'co': [0, 2, 4, 14, 24, 36, 48, 60],
    'o3_1h': [0, 160, 200, 300, 400, 800, 1000, 1200],
    'o3_8h': [0, 100, 160, 215, 265, 800, 1000, 1200],
}

IAQI = [0, 50, 100, 150, 200, 300, 400, 500]

AQI_GRADES = ["优", "良", "轻度污染", "中度污染", "重度污染", "严重污染", "爆表"]

AQI_LEVELS = [0, 50, 100, 150, 200, 300, 500]


def cal_IAQIp(ele, val, hourly_or_daily='hourly'):
    ''' ele in ELE_LIMITS
        type of val in float or int
        val of 'co' units in mg/m^3 else in ug/m^3 

        if hourly_or_daily == 'hourly':
            all eles limits in hourly, i.e. ELE_LIMITS.
        if hourly_or_daily == 'daily':
            all eles but o3 limits in 24h-mean, 
            o3 limits in 8h-mean, i.e. ELE_LIMITS_daily.
    '''
    if hourly_or_daily == 'hourly':
        ele_limits = ELE_LIMITS
    elif hourly_or_daily == 'daily':
        ele_limits = ELE_LIMITS_daily
    else:
        return 'InputError'
    if ele in ele_limits.keys() and val >= 0:
        if val == 0:
            return min(IAQI)  # 0
        elif val <= max(ele_limits.get(ele)):
            limits = np.array(ele_limits.get(ele))
            val_minus_limits = list(val - limits)
            BP_lo = limits[val_minus_limits.index(
                np.min([i for i in val_minus_limits if i > 0]))]
            BP_hi = limits[val_minus_limits.index(
                np.max([i for i in val_minus_limits if i <= 0]))]
            IAQI_hi, IAQI_lo = [IAQI[list(limits).index(i)] for i in (BP_hi, BP_lo)]
            IAQIp = (val - BP_lo) * (IAQI_hi - IAQI_lo) / (BP_hi - BP_lo) + IAQI_lo
            return np.ceil(IAQIp) # 上进位取整
        else:
            return max(IAQI)  # 500
    else:
        if val < 0: return 0 # 如果输入数据小于 0，则认为 IAQI = 0
        print ele, val, hourly_or_daily
        return 'InputError'


def cal_AQI(ele_val, hourly_or_daily='hourly', site_or_city='site'):
    ''' example input for hourly:
        ele_val = {
            'pm25': 29, 'pm10': 38, 'so2': 61, 'no2': 55, 'co': 3, 'o3': 9,
        }

        example input for daily:
        ele_val = {
            'pm25': 29, 'pm10': 38, 'so2': 61, 'no2': 55, 'co': 3, 'o3_1h': 39, 'o3_8h': 29,
        }
    '''
    # 城市 AQI 日值计算方法是用臭氧 8h 最大值和其余五项污染物 24h 平均均值，共 6 项指标，
    # 且这 6 个数值应该是该城市中所有站点的平均值。
    # 站点 AQI 日值计算方法是用臭氧 1h 最大值、8h 最大值和其余五项污染物 24h 平均值，共 7 项指标。
    if site_or_city == 'city':
        try: ele_val.pop('o3_1h')
        except KeyError: pass
    eles = ele_val.keys()
    IAQIps = [cal_IAQIp(ele, ele_val[ele], hourly_or_daily=hourly_or_daily) for ele in eles]
    AQI = np.max(IAQIps)
    AQI_grade = -1
    if AQI == 500: AQI_grade = 7
    elif AQI > 300: AQI_grade = 6
    elif AQI >= 201: AQI_grade = 5
    elif AQI >= 151: AQI_grade = 4
    elif AQI >= 101: AQI_grade = 3
    elif AQI >= 51: AQI_grade = 2
    elif AQI >= 0: AQI_grade = 1
    ELE_primary = [eles[i] for i, a in enumerate(IAQIps) if a == AQI] if AQI > 50 else None
    ELE_overproof = [eles[i] for i, a in enumerate(IAQIps) if a > 100]
    return AQI, AQI_grade, ELE_primary, ELE_overproof


if __name__ == '__main__':
    ele_val = {
        'pm25': 17, 'pm10': 19, 'so2': 35, 'no2': 39, 'co': 0.2, 'o3': 17,
    }
    print cal_AQI(ele_val, hourly_or_daily='hourly', site_or_city='site')
    print cal_AQI(ele_val, hourly_or_daily='hourly', site_or_city='city')
    ele_val = {
        'pm25': 43, 'pm10': 90, 'so2': 25, 'no2': 35, 'co': 0.791, 'o3_1h': 563, 'o3_8h': 143,
    }
    print cal_AQI(ele_val, hourly_or_daily='daily', site_or_city='site')
    print cal_AQI(ele_val, hourly_or_daily='daily', site_or_city='city')
