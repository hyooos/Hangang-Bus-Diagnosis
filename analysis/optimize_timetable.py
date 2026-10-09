"""③ 처방 메뉴: 선박 수 제약 하 시간표 격자 전수탐색.
결정변수: 노선별 배차(h_서측, h_동측), 여의도 출발 오프셋(잠실행 o1, 마곡행 o2), 동측 정차 패턴(교차/전편).
목적함수: 정류장 가중치 w로 합한 체감 통행시간(TFI) — 각 선착장에서 노선 끝(잠실 방향 → 잠실, 마곡 방향 → 마곡)까지.
제약: ceil(97/h_서측) + ceil(동측 왕복/h_동측) <= 12척, 운항 11~21시, 최소 환승 3분.
평가: 11:00~18:40 1분 간격 도착 승객이 TFI 최소 배 조합을 고른다고 보고 평균."""
import sys, math, itertools; sys.path.insert(0, 'analysis')
import numpy as np, pandas as pd

W_WAIT, PEN, MIN_TR, N_SHIP = 1.8, 10, 3, 12
T0, T1, START, END = 11 * 60, 18 * 60 + 40, 11 * 60 - 240, 21 * 60 + 30
# 현행 시간표에서 읽은 노선 시작점 기준 경과시간(분). 도착은 공식 구간시간 추정과 같은 방식
WEST_E = {'마곡': 0, '망원': 22, '여의도': 48}                     # 마곡 출발 → 여의도 도착
WEST_W = {'여의도': 0, '망원': 22, '마곡': 41}                      # 여의도 출발 → 마곡 도착
EAST_E = {'옥수': {'여의도': 0, '옥수': 35, '서울숲': 53, '뚝섬': 71, '잠실': 85},
          '압구정': {'여의도': 0, '압구정': 32, '서울숲': 53, '뚝섬': 71, '잠실': 85},
          '전편': {'여의도': 0, '압구정': 32, '옥수': 42, '서울숲': 60, '뚝섬': 78, '잠실': 92}}
EAST_W = {'옥수': {'잠실': 0, '뚝섬': 17, '서울숲': 35, '옥수': 52, '여의도': 90},
          '압구정': {'잠실': 0, '뚝섬': 17, '서울숲': 35, '압구정': 55, '여의도': 84},
          '전편': {'잠실': 0, '뚝섬': 17, '서울숲': 35, '옥수': 52, '압구정': 62, '여의도': 91}}
CYCLE_W, CYCLE_E = 97, {'교차': 180, '전편': 194}

def line(offsets_by_trip, h, phase):
    """출발 간격 h, 위상 phase로 하루 운항편 생성. 편마다 정차 패턴(dict)을 번갈아 적용."""
    trips = []
    for i, d in enumerate(range(START + phase, END, h)):
        pat = offsets_by_trip[i % len(offsets_by_trip)]
        trips.append({s: d + m for s, m in pat.items()})
    return trips

def legs(trips, o, dst):
    return sorted((t[o], t[dst]) for t in trips if o in t and dst in t)

def tfi_mean(L):
    out = []
    for t in range(T0, T1 + 1):
        best = None
        if len(L) == 1:
            for d, a in L[0]:
                if d >= t: c = W_WAIT * (d - t) + (a - d); best = c if best is None else min(best, c)
        else:
            for d1, a1 in L[0]:
                if d1 < t or d1 > t + 200: continue
                for d2, a2 in L[1]:
                    if d2 < a1 + MIN_TR or d2 > a1 + 200: continue
                    c = W_WAIT * ((d1 - t) + (d2 - a1)) + (a1 - d1) + (a2 - d2) + PEN
                    best = c if best is None else min(best, c)
        if best is not None: out.append(best)
    return np.mean(out)

PIERS = ['마곡', '망원', '여의도', '압구정', '옥수', '서울숲', '뚝섬', '잠실']
hci = pd.read_csv('results/hci_2026.csv', index_col=0, encoding='utf-8-sig')['HCI']
WEIGHTS = {'균등': pd.Series(1.0, index=PIERS), 'HCI': hci.reindex(PIERS)}

def evaluate(hw, he, pattern):
    pats_e = [EAST_E['전편']] if pattern == '전편' else [EAST_E['옥수'], EAST_E['압구정']]
    pats_w = [EAST_W['전편']] if pattern == '전편' else [EAST_W['옥수'], EAST_W['압구정']]
    we, ww = line([WEST_E], hw, 0), line([WEST_W], hw, 0)
    # 잠실 방향(동행): 서측 선착장은 여의도 환승(오프셋 o1에 의존), 동측 선착장은 직행
    east_fixed = {s: tfi_mean([legs(line(pats_e, he, 0), s, '잠실')]) for s in ['여의도', '압구정', '옥수', '서울숲', '뚝섬']}
    west_fixed = {s: tfi_mean([legs(line(pats_w, he, 0), s, '여의도'), legs(ww, '여의도', '마곡')]) * 0 for s in []}
    best_o1 = None
    for o1 in range(he):
        ee = line(pats_e, he, (48 + o1) % he)
        v = {s: tfi_mean([legs(we, s, '여의도'), legs(ee, '여의도', '잠실')]) for s in ['마곡', '망원']}
        if best_o1 is None or sum(v.values()) < sum(best_o1[1].values()): best_o1 = (o1, v)
    # 마곡 방향(서행): 동측 선착장은 여의도 환승(오프셋 o2), 서측 선착장(여의도·망원)은 직행
    west_direct = {s: tfi_mean([legs(ww, s, '마곡')]) for s in ['여의도', '망원']}
    best_o2 = None
    for o2 in range(hw):
        ewl = line(pats_w, he, 0)
        wwl = line([WEST_W], hw, o2)
        v = {s: tfi_mean([legs(ewl, s, '여의도'), legs(wwl, '여의도', '마곡')]) for s in ['잠실', '뚝섬', '서울숲', '옥수', '압구정']}
        if best_o2 is None or sum(v.values()) < sum(best_o2[1].values()): best_o2 = (o2, v)
    east = {**east_fixed, **best_o1[1]}; west = {**west_direct, **best_o2[1]}
    return east, west, best_o1[0], best_o2[0]

def score(east, west, w):
    num = sum(w[s] * east[s] for s in east) + sum(w[s] * west[s] for s in west)
    den = sum(w[s] for s in east) + sum(w[s] for s in west)
    return num / den

if __name__ == '__main__':
    H = [60, 45, 40, 30, 25, 20]
    rows = []
    for hw, he, pat in itertools.product(H, H, ['교차', '전편']):
        ships = math.ceil(CYCLE_W / hw) + math.ceil(CYCLE_E[pat] / he)
        if ships > N_SHIP: continue
        east, west, o1, o2 = evaluate(hw, he, pat)
        r = dict(서측배차=hw, 동측배차=he, 정차패턴=pat, 선박=ships, 오프셋_잠실행=o1, 오프셋_마곡행=o2,
                 마곡_잠실=east['마곡'], 뚝섬_잠실=east['뚝섬'], 잠실_마곡=west['잠실'])
        for k, w in WEIGHTS.items(): r[f'가중TFI_{k}'] = score(east, west, w)
        rows.append(r); print(r, flush=True)
    df = pd.DataFrame(rows)
    for k in WEIGHTS: df[f'순위_{k}'] = df[f'가중TFI_{k}'].rank().astype(int)
    df = df.sort_values('가중TFI_균등')
    df.to_csv('results/optimize_grid.csv', index=False, encoding='utf-8-sig')
    pd.set_option('display.width', 250); print(df.round(1).head(15).to_string(index=False))
    print('Spearman(균등 vs HCI)', round(df['가중TFI_균등'].rank().corr(df['가중TFI_HCI'].rank(), method='spearman'), 3))
