# -*- coding: utf-8 -*-
# @Author  : guoanboyu
# @Email   : guoanboyu@mlogcn.com
import glob
import random
import numpy as np
import pandas as pd
from netCDF4 import Dataset, num2date
from sklearn import linear_model, tree
from sklearn.metrics import precision_recall_curve, roc_curve, roc_auc_score, average_precision_score, precision_score, recall_score, f1_score, fbeta_score
from scipy.optimize import fsolve
import matplotlib.pyplot as plt


class MetIndex(object):
    """
    Calcualte all index used to express thunderbold
    """
    def __init__(self, filename):
        self.file = Dataset(filename, "r")
        self.level = self.file.variables["level"][:]
        self.time = self.file.variables["time"][:]
        self.lat = self.file.variables["latitude"][:]
        self.lon = self.file.variables["longitude"][:]
        self.units = self.file.variables['time'].units
        self.date = num2date(self.time[:], units=self.units, calendar='standard')

    def get_var(self, var, level):
        data = self.file.variables[var][0, self.level == level, (self.lat >= lat_S) & (self.lat <= lat_N), (self.lon >= lon_L) & (self.lon <= lon_R)]
        if var == "t":
            data -= 273.15
        else:
            data = data
        return data[0, :, :]

    def get_td(self, level):
        t = self.get_var("t", level)
        rh = self.get_var("r", level)
        a = np.where(t > -30, 17.269, 17.67)
        b = np.where(t > -30, 237.29, 243.5)
        es = 6.112*np.exp(a * t / (t + b))

        rh[rh < 1] = 1

        e = rh * es / 100
        c = np.log(e / 6.112)
        td = b * c / (a - c)
        return td

    def si_index(self):
        t850 = self.get_var("t", 850)
        td850 = self.get_td(850)
        t500 = self.get_var("t", 500)

        pp = 500.0

        si = 9999 * np.ones_like(t850)
        for i in range(si.shape[0]):
            for j in range(si.shape[1]):
                if t850[i, j] > 80 or t850[i, j] <= -100 or td850[i, j] > 80 or td850[i, j] <= -110:
                    continue

                es = 6.112 * np.exp(17.67 * t850[i, j] / (t850[i, j] + 243.5))
                e = 6.112 * np.exp(17.67 * td850[i, j] / (td850[i, j] + 243.5))

                r = 622 * e / (850.0 - e)
                u = e / es * 100
                tk = t850[i, j] + 273.15
                tlcl = 55.0 + 1 / (1 / (tk - 55.0) - np.log(u / 100) / 2840)

                thse = tk * ((1000.0 / 850.0) ** (0.2854 * (1 - 0.28 * 0.001 * r))) * np.exp(
                    (3.376 / tlcl - 0.00254) * r * (1 + 0.81 * 0.001 * r))
                plcl = 850 * ((tlcl / tk) ** (1004.07 / 287.05))
                if plcl < 500:
                    te500 = tk * ((500.0 / 850.0) ** (287.05 / 1004.07)) - 273.15
                else:
                    def pt500(x):
                        t1 = x[0]
                        e = 6.112 * np.exp(17.67 * t1 / (t1 + 243.5))
                        r = 622 * e / (pp - e)
                        thse1 = (t1 + 273.15) * (1000.0 / pp) ** (0.2854 * (1 - 0.28 * 0.001 * r)) * np.exp(
                            (3.376 / tlcl - 0.00254) * r * (1 + 0.81 * 0.001 * r))
                        return [thse1 - thse]

                    t1 = tlcl - 273.15
                    te500 = fsolve(pt500, [t1], xtol=1e-5)[0]

                si[i, j] = t500[i, j] - te500
        sii = np.where(si <= 0, 1, 0)
        return si

    def ki_index(self):
        t850 = self.get_var("t", 850)
        t500 = self.get_var("t", 500)
        t700 = self.get_var("t", 700)
        td850 = self.get_td(850)
        td700 = self.get_td(700)

        k = (t850 - t500) + td850 - (t700 - td700)
        ki = np.where(k >= 33, 1, 0)
        return k

    def dt_index(self, level):
        t = self.get_var("t", level)
        td = self.get_td(level)
        dt = t - td
        dti = np.where(dt <= 3, 1, 0)
        return dt

    def dt85_index(self):
        t500 = self.get_var("t", 500)
        t850 = self.get_var("t", 850)
        # print(t500.flatten(), t850.flatten())
        dt85 = t850 - t500
        dt85i = np.where(dt85 >= 23.0, 1, 0)
        return dt85

    def a_index(self):
        t850 = self.get_var("t", 850)
        td850 = self.get_td(850)
        t700 = self.get_var("t", 700)
        td700 = self.get_td(700)
        t500 = self.get_var("t", 500)
        td500 = self.get_td(500)

        ttd850 = t850 - td850
        ttd700 = t700 - td700
        ttd500 = t500 - td500

        a = t850 - t500 - ttd850 - ttd700 - ttd500
        ai = np.where(a > 10.0, 1, 0)
        return a

    def get_all_index(self):
        index = pd.DataFrame()
        index["d1000"] = self.get_var("d", 1000).flatten()
        index["pv1000"] = self.get_var("pv", 1000).flatten()
        index["q1000"] = self.get_var("q", 1000).flatten()
        index["r1000"] = self.get_var("r", 1000).flatten()
        index["t1000"] = self.get_var("t", 1000).flatten()
        index["u1000"] = self.get_var("u", 1000).flatten()
        index["v1000"] = self.get_var("v", 1000).flatten()
        index["w1000"] = self.get_var("w", 1000).flatten()
        index["d925"] = self.get_var("d", 925).flatten()
        index["pv925"] = self.get_var("pv", 925).flatten()
        index["q925"] = self.get_var("q", 925).flatten()
        index["r925"] = self.get_var("r", 925).flatten()
        index["t925"] = self.get_var("t", 925).flatten()
        index["u925"] = self.get_var("u", 925).flatten()
        index["v925"] = self.get_var("v", 925).flatten()
        index["w925"] = self.get_var("w", 925).flatten()
        index["d850"] = self.get_var("d", 850).flatten()
        index["pv850"] = self.get_var("pv", 850).flatten()
        index["q850"] = self.get_var("q", 850).flatten()
        index["r850"] = self.get_var("r", 850).flatten()
        index["t850"] = self.get_var("t", 850).flatten()
        index["u850"] = self.get_var("u", 850).flatten()
        index["v850"] = self.get_var("v", 850).flatten()
        index["w850"] = self.get_var("w", 850).flatten()
        index["d700"] = self.get_var("d", 700).flatten()
        index["pv700"] = self.get_var("pv", 700).flatten()
        index["q700"] = self.get_var("q", 700).flatten()
        index["r700"] = self.get_var("r", 700).flatten()
        index["t700"] = self.get_var("t", 700).flatten()
        index["u700"] = self.get_var("u", 700).flatten()
        index["v700"] = self.get_var("v", 700).flatten()
        index["w700"] = self.get_var("w", 700).flatten()
        index["d500"] = self.get_var("d", 500).flatten()
        index["pv500"] = self.get_var("pv", 500).flatten()
        index["q500"] = self.get_var("q", 500).flatten()
        index["r500"] = self.get_var("r", 500).flatten()
        index["t500"] = self.get_var("t", 500).flatten()
        index["u500"] = self.get_var("u", 500).flatten()
        index["v500"] = self.get_var("v", 500).flatten()
        index["w500"] = self.get_var("w", 500).flatten()
        # # index['ki'] = self.ki_index().flatten()
        # index['si'] = self.si_index().flatten()
        # index['a'] = self.a_index().flatten()
        # index['dt700'] = self.dt_index(700).flatten()
        # index['dt850'] = self.dt_index(850).flatten()
        # index['dt925'] = self.dt_index(925).flatten()
        # index['dt85'] = self.dt85_index().flatten()
        return np.array(index), index.columns

    def calc_thdstrm(self):
        k1 = np.where(self.ki_index() >= 33, 1, 0)
        k2 = np.where(self.si_index() <= 0, 1, 0)
        k3 = np.where(self.a_index() > 10.0, 1, 0)
        k4 = np.where(self.dt_index(700) <=3, 1, 0)
        k5 = np.where(self.dt_index(850) <=3, 1, 0)
        k6 = np.where(self.dt_index(925) <=3, 1, 0)
        k7 = np.where(self.dt85_index() >=23.0, 1, 0)
        thdstrm = 110.0 + 154 * k1 + 142 * k2 + 61 * k3 + 146 * k4 + 131 * k5 + 30 * k6 + 97 * k7
        thdstrm /= 10
        return thdstrm.flatten()


class ThunderNum(object):
    """
    Calculate the number of thunder
    """
    def __init__(self, filename):
        self.file = Dataset(filename, "r")
        self.time = self.file.variables["time"][:]
        self.lat = self.file.variables["latitude"][:]
        self.lon = self.file.variables["longitude"][:]

    def get_thunder_num(self):
        thunder = self.file.variables["td"][0, (self.lat >= lat_S) & (self.lat <= lat_N), (self.lon >= lon_L) & (self.lon <= lon_R)]
        thunder_num = np.where(thunder >=1, 1, 0).flatten()
        return thunder_num


class Model(object):
    def __init__(self):
        self.ec_dir = "/home/forcastcenter/ec/ec/" #r"e:/MLOG/thunderbolt/ec_data/"
        self.td_dir = "/home/forcastcenter/ec/td/" #r"e:/MLOG/thunderbolt/td_data/"

    def read_file(self, ec_files, td_files):
        global  index, thunder_num
        for num, file in enumerate(list(zip(ec_files, td_files))[:]):
            # print(file[0], file[1])
            met = MetIndex(file[0])
            index_new, columns_name = met.get_all_index()
            thunder = ThunderNum(file[1])
            thunder_num_new = thunder.get_thunder_num()
            if num == 0:
                index = index_new
                thunder_num = thunder_num_new
            else:
                index = np.vstack((index, index_new))
                thunder_num = np.hstack((thunder_num, thunder_num_new))
        data = pd.DataFrame(index, columns = columns_name)
        data["thunder"] = thunder_num
        return data

    def generate(self, filename, cvalue):
        ec_files = sorted(glob.glob(self.ec_dir + filename))
        td_files = sorted(glob.glob(self.td_dir + filename))

        data = self.read_file(ec_files, td_files)
        thunder_occur = data[data["thunder"] != 0]
        thunder_unoccur = data[data["thunder"] == 0]
        random_occur = [random.randint(0, thunder_occur.shape[0]-1) for _ in range(3800)]
        random_unoccur = [random.randint(0, thunder_unoccur.shape[0]-1) for _ in range(10000)]
        train_data = pd.concat([thunder_occur.iloc[random_occur, :], thunder_unoccur.iloc[random_unoccur, :]])

        clf = linear_model.LogisticRegression(penalty="l1", C=cvalue)
        # clf = tree.DecisionTreeClassifier(criterion="entropy")
        model = clf.fit(train_data[data.columns[:-1]], train_data["thunder"])
        return model

    def predict(self, model, filename):
        ec_files = sorted(glob.glob(self.ec_dir + filename))
        td_files = sorted(glob.glob(self.td_dir + filename))

        data = self.read_file(ec_files, td_files)
        data["thunder_predict"] = model.predict_proba(data[data.columns[:-1]])[:,1]
        # TP = data[(data["thunder"] == 1) & (data["thunder_predict"] >= 0.7)]
        # recall = TP.shape[0] / data[data["thunder"] == 1].shape[0]
        # precision = TP.shape[0] / data[data["thunder_predict"] >= 0.7].shape[0]
        # print("发生雷电次数：%s    预报雷电次数：%s" % (str(data[data["thunder"] == 1].shape[0]), str(data[data["thunder_predict"] >= 0.7].shape[0])))
        # print("查准率：%.2f%%    查全率：%.2f%%" % (precision * 100, recall * 100))      
        return data 


def process1(cvalue):
    model = Model()
    thunder_model = model.generate("*201705*", cvalue)
    # print("训练")
    # train_result = model.predict(thunder_model, "*201705*")
    # model.draw_PR(train_result)
    data = model.predict(thunder_model, "*201706*")
    return data

def process2():
    ec_dir = "/home/forcastcenter/ec/ec/" #r"e:/MLOG/thunderbolt/ec_data/"
    td_dir = "/home/forcastcenter/ec/td/" #r"e:/MLOG/thunderbolt/td_data/"
    ec_files = sorted(glob.glob(ec_dir + "*201706*"))
    td_files = sorted(glob.glob(td_dir + "*201706*"))
    for num, file in enumerate(list(zip(ec_files, td_files))[:]):
        met = MetIndex(file[0])
        index_new = met.calc_thdstrm()
        thunder = ThunderNum(file[1])
        thunder_num_new = thunder.get_thunder_num()
        if num == 0:
            index = index_new
            thunder_num = thunder_num_new
        else:
            index = np.hstack((index, index_new))
            thunder_num = np.hstack((thunder_num, thunder_num_new))
    data = pd.DataFrame()
    data["thunder"] = thunder_num
    data["thunder_predict"] = index / 100
    # TP = data[(data["thunder"] == 1) & (data["thunder_predict"] >= 0.7)]
    # recall = TP.shape[0] / data[data["thunder"] == 1].shape[0]
    # precision = TP.shape[0] / data[data["thunder_predict"] >= 0.7].shape[0]
    # print("发生雷电次数：%s    预报雷电次数：%s" % (str(data[data["thunder"] == 1].shape[0]), str(data[data["thunder_predict"] >= 0.7].shape[0])))
    # print("查准率：%.2f%%    查全率：%.2f%%" % (precision * 100, recall * 100))    
    return data


if __name__ == '__main__':
    lon_L = 107.75 #73
    lon_R = 116.75 #135
    lat_S = 28.25  #10
    lat_N = 34.25  #55
    for i in range(7):
        precision_list = []
        recall_list = []
        for num in range(10):
            data1 = process1(float(10**i))
            precision_score1 = precision_score(data1["thunder"], np.where(data1["thunder_predict"] >= 0.7, 1, 0), average="binary")
            recall_score1 = recall_score(data1["thunder"], np.where(data1["thunder_predict"] >= 0.7, 1, 0), average="binary")
            precision_list.append(precision_score1)
            recall_list.append(recall_score1)
        precision_avg = sum(precision_list)/len(precision_list)
        recall_avg = sum(recall_list)/len(recall_list)
        print("--机器学习 c={}--  查准率: {:.2f}%,  查全率: {:.2f}%".format(10**i, precision_avg*100, recall_avg*100))

    data2 = process2()
    precision_score2 = precision_score(data2["thunder"], np.where(data2["thunder_predict"] >= 0.7, 1, 0), average="binary")
    recall_score2 = recall_score(data2["thunder"], np.where(data2["thunder_predict"] >= 0.7, 1, 0), average="binary")
    print("--潜势计算--  查准率: {:.2f}%,  查全率: {:.2f}%".format(precision_score2*100, recall_score2*100))
    #ROC曲线
    fpr1, tpr1, thresholds1 = roc_curve(data1["thunder"], data1["thunder_predict"])
    fpr2, tpr2, thresholds2 = roc_curve(data2["thunder"], data2["thunder_predict"])
    auc1 = roc_auc_score(data1["thunder"], data1["thunder_predict"])
    auc2 = roc_auc_score(data2["thunder"], data2["thunder_predict"])
    #PR曲线
    precision1, recall1, thresholds1 = precision_recall_curve(data1["thunder"], data1["thunder_predict"])
    precision2, recall2, thresholds2 = precision_recall_curve(data2["thunder"], data2["thunder_predict"])
    average_precision1 = average_precision_score(data1["thunder"], data1["thunder_predict"])
    average_precision2 = average_precision_score(data2["thunder"], data2["thunder_predict"])   
    f1_score1 = f1_score(data1["thunder"], np.where(data1["thunder_predict"] >= 0.7, 1, 0)) 
    f1_score2 = f1_score(data2["thunder"], np.where(data2["thunder_predict"] >= 0.7, 1, 0)) 
    # # #画图
    # plt.figure(1)
    # plt.plot([0, 1], [0, 1], 'k--')
    # plt.plot(fpr1, tpr1, alpha=0.8, label=u"machine learning (area={:.2f})".format(auc1))
    # plt.plot(fpr2, tpr2, alpha=0.8, label=u"thunder potential (area={:.2f})".format(auc2))
    # # plt.fill_between(tpr, fpr, step='post', alpha=0.2, color='b')
    # plt.xlabel('False positive rate')
    # plt.ylabel('True positive rate')
    # plt.ylim([0.0, 1.0])
    # plt.xlim([0.0, 1.0])
    # plt.title('Receiver operating characteristic')
    # plt.legend(loc='best')
    # plt.savefig("./roc_local.png")
    # plt.show()

    # plt.figure(2)
    # plt.plot(recall1, precision1, alpha=0.8, color='b', label=u"machine learning AP={:.2f} f1={:.2f}".format(average_precision1, f1_score1))
    # plt.plot(recall2, precision2, alpha=0.8, color='r', label=u"thunder potential AP={:.2f} f1={:.2f}".format(average_precision2, f1_score2))
    # plt.fill_between(recall1, precision1, step='post', alpha=0.2, color='b')
    # plt.fill_between(recall2, precision2, step='post', alpha=0.2, color='r')
    # plt.xlabel('Recall')
    # plt.ylabel('Precision')
    # plt.ylim([0.0, 1.0])
    # plt.xlim([0.0, 1.0])
    # plt.title('Precision-Recall curve')
    # plt.legend(loc='best')
    # plt.savefig("./pr_local.png")
    # plt.show()