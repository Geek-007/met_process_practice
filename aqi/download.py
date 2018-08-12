# -*- coding: utf-8 -*-
from autos import *

def download():
    data = bbox(2017121802, (112, 35, 122, 43), [u"sta", u"ws_10mi_avg"])
    return data

if __name__ == '__main__':
    data = download()
    print(data)