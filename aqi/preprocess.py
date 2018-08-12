# -*- coding:utf-8 -*-
import pandas as pd
import glob
import datetime as dt
import numpy as np
import json

pd.set_option('display.max_columns', 1000)
pd.set_option('display.width', 1000)

def AQIpreprocess():
    data_ipath = r'E:\MLOG\aqi\data1221\aqi\*.json'
    data_npath = sorted(glob.glob(data_ipath))

    for file in data_npath:
        with open(file) as f:
            data = pd.read_json(f, orient='records')
            data['dataTime'] = pd.to_datetime(data['dataTime'], unit='ms')
            data = data.sort_values('dataTime')
            data['dataTime'] = data['dataTime'] + dt.timedelta(hours=8)
            data = data.set_index('dataTime')

            for i in range(len(data['values'])):
                df = pd.DataFrame(data['values'][i])
                df['Datetime'] = data.index[i]
                tptime = str(df.iloc[0, 4].time())
                ofname = file[:-15] + '\\aqi\\'+ str(df.iloc[0, 4].date()) + '_' + tptime[:2] + tptime[3:5]
                df.set_index(['Datetime', 'stCode'], inplace=True)
                df = df.sort_index()
                # print(df)
                # print(ofname)
            #
                # name = str(data.dataTime[0])[:10] + "_" + str(data.dataTime[0])[11:13] + "00.txt"
                df.to_csv(ofname + ".txt")

def EC_processing():
    data_ipath = r'E:\MLOG\aqi\data1221\*.json'
    data_npath = sorted(glob.glob(data_ipath))
    outpath = r"E:\MLOG\aqi\data1221\wind\\"

    for file in data_npath:
        # print(file)
        with open(file, 'rb') as f:
            data = json.loads(f.read())
        #
            data = sorted(data, key=lambda x: x["lonlat"][::-1])
            data = pd.DataFrame(data)
            # print(data)
            data['dataTime'] = pd.to_datetime(data['dataTime'], unit='ms')
            # data = data.sort_values('dataTime')
            data['dataTime'] = data['dataTime'] + dt.timedelta(hours=8)
            # data = data.set_index('dataTime')
            data['lon'] = [loc[0] for loc in data['lonlat']]
            data['lat'] = [loc[1] for loc in data['lonlat']]
            data.drop(['lonlat'], axis=1, inplace=True)
        #
            name = str(data.dataTime[0])[:10] + "_" + str(data.dataTime[0])[11:13] + "00.txt"
            print(name)
            data.to_csv(outpath + name)

        # data['winddir10m'] = np.nan
        # data['Wind10m'] = np.sqrt(data['u10'] ** 2 + data['v10'] ** 2)
        # mask = (data['u10'] > 0)
        # data.loc[mask, 'winddir10m'] = np.arccos(data.loc[mask, 'v10'] / data.loc[mask, 'Wind10m']) \
        #                                 * 180. / np.pi + 180.
        # mask = (data['u10'] < 0)
        # data.loc[mask, 'winddir10m'] = 180. - np.arccos(data.loc[mask, 'v10'] / data.loc[mask, 'Wind10m']) \
        #                                 * 180. / np.pi
        #
        #
        # tptime = str(data.index[0].time())
        # ofname = file[:-28] + '\\temp\\EC' + str(data.index[0].date()) + '_' + tptime[:2] + tptime[3:5]
        # data.to_csv(ofname + '.txt')
        # print(ofname)

def EC_his_processing():
    data_ipath = r'E:\MLOG\aqi\data1218\wind\*.json'
    data_npath = sorted(glob.glob(data_ipath))
    outpath = r"E:\MLOG\aqi\data1218\wind\\"

    for file in data_npath:
        with open(file, 'rb') as f:
            data = json.loads(f.read())
        #
            data = sorted(data, key=lambda x: x["lonlat"][::-1])
            data = pd.DataFrame(data)
            # print(data)
            # data['dataTime'] = pd.to_datetime(data['dataTime'], unit='ms')
            # # data = data.sort_values('dataTime')
            # data['dataTime'] = data['dataTime'] + dt.timedelta(hours=8)
            # data = data.set_index('dataTime')
            data['lon'] = [loc[0] for loc in data['lonlat']]
            data['lat'] = [loc[1] for loc in data['lonlat']]
            data.drop(['lonlat'], axis=1, inplace=True)
        #
            name = file.split('\\')[-1].split('.')[0] + "00.txt"
            data.to_csv(outpath + name)

if __name__ == '__main__':
   # EC_processing()
   AQIpreprocess()



