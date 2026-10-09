"""최소 환승시간(2/3/5분) 민감도: 현행 여의도 환승대기 + 통근 시나리오 TFI·순위."""
import sys; sys.path.insert(0, 'analysis')
import numpy as np, pandas as pd
import scenarios as S
from sim_core import tt

g = lambda r, d, s, c: tt[(tt.ROUTE_CD == r) & (tt.DIR_CD == d) & (tt.STOP_NM == s)][c].dropna().values
def tw(arr, dep, mt):
    dep = np.sort(dep); idx = np.searchsorted(dep, arr + mt); ok = idx < len(dep); return dep[idx[ok]] - arr[ok]

rows, tfi, rank = [], {}, {}
for mt in (2, 3, 5):
    a = tw(g('서측', '여의도행', '여의도', 'ARR'), g('동측', '잠실행', '여의도', 'DEP'), mt)
    b = tw(g('동측', '여의도행', '여의도', 'ARR'), g('서측', '마곡행', '여의도', 'DEP'), mt)
    rows.append({'최소환승(분)': mt, '마곡→잠실 평균': a.mean(), '범위': f'{a.min():.0f}~{a.max():.0f}',
                 '잠실→마곡 평균': b.mean(), '범위 ': f'{b.min():.0f}~{b.max():.0f}'})
    S.MIN_TR = mt
    t = S.table()
    tfi[f'{mt}분'] = t['마곡→잠실 TFI']; tfi[f'{mt}분 변화'] = t['마곡→잠실 변화']
    rank[f'{mt}분'] = t['마곡→잠실 TFI'].rank().astype(int)
tw_df = pd.DataFrame(rows); tf = pd.DataFrame(tfi); rk = pd.DataFrame(rank)
tw_df.to_csv('results/min_transfer_waits.csv', index=False, encoding='utf-8-sig')
tf.to_csv('results/min_transfer_scenarios.csv', encoding='utf-8-sig'); rk.to_csv('results/min_transfer_rank.csv', encoding='utf-8-sig')
pd.set_option('display.width', 200)
print(tw_df.round(1).to_string()); print(tf.round(3).to_string()); print(rk.to_string())
