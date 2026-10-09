"""⑤ 평일 낮(10~17시) 고령층 집중도 — 서울교통공사 노인 승하차 2024 (관할역만)."""
import sys; sys.path.insert(0, 'analysis')
import pandas as pd
from demand_signals import is_hol, PIER
e = pd.read_csv('data/seoulmetro_elderly_hourly_2024.csv', encoding='cp949')
e['DATE'] = pd.to_datetime(e['수송일자'])
e['STN'] = e['역명'].str.replace(r'\(.*\)', '', regex=True).str.strip()
hc = [c for c in e.columns if '시간대' in c]
dc = [f'{h:02d}-{h+1:02d}시간대' for h in range(10, 17)]
w = e[(e['승하차구분'] == '하차') & ~is_hol(e['DATE'])]
nd = w['DATE'].nunique()
g = w.groupby('STN')[hc].sum()
tab = pd.DataFrame({'평일낮비중': g[dc].sum(1) / g.sum(1), '평일낮_일평균': g[dc].sum(1) / nd, '평일전일_일평균': g.sum(1) / nd})
net = g[dc].sum().sum() / g.sum().sum()
tab['집중도지수'] = tab['평일낮비중'] / net
tab['평일낮_규모순위(전체역)'] = tab['평일낮_일평균'].rank(ascending=False).astype(int)
rows = {p: tab.loc[s] if s in tab.index else pd.Series(dtype=float) for p, (s, _, _) in PIER.items()}
out = pd.DataFrame(rows).T; out.insert(0, '인접역', [v[0] for v in PIER.values()])
out.to_csv('results/elderly_2024.csv', encoding='utf-8-sig')
print(f'관할역 전체 평일낮 비중 {net:.3f}, 평일 {nd}일, 역 {len(tab)}개, 역별 평일낮 일평균 중앙값 {tab["평일낮_일평균"].median():.0f}')
print(out.round(3).to_string())
