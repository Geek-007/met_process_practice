# -*- coding: utf-8 -*-
# Created by alan on 2016/10/27

from query import *
from model import *
import threading
from time import sleep


# def date():
#     params = ParamBuilder().typeCode('rnwst').time('20161001000000').build()
#     print Query(QueryType.DATE, params).query()
#     sleep(1)
#
#
# def station():
#     params = ParamBuilder().typeCode('rnwst').station('58547').timeRange('20161001000000', '20161002000000').build()
#     print Query(QueryType.STATION, params).query()
#     sleep(1)
#
#
# def nearby():
#     params = ParamBuilder().typeCode('rnwst').point(Point(120, 30)).dis(20000).timeRange('20161001000000',
#                                                                                          '20161002000000').build()
#     print Query(QueryType.NEARBY, params).query()
#     sleep(1)
#
#
# def circle():
#     params = ParamBuilder().typeCode('rnwst').point(Point(120, 30)).dis(20000).timeRange('20161001000000',
#                                                                                          '20161002000000').build()
#     print Query(QueryType.CIRCLE, params).query()
#     sleep(1)
#
#
# def grid():
#     params = ParamBuilder().typeCode('rnwst').grid(Grid(120, 30, 121, 31)).timeRange('20161001000000',
#                                                                                      '20161002000000').build()
#     print Query(QueryType.GRID, params).query()
#     sleep(1)


def single_point():
    params = ParamBuilder().typeCode("ghwst").date('2017021300').vars(["sta","rh","slp"]).stCode("45005").build()
    print params.items()
    print Query(QueryType.SinglePoint, params).query()

def single_point_zone():
    params = ParamBuilder().typeCode("ghwst").vars(["sta","rh","slp"]).stCode("45005").timeRange('2017021300', '2017021305').build()
    print Query(QueryType.SinglePointZone,params).query()

def nearest_point():
    params = ParamBuilder().typeCode("ghwst").date("2017021305").distance("50000").vars(["sta","rh","slp"]).point(Point(111.149,33.548)).build()
    print Query(QueryType.NearestPoint,params).query()

def nearest_layer_point():
    params = ParamBuilder().typeCode("rtempglb").date("2017020102").distance("50000").vars(["p","dt","t"]).point(Point(113.149,28.548)).layer("850").build()
    print Query(QueryType.NearestLayerPoint,params).query()

def bbox_cover():
    params = ParamBuilder().typeCode("ghwst").date("2017021305").bbox(Bbox(100,30,102,31)).vars(["sta","rh","slp"]).build()
    print Query(QueryType.BboxCover,params).query()

def bbox_cover_rloct():
    params = ParamBuilder().typeCode("rloct").timeRange('2017052100', '2017052109').bbox(Bbox(70, 20, 120, 38)).vars(["layer","lci","lms","loc_city","loc_cnty","loc_prov","poi_err","poi_type"]).build()
    print Query(QueryType.BboxCover, params).query()



def bbox_layer_cover():
    params = ParamBuilder().typeCode("rtempch").date("2017020102").bbox(Bbox(103,30,112,31)).vars(["sta","p","dt","t"]).layer("850").build()
    print Query(QueryType.BboxLayerCover,params).query()


class TestThread(threading.Thread):
    def __init__(self, thread_name):
        super(TestThread, self).__init__(name=thread_name)

    def run(self):
        # single_point()
        # single_point_zone()
        # nearest_point()
        # nearest_layer_point()
        # bbox_cover()
        bbox_cover_rloct()
        # bbox_layer_cover()


def main():
    # date()
    single_point()
    single_point_zone()
    nearest_point()
    nearest_layer_point()
    bbox_cover()
    bbox_layer_cover()


if __name__ == '__main__':
    # main()

    # 初始化Query配置，必填service_url, 其他选填
    QueryConfig.service_url = "http://123.56.237.5:8080/eureka/v2/apps"
    QueryConfig.proxies = {
        "http": "http://123.56.100.41:8000"
    }
    QueryConfig.delay_time = 30
    QueryConfig.retries = 3

    bbox_cover_rloct()

    # threads = []
    # for i in range(1):
    #     threads.append(TestThread(i))
    # for item in threads:
    #     item.start()
