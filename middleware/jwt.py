from jose import JWTError, jwt
from datetime import timedelta, datetime
from fastapi import HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
import json

se = json.loads(open('./secret2.json').read())
SECRET_KEY = se.get("KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
""" 토큰 생성 """


def create_access_token(data: dict, expires_delta: timedelta):
    toEncode = data.copy()
    expire = datetime.utcnow() + expires_delta
    toEncode.update({"exp": expire})
    encode_jwt = jwt.encode(toEncode, SECRET_KEY, algorithm="HS256")
    return encode_jwt


""" 토큰 검증 """


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if list(payload.keys())[0] in se.get("JWT") and list(payload.keys())[1] in se.get("JWT"):
            return True
        else:
            return False
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def checkToken(request: Request, template: Jinja2Templates.TemplateResponse, response: RedirectResponse):
    # JWT 토큰 검증
    try:
        if verify_token(request.cookies.get("token")):
            # 검증완료
            return template
        else:
            response = RedirectResponse(url='/', status_code=303)
            response.delete_cookie(key='token', path='/')
            return response
    except AttributeError as a:
        response = RedirectResponse(url='/', status_code=303)
        response.delete_cookie(key='token', path='/')
        return response


if __name__ == "__main__":
    d = {"key": "hello"}
    token = create_access_token(d, timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES), SECRET_KEY=SECRET_KEY)
    print(2, verify_token(token))
