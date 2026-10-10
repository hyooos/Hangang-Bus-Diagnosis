"""5-C ① 요일유형별 시간대 수요 비율 — 일 단위 자료로 평일/주말·휴일을 직접 분리.
입력: 서울교통공사 역별 일별 시간대별 승하차인원(data.go.kr 15048032, 2024년, 관할역만)
      ※ 월별 시간대 자료(OA-12252)는 서비스 종료. 일 단위라 GLM의 휴일비율 외삽이 필요 없음
출력: results/timeslot_shares.csv (인접역 전체) / results/timeslot_shares_river.csv (한강 지향역만, 인자 river)
      results/timeslot_hourly_profile.csv (역 × 요일유형 × 시간 하차 일평균)
수요 = 인접역 하차(한강 쪽으로 오는 사람). 양천향교(9호선)·서울숲(수인분당선)은 자료 없음 → 노선 내 나머지 역으로 대체"""
import sys; sys.path.insert(0, 'analysis')
import pandas as pd
from demand_signals import is_hol

ALL = {'서측': ['양천향교', '마포구청', '여의나루'],
       '동측': ['여의나루', '압구정', '옥수', '서울숲', '자양', '잠실새내']}
# 한강 지향역: 휴일 쏠림 지수(HCI)가 높은 역만(여의나루 1.43, 자양 1.53) — 업무·주거 역의 통근 하차를 배제
RIVER = {'서측': ['여의나루'], '동측': ['여의나루', '자양']}
VARIANT = sys.argv[1] if len(sys.argv) > 1 else 'all'
ROUTES = RIVER if VARIANT == 'river' else ALL
BLOCKS = [(11, 13), (13, 15), (15, 17), (17, 19), (19, 21)]
d = pd.read_csv('data/seoulmetro_hourly_2024.csv', encoding='cp949')
d['DATE'] = pd.to_datetime(d['수송일자']); d['요일유형'] = is_hol(d['DATE']).map({True: '주말·휴일', False: '평일'})
d['STN'] = d['역명'].str.replace(r'\(.*\)', '', regex=True).str.strip()
d = d[(d['승하차구분'] == '하차') & d['STN'].isin(sum(ALL.values(), []))]
hcol = {h: f'{h:02d}-{h+1:02d}시간대' for h in range(11, 21)}
days = d.groupby('요일유형')['DATE'].nunique()
prof = (d.groupby(['STN', '요일유형'])[list(hcol.values())].sum().div(days, level='요일유형', axis=0))
prof.columns = list(hcol.keys())
prof.to_csv('results/timeslot_hourly_profile.csv', encoding='utf-8-sig')

rows = []
for day in ['평일', '주말·휴일']:
    for r, stns in ROUTES.items():
        p = prof.xs(day, level='요일유형').reindex([s for s in stns if s in prof.index.get_level_values(0)])
        tot = {b: p[list(range(*b))].sum().sum() for b in BLOCKS}; z = sum(tot.values())
        for b in BLOCKS:
            rows.append({'요일유형': day, '노선': r, '시간대': f'{b[0]}~{b[1]}시', '수요비율': round(tot[b] / z, 4),
                         '하차_일평균': round(tot[b]), '사용역': '·'.join(p.index)})
out = pd.DataFrame(rows); out.to_csv('results/timeslot_shares.csv' if VARIANT == 'all' else 'results/timeslot_shares_river.csv', index=False, encoding='utf-8-sig')
pd.set_option('display.width', 200)
print('일수', days.to_dict())
print(out.pivot_table(index=['요일유형', '노선'], columns='시간대', values='수요비율').round(3).to_string())
lvl = prof[list(hcol.keys())].sum(axis=1).unstack()
print('역별 주말·휴일 ÷ 평일 하루 하차(11~21시)\n', (lvl['주말·휴일'] / lvl['평일']).round(2).to_string())
