"""시간대 수요 비율 예측 (한강버스 데이터레시피 5-C-1 단계, 포털 분류: 예측 모델 / GLM 예측)

목적: 다음 시간표 개편 시점(예: 2027년 4월)의 요일유형별 시간대 수요 비율을 예측해
      timeslot_allocation.py 의 배분 가중치로 넘긴다.

입력: 서울 열린데이터광장 '지하철 호선별 역별 시간대별 승하차 인원 정보' 월별 CSV 여러 개
      (각 파일에 사용월, 호선명, 지하철역, 'HH시-HH시 하차인원' 컬럼)
모델: 포아송 GLM (로그 링크), 단위 = 역 x 월 x 시간대(11~20시), 타깃 = 하차 인원
      log E[y] = log(그 달 일수) + 역×시간대 + 시간대×휴일비율 + 역×휴일비율 + 월(계절)
      월 합계 자료라 평일·주말이 섞여 있지만, 달마다 주말·공휴일 비율이 달라서
      '휴일비율' 항으로 평일 모양(휴일비율=0)과 주말·휴일 모양(=1)을 분리해 낸다.
검증: 마지막 6개월을 떼어 두고 블록 비율 WAPE를 기준값(전년 같은 달 실측 비율)과 비교.
      GLM이 기준값을 이기지 못하면 기준값 비율을 그대로 쓴다.

실행: python3 timeslot_demand_glm.py <CSV들이 있는 폴더> <예측 대상 월 YYYYMM>
출력: timeslot_shares.csv (요일유형, 노선, 시간대 블록, 수요 비율)
"""
import glob
import re
import sys
import calendar

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import holidays as hol

ROUTES = {"서측": ["양천향교", "마포구청", "여의나루"],
          "동측": ["여의나루", "압구정", "옥수", "서울숲", "자양", "잠실새내"]}
STATIONS = sorted(set(sum(ROUTES.values(), [])))
HOURS = range(11, 21)
BLOCKS = [(11, 13), (13, 15), (15, 17), (17, 19), (19, 21)]
EXCLUDE = {"05-01", "07-17"}  # 팀 HCI 계산과 같은 공휴일 기준을 쓰기 위한 제외 목록(확인 필요)


def holiday_share(yyyymm):
    y, m = divmod(int(yyyymm), 100)
    kr = hol.KR(years=[y])
    days = calendar.monthrange(y, m)[1]
    n = 0
    for d in range(1, days + 1):
        dt = pd.Timestamp(y, m, d)
        if dt.weekday() >= 5 or (dt.date() in kr and dt.strftime("%m-%d") not in EXCLUDE):
            n += 1
    return n / days, days


def load(folder):
    frames = []
    for f in sorted(glob.glob(f"{folder}/*.csv")):
        for enc in ("utf-8-sig", "cp949"):
            try:
                df = pd.read_csv(f, encoding=enc)
                break
            except UnicodeDecodeError:
                continue
        mon_col = next(c for c in df.columns if "월" in c and "인원" not in c)
        stn_col = next(c for c in df.columns if "역" in c and "인원" not in c)
        df["STN"] = df[stn_col].astype(str).str.replace(r"\(.*\)", "", regex=True).str.strip()
        df = df[df["STN"].isin(STATIONS)]
        for c in df.columns:
            mm = re.match(r"\s*(\d{1,2})시-\d{1,2}시\s*하차", str(c))
            if mm and int(mm.group(1)) in HOURS:
                g = df.groupby([mon_col, "STN"])[c].sum().reset_index()
                g.columns = ["ym", "stn", "y"]
                g["hour"] = int(mm.group(1))
                frames.append(g)
    d = pd.concat(frames).groupby(["ym", "stn", "hour"], as_index=False)["y"].sum()
    d["ym"] = d["ym"].astype(int)
    hs = {ym: holiday_share(ym) for ym in d["ym"].unique()}
    d["hshare"] = d["ym"].map(lambda v: hs[v][0])
    d["days"] = d["ym"].map(lambda v: hs[v][1])
    d["moy"] = d["ym"] % 100
    return d


FORMULA = "y ~ C(stn):C(hour) + C(hour):hshare + C(stn):hshare + C(moy)"


def fit(d):
    return smf.glm(FORMULA, data=d, family=sm.families.Poisson(),
                   offset=np.log(d["days"])).fit()


def route_block_shares(frame, col):
    out = {}
    for r, stns in ROUTES.items():
        s = frame[frame["stn"].isin(stns)]
        tot = {b: s[(s["hour"] >= b[0]) & (s["hour"] < b[1])][col].sum() for b in BLOCKS}
        z = sum(tot.values())
        out[r] = {b: tot[b] / z for b in BLOCKS}
    return out


def wape(pred, act):
    num = sum(abs(pred[r][b] - act[r][b]) for r in ROUTES for b in BLOCKS)
    return num / sum(act[r][b] for r in ROUTES for b in BLOCKS)


def main(folder, target):
    d = load(folder)
    months = sorted(d["ym"].unique())
    test = months[-6:]
    train = d[~d["ym"].isin(test)]
    m = fit(train)
    w_glm, w_base = [], []
    for ym in test:
        act_f = d[d["ym"] == ym]
        act = route_block_shares(act_f, "y")
        p = act_f.copy()
        p["mu"] = m.predict(p, offset=np.log(p["days"]))
        w_glm.append(wape(route_block_shares(p, "mu"), act))
        prev = d[d["ym"] == ym - 100]
        if len(prev):
            w_base.append(wape(route_block_shares(prev, "y"), act))
    g, b = np.mean(w_glm), (np.mean(w_base) if w_base else float("nan"))
    print(f"검증(마지막 6개월) 블록 비율 WAPE: GLM {g:.3f} / 기준값(전년 같은 달) {b:.3f}")
    use_glm = not (b == b) or g < b

    full = fit(d)
    rows = []
    t = int(target)
    for day, h in (("평일", 0.0), ("주말·휴일", 1.0)):
        grid = pd.DataFrame([(s, hr) for s in STATIONS for hr in HOURS], columns=["stn", "hour"])
        grid["hshare"], grid["moy"], grid["days"] = h, t % 100, 1
        grid["mu"] = full.predict(grid, offset=np.zeros(len(grid)))
        if use_glm:
            sh = route_block_shares(grid, "mu")
        else:
            prev = d[d["ym"] == t - 100]
            sh = route_block_shares(prev if len(prev) else d[d["ym"] == months[-1]], "y")
        for r in ROUTES:
            for blk in BLOCKS:
                rows.append({"요일유형": day, "노선": r, "시간대": f"{blk[0]}~{blk[1]}시",
                             "수요비율": round(sh[r][blk], 4)})
        lvl = grid.groupby("stn")["mu"].sum()
        if day == "평일":
            wd = lvl
        else:
            print("모델이 본 역별 주말·휴일/평일 하루 하차 비(11~21시):",
                  (lvl / wd).round(2).to_dict())
    pd.DataFrame(rows).to_csv("timeslot_shares.csv", index=False, encoding="utf-8-sig")
    print(f"사용한 비율: {'GLM 예측' if use_glm else '기준값(전년 같은 달)'} → timeslot_shares.csv")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
