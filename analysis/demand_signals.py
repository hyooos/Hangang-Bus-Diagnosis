"""② 휴일 쏠림 지수(HCI) — 공식 연계교통 안내(노선도) 기준 인접역. 2026.1~8 본 분석, 2025.1~8 검증."""
import glob, numpy as np, pandas as pd

HOL = pd.to_datetime([
    '2025-01-01', '2025-01-27', '2025-01-28', '2025-01-29', '2025-01-30', '2025-03-03', '2025-05-05', '2025-05-06',
    '2025-06-03', '2025-06-06', '2025-08-15',
    '2026-01-01', '2026-02-16', '2026-02-17', '2026-02-18', '2026-03-02', '2026-05-05', '2026-05-25', '2026-06-03', '2026-08-17',
    '2024-01-01', '2024-02-09', '2024-02-12', '2024-03-01', '2024-04-10', '2024-05-06', '2024-05-15', '2024-06-06',
    '2024-08-15', '2024-09-16', '2024-09-17', '2024-09-18', '2024-10-01', '2024-10-03', '2024-10-09', '2024-12-25'])
is_hol = lambda d: (d.dt.weekday >= 5) | d.isin(HOL)

# 선착장: (1순위 공식 인접역, 도보 m), 2순위(검증용), 기존 분석에서 쓴 역
PIER = {'마곡':   ('양천향교', 720, '마곡나루'),   '망원':  ('마포구청', 1600, '망원'),
        '여의도': ('여의나루', 230, '여의도'),     '압구정': ('압구정', 1300, None),
        '옥수':   ('옥수', 320, None),           '서울숲': ('서울숲', 980, None),
        '뚝섬':   ('자양', 190, None),           '잠실':  ('잠실새내', 770, '잠실')}

def load(year):
    fs = sorted(glob.glob(f'data/CARD_SUBWAY_MONTH_{year}*.csv'))
    def rd(f):
        for enc in ('utf-8-sig', 'cp949'):
            try: return pd.read_csv(f, encoding=enc, index_col=False)
            except UnicodeDecodeError: pass
    df = pd.concat([rd(f) for f in fs], ignore_index=True)
    df['DATE'] = pd.to_datetime(df['사용일자'].astype(str), format='%Y%m%d')
    df['HOL'] = is_hol(df['DATE'])
    df['STN'] = df['역명'].str.replace(r'\(.*\)', '', regex=True).str.strip()
    return df

def hci_table(df):
    day_all = df.groupby(['DATE', 'HOL'])['하차총승객수'].sum().reset_index()
    seoul = day_all[day_all.HOL]['하차총승객수'].mean() / day_all[~day_all.HOL]['하차총승객수'].mean()
    day = df.groupby(['DATE', 'HOL', 'STN'])['하차총승객수'].sum().reset_index()
    def one(stn):
        d = day[day.STN == stn]
        if d.empty: return (np.nan,) * 3
        w, h = d[~d.HOL]['하차총승객수'].mean(), d[d.HOL]['하차총승객수'].mean()
        return w, h, h / w
    rows = []
    for pier, (s1, dist, s2) in PIER.items():
        w, h, r = one(s1)
        r2 = one(s2)[2] if s2 else np.nan
        rows.append(dict(선착장=pier, 인접역=s1, 도보m=dist, 평일평균하차=w, 휴일평균하차=h,
                         휴일평일비=r, HCI=r / seoul, 비교역=s2, 비교역HCI=r2 / seoul if s2 else np.nan))
    return pd.DataFrame(rows).set_index('선착장'), seoul, day

if __name__ == '__main__':
    pd.set_option('display.width', 220)
    out = {}
    for y in (2026, 2025):
        t, seoul, day = hci_table(load(y)); out[y] = t
        print(f'== {y}.1~8  서울 전체 휴일/평일 = {seoul:.3f}  (일수 {day.DATE.nunique()})')
        print(t.sort_values('HCI', ascending=False).round(2).to_string())
        t.to_csv(f'results/hci_{y}.csv', encoding='utf-8-sig')
        if y == 2026:
            # 월별 휴일 일평균 하차(계절성)
            day['월'] = day.DATE.dt.month
            mon = (day[day.HOL & day.STN.isin([v[0] for v in PIER.values()])]
                   .groupby(['STN', '월'])['하차총승객수'].mean().unstack().round(0))
            mon.to_csv('results/holiday_monthly_2026.csv', encoding='utf-8-sig'); print(mon.to_string())
    r = pd.concat({y: out[y]['HCI'].rank(ascending=False) for y in out}, axis=1)
    print('순위 비교(2026 vs 2025)\n', r.to_string(), '\nSpearman', r.corr(method='spearman').iloc[0, 1].round(3))
