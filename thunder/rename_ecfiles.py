import os
import glob
import sys
import datetime

def rename():
    """
    Rename EC files' name making it have the same pattern with TD file.
    :param dir: EC file's directory
    """
    # dir = sys.argv[1]
    # print(dir)
    # if dir == ".":
    #     dir = os.path.abspath(".")
    # else:
    #     dir = dir
    ec_files = glob.glob("/home/forcastcenter/ec/ec/" + "*2017*")

    for file in ec_files[:]:
        if "_3." in file:
            new_name = file.replace('_3.', '03.')
        elif "_6." in file:
            new_name = file.replace('_6.', '06.')
        elif "_9." in file:
            new_name = file.replace('_9.', '09.')
        elif "_12." in file:
            new_name = file.replace('_12.', '12.')
        elif "_15." in file:
            new_name = file.replace('_15.', '15.')
        elif "18." in file:
            new_name = file.replace('_18.', '18.')
        elif "_21." in file:
            new_name = file.replace('_21.', '21.')
        elif "_24." in file:
            day_index = file.find("_24.")
            day = file[day_index - 2:day_index]
            mon = file[day_index - 4:day_index - 2]
            year = file[day_index - 8:day_index - 4]
            date = (datetime.datetime.strptime(year + mon + day, '%Y%m%d') + datetime.timedelta(days=1)).strftime('%Y%m%d%H')
            new_name = file.replace(year + mon + day + "_24", str(date))
        else:
            continue
        print(file, new_name)
        # os.rename(file, new_name)

if __name__ == '__main__':
    rename()