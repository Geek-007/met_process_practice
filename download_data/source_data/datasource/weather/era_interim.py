#!/usr/bin/env python
#
# (C) Copyright 2012-2013 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0. 
# In applying this licence, ECMWF does not waive the privileges and immunities 
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.
#

from .ecmwfapi import ECMWFDataServer

# To run this example, you need an API key 
# available from https://api.ecmwf.int/v1/key/

class ERA-InterimDownloader(object):
   """
   每月下载ERA-Interim数据

   Args:
       date_s: 下载起始时间 eg: "2017-01-01";
       date_e: 下载结束时间 eg: "2017-01-31";
       dir: 数据下载路径

   """

   def __init__(self, date_s, date_e, dir):
      self.date_s = date_s
      self.date_e = date_e
      self.dir = dir

   def era_interim_downloader(self):
      server = ECMWFDataServer()
      server.retrieve({
         'dataset': "interim",
         'step': "0",
         'number': "all",
         'levtype': "sfc",
         'date': self.date_s + "/to/" + self.date_e,
         'time': "00/06/12/18",
         'origin': "all",
         'type': "an",
         'format': "netcdf",
         'param': "31.128/32.128/33.128/34.128/35.128/36.128/37.128/38.128/39.128/40.128/41.128/42.128/53.162/54.162/55.162/56.162/57.162/58.162/59.162/60.162/61.162/62.162/63.162/64.162/65.162/66.162/67.162/68.162/69.162/70.162/71.162/72.162/73.162/74.162/75.162/76.162/77.162/78.162/79.162/80.162/81.162/82.162/83.162/84.162/85.162/86.162/87.162/88.162/89.162/90.162/91.162/92.162/134.128/136.128/137.128/139.128/141.128/148.128/151.128/164.128/165.128/166.128/167.128/168.128/170.128/173.128/174.128/183.128/186.128/187.128/188.128/198.128/206.128/234.128/235.128/236.128/238.128",
         'area': "60/60/0/140",
         'grid': "0.75/0.75",
         'target': dir + self.date_s[:-3] + ".nc"
      })





