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

KAKAO_REST_API_KEY = "e80c1b2bc71b22df2dd4b41975e11537"

# 카카오 API 인증 헤더
headers = {
    "Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"
}

# ==========================================
# 음식 카테고리 분류 함수
# ==========================================

def classify_category(category):

    if "한식" in category:
        return "한식"

    elif "중식" in category or "중국요리" in category:
        return "중식"

    elif "일식" in category or "초밥" in category:
        return "일식"

    elif "양식" in category or "피자" in category or "패스트푸드" in category:
        return "양식"

    else:
        return "기타"

# ==========================================
# 맛집 검색 함수
# ==========================================

@st.cache_data
def search_restaurants():

    # 카카오 장소 검색 API
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"

    # 맛집 데이터를 저장할 리스트
    restaurant_list = []

    # 여러 키워드 사용
    queries = [
        "맛집",
        "한식",
        "중식",
        "일식",
        "양식",
        "카페"
    ]

    # 여러 페이지 조회
    for query in queries:

        for page in range(1, 6):

            # API 요청 파라미터
            params = {

                # 검색 키워드
                "query": query,

                # 부산대학교 중심 좌표
                "x": 129.0796,
                "y": 35.2332,

                # 검색 범위
                "radius": 5000,

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

            # API 요청 간격
            time.sleep(0.2)

            # 응답 오류 확인
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

                    # 지도용 좌표
                    "위도": float(place.get('y', 0)),
                    "경도": float(place.get('x', 0))
                }

                restaurant_list.append(restaurant)

    # DataFrame 생성
    df = pd.DataFrame(restaurant_list)

    # 중복 제거
    df = df.drop_duplicates(subset=["가게명"])

    return df

# ==========================================
# 데이터 불러오기
# ==========================================

df = search_restaurants()

# ==========================================
# 카테고리 라디오 버튼
# ==========================================

category_option = st.radio(
    "🍽️ 음식 종류 선택",
    ["전체", "한식", "중식", "일식", "양식", "기타"],
    horizontal=True
)

# ==========================================
# 카테고리 필터링
# ==========================================

if category_option == "전체":
    filtered_df = df

else:
    filtered_df = df[df["카테고리"] == category_option]

# ==========================================
# CSV 저장
# ==========================================

# data 폴더 없으면 생성
if not os.path.exists("data"):
    os.makedirs("data")

# CSV 저장용 데이터
save_df = filtered_df.drop(columns=["위도", "경도"])

# CSV 저장
save_df.to_csv(
    "data/restaurants.csv",
    index=False,
    encoding="utf-8-sig"
)

# ==========================================
# 맛집 데이터 출력
# ==========================================

st.subheader("📋 부산대학교 주변 맛집 목록")

# 화면 표시용 데이터
display_df = filtered_df.drop(columns=["위도", "경도"])

st.dataframe(display_df)

# ==========================================
# Folium 지도 생성
# ==========================================

# 부산대학교 중심 좌표
map_center = [35.2332, 129.0796]

# 지도 생성
m = folium.Map(
    location=map_center,
    zoom_start=15
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
# 지도 마커 추가
# ==========================================

for idx, row in filtered_df.iterrows():

    # 마커 클릭 시 표시 내용
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