"""지하철 대비 TFI 비율. 서울교통공사 도시철도 열차운행시각표(2026.9.14, 평일) + 환승 소요시간(2025.3.17).
Connection Scan으로 출발역 도착 시각 t(11:00~18:40, 5분 간격)마다 가장 빨리 도착하는 경로를 찾고, 한강버스와 같은 TFI 식으로 환산."""
import sys; sys.path.insert(0, 'analysis')
import numpy as np, pandas as pd
from collections import defaultdict

W_WAIT, PEN, WALK_W = 1.8, 10, 1.6          # 환승 도보 1분 = 체감 1.6분(외부 보행 100m당 2분과 같은 비율)
T0, T1, STEP = 11 * 60, 18 * 60 + 40, 5

tt = pd.read_csv('data/subway_timetable_20260914.csv', encoding='cp949', low_memory=False)
tt = tt[tt['주중주말'] == 'DAY'].copy()
def tm(s):
    if not isinstance(s, str): return np.nan
    h, m, sec = map(int, s.split(':')); return h * 60 + m + sec / 60
tt['ARR'] = tt['열차도착시간'].map(tm); tt['DEP'] = tt['열차출발시간'].map(tm)
tt['ARR'] = tt['ARR'].fillna(tt['DEP']); tt['DEP'] = tt['DEP'].fillna(tt['ARR'])
tt = tt[(tt.DEP >= T0 - 30) & (tt.ARR <= T1 + 240)]
tt['STN'] = tt['역사명'].astype(str).str.replace(r'\(.*\)', '', regex=True).str.strip()

# 열차별 정차 순서 → 연결(connection)
conns = []
for (line, dirc, code), g in tt.sort_values('DEP').groupby(['호선', '방향', '열차코드']):
    g = g.sort_values('DEP'); rows = g[['STN', 'ARR', 'DEP']].values
    trip = f'{line}-{dirc}-{code}'; seg = 0
    for k in range(len(rows) - 1):
        (s1, a1, d1), (s2, a2, d2) = rows[k], rows[k + 1]
        if a2 - d1 > 20 or a2 < d1: seg += 1; continue          # 같은 코드의 다른 운행 분리
        conns.append((d1, a2, (line, s1), (line, s2), f'{trip}-{seg}'))
conns.sort(key=lambda c: c[0])
C_DEP = np.array([c[0] for c in conns])

# 환승: 같은 역명의 다른 호선 노드 간 도보(분)
tr = pd.read_csv('data/seoulmetro_transfer_20250317.csv', encoding='cp949')
def mm(s): m, sec = map(int, str(s).split(':')); return m + sec / 60
tr = tr.dropna(subset=['소요시간']); tr['MIN'] = tr['소요시간'].map(mm)
def ln(x):
    x = str(x).strip(); return int(x) if x.isdigit() else x
TRW = tr.assign(a=tr['환승시작 호선'].map(ln), b=tr['환승종료 호선'].map(ln), s=tr['환승시작역'].str.replace(r'\(.*\)', '', regex=True).str.strip()) \
        .groupby(['s', 'a', 'b'])['MIN'].median().to_dict()
lines_at = defaultdict(set)
for c in conns: lines_at[c[2][1]].add(c[2][0]); lines_at[c[3][1]].add(c[3][0])
def walk(s, a, b): return TRW.get((s, a, b), 4.0)                   # 자료에 없으면 4분 가정

def csa(origin, dest, t):
    S = defaultdict(lambda: np.inf); J = {}; T = {}
    for l in lines_at[origin]: S[(l, origin)] = t
    i0 = np.searchsorted(C_DEP, t)
    best = np.inf
    for d, a, u, v, trip in conns[i0:]:
        if d > best or d > t + 240: break
        if trip in T or S[u] <= d:
            if trip not in T: T[trip] = (d, u)
            if a < S[v]:
                S[v] = a; J[v] = (trip, T[trip], a, v)
                if v[1] == dest: best = min(best, a)
                for l2 in lines_at[v[1]]:
                    if l2 != v[0]:
                        w = walk(v[1], v[0], l2); n2 = (l2, v[1])
                        if a + w < S[n2]: S[n2] = a + w; J[n2] = ('walk', (a, v), a + w, n2)
    ends = [(S[(l, dest)], (l, dest)) for l in lines_at[dest]]
    fin, node = min(ends)
    if not np.isfinite(fin): return None
    legs, walks = [], []
    while node in J:
        kind, start, arr, n = J[node]
        if kind == 'walk': walks.append(arr - start[0]); node = start[1]
        else: legs.append((start[0], arr)); node = start[1]
    legs.reverse()
    if not legs: return None
    w1 = legs[0][0] - t; ivt = sum(a - d for d, a in legs); tw = sum(walks)
    wtr = sum(legs[k + 1][0] - legs[k][1] for k in range(len(legs) - 1)) - tw
    n = len(legs) - 1
    return dict(첫대기=w1, 환승대기=wtr, 환승도보=tw, 차내=ivt, 환승=n, 소요=fin - t,
                TFI=ivt + W_WAIT * (w1 + wtr) + PEN * n + WALK_W * tw)

ODS = [('마곡→잠실', '양천향교', '잠실새내'), ('뚝섬→잠실', '자양', '잠실새내'), ('여의도→잠실', '여의나루', '잠실새내'),
       ('마곡→여의도', '양천향교', '여의나루'), ('압구정→잠실', '압구정', '잠실새내')]
if __name__ == '__main__':
    out = {}
    for name, o, d in ODS:
        r = pd.DataFrame([x for t in range(T0, T1 + 1, STEP) if (x := csa(o, d, t))])
        out[name] = r.mean().round(1); print(name, o, '→', d, out[name].to_dict(), flush=True)
    pd.DataFrame(out).T.to_csv('results/subway_tfi.csv', encoding='utf-8-sig')
