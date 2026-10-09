"""역→역 기준 한강버스 TFI(도보 포함) ÷ 지하철 TFI."""
import sys; sys.path.insert(0, 'analysis')
import pandas as pd
from sim_core import leg
from scenarios import evaluate, run, current_sync
WALK = {'마곡': 720, '망원': 1600, '여의도': 230, '압구정': 1300, '옥수': 320, '서울숲': 980, '뚝섬': 190, '잠실': 770}
OD = {'마곡→잠실': ('마곡', '잠실', [leg('서측', '여의도행', '마곡', '여의도'), leg('동측', '잠실행', '여의도', '잠실')]),
      '뚝섬→잠실': ('뚝섬', '잠실', [leg('동측', '잠실행', '뚝섬', '잠실')]),
      '여의도→잠실': ('여의도', '잠실', [leg('동측', '잠실행', '여의도', '잠실')]),
      '마곡→여의도': ('마곡', '여의도', [leg('서측', '여의도행', '마곡', '여의도')]),
      '압구정→잠실': ('압구정', '잠실', [leg('동측', '잠실행', '압구정', '잠실')])}
sub = pd.read_csv('results/subway_tfi.csv', index_col=0, encoding='utf-8-sig')
best = {'마곡→잠실': run(15, sync=True)[0].TFI, '뚝섬→잠실': run(15, sync=True)[1].TFI}
rows = {}
for k, (o, d, legs) in OD.items():
    b = evaluate(legs); w = (WALK[o] + WALK[d]) * 2 / 100
    r = dict(한강버스_배TFI=b.TFI, 도보부담=w, 한강버스_역역TFI=b.TFI + w, 배위=b.배위,
             마찰비중=(b.TFI + w - b.배위) / (b.TFI + w), 지하철TFI=sub.loc[k, 'TFI'], 지하철소요=sub.loc[k, '소요'],
             지하철환승=sub.loc[k, '환승'])
    r['비율_현행'] = r['한강버스_역역TFI'] / r['지하철TFI']
    if k in best: r['비율_15분동기화'] = (best[k] + w) / r['지하철TFI']
    rows[k] = r
df = pd.DataFrame(rows).T
df.to_csv('results/boat_vs_subway.csv', encoding='utf-8-sig')
pd.set_option('display.width', 220); print(df.astype(float).round(2).to_string())
