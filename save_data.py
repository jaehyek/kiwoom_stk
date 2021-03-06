import sys
from PyQt5.QtWidgets import QApplication
from pykiwoom.wrapper import *
import numpy as np
import pandas as pd
import sqlite3
import datetime

MARKET_KOSPI   = 0
MARKET_KOSDAK  = 10

class DailyData:
    def __init__(self):
        self.wrapper = KiwoomWrapper()
        self.get_code_list()
        print(len(self.kospi_codes))
        print(len(self.kosdak_codes))

    def get_code_list(self):
        self.kospi_codes = self.wrapper.get_codelist_by_market(MARKET_KOSPI)
        self.kosdak_codes = self.wrapper.get_codelist_by_market(MARKET_KOSDAK)

    def check_recent_file(self, code):
        import os
        from time import strftime, gmtime, time
        fname = '../data/hdf/%s.hdf'%code
        try:
            print(time() - os.path.getmtime(fname))
            if (time() - os.path.getmtime(fname)) < 200000:
                return True
        except FileNotFoundError:
            return False
        return False

    def save_all_data(self):
        today = datetime.date.today().strftime("%Y%m%d")

        # 일단 2017.10.9일 까지만 모두 저장한다. 이후 다시 update 한다.
        # today = datetime.date(2017,10,9).strftime("%Y%m%d")
        print(today)

        # load code list from account
        DATA = []
        try:
            with open('../data/stocks_in_account.txt', encoding='utf-8') as f_stocks:
                for line in f_stocks.readlines():
                    data = line.split(',')
                    DATA.append([data[6].replace('A', ''), data[1], data[0]])
            for idx, code in enumerate(DATA):
                if code == '':
                    continue
                print("get data of %s" % code)
                if self.check_recent_file(code[0]): continue
                self.save_table(code[0], today)
        except:
            pass

        for code in self.kospi_codes:
            if code == '':
                continue
            print("Kospi : get data of %s" % (code))
            if self.check_recent_file(code): continue
            self.save_table(code, today)

        for code in self.kosdak_codes:
            if code == '':
                continue
            print("Kosdak : get data of %s" % (code))
            if self.check_recent_file(code): continue
            self.save_table(code, today)
        print("Job finished...")
    def save_table(self, code, date):
        TR_REQ_TIME_INTERVAL = 4
        time.sleep(TR_REQ_TIME_INTERVAL)
        data_81 = self.wrapper.get_data_opt10081(code, date)
        time.sleep(TR_REQ_TIME_INTERVAL)
        data_86 = self.wrapper.get_data_opt10086(code, date)
        col_86 = ['전일비', '등락률', '금액(백만)', '신용비', '개인', '기관', '외인수량', '외국계', '프로그램',
                  '외인비', '체결강도', '외인보유', '외인비중', '외인순매수', '기관순매수', '개인순매수', '신용잔고율']
        data = pd.concat([data_81, data_86.loc[:, col_86]], axis=1)
        #con = sqlite3.connect("../data/stock.db")
        try:
            # data.index 은 20170904 와 같이 숫자이다.
            data = data.loc[data.index > int(self.wrapper.start_date)]
            #orig_data = pd.read_sql("SELECT * FROM '%s'" % code, con, index_col='일자').sort_index()
            orig_data = pd.read_hdf("../data/hdf/%s.hdf" % code, 'day').sort_index()
            end_date = orig_data.index[-1]
            orig_data = orig_data.loc[orig_data.index < end_date]
            data = data.loc[data.index >= end_date]
            data = pd.concat([orig_data, data], axis=0)
        except (FileNotFoundError, IndexError, OSError, IOError) as e:
            # pandas=0.18.1은 OSError, IOError가 난다.
            print(e)
            pass
        finally:
            data.index.name = '일자'
            if len(data) != 0:
                #data.to_sql(code, con, if_exists='replace')
                data.to_hdf('../data/hdf/%s.hdf'%code, 'day', mode='w')
                print("save to ../data/hdf/%s.hdf"%code)


if __name__ == '__main__':
    app = QApplication(sys.argv)

    daily_data = DailyData()
    daily_data.save_all_data()

    import glob
    import zipfile
    filelist = glob.glob('../data/hdf/*.hdf')
    with zipfile.ZipFile('../data/hdf.zip', 'w', zipfile.ZIP_DEFLATED) as myzip:
        for f in filelist:
            myzip.write(f)
