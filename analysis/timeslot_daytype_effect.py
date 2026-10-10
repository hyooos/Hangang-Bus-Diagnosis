"""5-C ③ 요일유형 구분의 효과: 주간 이용 가중 기대대기 vs 주간 선박 운용일(선박·일).
주간 이용 비중: 주말 51%, 평일 49%[S4]. 운항 10시간(11~21시), 방향당 하루 편수 N → 배차 600/N분, 기대대기 300/N분.
필요 선박 = ceil(97/배차) + ceil(180/배차)."""
import math, pandas as pd
WKND = 0.51
def plan(nw, ne):
    def one(n):
        h = 600 / n; return 300 / n, math.ceil(97 / h) + math.ceil(180 / h)
    (ww, sw), (we, se) = one(nw), one(ne)
    return dict(평일편수=nw, 주말편수=ne, 평일대기=ww, 주말대기=we, 주간가중대기=(1 - WKND) * ww + WKND * we,
                평일선박=sw, 주말선박=se, 주간선박일=5 * sw + 2 * se)
rows = {'A 매일 10편(현행 편수)': plan(10, 10), 'B 평일 10편 / 주말·휴일 20편': plan(10, 20),
        'C 매일 20편(30분 배차)': plan(20, 20), 'D 평일 10편 / 주말·휴일 24편(25분)': plan(10, 24)}
t = pd.DataFrame(rows).T
base = t.loc['A 매일 10편(현행 편수)']
t['대기변화'] = t['주간가중대기'] / base['주간가중대기'] - 1
t['추가선박일'] = t['주간선박일'] - base['주간선박일']
t['선박일당_대기감소(%p)'] = (-t['대기변화'] * 100 / t['추가선박일']).where(t['추가선박일'] > 0)
t.to_csv('results/timeslot_daytype_effect.csv', encoding='utf-8-sig')
pd.set_option('display.width', 220); print(t.round(2).to_string())
