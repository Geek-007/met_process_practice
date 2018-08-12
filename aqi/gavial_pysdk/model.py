# -*- coding: utf-8 -*-
# Created by alan on 2016/10/28


# Point
class Point(object):
    def __init__(self, lon, lat):
        self.lon = lon
        self.lat = lat


# Circle
class Circle(object):
    def __init__(self, lon, lat, dis):
        self.lon = lon
        self.lat = lat
        self.dis = dis


# Grid
class Grid(object):
    def __init__(self, lon_left, lat_left, lon_right, lat_right):
        self.lonLeft = lon_left
        self.latLeft = lat_left
        self.lonRight = lon_right
        self.latRight = lat_right

class Bbox(object):
    def __init__(self, minLon, minLat, maxLon, maxLat):
        self.minLon = minLon
        self.minLat = minLat
        self.maxLon = maxLon
        self.maxLat = maxLat
