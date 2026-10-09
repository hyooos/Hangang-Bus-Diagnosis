"""② 원인 분해: 정류장·방향별 기대대기를 '배차가 긴 몫(평균배차÷2)'과 '불규칙한 몫'으로 나누고 진단 신호를 판정."""
import sys; sys.path.insert(0, 'analysis')
import numpy as np, pandas as pd
from sim_core import tt

def ew(d):
    h = np.diff(np.sort(d)); return (h ** 2).sum() / (2 * h.sum())

rows = []
for (r, d, s), g in tt.dropna(subset=['DEP']).groupby(['ROUTE_CD', 'DIR_CD', 'STOP_NM']):
    dep = g['DEP'].values; h = np.diff(np.sort(dep))
    rows.append(dict(노선=r, 방향=d, 선착장=s, 편수=len(dep), 평균배차=h.mean(), 기대대기=ew(dep),
                     배차몫=h.mean() / 2, 불규칙몫=ew(dep) - h.mean() / 2, 불규칙성벌점=ew(dep) / (h.mean() / 2)))
t = pd.DataFrame(rows)
# 같은 노선·방향의 최대 편수 대비 정차 편수가 절반 이하이면 교차(격편) 정차 → 배차가 약 2배
t['노선최대편수'] = t.groupby(['노선', '방향'])['편수'].transform('max')
def diag(x):
    sig = []
    if x['불규칙성벌점'] >= 1.25: sig.append('불규칙')
    if x['편수'] <= x['노선최대편수'] / 2: sig.append('교차 정차')
    if x['평균배차'] >= 30: sig.append('배차 길이')
    return '·'.join(sig) if sig else '양호'
t['진단'] = t.apply(diag, axis=1)
t = t.drop(columns='노선최대편수').sort_values('기대대기')
t.to_csv('results/wait_decomposition.csv', index=False, encoding='utf-8-sig')
pd.set_option('display.width', 200); print(t.round(2).to_string(index=False))
print('기대대기 범위', round(t.기대대기.min(), 1), '~', round(t.기대대기.max(), 1), '/ 벌점', round(t.불규칙성벌점.min(), 2), '~', round(t.불규칙성벌점.max(), 2))
