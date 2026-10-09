import numpy as np, pandas as pd
tt = pd.read_csv('data/hangang_timetable.csv', dtype=str, keep_default_na=False)
m = lambda s: int(s[:2]) * 60 + int(s[3:]) if s else np.nan
tt['DEP'] = tt.DEP_HM.map(m); tt['ARR'] = tt.ARR_HM.map(m)

def expected_wait(d):
    h = np.diff(np.sort(d)); return (h**2).sum() / (2*h.sum())
ew = (tt.dropna(subset=['DEP']).groupby(['ROUTE_CD','DIR_CD','STOP_NM'])['DEP']
        .agg(편수='count', 첫배=lambda x: f'{int(x.min())//60:02d}:{int(x.min())%60:02d}',
             평균배차=lambda x: np.diff(np.sort(x)).mean(), 최대배차=lambda x: np.diff(np.sort(x)).max(),
             기대대기=expected_wait))
ew['균일시대기'] = ew.평균배차/2; ew['불규칙성벌점'] = ew.기대대기/ew.균일시대기
print(ew.round(2).to_string())

def tw(arr, dep, mt=3):
    dep = np.sort(dep); idx = np.searchsorted(dep, arr+mt); ok = idx < len(dep)
    return dep[idx[ok]] - arr[ok]
g = lambda r,d,s,c: tt[(tt.ROUTE_CD==r)&(tt.DIR_CD==d)&(tt.STOP_NM==s)][c].dropna().values
a1 = g('서측','여의도행','여의도','ARR'); w1 = tw(a1, g('동측','잠실행','여의도','DEP'))
a2 = g('동측','여의도행','여의도','ARR'); w2 = tw(a2, g('서측','마곡행','여의도','DEP'))
print('마곡→잠실 환승대기', w1, w1.mean(), w1.min(), w1.max())
print('잠실→마곡 환승대기', w2, w2.mean(), w2.min(), w2.max())
