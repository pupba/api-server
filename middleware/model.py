from sklearn.preprocessing import MinMaxScaler
import pandas as pd
import mlflow
import json
import os
import numpy as np
from scipy.stats import scoreatpercentile
# db
from middleware.db import dbConnect

"""
datapreprocessing
"""


def getMenuTable() -> dict:
    db, session = dbConnect(port=7777, db='warehouse')
    menu = pd.read_sql("select * from menu", con=db)
    table = dict(zip(menu.loc[:, 'menu'], [float(i) for i in menu.index]))
    return table


def splitDate(df: pd.DataFrame) -> pd.DataFrame:
    date = df.iloc[:, 0].dt.strftime('%Y%m%d').astype(int)
    date = pd.concat([date, df.iloc[:, 1:]], axis=1)
    return date


def ps(se: pd.Series) -> pd.Series:
    c = se.copy()
    temp = np.sqrt(se)
    temp = np.log10(temp)
    tmp = 1/temp
    return tmp


def outlier_capping(data, upper_cap=95, lower_cap=5):
    upper_bound = scoreatpercentile(data, upper_cap)
    lower_bound = scoreatpercentile(data, lower_cap)

    capped_data = np.clip(data, lower_bound, upper_bound)

    return capped_data


def bimodal_preprocessing(se: pd.Series, col: str) -> pd.Series:
    s = se.copy()
    # abs(x - mean(x)) -> bimodal 형태의 데이터를 한지점으로 모아 정규분포 처럼 변경
    t = np.abs(s - np.mean(s))
    # outlier capping
    o = outlier_capping(t)
    # MinMax
    scaler = MinMaxScaler()
    result = scaler.fit_transform(pd.DataFrame({f"{col}": o}))
    return result


def di_one_hot(di: pd.Series, Type: str) -> pd.DataFrame:
    if Type == "breakfast":
        T = 'b'
    elif Type == "lunch":
        T = 'l'
    else:
        T = 'd'
    data = {f'di_{T}_high': [], f'di_{T}_low': [],
            f'di_{T}_normal': [], f'di_{T}_vhigh': []}
    for i in di:
        value = i
        if value == "vhigh":
            data[f'di_{T}_vhigh'].append(1)
            data[f'di_{T}_high'].append(0)
            data[f'di_{T}_normal'].append(0)
            data[f'di_{T}_low'].append(0)
        elif value == "high":
            data[f'di_{T}_vhigh'].append(0)
            data[f'di_{T}_high'].append(1)
            data[f'di_{T}_normal'].append(0)
            data[f'di_{T}_low'].append(0)
        elif value == "normal":
            data[f'di_{T}_vhigh'].append(0)
            data[f'di_{T}_high'].append(0)
            data[f'di_{T}_normal'].append(1)
            data[f'di_{T}_low'].append(0)
        else:
            data[f'di_{T}_vhigh'].append(0)
            data[f'di_{T}_high'].append(0)
            data[f'di_{T}_normal'].append(0)
            data[f'di_{T}_low'].append(1)
    return pd.DataFrame(data)


def weekday_one_hot(weekday: pd.Series) -> pd.DataFrame:
    data = {'weekday_mon': [], 'weekday_tue': [], 'weekday_wen': [],
            'weekday_thu': [], 'weekday_fri': [], 'weekday_set': [],
            'weekday_sun': []}
    for i in weekday:
        value = i
        if value == "mon":
            data['weekday_mon'].append(1)
            data['weekday_tue'].append(0)
            data['weekday_wen'].append(0)
            data['weekday_thu'].append(0)
            data['weekday_fri'].append(0)
            data['weekday_set'].append(0)
            data['weekday_sun'].append(0)
        elif value == "tue":
            data['weekday_mon'].append(0)
            data['weekday_tue'].append(1)
            data['weekday_wen'].append(0)
            data['weekday_thu'].append(0)
            data['weekday_fri'].append(0)
            data['weekday_set'].append(0)
            data['weekday_sun'].append(0)
        elif value == "wen":
            data['weekday_mon'].append(0)
            data['weekday_tue'].append(0)
            data['weekday_wen'].append(1)
            data['weekday_thu'].append(0)
            data['weekday_fri'].append(0)
            data['weekday_set'].append(0)
            data['weekday_sun'].append(0)
        elif value == "thu":
            data['weekday_mon'].append(0)
            data['weekday_tue'].append(0)
            data['weekday_wen'].append(0)
            data['weekday_thu'].append(1)
            data['weekday_fri'].append(0)
            data['weekday_set'].append(0)
            data['weekday_sun'].append(0)
        elif value == "fri":
            data['weekday_mon'].append(0)
            data['weekday_tue'].append(0)
            data['weekday_wen'].append(0)
            data['weekday_thu'].append(0)
            data['weekday_fri'].append(1)
            data['weekday_set'].append(0)
            data['weekday_sun'].append(0)
        elif value == "set":
            data['weekday_mon'].append(0)
            data['weekday_tue'].append(0)
            data['weekday_wen'].append(0)
            data['weekday_thu'].append(0)
            data['weekday_fri'].append(0)
            data['weekday_set'].append(1)
            data['weekday_sun'].append(0)
        else:
            data['weekday_mon'].append(0)
            data['weekday_tue'].append(0)
            data['weekday_wen'].append(0)
            data['weekday_thu'].append(0)
            data['weekday_fri'].append(0)
            data['weekday_set'].append(0)
            data['weekday_sun'].append(1)

    return pd.DataFrame(data)


def event_one_hot(event: pd.Series) -> pd.DataFrame:
    data = {'event_No': [],
            'event_Trav': [],
            'event_final_exam': [],
            'event_holiday': [],
            'event_mid_exam': []}
    for i in event:
        value = i
        if value == "No":
            data['event_No'].append(1)
            data['event_Trav'].append(0)
            data['event_final_exam'].append(0)
            data['event_holiday'].append(0)
            data['event_mid_exam'].append(0)
        elif value == "Trav":
            data['event_No'].append(0)
            data['event_Trav'].append(1)
            data['event_final_exam'].append(0)
            data['event_holiday'].append(0)
            data['event_mid_exam'].append(0)
        elif value == "final_exam":
            data['event_No'].append(0)
            data['event_Trav'].append(0)
            data['event_final_exam'].append(1)
            data['event_holiday'].append(0)
            data['event_mid_exam'].append(0)
        elif value == "holiday":
            data['event_No'].append(0)
            data['event_Trav'].append(0)
            data['event_final_exam'].append(0)
            data['event_holiday'].append(1)
            data['event_mid_exam'].append(0)
        else:
            data['event_No'].append(0)
            data['event_Trav'].append(0)
            data['event_final_exam'].append(0)
            data['event_holiday'].append(0)
            data['event_mid_exam'].append(1)
    return pd.DataFrame(data)


def one_hot(df: pd.DataFrame, Type: str):
    # 요일 영어
    weedic = {'월': 'mon', '화': 'tue', '수': 'wen',
              '목': 'thu', '금': 'fri', '토': 'set', '일': 'sun'}
    df.loc[:, 'weekday'] = df.loc[:, 'weekday'].apply(lambda x: weedic[x])
    # event 종류 영어
    event_dic = {"없음": "No", "견학": "Trav", "중간고사": "mid_exam",
                 "기말고사": "final_exam", "휴일": "holiday"}
    df.loc[:, 'event'] = df.loc[:, 'event'].apply(lambda x: event_dic[x])
    # 메뉴 -> 번호
    menu_dic = getMenuTable()
    df.iloc[:, 3] = df.iloc[:, 3].apply(lambda x: menu_dic[x])
    df.iloc[:, 4] = df.iloc[:, 4].apply(lambda x: menu_dic[x])
    # one-hot
    # weekday
    weekday = weekday_one_hot(df.loc[:, 'weekday'])
    # event
    event = event_one_hot(df.loc[:, 'event'])
    # di
    di = di_one_hot(df.iloc[:, -1], Type)
    d = pd.concat([df.iloc[:, 0], weekday, event,
                  di, df.iloc[:, 3:-1]], axis=1)
    return d


def preprocessing(X: pd.DataFrame, Type: str):
    df = X.copy()
    df = splitDate(df)
    # scaler
    rainfall = MinMaxScaler()
    rh = MinMaxScaler()
    # rainfall
    tmp = df.loc[:, 'rainfall'].copy()
    o = outlier_capping(tmp, 80)
    df.loc[:, 'rainfall'] = rainfall.fit_transform(
        pd.DataFrame({'rainfall': o})
    )
    # avg_rh
    tmp = df.loc[:, 'avg_rh'].copy()
    df.loc[:, 'avg_rh'] = rh.fit_transform(
        pd.DataFrame({'avg_rh': tmp})
    )
    # max_temp
    # max_temp
    df.loc[:, 'max_temp'] = bimodal_preprocessing(
        df.loc[:, 'max_temp'].astype('float64'), 'max_temp')
    # min_temp
    df.loc[:, 'min_temp'] = bimodal_preprocessing(
        df.loc[:, 'min_temp'].astype('float64'), 'min_temp')
    # avg_temp
    df.loc[:, 'avg_temp'] = bimodal_preprocessing(
        df.loc[:, 'avg_temp'].astype('float64'), 'avg_temp')

    # one-hot
    df = one_hot(df, Type)
    return df


"""
Model Load
"""
secret = json.loads(open('./secret1.json').read())


def init_registry():
    os.environ['MLFLOW_S3_ENDPOINT_URL'] = secret.get('MLFLOW_S3_ENDPOINT_URL')
    os.environ['MLFLOW_TRACKING_URI'] = secret.get('MLFLOW_TRACKING_URI')
    os.environ['AWS_ACCESS_KEY_ID'] = secret.get('AWS_ACCESS_KEY_ID')
    os.environ['AWS_SECRET_ACCESS_KEY'] = secret.get('AWS_SECRET_ACCESS_KEY')


def LSTMInput(X, seq=1):
    input_X = []
    # train
    for i in range(len(X)-seq+1):
        temp = X.iloc[i:i+seq].values
        input_X.append(temp)
    return np.array(input_X)


def loadModel(name: str):
    """
    - name : str, ex. breakfast, lunch, dinner
    """
    init_registry()

    model_type = name
    experiments = "Diners-Forecasting-Models"
    best = mlflow.search_runs(
        filter_string=f'tags.model="{model_type}"', experiment_names=[experiments])
    algorithm = best.loc[0, "tags.desc"]
    uri = best.loc[0, 'artifact_uri']+"/" + \
        best.loc[0, 'tags.mlflow.runName']

    model = mlflow.pyfunc.load_model(
        model_uri=uri)
    return model, algorithm


def predict(X, algorithm, model):
    """
    - X : 
    - algorithm : 
    - model : 
    """
    date = X.iloc[:, 0].astype('object')
    if algorithm in ['XGB', 'RF']:
        pred = model.predict(X.iloc[:, 1:])

    elif algorithm == "DNN":
        pred = model.predict(X.iloc[:, 1:])
    else:
        x = LSTMInput(X.iloc[:, 1:])
        pred = model.predict(x)
    pred = pd.concat(
        [date, pd.DataFrame({"predict": pred}, index=None)], axis=1)
    pred.loc[:, 'predict'] = pred.loc[:, 'predict'].apply(lambda x: round(x))
    return pred


if __name__ == "__main__":
    a, b = loadModel('dinner')
    print(b)
