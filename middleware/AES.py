from urllib.parse import quote, unquote
from io import StringIO
import pandas as pd
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import hashlib
# 암호화를 위한 키 생성
KEY = get_random_bytes(16)  # 128비트 키 생성

# 평문 데이터
plaintext = "암호화할 데이터"


def getKey(key: str) -> bytes:
    hashvalue = hashlib.sha256(key.encode()).digest()
    return hashvalue[:16]


def encryption(key, plaintext: str) -> tuple:
    # 암호화
    cipher = AES.new(key, AES.MODE_CBC)
    ciphertext = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    return cipher.iv, ciphertext


def decryption(key, iv, ciphertext: str) -> str:
    # 복호화
    decipher = AES.new(key, AES.MODE_CBC, iv=iv)
    dec_data = unpad(decipher.decrypt(ciphertext), AES.block_size).decode()
    return StringIO(dec_data)


if __name__ == "__main__":
    df = pd.DataFrame({'a': [1, 2, 3], 'b': [2, 3, 4], 'c': [5, 6, 7]})
    KEY = getKey("pupbani1")
    print(df)
    print(KEY, '\n', type(KEY))
    vi, ciphertext = encryption(KEY, df.to_json())
    KEY1 = getKey("pupbani1")
    v = quote(vi.decode('latin-1'))
    vv = unquote(v)
    vi = vv.encode('latin-1')
    djs = decryption(KEY1, iv=vi, ciphertext=ciphertext)
    a = pd.read_json(djs)
    print(a)
