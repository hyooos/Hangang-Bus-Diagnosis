"""고령층 보행속도 가정 비교: 기존(1.2→1.0m/s, 배율 1.2) vs 경찰청 신호 설계 속도(1.0→0.8m/s, 배율 1.25)."""
import pandas as pd
d = pd.read_csv('results/pier_diagnosis.csv', index_col=0, encoding='utf-8-sig')
v = pd.read_csv('results/boat_vs_subway.csv', index_col=0, encoding='utf-8-sig')
kc = pd.read_csv('results/kyungrodang_courses.csv', encoding='utf-8-sig')
OLD, NEW = 1.2 / 1.0, 1.0 / 0.8
# 1) 선착장별 도보 부담(체감, 분)과 실제 걷는 시간(분)
t = pd.DataFrame(index=d.index)
t['인접역'] = d['인접역']; t['도보m'] = d['공식도보m']
t['일반 체감(분)'] = d['도보부담_일반(분)']
t['고령 체감_기존(×1.2)'] = t['일반 체감(분)'] * OLD
t['고령 체감_경찰청(×1.25)'] = t['일반 체감(분)'] * NEW
t['실제 걷는 시간 1.0m/s'] = t['도보m'] / 1.0 / 60
t['실제 걷는 시간 0.8m/s'] = t['도보m'] / 0.8 / 60
t.to_csv('results/elderly_speed_pier.csv', encoding='utf-8-sig')
# 2) 역→역 TFI(고령층): 도보 부분만 배율 적용
WALK = {'마곡': 720, '망원': 1600, '여의도': 230, '압구정': 1300, '옥수': 320, '서울숲': 980, '뚝섬': 190, '잠실': 770}
OD = {'마곡→잠실': ('마곡', '잠실'), '뚝섬→잠실': ('뚝섬', '잠실'), '여의도→잠실': ('여의도', '잠실'), '마곡→여의도': ('마곡', '여의도'), '압구정→잠실': ('압구정', '잠실')}
r = []
for k, (o, de) in OD.items():
    w = (WALK[o] + WALK[de]) * 2 / 100
    base = v.loc[k, '한강버스_배TFI']
    r.append({'구간': k, '일반': base + w, '고령_기존': base + w * OLD, '고령_경찰청': base + w * NEW,
              '차이(경찰청-기존)': w * (NEW - OLD), '지하철 대비_일반': (base + w) / v.loc[k, '지하철TFI'],
              '지하철 대비_고령_경찰청': (base + w * NEW) / v.loc[k, '지하철TFI']})
od = pd.DataFrame(r).set_index('구간'); od.to_csv('results/elderly_speed_od.csv', encoding='utf-8-sig')
# 3) 경로당 코스 소요시간(걷는 시간만): 8,000보 = 5,200m, 0.8 vs 1.0m/s
c = kc.sort_values('경로당_선착장m').groupby(['출발선착장', '도착']).head(2).copy()
c['경로당→선착장 1.0m/s(분)'] = c['경로당_선착장m'] / 1.0 / 60
c['경로당→선착장 0.8m/s(분)'] = c['경로당_선착장m'] / 0.8 / 60
c['8000보 총 걷는시간 1.0m/s(분)'] = 8000 * 0.65 / 1.0 / 60
c['8000보 총 걷는시간 0.8m/s(분)'] = 8000 * 0.65 / 0.8 / 60
c = c[['출발선착장', '도착', '경로당', '경로당_선착장m', '경로당→선착장 1.0m/s(분)', '경로당→선착장 0.8m/s(분)',
       '배위분', '8000보 총 걷는시간 1.0m/s(분)', '8000보 총 걷는시간 0.8m/s(분)']]
c.to_csv('results/elderly_speed_course.csv', index=False, encoding='utf-8-sig')
pd.set_option('display.width', 250)
print(t.round(1).to_string()); print(od.round(2).to_string()); print(c.round(1).to_string())
