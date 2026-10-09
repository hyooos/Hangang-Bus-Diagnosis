import numpy as np, pandas as pd
tt = pd.read_csv('data/hangang_timetable.csv', dtype=str, keep_default_na=False)
m = lambda s: int(s[:2]) * 60 + int(s[3:]) if s else np.nan
tt['DEP'] = tt.DEP_HM.map(m); tt['ARR'] = tt.ARR_HM.map(m)

def leg(route, dirc, o, d):
    """현행 시간표에서 o 출발 → d 도착 [(출발, 도착)]"""
    out = []
    for _, tr in tt[(tt.ROUTE_CD == route) & (tt.DIR_CD == dirc)].groupby('TRIP_NO'):
        tr = tr.set_index('STOP_NM')
        if o in tr.index and d in tr.index:
            dep = tr.loc[o, 'DEP']; arr = tr.loc[d, 'ARR'] if not np.isnan(tr.loc[d, 'ARR']) else tr.loc[d, 'DEP']
            out.append((dep, arr))
    return sorted(out)

def earliest_arrival(t, legs, i=0, min_tr=3):
    if i == len(legs): return t, []
    ready = t if i == 0 else t + min_tr
    best, bp = np.inf, None
    for dep, arr in legs[i]:
        if dep < ready: continue
        if dep >= best: break
        fin, p = earliest_arrival(arr, legs, i + 1, min_tr)
        if p is not None and fin < best: best, bp = fin, [(dep, arr)] + p
    return best, bp

def evaluate(legs, t0, t1, w=1.8, pen=10):
    rows = []
    for t in range(int(t0), int(t1) + 1):
        _, p = earliest_arrival(t, legs)
        if p is None: continue
        w1 = p[0][0] - t; wtr = sum(p[k+1][0] - p[k][1] for k in range(len(p) - 1)); ivt = sum(a - d for d, a in p)
        rows.append((w1, wtr, ivt, ivt + w * (w1 + wtr) + pen * (len(p) - 1)))
    return pd.DataFrame(rows, columns=['첫대기', '환승대기', '배위', 'TFI']).mean()
