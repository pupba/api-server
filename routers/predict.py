import os
from io import BytesIO
from datetime import datetime
import pandas as pd
from fastapi import APIRouter, Request, Form, UploadFile
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
# 암호화
from urllib.parse import quote, unquote
from middleware.AES import getKey, encryption, decryption
# JWT
from middleware.jwt import *
# middleware
from middleware.datacleaning import calDI
from middleware.model import loadModel, preprocessing, predict
router = APIRouter(
    prefix='/predict',
    tags=['predict'],
    responses={404: {'description': 'Not Found...'}}
)

templates = Jinja2Templates(directory="templates")


@router.get('/', response_class=HTMLResponse)
async def root(request: Request):
    template = templates.TemplateResponse(
        request=request, name='predict_root.html')  # Target
    response = RedirectResponse(url='/', status_code=303)  # 실패시 리다이렉트
    response = checkToken(request, template, response)  # Token 확인
    return response


@router.get('/breakfast', response_class=HTMLResponse)
# breakfast
async def breakfast(request: Request):
    template = templates.TemplateResponse(
        request=request, name='predict_breakfast.html')  # Target
    response = RedirectResponse(url='/', status_code=303)  # 실패시 리다이렉트
    response = checkToken(request, template, response)  # Token 확인
    return response


@router.get('/lunch', response_class=HTMLResponse)
# lunch
async def lunch(request: Request):
    template = templates.TemplateResponse(
        request=request, name='predict_lunch.html')  # Target
    response = RedirectResponse(url='/', status_code=303)  # 실패시 리다이렉트
    response = checkToken(request, template, response)  # Token 확인
    return response


@router.get('/dinner', response_class=HTMLResponse)
# dinner
async def dinner(request: Request):
    template = templates.TemplateResponse(
        request=request, name='predict_dinner.html')  # Target
    response = RedirectResponse(url='/', status_code=303)  # 실패시 리다이렉트
    response = checkToken(request, template, response)  # Token 확인
    return response


def di(value: str) -> str:
    if value == "breakfast":
        return "b"
    elif value == "lunch":
        return "l"
    elif value == "dinner":
        return "d"


class UTF8Headers(dict):
    """
    header로 csv 파일을 보내기 위한 코드
    """

    def __setitem__(self, key, value):
        if isinstance(value, str):
            value = value.encode("utf-8")
        super().__setitem__(key, value)


@router.post('/get-form', response_class=HTMLResponse)
async def get_form(
    request: Request,
    mtype: str = Form(..., title="type"),
    date: datetime = Form(..., title="date"),
    weekday: str = Form(..., title="weekday"),
    event: str = Form(..., title="event"),
    menu1: str = Form(..., title="menu1"),
    menu2: str = Form(..., title="menu2"),
    rainfall: float = Form(..., title="rainfall"),
    avg_rh: float = Form(..., title="avg_rh"),
    max_temp: float = Form(..., title="max_temp"),
    min_temp: float = Form(..., title="min_temp")
):
    """
    ## Get Form
    1. Form으로부터 데이터를 받아서 처리후 DataFrame 생성
    2. MLflow Registry로 부터 모델을 불러와서 예측 진행
    3. 예측값 저장
    """
    data = {
        "date": date,
        "weekday": weekday,
        "event": event,
        "menu1": menu1,
        "menu2": menu2,
        "rainfall": rainfall,
        "avg_rh": avg_rh,
        "max_temp": max_temp,
        "min_temp": min_temp,
        "avg_temp": round((max_temp+min_temp)/2, 1),
        f"DI_{di(mtype)}": calDI(temp=round((max_temp+min_temp)/2, 1), humi=avg_rh)
    }
    df = pd.DataFrame(data, index=[0])
    df_json = df.to_json()
    # 데이터 암호화
    token = request.cookies.get('token')
    KEY = getKey(token)
    # 암호화
    df_vi, en_df_json = encryption(KEY, df.to_json())
    name_vi, en_name = encryption(KEY, mtype)
    # decoding
    en_df_json_de = en_df_json.decode('latin-1')
    en_name_de = en_name.decode('latin-1')
    en_df_vi = df_vi.decode('latin-1')
    en_name_vi = name_vi.decode('latin-1')
    # url
    url = f"/predict/result?name={quote(en_name_de)}&cipher1={quote(en_name_vi)}&data={quote(en_df_json_de)}&cipher2={quote(en_df_vi)}"

    response = RedirectResponse(url=url, status_code=303)
    return response


@router.post('/get-data', response_class=HTMLResponse)
async def get_data(request: Request, data: UploadFile = Form(..., title="Data")):
    name = data.filename[:-5]  # Type
    df = pd.read_excel(BytesIO(await data.read()))  # read upload file
    l = len(df)  # length
    # 평균 온도 추가
    df['avg_temp'] = round(
        (df.loc[:, 'max_temp']+df.loc[:, 'min_temp']/2), 1)
    # 불쾌지수 추가
    DI = [calDI(df.loc[i, 'avg_temp'], df.loc[i, 'avg_rh'])
          for i in range(l)]
    df[f'DI_{di(name)}'] = pd.DataFrame(
        {f"di_{di(name)}": DI}, index=range(l))
    # 데이터 추가
    # json 암호화
    # 데이터 암호화
    token = request.cookies.get('token')
    KEY = getKey(token)
    # 암호화
    df_vi, en_df_json = encryption(KEY, df.to_json())
    name_vi, en_name = encryption(KEY, name)
    # decoding
    en_df_json_de = en_df_json.decode('latin-1')
    en_name_de = en_name.decode('latin-1')
    en_df_vi = df_vi.decode('latin-1')
    en_name_vi = name_vi.decode('latin-1')
    # url
    url = f"/predict/result?name={quote(en_name_de)}&cipher1={quote(en_name_vi)}&data={quote(en_df_json_de)}&cipher2={quote(en_df_vi)}"
    response = RedirectResponse(url=url, status_code=303)

    return response


@router.get("/result")
async def predictDiner(request: Request):
    # csv 데이터 DataFrame으로
    params = request.query_params
    # data 가져오기
    # 데이터 복호화
    KEY = getKey(request.cookies.get("token"))
    # decoding
    # iv
    cipher1 = unquote(params.get('cipher1')).encode('latin-1')
    # name
    dn = unquote(params.get('name')).encode('latin-1')  # 예측할 모델 이름
    # 복호화
    name = decryption(key=KEY, iv=cipher1, ciphertext=dn).getvalue()

    # decoding
    # iv
    cipher2 = unquote(params.get('cipher2')).encode('latin-1')
    # df
    d = unquote(params.get('data')).encode('latin-1')
    # 복호화
    dd = decryption(key=KEY, iv=cipher2, ciphertext=d)
    data = pd.read_json(dd)  # Feature Data

    # ML 모델 Load해서 예측 후 예측값 저장
    model, algorithm = loadModel(name)
    X = preprocessing(data, name)
    pred = predict(X=X, algorithm=algorithm, model=model)
    # 바탕화면 저장
    if os.name == 'nt':  # window
        desktop_path = os.path.join(os.path.join(
            os.environ['USERPROFILE']), 'Desktop')
        file_path = os.path.join(desktop_path, f'{name}_pred.xlsx')
        pred.to_excel(file_path, index=None)
    elif os.name == 'posix':  # linux, macOS
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        file_path = os.path.join(desktop_path, f"{name}_pred.xlsx")
        pred.to_excel(file_path, index=None)
    else:  # don't know
        pred.to_excel(f'./{name}_pred.xlsx', index=None)
    response = RedirectResponse(url='/predict', status_code=303)
    return response
