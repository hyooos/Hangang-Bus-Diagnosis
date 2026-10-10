"""요일유형 x 시간대 배차 배분 (한강버스 데이터레시피 5-C 단계)

입력: 서울 열린데이터광장 '지하철 호선별 역별 시간대별 승하차 인원 정보'(OA-12252) 월별 CSV
      (사용월, 호선명, 지하철역, 'HH시-HH시 승차인원', 'HH시-HH시 하차인원' ... 형식)
출력: 노선(서측/동측) x 요일유형(평일/주말·휴일) x 2시간 블록별 편수, 배차, 필요 선박,
      수요 가중 기대대기(같은 편수를 균등 배분했을 때 대비)

방법: 블록 b의 편수를 n_b라 하면 그 블록 배차는 120/n_b분, 기대대기는 60/n_b분.
      목적 = Σ_b w_b · 60/n_b 를 최소화, 제약 = Σ_b n_b = N(하루 편수), n_b ≥ n_min,
      블록마다 서측+동측 필요 선박 ≤ 12척.
      목적이 n_b에 대해 볼록하고 분리 가능하므로, 최소 편수에서 시작해 한 편씩
      한계 효과 w_b·60·(1/n − 1/(n+1))가 가장 큰 블록에 더하는 탐욕법이 정수 최적해다.
      (제약이 없으면 연속해는 n_b ∝ √w_b, 즉 제곱근 규칙과 같다.)

실행: python3 analysis/timeslot_allocation.py results/timeslot_shares.csv [운항 선박 상한, 기본 12]
      (예비선 1척이면 11, 2척이면 10). 결과는 results/timeslot_allocation_<입력>_<선박>.csv
"""
import math
import re
import sys

import pandas as pd

# ---- 레시피 입력값 -------------------------------------------------------
ROUTES = {  # 노선: (선착장 공식 인접역, 왕복 운항시간 분)
    "서측": (["양천향교", "마포구청", "여의나루"], 97),
    "동측": (["여의나루", "압구정", "옥수", "서울숲", "자양", "잠실새내"], 180),
}
BLOCKS = [(11, 13), (13, 15), (15, 17), (17, 19), (19, 21)]  # 운항 시간대 11~21시
BUDGET = {"평일": 10, "주말·휴일": 20}  # 방향당 하루 편수: 평일=현행 유지, 주말=30분 배차(10척) 수준
FLEET = int(sys.argv[2]) if len(sys.argv) > 2 else 12   # 운항 선박 상한(예비선 제외)
N_MIN = 1  # 블록(2시간)당 최소 1편 = 최대 배차 120분


def read_csv(path):
    for enc in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("인코딩을 읽을 수 없음")


def block_weights(df):
    """노선별 2시간 블록 수요 비율 = 인접역 하차 합계를 11~21시 안에서 정규화."""
    stn_col = next(c for c in df.columns if "역" in c and "인원" not in c)
    df = df.copy()
    df["STN"] = df[stn_col].astype(str).str.replace(r"\(.*\)", "", regex=True).str.strip()
    hour_cols = {}
    for c in df.columns:
        m = re.match(r"\s*(\d{1,2})시-\d{1,2}시\s*하차", str(c))
        if m:
            hour_cols[int(m.group(1))] = c
    out = {}
    for r, (stations, _) in ROUTES.items():
        sub = df[df["STN"].isin(stations)]
        missing = set(stations) - set(sub["STN"])
        if missing:
            print(f"[경고] {r} 노선 인접역 미발견: {sorted(missing)}")
        tot = {b: sum(pd.to_numeric(sub[hour_cols[h]], errors="coerce").sum()
                      for h in range(b[0], b[1]) if h in hour_cols) for b in BLOCKS}
        s = sum(tot.values())
        out[r] = {b: tot[b] / s for b in BLOCKS}
    return out


def ships(n, T):
    """블록에 n편(120분 동안)을 띄울 때 필요한 선박 = ceil(왕복시간 / 배차)."""
    return math.ceil(T * n / 120)


def fleet_ok(plan, b):
    return sum(ships(plan[r][b], ROUTES[r][1]) for r in ROUTES) <= FLEET


def allocate(W, N):
    """두 노선을 함께 배정: 아직 N편을 못 채운 노선 중, 선박 제약을 지키면서
    가중 대기 감소가 가장 큰 (노선, 블록)에 한 편씩 더함. 노선 순서에 따른 왜곡이 없음."""
    plan = {r: {b: N_MIN for b in BLOCKS} for r in ROUTES}
    while any(sum(plan[r].values()) < N for r in ROUTES):
        best, gain = None, -1
        for r in ROUTES:
            if sum(plan[r].values()) >= N:
                continue
            for b in BLOCKS:
                n = plan[r][b]
                plan[r][b] += 1
                ok = fleet_ok(plan, b)
                plan[r][b] -= 1
                g = W[r][b] * 60 * (1 / n - 1 / (n + 1))
                if ok and g > gain:
                    best, gain = (r, b), g
        if best is None:
            print(f"[경고] 선박 제약({FLEET}척)으로 하루 {N}편을 다 배치하지 못함")
            break
        plan[best[0]][best[1]] += 1
    return plan


def wait(w, nb):
    return sum(w[b] * 60 / nb[b] for b in BLOCKS)


def shares_from_file(path):
    """timeslot_demand_glm.py 가 만든 요일유형별 비율을 읽음."""
    s = read_csv(path)
    out = {}
    for (day, r), g in s.groupby(["요일유형", "노선"]):
        out.setdefault(day, {})[r] = {
            tuple(int(x) for x in re.findall(r"\d+", row["시간대"])): row["수요비율"]
            for _, row in g.iterrows()}
    return out


def main(path):
    if "shares" in path:  # 예측 모델 결과(요일유형별 모양이 다름)
        WD = shares_from_file(path)
    else:                 # 월별 원자료 그대로(요일유형은 편수 예산으로만 구분)
        W0 = block_weights(read_csv(path))
        WD = {day: W0 for day in BUDGET}
    rows = []
    for day, N in BUDGET.items():
        W = WD[day]
        plan = allocate(W, N)
        for r, (_, T) in ROUTES.items():
            uni = {b: N / len(BLOCKS) for b in BLOCKS}
            base, opt = wait(W[r], uni), wait(W[r], plan[r])
            for b in BLOCKS:
                n = plan[r][b]
                rows.append({"요일유형": day, "노선": r, "시간대": f"{b[0]}~{b[1]}시",
                             "수요비율": round(W[r][b], 3), "편수": n,
                             "배차_분": round(120 / n), "필요선박": ships(n, T)})
            rows.append({"요일유형": day, "노선": r, "시간대": "합계",
                         "수요비율": 1.0, "편수": sum(plan[r].values()),
                         "필요선박": max(ships(plan[r][b], T) for b in BLOCKS),
                         "균등_가중대기_분": round(base, 1), "추천_가중대기_분": round(opt, 1),
                         "변화_pct": round((opt - base) / base * 100, 1)})
    res = pd.DataFrame(rows)
    import os
    tag = os.path.splitext(os.path.basename(path))[0].replace("timeslot_shares", "shares")
    res.to_csv(f"results/timeslot_allocation_{tag}_{FLEET}.csv", index=False, encoding="utf-8-sig")
    print(f"[운항 선박 상한 {FLEET}척, 입력 {path}]")
    print(res.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1])
