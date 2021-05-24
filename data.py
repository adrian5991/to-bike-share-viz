import os
from urllib.parse import urlparse
import requests
import json
import pandas as pd
from zipfile import ZipFile
from io import BytesIO
from sqlalchemy import create_engine


class Data:
    def __init__(self, resources=None, df=None):
        self.df = df
        self.resources = resources

    def call_api(self, url, params):
        self.package = requests.get(url, params = params).json()
        self.resources = self.package["result"]["resources"]

        return json.dumps(self.package, indent=4)

    def get_file_type(self, included=True, url=None):
        if included:
            ext = self.resource["format"]
            return "Extension type is {}".format(ext)
        else:
            path = urlparse.urlparse(url).path
            ext = os.path.splitext(path)[1]
            return "Extension type is {}".format(ext)
    
    def get_file_ind(self, file_names):
        ind = []
        for f in file_names:
            for res in self.resources:
                if res["name"] == f:
                    ind.append(res["position"])

        return ind

    def process_api_file(self, file_name_list, download=False):
        temp_dfs = []
        resource_ind = self.get_file_ind(file_name_list)

        for i in resource_ind:
            ext = self.resources[i]["format"].lower()

            if ext == "csv":
                temp_dfs.append(pd.read_csv(self.resources[i]["url"], encoding='cp1252'))
            elif ext == "xlsx":
                temp_dfs.append(pd.read_excel(self.resources[i]["url"], engine="openpyxl"))
            elif ext == "zip":
                r = requests.get(self.resources[i]["url"])
                files = ZipFile(BytesIO(r.content))
                for f in files.namelist():
                    temp_dfs.append(pd.read_csv(files.open(f),  encoding='cp1252'))
                        
        self.df = pd.concat(temp_dfs, ignore_index=True)
        self.df.drop(columns=["ï»¿Trip Id", "Trip Id"], inplace=True)

        if download:
            self.download_file(self.df, "bike-share-2019_2021")
            print("Download successful")

        return self.df
    
    def read_csv(self, file_name):
        df1 = pd.read_csv(file_name, nrows=1000000, encoding="utf-8")
        df1["Start Time"] = pd.to_datetime(df1["Start Time"], errors="coerce", infer_datetime_format=True)
        df1["Trip  Duration"] = df1["Trip  Duration"].div(60)
        return df1        

    def download_file(self, df, file_name):
        n = "{}.csv".format(file_name)
        df.to_csv(n, encoding="utf-8", index=False)
        
    def resource_to_sql(self, file_name_list):
        resource_ind = self.get_file_ind(file_name_list)
        engine = self.get_conn()
        self.process_api_file(resource_ind)
        self.df.iloc[0:5000].to_sql("testing", con=engine)

    def get_conn(self):
        try:
            db_engine = create_engine('postgresql://')
    
            print('PostgreSQL database version:')
            vrs = db_engine.execute('SELECT version()')
            for r in vrs:  
                print(r)

            return db_engine
        except (Exception) as error:
            print(error)
    

    
