#!/usr/bin/env python
#coding=utf-8

import urllib.request

class MapClass():
	# URL字段
	leftUrl = "http://192.168.100.16:7090/rest/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER=layer_id&STYLE=default&TILEMATRIXSET=matrix_id&TILEMATRIX="
	rightUrl = "&FORMAT=image%2Fjpeg"
	# 计数
	count = 0

	def __init__(self, left, right, bottom, top, tilematrix):
		self.left = float(left)
		self.right = float(right)
		self.bottom = float(bottom)
		self.top = float(top)
		# 初始化行列
		self.minRow = 0
		self.maxRow = 0
		self.minCol = 0
		self.maxCol = 0
		# 经纬最大范围
		self.Xmin = -180.0
		self.Xmax = 180.0
		self.Ymin = -90.0
		self.Ymax = 90.0

		# 等级:0-15
		self.TILEMATRIX = int(tilematrix)

	def run(self):
		# 调用转换函数
		self.change()
		# 循环遍历行列
		# print(self.minRow,self.maxRow, self.minCol, self.maxCol)
		for i in range(self.minRow, self.maxRow+1):
			for j in range(self.minCol, self.maxCol+1):
				# 计数增加
				self.count += 1
				# 调用下载图片函数
				self.download(i, j)
				j += 1
			i += 1

	# 经纬度转化为行列
	def change(self):
		power = 2 ** (self.TILEMATRIX + 1)
		for i in range(power):
			Xminleft = (self.Xmax - self.Xmin) / power * i + self.Xmin
			Xmaxright = (self.Xmax - self.Xmin) / power * (i + 1) + self.Xmin
			
			if self.left >= Xminleft and self.left <= Xmaxright:
				self.minCol = i
			if self.right >= Xminleft and self.right <= Xmaxright:
				self.maxCol = i
		power = 2 ** self.TILEMATRIX
		for i in range(power):
			Ymaxtop = self.Ymax - (self.Ymax - self.Ymin) / power * i
			Yminbottom = self.Ymax - (self.Ymax - self.Ymin) / power * (i + 1)

			if self.top >= Yminbottom and self.top <= Ymaxtop:
				self.minRow = i
			if self.bottom >= Yminbottom and self.bottom <= Ymaxtop:
				self.maxRow = i

	def download(self, TILEROW, TILECOL):

		# 拼接url
		TILEROW = str(TILEROW)
		TILECOL = str(TILECOL)
		url = self.leftUrl + str(self.TILEMATRIX) + "&TILEROW=" + TILEROW + "&TILECOL=" + TILECOL + self.rightUrl
		# 拼接名字 如13-9
		name = TILEROW + "-" + TILECOL + "-" + str(self.TILEMATRIX)
		print("正在下载第%d张的%s图片......"%(self.count, name))
		urllib.request.urlretrieve(url, "./map_png/%s.png" % name)
		print("已保存第%d张的%s图片"%(self.count, name))


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
	# 传入开始和结束经纬度和等级
	mapclass = MapClass(left, right, bottom, top, tilematrix)
	mapclass.run()