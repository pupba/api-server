"""
excel 파일을 받아서 DataFrame으로 변경 -> 데이터 처리 후 SQL로 API
"""
from io import BytesIO
import pandas as pd
from fastapi import APIRouter, Request, UploadFile, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
# file response
from starlette.responses import FileResponse
# JWT
from middleware.jwt import *
# data Processing
from middleware.datacleaning import meal as mealFunc, weather as weatherFunc
# DB
from middleware.db import dbConnect, DatabaseError
engine, session = dbConnect("warehouse", 7777)

router = APIRouter(
    prefix='/save',
    tags=['Data Add & Schema Down'],
    responses={404: {'description': 'Not Found...'}}
)

templates = Jinja2Templates(directory="templates")


@router.get('/', response_class=HTMLResponse)
async def pick(request: Request):
    template = templates.TemplateResponse(
        request=request, name='save_root.html')  # Target
    response = RedirectResponse(url='/', status_code=303)  # 실패시 리다이렉트
    response = checkToken(request, template, response)
    return response


@router.get('/download', response_class=HTMLResponse)
async def down(request: Request):
    template = templates.TemplateResponse(
        request=request, name='save_down.html')  # Target
    response = RedirectResponse(url='/', status_code=303)  # 실패시 리다이렉트
    response = checkToken(request, template, response)
    return response


@router.get('/upload', response_class=HTMLResponse)
async def upload(request: Request):
    template = templates.TemplateResponse(
        request=request, name='save_upload.html')  # Target
    response = RedirectResponse(url='/', status_code=303)  # 실패시 리다이렉트
    response = checkToken(request, template, response)
    return response


@router.get('/schema/{filename}', response_class=FileResponse)
async def downLoadSchema(filename: str):
    """
    # Schema File Download
    - 데이터 입력을 위한 틀 다운로드
    """
    path = "./static/schema/"
    targetFile = path+filename
    response = FileResponse(
        targetFile,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename)
    return response


@router.post('/get-file', response_class=HTMLResponse)
async def getFiles(
    meal: UploadFile = Form(..., title="식당 데이터"),
    rainfall: UploadFile = Form(..., title="강수량 데이터"),
    rh: UploadFile = Form(..., title="습도 데이터"),
    temp: UploadFile = Form(..., title="기온 데이터"),
):
    """
    # Get Files
    - Form으로 부터 파일을 받아와서 DataFrame으로 변경
    - 데이터 전처리 후 파일 추가
    - https://github.com/pupba/data-ware-house/blob/main/dataCleaning.py 모듈 참고하여 데이터 정제
    - warehouse db에 추가
    """
    dfs = [pd.read_excel(BytesIO(await i.read())) for i in [meal, rainfall, rh, temp]]
    # Data Cleaning
    b, l, d = mealFunc(dfs[0])
    df = weatherFunc(dfs[1], dfs[2], dfs[3])

    # response
    response = RedirectResponse(url='/save/upload', status_code=303)

    # recolumns
    col = ['date', 'rainfall', 'avg_rh', 'max_temp',
           'min_temp', 'avg_temp', 'di_b', 'di_l', 'di_d']
    df.columns = col
    try:
        df.to_sql(name="weather", con=engine, if_exists='append', index=False)
    except DatabaseError as e:
        return RedirectResponse(url='/save/upload?error=weather', status_code=303)
    col = ['date', 'weekday', 'b_diners', 'event', 'menu1', 'menu2']
    b.columns = col
    try:
        b.to_sql(name="breakfast", con=engine, if_exists='append', index=False)
    except DatabaseError as e:
        return RedirectResponse(url='/save/upload?error=breakfast', status_code=303)
    col = ['date', 'weekday', 'l_diners', 'event', 'menu1', 'menu2']
    l.columns = col
    try:
        l.to_sql(name="lunch", con=engine, if_exists='append', index=False)
    except DatabaseError as e:
        return RedirectResponse(url='/save/upload?error=lunch', status_code=303)
    col = ['date', 'weekday', 'd_diners', 'event', 'menu1', 'menu2']
    d.columns = col
    try:
        d.to_sql(name="dinner", con=engine, if_exists='append', index=False)
    except DatabaseError as e:
        return RedirectResponse(url='/save/upload?error=dinner', status_code=303)
    return response
