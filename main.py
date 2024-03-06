import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
# router
from routers import login
# JWT
from middleware.jwt import *

app = FastAPI(
    title="API Server & Jinja Frontend For ML Application",
    version="v0.0.1",
    summary="🐱 FastAPI API 서버와 Jinja Frontend 구축"
)

# 라우팅
app.include_router(login.router)

app.mount("/static", StaticFiles(directory='static'), name="static")
templates = Jinja2Templates(directory="templates")


@app.exception_handler(HTTPException)
# 잘못된 접근 차단
async def http_exception_handler(request, exc):
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        response = RedirectResponse(url='/', status_code=303)
        response.delete_cookie(key='token', path='/')
        return response


@app.get('/', response_class=HTMLResponse, tags=['mainpage'])
async def root(request: Request):
    response = templates.TemplateResponse(request=request, name='index.html')
    response.delete_cookie(key='token', path='/')
    return response


@app.get('/main', response_class=HTMLResponse, tags=['mainpage'])
async def main(
    request: Request
):
    # JWT 토큰 검증
    try:
        if verify_token(request.cookies.get("token")):
            # 검증완료
            return templates.TemplateResponse(
                request=request, name='main.html')
        else:
            response = RedirectResponse(url='/', status_code=303)
            response.delete_cookie(key='token', path='/')
            return response
    except AttributeError as a:
        response = RedirectResponse(url='/', status_code=303)
        response.delete_cookie(key='token', path='/')
        return response


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
