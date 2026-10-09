"""통근 시나리오 시뮬레이션. 평가 창: 11:00~18:40에 1분 간격으로 도착하는 가상 승객(전 시나리오 공통).
승객은 체감비용(TFI)이 가장 작은 배 조합을 고름. 무조정(비동기화) 시나리오는 두 노선 출발시각 차이를 0~배차-1분까지 1분 간격으로 바꿔 평균."""
import math, sys
import numpy as np, pandas as pd
sys.path.insert(0, 'analysis'); from sim_core import leg

W_WAIT, PEN, MIN_TR = 1.8, 10, 3
T_W, T_E, T_E_EXP, T_YD_TT = 48, 85, 69, 71      # 마곡→여의도, 여의도→잠실(일반/급행), 여의도 출발→뚝섬 출발
T0, T1 = 11 * 60, 18 * 60 + 40

def best(t, legs, w=W_WAIT, pen=PEN):
    if len(legs) == 1:
        c = [(w * (d - t) + (a - d), d - t, 0, a - d) for d, a in legs[0] if d >= t]
        return min(c) if c else None
    out = None
    for d1, a1 in legs[0]:
        if d1 < t or d1 > t + 180: continue
        for d2, a2 in legs[1]:
            if d2 < a1 + MIN_TR or d2 > a1 + 180: continue
            c = (w * ((d1 - t) + (d2 - a1)) + (a1 - d1) + (a2 - d2) + pen, d1 - t, d2 - a1, (a1 - d1) + (a2 - d2))
            if out is None or c < out: out = c
    return out

def evaluate(legs, w=W_WAIT, pen=PEN):
    r = [best(t, legs, w, pen) for t in range(T0, T1 + 1)]
    r = np.array([x for x in r if x is not None])
    return pd.Series(dict(TFI=r[:, 0].mean(), 첫대기=r[:, 1].mean(), 환승대기=r[:, 2].mean(), 배위=r[:, 3].mean()))

def gen(hw, offset=0, sync=False, express=False, first=11 * 60, last=21 * 60):
    w0 = first - 4 * 60                                  # 평가 창 이전부터 이미 운항 중인 상태로 생성
    west = [(d, d + T_W) for d in range(w0, last, hw)]
    e0 = (w0 + T_W + MIN_TR) if sync else (w0 + offset)
    east = [(d, d + (T_E_EXP if (express and i % 2) else T_E), express and i % 2 == 1)
            for i, d in enumerate(range(e0, last, hw))]
    mz = [west, [(d, a) for d, a, _ in east]]
    tj = [[(d + T_YD_TT, d + T_E) for d, a, x in east if not x]]
    return mz, tj

def ships(hw, express=False):
    east_cycle = (180 + (180 - 2 * (T_E - T_E_EXP))) / 2 if express else 180
    return math.ceil(97 / hw) + math.ceil(east_cycle / hw)

def run(hw, sync=False, express=False, w=W_WAIT, pen=PEN):
    offs = [0] if sync else range(0, hw, 1)
    a = [evaluate(gen(hw, o, sync, express)[0], w, pen) for o in offs]
    b = [evaluate(gen(hw, o, sync, express)[1], w, pen) for o in offs]
    return pd.concat(a, axis=1).mean(1), pd.concat(b, axis=1).mean(1)

def current_sync():
    """현행 편성 유지 + 여의도 동기화: 서측 출발은 그대로, 동측 잠실행 출발을 서측 도착+3분으로 이동"""
    west = leg('서측', '여의도행', '마곡', '여의도')
    east = [(a + MIN_TR, a + MIN_TR + T_E) for _, a in west]
    return [west, east], [[(d + T_YD_TT, d + T_E) for d, _ in east]]

SC = {
    '현행 시간표':                    None,
    '현행 편성 + 여의도 동기화':        'cur_sync',
    '60분 배차(무조정)':               dict(hw=60),
    '60분 배차 + 동기화':              dict(hw=60, sync=True),
    '60분 배차 + 격편 급행(무조정)':     dict(hw=60, express=True),
    '30분 배차 + 동기화':              dict(hw=30, sync=True),
    '15분 배차(무조정)':               dict(hw=15),
    '15분 배차 + 동기화':              dict(hw=15, sync=True),
    '15분 배차 + 동기화 + 격편 급행':    dict(hw=15, sync=True, express=True),
}

def table(w=W_WAIT, pen=PEN):
    rows = {}
    for name, kw in SC.items():
        if kw is None:
            mz = [leg('서측', '여의도행', '마곡', '여의도'), leg('동측', '잠실행', '여의도', '잠실')]
            tj = [leg('동측', '잠실행', '뚝섬', '잠실')]
            a, b, s = evaluate(mz, w, pen), evaluate(tj, w, pen), None
        elif kw == 'cur_sync':
            mz, tj = current_sync(); a, b, s = evaluate(mz, w, pen), evaluate(tj, w, pen), None
        else:
            a, b = run(w=w, pen=pen, **kw); s = ships(kw['hw'], kw.get('express', False))
        rows[name] = {'마곡→잠실 TFI': a.TFI, '첫대기': a.첫대기, '환승대기': a.환승대기, '배위': a.배위,
                      '뚝섬→잠실 TFI': b.TFI, '뚝섬 첫대기': b.첫대기, '필요 선박': s}
    df = pd.DataFrame(rows).T
    for col, base in [('마곡→잠실 TFI', df.iloc[0]['마곡→잠실 TFI']), ('뚝섬→잠실 TFI', df.iloc[0]['뚝섬→잠실 TFI'])]:
        df[col.split()[0] + ' 변화'] = df[col] / base - 1
    for e in (-0.3, -0.5, -0.7):
        df[f'수요 ε={e}'] = (df['마곡→잠실 TFI'] / df.iloc[0]['마곡→잠실 TFI']) ** e - 1
    return df

if __name__ == '__main__':
    df = table()
    df.to_csv('results/scenarios.csv', encoding='utf-8-sig')
    pd.set_option('display.width', 250)
    print(df.round(3).to_string())
    # 민감도: 가중치에 따른 순위
    ranks = {}
    for w in (1.7, 1.8, 2.0):
        for pen in (10, 15):
            t = table(w, pen)
            ranks[f'w={w},pen={pen}'] = t['마곡→잠실 TFI'].rank().astype(int)
    rk = pd.DataFrame(ranks); rk.to_csv('results/scenario_rank_sensitivity.csv', encoding='utf-8-sig')
    print(rk.to_string())
