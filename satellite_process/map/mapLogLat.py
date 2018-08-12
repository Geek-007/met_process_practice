#!/usr/bin/env python
#coding=utf-8

#http://192.168.100.16:7090/rest/wms?LAYERS=basic&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&FORMAT=image%2Fjpeg&SRS=WGS84&BBOX=91.1690000000,28.914000000000,91.17037329101,28.915373291016&WIDTH=256&HEIGHT=256
# http://192.168.100.16:7090/rest/wms?LAYERS=basic&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&FORMAT=image%2Fjpeg&SRS=WGS84&BBOX=91.169,29.598,91.679,28.914&WIDTH=256&HEIGHT=256
# 91.169     29.598
# 91.679     28.914

# 1、http://192.168.100.16:7090/view.jsp?/rest/wms?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetCapabilities&SRS=WGS84&
# 2、http://192.168.100.16:7090/rest/wms?LAYERS=basic&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&FORMAT=image%2Fjpeg&SRS=WGS84&BBOX=90,0,135,45&WIDTH=256&HEIGHT=256
# 3、BBOX=67.5,22.5,90,45
# 
# TILEMATRIX=3
# &TILEROW=1&TILECOL=11

import urllib.request
from time import sleep

class MapClass():
	# 等级对应的经纬度差值
	longAdds = {"1":90, "2":45, "3":22.5, "4":11.25, "5":5.625, "6": 2.8125, "7": 1.40625, "8":0.703125,"9":0.3515625,"10":0.17578125,"11":0.087890625,"12":0.0439453125,"13":0.02197265625, "14":0.010486328125, "15":0.0052431640625, "16":0.00262158203125, "17":0.00137329101}
	latAdds = {"1":90, "2":45, "3":22.5, "4":11.25, "5":5.625, "6": 2.8125, "7": 1.40625, "8":0.703125,"9":0.3515625,"10":0.17578125,"11":0.087890625,"12":0.0439453125,"13":0.02197265625, "14":0.010486328125, "15":0.0052431640625, "16":0.00262158203125, "17":0.00137329101}
	# URL字段
	leftUrl = "http://192.168.100.16:7090/rest/wms?LAYERS=basic&SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&STYLES=&FORMAT=image%2Fjpeg&"
	rightUrl = "&WIDTH=256&HEIGHT=256"
	# 计数
	count = 0

	def __init__(self, left, right, up, down, grade):
		# 左上，右下
		self.left = float(left)
		self.right = float(right)
		self.up = float(up)
		self.down = float(down)
		# 等级
		self.grade = grade
		# 经纬差值
		self.longAdd = self.latAdds[str(grade)]
		self.latAdd = self.latAdds[str(grade)]

	def run(self):

		# 循环生成
		while self.left < self.right:

			top = self.up
			while top < self.down:
				temporaryRight = self.left + self.longAdd
				temporaryBottom = top + self.latAdd
				num=[self.left, top, temporaryRight, temporaryBottom]
				self.count += 1
				# 调用下载函数
				self.download(num)
				top += self.latAdd
			sleep(1)
			print("-"*30)
			self.left += self.longAdd

	def download(self, num):
		
		for i in range(0,len(num)):
			num[i] = str(num[i])

		BBOX = ",".join(num)
		# 拼接url
		url = self.leftUrl + "BBOX=" + BBOX + self.rightUrl
		print("正在保存第%d张的%s图片"%(self.count, BBOX))
		urllib.request.urlretrieve(url,'./map_png/%s.jpg' % BBOX)


if __name__ == "__main__":
	left = input("请输入开始经度(-180~180)：")
	while float(left) > float(180) or float(left) < float(-180):
		left = input("输入开始经度不在范围内，请重新输入(-180~180)：")

	right = input("请输入结束经度(-180~180)：")
	while float(right) >= float(180) or float(right) < float(-180):
		right = input("输入结束经度不在范围内，请重新输入(-180~180)：")

	bottom = input("请输入开始纬度(-90~90)：")
	while float(bottom) > float(90) or float(bottom) < float(-90):
		bottom = input("输入开始纬度不在范围内，请重新输入(-90~90)：")

	top = input("请输入结束纬度(-90~90)：")
	while float(top) > float(90) or float(top) < float(-90):
		top = input("输入结束纬度不在范围内，请重新输入(-90~90)：")

	tilematrix = input("请输入等级(0-15)：")
	while int(tilematrix) > 15 or int(tilematrix) < 0:
		tilematrix = input("输入等级不在范围内，请重新输入(0-15)：")
	mapclass = MapClass(left, right, up, down, grade)
	mapclass.run()
	

 
