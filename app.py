import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import os
import time

# ==========================================
# Streamlit 페이지 설정
# ==========================================

st.set_page_config(
    page_title="부산대학교 맛집 지도",
    layout="wide"
)

st.title("🍴 부산대학교 맛집 지도")

# ==========================================
# 카카오 REST API KEY
# ==========================================

# 본인의 카카오 REST API KEY 입력
KAKAO_REST_API_KEY = ("e80c1b2bc71b22df2dd4b41975e11537")

# 카카오 API 인증 헤더
headers = {
    "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
}

# ==========================================
# 음식 카테고리 분류 함수
# ==========================================

def classify_category(category):

    # 한식 분류
    if "한식" in category:
        return "한식"

    # 중식 분류
    elif "중식" in category or "중국요리" in category:
        return "중식"

    # 일식 분류
    elif "일식" in category or "초밥" in category:
        return "일식"

    # 양식 분류
    elif (
        "양식" in category or
        "피자" in category or
        "패스트푸드" in category
    ):
        return "양식"

    # 나머지는 기타
    else:
        return "기타"

# ==========================================
# 맛집 검색 함수
# ==========================================

@st.cache_data
def search_restaurants():

    # 카카오 장소 검색 API
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    # 맛집 저장 리스트
    restaurant_list = []

    # 검색 키워드
    queries = [
        "맛집",
        "한식",
        "중식",
        "일식",
        "양식",
        "카페"
    ]

    # 여러 키워드 검색
    for query in queries:

        # 여러 페이지 검색
        for page in range(1, 16):

            params = {

                # 검색 키워드
                "query": query,

                # 부산대학교 중심 좌표
                "x": 129.0796,
                "y": 35.2332,

                # 장전동 중심 검색 범위
                "radius": 1500,

                # 페이지당 최대 개수
                "size": 15,

                # 페이지 번호
                "page": page,

                # 정확도 순 정렬
                "sort": "accuracy",

                # 음식점 카테고리
                "category_group_code": "FD6"
            }

            # API 요청
            response = requests.get(
                url,
                headers=headers,
                params=params
            )

            # 서버 과부하 방지
            time.sleep(0.2)

            # 오류 발생 시
            if response.status_code != 200:

                st.error("카카오 API 요청 실패")
                st.write(response.text)

                return pd.DataFrame()

            # JSON 데이터 변환
            data = response.json()

            # 맛집 정보 추출
            for place in data['documents']:

                restaurant = {

                    "가게명": place.get('place_name', ''),

                    "카테고리": classify_category(
                        place.get('category_name', '')
                    ),

                    "주소": place.get('road_address_name', ''),

                    "전화번호": place.get('phone', ''),

                    # 지도 표시용 좌표
                    "위도": float(place.get('y', 0)),
                    "경도": float(place.get('x', 0))
                }

                restaurant_list.append(restaurant)

    # 데이터프레임 생성
    df = pd.DataFrame(restaurant_list)

    # 중복 제거
    df = df.drop_duplicates(subset=["가게명"])

    return df

# ==========================================
# 데이터 불러오기
# ==========================================

df = search_restaurants()

# ==========================================
# 음식 종류 선택
# ==========================================

category_option = st.radio(
    "🍽️ 음식 종류 선택",
    ["전체", "한식", "중식", "일식", "양식", "기타"],
    horizontal=True
)

# ==========================================
# 음식 카테고리 필터링
# ==========================================

if category_option == "전체":

    filtered_df = df

else:

    filtered_df = df[
        df["카테고리"] == category_option
    ]

# ==========================================
# 식당 이름 검색
# ==========================================

search_name = st.text_input(
    "🔍 식당 이름 검색",
    placeholder="예: 북문분식"
)

# 검색어가 있을 경우
if search_name.strip() != "":

    filtered_df = filtered_df[
        filtered_df["가게명"].str.contains(
            search_name,
            case=False,
            na=False
        )
    ]

# ==========================================
# CSV 저장
# ==========================================

# data 폴더 생성
if not os.path.exists("data"):
    os.makedirs("data")

# CSV 저장용 데이터
save_df = filtered_df.drop(
    columns=["위도", "경도"]
)

# CSV 저장
save_df.to_csv(
    "data/restaurants.csv",
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 맛집 목록 출력
# ==========================================

st.subheader("📋 부산대학교 주변 맛집 목록")

# 표 출력용 데이터
display_df = filtered_df.drop(
    columns=["위도", "경도"]
)

# 표 출력
st.dataframe(display_df)

# ==========================================
# Folium 지도 생성
# ==========================================

m = folium.Map(
    location=[35.2332, 129.0796],
    zoom_start=16
)

# ==========================================
# 카테고리별 마커 색상
# ==========================================

color_dict = {

    "한식": "red",
    "중식": "blue",
    "일식": "green",
    "양식": "purple",
    "기타": "orange"
}

# ==========================================
# 음식점 마커 추가
# ==========================================

for idx, row in filtered_df.iterrows():

    # 팝업 내용
    popup_text = f"""
    <b>{row['가게명']}</b><br>
    카테고리: {row['카테고리']}<br>
    주소: {row['주소']}<br>
    전화번호: {row['전화번호']}
    """

    # 지도 마커 추가
    folium.Marker(
        location=[row['위도'], row['경도']],
        popup=popup_text,
        tooltip=row['가게명'],
        icon=folium.Icon(
            color=color_dict[row['카테고리']]
        )
    ).add_to(m)

# ==========================================
# 지도 출력
# ==========================================

st.subheader("🗺️ 부산대학교 맛집 지도")

st_folium(
    m,
    width=1000,
    height=600
)
