import datetime
from fractions import Fraction
import pandas as pd
from typing import Tuple


def event(df: pd.DataFrame) -> pd.DataFrame:
    def event_converter(event: str):
        if "휴일" in event:
            return "휴일"
        elif event == "중간고사":
            return "중간고사"
        elif event == "기말고사":
            return "기말고사"
        elif "MT" in event or "견학" in event:
            return "견학"
        else:
            return "없음"
    df.loc[:, "행사"] = df.loc[:, "행사"].apply(event_converter)
    return df


def split_data(df: pd.DataFrame) -> tuple:
    """
    ## 데이터 분리
        - 회귀를 위한 모델 학습을 위한 데이터를 만들기 위해 ,로 구분되어 있는 메뉴 문자열을 분리해야 한다.
        - 조식, 중식, 석식 메뉴 개수가 각각 다르다.
        - 통합으로 최소 메뉴 개수를 기준으로 분리하면 데이터 손실이 발생할 수 있음.
        - 조식, 중식, 석식을 위한 데이터로 구분
    """
    # 조식
    breakfast = df.iloc[:, [0, 1, 2, 3, 9]].copy()
    breakfast.drop(breakfast[(breakfast.loc[:, '조식 메뉴'] == "없음") | (breakfast.loc[:, '조식 메뉴'] == "추석") | (
        breakfast.loc[:, '조식 메뉴'] == "1학기") | (breakfast.loc[:, '조식 메뉴'] == "2학기")].index, axis=0, inplace=True)
    breakfast.index = range(len(breakfast))
    # 공백 처리
    breakfast.loc[:, '조식 메뉴'] = breakfast.loc[:,
                                              '조식 메뉴'].apply(lambda x: x.strip())
    # 중식
    lunch = df.iloc[:, [0, 1, 4, 5, 9]].copy()
    lunch.drop(lunch[(lunch.loc[:, '중식 메뉴'] == "없음") | (lunch.loc[:, '중식 메뉴'] == "추석") | (
        lunch.loc[:, '중식 메뉴'] == "1학기") | (lunch.loc[:, '중식 메뉴'] == "2학기")].index, axis=0, inplace=True)
    lunch.index = range(len(lunch))
    # 공백 처리
    lunch.loc[:, '중식 메뉴'] = lunch.loc[:,
                                      '중식 메뉴'].apply(lambda x: x.strip())
    # 석식
    dinner = df.iloc[:, [0, 1, 6, 7, 9]].copy()
    dinner.drop(dinner[(dinner.loc[:, '석식 메뉴'] == "없음") | (dinner.loc[:, '석식 메뉴'] == "추석") | (
        dinner.loc[:, '석식 메뉴'] == "1학기") | (dinner.loc[:, '석식 메뉴'] == "2학기")].index, axis=0, inplace=True)
    dinner.index = range(len(dinner))
    # 공백 처리
    dinner.loc[:, '석식 메뉴'] = dinner.loc[:,
                                        '석식 메뉴'].apply(lambda x: x.strip())

    return (breakfast, lunch, dinner)


def menuProcessing(df: pd.DataFrame) -> pd.DataFrame:
    """
    ### 1. 메뉴 분리
        - 메뉴의 첫번째 값을 살펴보니 "잡곡밥","밥" 다른 날은 국이나 특별한 음식이 나오는데, 잡곡밥이 나오는 경우가 있음.
        - "김치"가 마지막에 나오거나 중간에 나오는 경우가 있는데 김치는 식사 인원에 영양을 줄 것 같지 않음.
        - 이 잡곡밥, 밥, 김치는 식수 인원에 크게 영향을 줄 것 같지 않음.
                - 잡곡밥,밥, 김치가 나올 경우 다음 메뉴로 선택
        - "쨈","~장"이 마지막에 나오는 경우가 있음.
                - 쨈, ~장이 나올경우 그 전꺼 선택
        - 한 개의 문자열로 된 메뉴를 분리할 때, 메뉴의 개수도 제각각 이기 때문에 제일 적은 메뉴 개수를 기준으로 분리해야함.
                - ex. 메뉴가 5,6개 있으면 5개로 설정해서 6개 중 5개 선택
        - 메뉴 선택 우선순위
                - 1) 제일 뒤 메뉴(부식이 있으면 이 위치)
                - 2) 제일 앞
                - 3) 앞에서 두번째
                - 4) ...
        - 메뉴에 공백이 있는 경우가 있어 양쪽 split 전에 공백 제거해줘함.

    ### 2. 메뉴 분석
        - 메뉴 데이터를 살펴보면 같은 메뉴의 종류가 너무 많음.
        - 메뉴의 대분류를 이용하면 종류의 개수를 줄일 수 있을 것 같음.
    """
    def delMenu(l: list, delList: list):
        d_ = l.copy()
        for idx, i in enumerate(l):
            if '&' in i:  # &로 묶여 있는 메뉴는 앞에 것을 사용
                l[idx] = i.split('&')[0]
            if i.endswith('소스'):
                l[idx] = ' '
            if i.endswith('장'):
                l[idx] = ' '
            if '겉절이' in i:
                l[idx] = ' '
            if '쌈' in i:
                l[idx] = ' '
            if '다시마' in i:
                l[idx] = ' '
        for delItem in delList:
            if delItem in l:
                l.remove(delItem)
        # 공백 없애기
        l = [i for i in l if i != ' ']
        return l

    # def min_len_menu(df: pd.DataFrame, delList: list = ['', ' ']):
    #     min_m_l = min(df.apply(lambda x: len(
    #         delMenu(x.split(','), delList))))
    #     return min_m_l

    # 메뉴 분리하여 데이터 프레임 만들기

    def splitMenu(menus: pd.Series, count: int, delList: list) -> pd.DataFrame:
        cols = {f"{menus.name}{i}": [] for i in range(1, count+1)}
        for menu in menus:
            # ,로 시작하거나 끝나는 경우
            if menu.startswith(','):
                menu = menu[1:]
            if menu.endswith(','):
                menu = menu[:-1]
            # 공백이 포함되었을 수 있음
            l = menu.strip().split(',')
            # 분리된 메뉴 자체에 공백이 있을 수 있음
            l = list(map(lambda x: x.strip(), l))
            l = delMenu(l, delList)
            for i in range(1, count+1):
                if i == 1:
                    cols[f"{menus.name}{i}"].append(l[-1].strip())
                else:
                    cols[f"{menus.name}{i}"].append(l[i-1].strip())
        df = pd.DataFrame(cols, columns=cols.keys())
        return df

    def makeTable(l: list):
        tables = {
            '장조림': [],
            '조림 요리': [],
            '무침 요리': [],
            '볶음 요리': [],
            '떡볶이': [],
            '만두': [],
            '스파게티': [],
            '샐러드': [],
            '훈제오리': [],
            '음료': [],
            '디저트': [],
            '과일': [],
            '장아찌': [],
            '나물': [],
            '동그랑땡': [],
            '떡갈비': [],
            '계란찜': [],
            '미트볼': [],
            '돈까스': [],
            '소세지': [],
            '국': [],
            '김치찌개': [],
            '탕수육': [],
            '찜닭': [],
            '갈비': [],
            '잡채': [],
            '생선구이': [],
            '고기구이': [],
            '함박스테이크': [],
            '산적구이': [],
            '불고기': [],
            '볶음밥': []
        }

        drink = ['쥬스', '주스', '음료', '우유', '두유', '비피더스', '피크닉', '쿨피스', '쵸코드링크',
                 '냉매실', '식혜', '플리또', '허쉬쵸코', '요구르트', '식이섬유', '쵸코에몽']  # 음료
        deserts = ['빵', '도넛', '파이', '와플', '푸딩', '크로무슈', '비요뜨',
                   '모닝롤', '케익', '도너츠', '핫도그', '요거트', '피자', '크로크무슈', '휘낭시에', '크림치즈', '카스테라', '소시지데니쉬', '데니쉬', '쵸코쿠키', '쵸코칩트위스트', '경단떡',
                   '판젤리', '본저쿠키', '회오리감자']
        fruits = ['바나나', '키위', '황도', '방울토마토', '오렌지',
                  '포도', '파인애플', '수박', '귤', '토마토', '사과']
        soup = ['된장국', '미역국', '두부국', '계란국', '무국', '콩나물국', '콩나물김치국']
        fish = ['조기구이', '갈치구이', '가자미카레구이', '가자미버터구이', '삼치카레구이', '삼치구이']
        meat = ['삼겹', '목살']
        for item in l:
            if '장조림' not in item and item.endswith("조림"):  # 조림 요리
                tables['조림 요리'].append(item)
            elif '장조림' in item:  # 장조림
                tables['장조림'].append(item)
            elif item.endswith("무침"):  # 무침 요리
                tables['무침 요리'].append(item)
            elif item.endswith("볶음"):  # 볶음 요리
                tables['볶음 요리'].append(item)
            elif item.endswith('떡볶이'):  # 떡볶이
                tables['떡볶이'].append(item)
            elif item.endswith('만두'):  # 만두
                tables['만두'].append(item)
            elif item.endswith('스파게티') or item.endswith('파스타'):  # 스파게티
                tables['스파게티'].append(item)
            elif item.endswith('샐러드'):  # 샐러드
                tables['샐러드'].append(item)
            elif item.endswith('나물'):  # 나물
                tables['나물'].append(item)
            elif item.endswith('잡채'):  # 잡채
                tables['잡채'].append(item)
            elif '훈제오리' in item:  # 훈제오리
                tables['훈제오리'].append(item)
            elif '장아찌' in item:  # 장아찌
                tables['장아찌'].append(item)
            elif '동그랑땡' in item:  # 동그랑땡
                tables['동그랑땡'].append(item)
            elif '떡갈비' in item:  # 떡갈비
                tables['떡갈비'].append(item)
            elif '계란찜' in item:  # 계란찜
                tables['계란찜'].append(item)
            elif '미트볼' in item:  # 미트볼
                tables['미트볼'].append(item)
            elif '까스' in item:  # 돈까스
                tables['돈까스'].append(item)
            elif '카츠' in item:  # 돈까스
                tables['돈까스'].append(item)
            elif '소세지' in item:  # 소세지
                tables['소세지'].append(item)
            elif '김치찌개' in item:  # 김치찌개
                tables['김치찌개'].append(item)
            elif '탕수육' in item:  # 탕수육
                tables['탕수육'].append(item)
            elif '찜닭' in item:  # 찜닭
                tables['찜닭'].append(item)
            elif '갈비' in item:  # 갈비
                tables['갈비'].append(item)
            elif '함박' in item:  # 함박스테이크
                tables['함박스테이크'].append(item)
            elif '산적구이' in item:  # 산적구이
                tables['산적구이'].append(item)
            elif '불고기' in item:  # 불고기
                tables['불고기'].append(item)
            elif '볶음밥' in item:  # 볶음밥
                tables['볶음밥'].append(item)
            else:
                for d in drink:
                    if d in item:
                        tables['음료'].append(item)
                for d in deserts:
                    if d in item:
                        tables['디저트'].append(item)
                for d in fruits:
                    if d in item:
                        tables['과일'].append(item)
                for d in soup:
                    if d in item:
                        tables['국'].append(item)
                for d in fish:
                    if d in item:
                        tables['생선구이'].append(item)
                for d in meat:
                    if d in item:
                        tables['고기구이'].append(item)
        return tables

    def mapping(menus: pd.DataFrame, tables: dict):
        for t in menus.columns:
            for idx, row in enumerate(menus.loc[:, t]):
                for k, v in tables.items():
                    if row in v:
                        menus.loc[idx, t] = k
        return menus

    def menu_mapper(menus: pd.DataFrame):
        menu_l = pd.concat([menus.loc[:, i]
                            for i in menus.columns], axis=0)
        menu_l = menu_l.unique()
        tables = makeTable(menu_l)
        result = mapping(menus, tables)
        return result

    delList = ['김치', '잡곡밥', '밥', '쨈', '케찹']
    menu = splitMenu(df.iloc[:, 2], 2, delList)

    # mapping
    m = menu_mapper(menu)
    df = pd.concat([df, m], axis=1).drop(df.columns[2], axis=1)
    return df


def meal(df: pd.DataFrame) -> tuple:
    """
    # Meal Data Cleaning
    ## Input
        - df: Pandas DataFrame - 식사 데이터
    ## Output
        - df: Pandas DataFrame - Cleaning된 식사 데이터
    """
    # event 처리
    df: pd.DataFrame = event(df)
    # 데이터 분리
    b, l, d = split_data(df)
    # 조식
    b: pd.DataFrame = menuProcessing(b)
    # 중식
    l: pd.DataFrame = menuProcessing(l)
    # 석식
    d: pd.DataFrame = menuProcessing(d)

    return (b, l, d)


def merged(rain: pd.DataFrame, rh: pd.DataFrame, temp: pd.DataFrame):
    rain = rain.fillna(0)
    rh = rh.fillna(0)
    temp = temp.fillna(0)
    df = pd.concat([rain.iloc[:, 2:], rh.iloc[:, 3:],
                   temp.iloc[:, 3:]], axis=1)

    def deleteComma(x):
        if ',' in str(x):
            return x[1:]
        else:
            return x
    df.loc[:, '일교차'] = df.loc[:, '일교차'].apply(deleteComma)
    df.index = range(len(df))
    """
    필요 컬럼만 고르기
        - 일시
        - 강수량(mm)
        - 평균 습도(%rh)
        - 최고기온(℃)
        - 최고기온시각
        - 최저기온(℃)
        - 최저기온시각
    """
    col = ['일시', '강수량(mm)', '평균습도(%rh)', '최고기온(℃)',
           '최고기온시각', '최저기온(℃)', '최저기온시각']
    df = df.loc[:, col]
    # columns 명 수정
    df.columns = ['날짜', '강수량', '평균상대습도',
                  '최고기온', '최고기온시각', '최저기온', '최저기온시각']
    # 평균기온 컬럼 추가
    df.loc[:, '평균기온'] = df.loc[:, '최고기온'] + df.loc[:, '최저기온'] / 2
    return df


def makeDIColumn(df: pd.DataFrame) -> pd.DataFrame:
    """
    ### 불쾌지수 Columns 추가
    1. 최고기온시각, 최저기온시각을 체크하여 각각 어느 시간대에 최고기온, 최저기온, 평균기온을 사용할지 체크
            - 만약 같은 시간대에 두 기온이 True로 체크될 시 최고기온 사용하여 불쾌지수 구함
    2. 각 식사 시간대별로 불쾌지수 단계 설정
    3. 시각 컬럼 삭제
    """

    def calDI(temp: float, humi: float):
        """
        ### 기온과 습도를 통한 불쾌지수
        ### 단계
            - 매우높음 80이상
            - 높음 75 ~ 79
            - 보통 68 ~ 74
            - 낮음 68 미만
        ### 공식
        DI = 9/5T - 0.55(1 - 0.01humi)(9/5T - 26) + 32
        """
        t = Fraction('9/5') * temp
        r = 0.55 * (1 - 0.01 * humi) * (t - 26)
        DI = t - r + 32
        if 80 <= DI:
            return 'vhigh'
        elif 75 <= DI and DI < 80:
            return 'high'
        elif 68 <= DI and DI < 75:
            return 'normal'
        else:
            return 'low'

    def checkTime(times: list):
        """
        ### 식사 시간에 최고 또는 최저 온도가 없을 경우
            - 평균온도(최고 + 최저 / 2)를 통해 평균 불쾌지수 계산

        ### 식사 시간에 최고 또는 최저 온도가 있을 경우
            - 그 시간 때의 불쾌지수 계산
        ### 식사시간
            - 아침 -> 08:00 ~ 09:00
            - 점심 -> 11:30 ~ 13:30
            - 저녁 -> 17:30 ~ 18:00
        """
        bstart_time = datetime.time(8, 0, 0)
        bend_time = datetime.time(9, 0, 0)
        lstart_time = datetime.time(11, 30, 0)
        lend_time = datetime.time(13, 30, 0)
        dstart_time = datetime.time(17, 30, 0)
        dend_time = datetime.time(18, 30, 0)
        # 시간이 범위 내에 있는지 체크
        # [아침, 점심, 저녁]
        temps = [[False, False, False], [
            False, False, False]]  # 1. 최고기온, 2. 최저기온
        for idx, time in enumerate(times):
            # datetime 객체면 time 객체로
            if type(time) == datetime.datetime:
                time = time.time()
            if bstart_time <= time <= bend_time:  # 아침에
                temps[idx][0] = True
            if lstart_time <= time <= lend_time:  # 점심에
                temps[idx][1] = True
            if dstart_time <= time <= dend_time:  # 저녁에
                temps[idx][2] = True
        return tuple(temps)

    col = {"DI_B": [], "DI_L": [], "DI_D": []}
    for idx in df.index:
        h, l = checkTime(df.loc[idx, ['최고기온시각', '최저기온시각']].to_list())
        for i, key in enumerate(col.keys()):
            # 아침
            if (h[i] == True and l[i] == True) or (h[i] == True and l[i] == False):
                temp = df.loc[idx, '최고기온']
                humi = df.loc[idx, '평균상대습도']
            elif h[i] == False and l[i] == True:
                temp = df.loc[idx, '최저기온']
                humi = df.loc[idx, '평균상대습도']
            else:  # 둘다 False
                temp = df.loc[idx, '평균기온']
                humi = df.loc[idx, '평균상대습도']
            col[key].append(calDI(temp, humi))
    DIs = pd.DataFrame(col, columns=col.keys())
    col = ['날짜', '강수량', '평균상대습도', '최고기온',
           '최저기온', '평균기온', 'DI_B', 'DI_L', 'DI_D']
    df = pd.concat([df, DIs], axis=1).loc[:, col]
    return df


def weather(rain: pd.DataFrame, rh: pd.DataFrame, temp: pd.DataFrame) -> pd.DataFrame:
    """
    # Weather Data Cleaning
    ## Input
        - rain: Pandas DataFrame - 강수량 데이터
        - rh: Pandas DataFrame - 습도 데이터
        - temp: Pandas DataFrame - 기온 데이터
    ## Output
        - df: Pandas DataFrame - Cleaning되고 합쳐진 날씨 데이터
    """
    df = merged(rain, rh, temp)
    df = makeDIColumn(df)
    return df


if __name__ == "__main__":
    path = "./static/schema/"
    b, l, d = meal(pd.read_excel(path+"MealData.xlsx"))
    print(b)
    print(l)
    print(d)
    df1 = pd.read_excel(path+"강수량.xlsx")
    df2 = pd.read_excel(path+"습도.xlsx")
    df3 = pd.read_excel(path+"기온.xlsx")
    df = weather(df1, df2, df3)
    print(df)
