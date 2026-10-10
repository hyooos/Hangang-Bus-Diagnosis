# data/

## 저장소에 포함된 파일

| 파일 | 내용 | 출처 |
| --- | --- | --- |
| `hangang_timetable.csv` | 한강버스 운항 시간표 정형화(2026.8.15 적용, 160행) | 한강버스 누리집 시간표 이미지 판독 (`analysis/build_timetable.py`) |
| `access_paths.csv` | 인접역 → 선착장 일반/계단 없는 보행 경로 거리 | OpenStreetMap 계산 결과 (`analysis/access_osm.py`) |
| `kyungrodang_standard_seoul.csv` | 전국마을회관및경로당표준데이터 중 서울분(좌표 포함) | [data.go.kr 15114136](https://www.data.go.kr/data/15114136/standard.do) |
| `pet_registration_2022.csv` | 행정구역별 반려동물등록 개체 수(2022) | [data.go.kr 15125454](https://www.data.go.kr/data/15125454/fileData.do) |
| `seoulmetro_elevator_20260901.csv` | 서울교통공사 엘리베이터 설치현황 | [data.go.kr 15044261](https://www.data.go.kr/data/15044261/fileData.do) |
| `seoulmetro_transfer_20250317.csv` | 서울교통공사 환승 소요시간 | [열린데이터광장 OA-22521](https://data.seoul.go.kr/dataList/OA-22521/F/1/datasetView.do) |
| `seoulmetro_station_runtime_240810.csv` | 서울교통공사 역간 소요시간(1\~8호선, 참고용) | [열린데이터광장 OA-12034](https://data.seoul.go.kr/dataList/OA-12034/S/1/datasetView.do) |

## 직접 내려받아야 하는 파일 (용량 문제로 제외)

아래 파일을 내려받아 **아래 파일명 그대로** `data/`에 넣으면 `run_all.sh`로 전체 분석을 재현할 수 있습니다.

| 저장할 파일명 | 데이터 | 출처 |
| --- | --- | --- |
| `CARD_SUBWAY_MONTH_202501.csv` \~ `202508.csv`, `CARD_SUBWAY_MONTH_202601.csv` \~ `202608.csv` (16개) | 서울시 지하철호선별 역별 승하차 인원(일 단위) | [열린데이터광장 OA-12914](https://data.seoul.go.kr/dataList/OA-12914/S/1/datasetView.do) |
| `seoulmetro_elderly_hourly_2024.csv` | 서울교통공사 역별 일별 시간대별 노인 승하차인원(2024) | [data.go.kr 15101985](https://www.data.go.kr/data/15101985/fileData.do) |
| `subway_timetable_20260914.csv` | 서울교통공사 도시철도 열차운행시각표(1\~9호선) | [data.go.kr 15098251](https://www.data.go.kr/data/15098251/fileData.do) |
| `seoulmetro_hourly_2024.csv` | 서울교통공사 역별 일별 시간대별 승하차인원(2024, 전체 승객) — 요일유형·시간대 배분 | [data.go.kr 15048032](https://www.data.go.kr/data/15048032/fileData.do) |
| `seoul_kyungrodang_202506.xlsx` | 서울시 경로당 정보(2025.6, 3,644곳, 주소) — 참고용 | [열린데이터광장 OA-15052](https://data.seoul.go.kr/dataList/OA-15052/S/1/datasetView.do) |

- 2026년 교통카드 파일은 UTF-8, 2025년 파일과 서울교통공사 파일은 CP949 인코딩입니다(스크립트가 자동 처리).
- 모든 공공데이터는 공공누리 제1유형(출처표시) 또는 데이터별 이용조건을 따릅니다.
