资源卫星切片数据下载

===
1. 使用说明
---
脚本为两种形式：
WMTX.py为通过经纬范围转化为行列块，文件保存形式是：行-列-等级.png。 
mapLogLat.py为通过经纬范围地图切片，文件保存形式是：左 下 右 上.png。
保存到当前下map文件夹
>
WMTX.py：
left是开始经度(0~180)
right是结束经度(0~180)
bottom是开始纬度(-90~90)
top是结束纬度(-90~90)
tilematrix是等级(0-15)

mapLogLat.py：
left是开始经度(0~180)
right是结束经度(0~180)
up是开始纬度(-90~90)
down是结束纬度(-90~90)
grade是等级(0-15)
longAdds是等级对应的经度差值
latAdds是等级对应的纬度差值





2.运行环境
---
ubuntu 系统 Python 3.5
依赖包: urllib


拼接地图切片
MOSAIC.py

===
1. 使用说明
---
脚本为两种形式：
MOSAIC.py为将图片拼接起来，保存到当前下map-photo文件夹。
确保当前下map文件夹有图片，图片形式是：行-列-等级.png

>
# 经纬最大范围
self.Xmin = -180.0
self.Xmax = 180.0
self.Ymin = -90.0
self.Ymax = 90.0
# 等级:0-15
self.TILEMATRIX = 0
# 初始这个切片的左下经纬
self.minLeft = 0
self.minBottom = 0

self.longAdd = 0
self.latAdd = 0
# 初始这个切片的行列
self.Col = 0
self.Row = 0

2.运行环境
---
ubuntu 系统 Python 3.5
依赖包: gdal,osr,numpy,os,re,glob


运行方式：python main.py