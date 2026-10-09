"""③ 가족 축 매트릭스, 이용층별 접근 부담, ⑥ 건강 코스 걸음 수, ④ 요금 시나리오 표."""
import numpy as np, pandas as pd
OFFICIAL_M = {'마곡': 720, '망원': 1600, '여의도': 230, '압구정': 1300, '옥수': 320, '서울숲': 980, '뚝섬': 190, '잠실': 770}
GU = {'마곡': '강서구', '망원': '마포구', '여의도': '영등포구', '압구정': '강남구', '옥수': '성동구', '서울숲': '성동구', '뚝섬': '광진구', '잠실': '송파구'}
# 엘리베이터: 서울교통공사 설치현황(2026.9.1) 지상 출구 엘리베이터 / 비관할역은 OSM 확인 여부
ELEV = {'마곡': 'OSM 확인(9호선)', '망원': '2·8번 출구', '여의도': '4번 출구', '압구정': '2·3번 출구', '옥수': '4·5번 출구',
        '서울숲': '미확인(코레일)', '뚝섬': '1번 출구', '잠실': '2·7번 출구'}

hci = pd.read_csv('results/hci_2026.csv', index_col=0, encoding='utf-8-sig')
pet = pd.read_csv('data/pet_registration_2022.csv', encoding='cp949')
dogs = pet[pet['시도'] == '서울특별시'].set_index('시군구')['개등록 누계']
acc = pd.read_csv('data/access_paths.csv', index_col=0, encoding='utf-8-sig')

t = pd.DataFrame(index=list(OFFICIAL_M))
t['인접역'] = hci['인접역']; t['공식도보m'] = pd.Series(OFFICIAL_M); t['HCI'] = hci['HCI']
t['자치구'] = pd.Series(GU); t['반려견등록(구)'] = t['자치구'].map(dogs)
mm = lambda s: (s - s.min()) / (s.max() - s.min())
t['가족수요점수'] = (mm(t['HCI']) + mm(t['반려견등록(구)'])) / 2
t['엘리베이터'] = pd.Series(ELEV)
t['OSM일반m'] = acc['일반경로m'].round(0); t['OSM계단없음m'] = acc['계단없는경로m'].round(0)
t['OSM검증오차'] = (t['OSM일반m'] / t['공식도보m'] - 1)
t['OSM신뢰'] = t['OSM검증오차'].abs() <= 0.3
t['유아차추가m'] = np.where(t['OSM신뢰'], (t['OSM계단없음m'] - t['OSM일반m']).clip(lower=0), np.nan)
t['도보부담_일반(분)'] = t['공식도보m'] * 2 / 100
t['도보부담_고령층(분)'] = t['도보부담_일반(분)'] * 1.2
t['도보부담_유아차(분)'] = (t['공식도보m'] + t['유아차추가m']) * 2 / 100
t.to_csv('results/pier_diagnosis.csv', encoding='utf-8-sig')

# ⑥ 건강 코스: 출발역 → 승선 선착장 → (배) → 하선 선착장 → 공원 산책 → 도착역. 경로당 좌표 확보 전 역을 출발점으로 둔 기본형
C = [('잠실→뚝섬', '잠실', '뚝섬', 17, '11:00·12:00·13:00·14:00·15:30·16:30'),
     ('여의도→망원', '여의도', '망원', 22, '12:12·13:12·14:12·15:12·16:52'),
     ('옥수→서울숲', '옥수', '서울숲', 18, '13:13·15:15·16:35')]
rows = []
for name, a, b, ivt, deps in C:
    base_m = OFFICIAL_M[a] + OFFICIAL_M[b]
    for stride in (0.6, 0.65, 0.7):
        rows.append(dict(코스=name, 보폭=stride, 접근도보m=base_m, 접근걸음=base_m / stride,
                         배위분=ivt, 평일낮출발=deps,
                         **{f'{g}보_필요산책m': max(0, g * stride - base_m) for g in (6000, 8000)}))
course = pd.DataFrame(rows); course.to_csv('results/health_courses.csv', index=False, encoding='utf-8-sig')

# ④ 요금 시나리오
fare = []
for f in (3000, 5000, 7000, 10000):
    r = {'주말 성인 요금': f, '가족 왕복(성인2·어린이2)': (f * 2 + 1100 * 2) * 2}
    for e in (-0.3, -0.43, -0.6):
        q = (f / 3000) ** e; r[f'이용변화 ε={e}'] = q - 1; r[f'운임수입변화 ε={e}'] = q * f / 3000 - 1
    fare.append(r)
fare = pd.DataFrame(fare); fare.to_csv('results/fare_scenarios.csv', index=False, encoding='utf-8-sig')

pd.set_option('display.width', 250)
print(t.round(2).to_string()); print(course.round(0).to_string()); print(fare.round(3).to_string())
