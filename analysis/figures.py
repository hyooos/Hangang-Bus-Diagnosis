import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family': 'AppleGothic', 'axes.unicode_minus': False, 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False, 'axes.edgecolor': '#b5b4ae',
                     'axes.labelcolor': '#52514e', 'xtick.color': '#52514e', 'ytick.color': '#52514e',
                     'figure.facecolor': '#fcfcfb', 'axes.facecolor': '#fcfcfb', 'savefig.dpi': 200})
B, O, A, Y, GRAY, INK, INK2 = '#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#c9c8c1', '#0b0b0b', '#52514e'
OUT = 'results/figures/'
def grid(ax, axis='x'): ax.grid(axis=axis, color='#e7e6e1', lw=0.8); ax.set_axisbelow(True)

# [1] 시나리오 TFI 구성
sc = pd.read_csv('results/scenarios.csv', index_col=0, encoding='utf-8-sig')
order = ['현행 시간표', '현행 편성 + 여의도 동기화', '60분 배차 + 동기화', '60분 배차 + 격편 급행(무조정)',
         '30분 배차 + 동기화', '15분 배차 + 동기화', '15분 배차 + 동기화 + 격편 급행']
d = sc.loc[order][::-1]
fig, ax = plt.subplots(figsize=(9, 4.6))
y = np.arange(len(d)); left = np.zeros(len(d))
parts = [('배위', '배 위 시간', B, 1), ('첫대기', '첫 대기 ×1.8', O, 1.8), ('환승대기', '환승대기 ×1.8', Y, 1.8)]
for col, lab, c, w in parts:
    v = d[col].values * w; ax.barh(y, v, left=left, color=c, height=0.6, label=lab, edgecolor='#fcfcfb', lw=1.5); left += v
ax.barh(y, np.full(len(d), 10), left=left, color=GRAY, height=0.6, label='환승 벌점 10분', edgecolor='#fcfcfb', lw=1.5); left += 10
for i, (n, r) in enumerate(d.iterrows()):
    ship = '' if np.isnan(r['필요 선박']) else f"  ·  선박 {int(r['필요 선박'])}척"
    chg = '' if n == '현행 시간표' else f" ({r['마곡→잠실 TFI'] / sc.loc['현행 시간표', '마곡→잠실 TFI'] - 1:+.0%})"
    ax.text(left[i] + 3, i, f"{r['마곡→잠실 TFI']:.0f}분{chg}{ship}", va='center', color=INK, fontsize=9)
ax.set_yticks(y, d.index); ax.set_xlim(0, 330); ax.set_xlabel('체감 통행시간 TFI (분) — 마곡 → 잠실')
ax.legend(ncol=4, frameon=False, loc='upper center', bbox_to_anchor=(0.45, 1.12), fontsize=9); grid(ax)
ax.set_title('[1] 통근 시나리오별 체감 통행시간 구성', loc='left', color=INK, pad=28, fontsize=12)
fig.tight_layout(); fig.savefig(OUT + 'fig1_scenarios.png'); plt.close(fig)

# [1]-보조 여의도 환승대기(도착편별)
import sys; sys.path.insert(0, 'analysis')
from sim_core import tt
g = lambda r, dd, s, c: tt[(tt.ROUTE_CD == r) & (tt.DIR_CD == dd) & (tt.STOP_NM == s)][c].dropna().values
def tw(arr, dep):
    dep = np.sort(dep); idx = np.searchsorted(dep, arr + 3); return dep[idx] - arr
hm = lambda x: f'{int(x)//60:02d}:{int(x)%60:02d}'
fig, axs = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
for ax, (lab, a, dpt) in zip(axs, [('마곡→잠실 (서측 도착 → 동측 출발)', g('서측', '여의도행', '여의도', 'ARR'), g('동측', '잠실행', '여의도', 'DEP')),
                                   ('잠실→마곡 (동측 도착 → 서측 출발)', g('동측', '여의도행', '여의도', 'ARR'), g('서측', '마곡행', '여의도', 'DEP'))]):
    w = tw(np.sort(a), dpt); x = np.arange(len(w))
    ax.bar(x, w, color=[O if v > 30 else B for v in w], width=0.7)
    ax.axhline(30, color=INK2, lw=1, ls='--'); ax.text(len(w) - 0.5, 31, '무조정 기대값 30분', ha='right', fontsize=8, color=INK2)
    ax.axhline(4, color=A, lw=1, ls=':'); ax.text(len(w) - 0.5, 5, '동기화 시 3~5분', ha='right', fontsize=8, color=INK2)
    ax.set_xticks(x, [hm(v) for v in np.sort(a)], rotation=45, fontsize=8); ax.set_title(f'{lab}\n평균 {w.mean():.0f}분 · 최대 {w.max():.0f}분', fontsize=10, color=INK, loc='left')
    grid(ax, 'y')
axs[0].set_ylabel('환승 대기(분)'); axs[0].set_xlabel('여의도 도착 시각'); axs[1].set_xlabel('여의도 도착 시각')
fig.tight_layout(); fig.savefig(OUT + 'fig1b_transfer_wait.png'); plt.close(fig)

# [2] HCI + 월별 휴일 하차
h = pd.read_csv('results/hci_2026.csv', index_col=0, encoding='utf-8-sig').sort_values('HCI')
h25 = pd.read_csv('results/hci_2025.csv', index_col=0, encoding='utf-8-sig')
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), gridspec_kw={'width_ratios': [1, 1.2]})
ax = axs[0]; yy = np.arange(len(h))
ax.barh(yy, h['HCI'], color=[B if v > 1 else GRAY for v in h['HCI']], height=0.6)
ax.scatter(h25.loc[h.index, 'HCI'], yy, color=INK, s=14, zorder=3, label='2025.1~8')
for i, (n, r) in enumerate(h.iterrows()): ax.text(r['HCI'] + 0.03, i, f"{r['HCI']:.2f}", va='center', fontsize=9)
ax.axvline(1, color=INK2, lw=1, ls='--'); ax.text(1.01, len(h) - 0.4, '서울 평균', fontsize=8, color=INK2)
ax.set_yticks(yy, [f'{n}({r["인접역"]})' for n, r in h.iterrows()]); ax.set_xlim(0, 1.8); grid(ax)
ax.set_xlabel('휴일 쏠림 지수 HCI (2026.1~8, 막대) · 점 = 2025.1~8'); ax.set_title('[2] 선착장 인접역 휴일 쏠림 지수', loc='left', color=INK, fontsize=12)
mon = pd.read_csv('results/holiday_monthly_2026.csv', index_col=0, encoding='utf-8-sig')
ax = axs[1]
for stn, c in [('여의나루', B), ('자양', O), ('서울숲', A)]:
    ax.plot(mon.columns.astype(int), mon.loc[stn], color=c, lw=2, marker='o', ms=4); ax.text(8.1, mon.loc[stn].iloc[-1] + {'여의나루':0,'자양':450,'서울숲':-450}[stn], stn, color=INK, fontsize=9, va='center')
for stn in ['잠실새내', '압구정', '옥수', '마포구청', '양천향교']:
    ax.plot(mon.columns.astype(int), mon.loc[stn], color=GRAY, lw=1)
ax.set_xticks(range(1, 9), [f'{m}월' for m in range(1, 9)]); ax.set_xlim(0.8, 9); ax.set_ylabel('휴일 일평균 하차(명)'); grid(ax, 'y')
ax.set_title('휴일 일평균 하차의 계절 변화 (회색 = 나머지 인접역)', loc='left', color=INK, fontsize=10)
fig.tight_layout(); fig.savefig(OUT + 'fig2_hci.png'); plt.close(fig)

# [3] 가족 축 매트릭스
t = pd.read_csv('results/pier_diagnosis.csv', index_col=0, encoding='utf-8-sig')
fig, ax = plt.subplots(figsize=(7.5, 5))
xm, ym = t['도보부담_일반(분)'].median(), t['가족수요점수'].median()
ax.axvline(xm, color=GRAY, lw=1); ax.axhline(ym, color=GRAY, lw=1)
for n, r in t.iterrows():
    ok = '미확인' not in r['엘리베이터']
    ax.scatter(r['도보부담_일반(분)'], r['가족수요점수'], s=90, color=B if ok else '#fcfcfb', edgecolor=B, lw=2, zorder=3)
    ax.annotate(f"{n} ({r['인접역']} {int(r['공식도보m'])}m)", (r['도보부담_일반(분)'], r['가족수요점수']), xytext=(7, 4), textcoords='offset points', fontsize=9, color=INK)
ax.text(0.02, 0.97, '수요 높음 · 접근 쉬움\n→ 유아차 동반 탑승 시범', transform=ax.transAxes, va='top', fontsize=9, color=INK2)
ax.text(0.98, 0.97, '수요 높음 · 접근 어려움\n→ 접근 경로 개선 우선', transform=ax.transAxes, va='top', ha='right', fontsize=9, color=INK2)
ax.set_xlabel('인접역→선착장 도보 부담 (분, 공식 도보거리 × 100m당 2분)'); ax.set_ylabel('가족 수요 점수 (HCI·자치구 반려견 등록 수 정규화 평균)')
ax.set_xlim(0, 36); ax.set_ylim(0.1, 0.8); grid(ax, 'both')
ax.set_title('[3] 가족 축: 수요 × 접근 부담 (속 빈 점 = 역 엘리베이터 미확인)', loc='left', color=INK, fontsize=12)
fig.tight_layout(); fig.savefig(OUT + 'fig3_family_matrix.png'); plt.close(fig)

# [4] 요금
f = pd.read_csv('results/fare_scenarios.csv', encoding='utf-8-sig')
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8))
ax = axs[0]
ax.fill_between(f['주말 성인 요금'], f['이용변화 ε=-0.3'] * 100, f['이용변화 ε=-0.6'] * 100, color=B, alpha=0.15, lw=0)
ax.plot(f['주말 성인 요금'], f['이용변화 ε=-0.43'] * 100, color=B, lw=2, marker='o', ms=5)
for _, r in f.iloc[1:].iterrows(): ax.text(r['주말 성인 요금'], r['이용변화 ε=-0.43'] * 100 + 3, f"{r['이용변화 ε=-0.43']:+.0%}", ha='center', fontsize=9)
ax.set_xticks(f['주말 성인 요금'], [f'{v:,}원' for v in f['주말 성인 요금']]); ax.set_ylabel('주말 이용 변화 (%)'); grid(ax, 'y')
ax.set_title('주말 이용 변화 (선 ε=-0.43, 음영 -0.3~-0.6)', loc='left', fontsize=10, color=INK)
ax = axs[1]
ax.bar([f'{v:,}원' for v in f['주말 성인 요금']], f['가족 왕복(성인2·어린이2)'], color=[GRAY, O, O, O], width=0.6)
for i, v in enumerate(f['가족 왕복(성인2·어린이2)']): ax.text(i, v + 600, f'{v:,}원', ha='center', fontsize=9)
ax.set_ylabel('가족 왕복 부담 (원)'); grid(ax, 'y'); ax.set_title('성인 2·어린이 2 가족 왕복 부담', loc='left', fontsize=10, color=INK)
fig.suptitle('[4] 주말 요금 인상 시나리오', x=0.01, ha='left', fontsize=12, color=INK); fig.tight_layout(); fig.savefig(OUT + 'fig4_fare.png'); plt.close(fig)

# [5] 고령층 (두 패널, 한 축씩)
e = pd.read_csv('results/elderly_2024.csv', index_col=0, encoding='utf-8-sig').dropna(subset=['평일낮비중']).sort_values('평일낮_일평균')
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
yy = np.arange(len(e)); lab = [f'{n}({r["인접역"]})' for n, r in e.iterrows()]
axs[0].barh(yy, e['평일낮_일평균'], color=B, height=0.6); axs[0].axvline(1267, color=INK2, ls='--', lw=1)
axs[0].text(1290, len(e) - 0.45, '관할역 중앙값 1,267명', fontsize=8, color=INK2)
for i, v in enumerate(e['평일낮_일평균']): axs[0].text(v + 40, i, f'{v:,.0f}', va='center', fontsize=9)
axs[0].set_yticks(yy, lab); axs[0].set_xlabel('평일 10~17시 노인 하차 일평균(명)'); grid(axs[0])
axs[1].barh(yy, e['평일낮비중'] * 100, color=GRAY, height=0.6); axs[1].axvline(56.4, color=INK2, ls='--', lw=1)
axs[1].text(56.8, len(e) - 0.45, '관할역 평균 56.4%', fontsize=8, color=INK2)
for i, v in enumerate(e['평일낮비중']): axs[1].text(v * 100 + 0.5, i, f'{v:.1%}', va='center', fontsize=9)
axs[1].set_xlim(40, 62); axs[1].set_xlabel('평일 노인 하차 중 10~17시 비중(%)'); grid(axs[1])
fig.suptitle('[5] 선착장 인접역 평일 낮 고령층 이동 (2024, 서울교통공사 관할역)', x=0.01, ha='left', fontsize=12, color=INK)
fig.tight_layout(); fig.savefig(OUT + 'fig5_elderly.png'); plt.close(fig)

# [6] 건강 코스
c = pd.read_csv('results/health_courses.csv', encoding='utf-8-sig'); c = c[c['보폭'] == 0.65]
fig, ax = plt.subplots(figsize=(8, 3.4)); yy = np.arange(len(c))
ax.barh(yy, c['접근걸음'], color=B, height=0.55, label='역-선착장 도보')
ax.barh(yy, c['8000보_필요산책m'] / 0.65, left=c['접근걸음'], color=A, height=0.55, label='도착 공원 산책(8,000보까지)', edgecolor='#fcfcfb', lw=1.5)
for x, l in [(6000, '6,000보'), (8000, '8,000보')]: ax.axvline(x, color=INK2, ls='--', lw=1); ax.text(x, len(c) - 0.45, l, ha='center', fontsize=8, color=INK2)
for i, (_, r) in enumerate(c.iterrows()):
    ax.text(r['접근걸음'] / 2, i, f"{r['접근걸음']:,.0f}보", ha='center', va='center', color='white', fontsize=9)
    ax.text(8150, i, f"산책 {r['8000보_필요산책m'] / 1000:.1f}km · 배 {r['배위분']}분", va='center', fontsize=9, color=INK)
ax.set_yticks(yy, c['코스']); ax.set_xlim(0, 11000); ax.set_ylim(-1.3, len(c) - 0.4); ax.set_xlabel('하루 걸음 수 (보폭 0.65m)'); grid(ax)
ax.legend(frameon=False, loc='lower right', ncol=1, fontsize=8)
ax.set_title('[6] 건강 코스 걸음 수 (출발·도착 = 인접역 기본형)', loc='left', color=INK, fontsize=12, pad=18)
fig.tight_layout(); fig.savefig(OUT + 'fig6_health_course.png'); plt.close(fig)
print('ok')

# [7] 지하철 대비 TFI (역→역)
v = pd.read_csv('results/boat_vs_subway.csv', index_col=0, encoding='utf-8-sig').sort_values('비율_현행')
fig, ax = plt.subplots(figsize=(9, 3.8)); yy = np.arange(len(v)); hgt = 0.36
ax.barh(yy + hgt / 2, v['지하철TFI'], height=hgt, color=GRAY, label='지하철 TFI')
ax.barh(yy - hgt / 2, v['한강버스_역역TFI'], height=hgt, color=B, label='한강버스 TFI(현행, 역-선착장 도보 포함)')
for i, (n, r) in enumerate(v.iterrows()):
    t = f"{r['비율_현행']:.1f}배"
    if not np.isnan(r.get('비율_15분동기화', np.nan)): t += f"  (15분 배차+동기화 시 {r['비율_15분동기화']:.1f}배)"
    ax.text(r['한강버스_역역TFI'] + 4, i - hgt / 2, t, va='center', fontsize=9, color=INK)
    ax.text(r['지하철TFI'] + 4, i + hgt / 2, f"{r['지하철TFI']:.0f}분", va='center', fontsize=8, color=INK2)
ax.set_yticks(yy, v.index); ax.set_xlim(0, 400); ax.set_xlabel('체감 통행시간 TFI (분, 역→역, 평일 11:00~18:40 출발)'); grid(ax)
ax.axvline(0, color=INK2)
ax.legend(frameon=False, loc='lower right', fontsize=8)
ax.set_title('[7] 한강버스 vs 지하철 체감 통행시간 (판단선: 1.0 이하 경쟁 / 1.5 이상 통근 대체 어려움)', loc='left', color=INK, fontsize=11)
fig.tight_layout(); fig.savefig(OUT + 'fig7_boat_vs_subway.png'); plt.close(fig)

# [6]-b 경로당 출발 코스
kc = pd.read_csv('results/kyungrodang_courses.csv', encoding='utf-8-sig')
kc = kc.sort_values('경로당_선착장m').groupby(['출발선착장', '도착']).head(4)
kc = kc[~((kc['출발선착장'] == '압구정') & (kc['도착'] == '여의도'))]
kc['lab'] = kc['경로당'].str.replace('㉵', '') + ' (' + kc['출발선착장'] + '→' + kc['도착'] + ')'
kc = kc.iloc[::-1]; yy = np.arange(len(kc))
fig, ax = plt.subplots(figsize=(9, 4))
ax.barh(yy, kc['기본걸음'], color=B, height=0.55, label='경로당→선착장 + 도착 선착장→역')
ax.barh(yy, kc['산책_8000보m'] / 0.65, left=kc['기본걸음'], color=A, height=0.55, label='도착 공원 산책(8,000보까지)', edgecolor='#fcfcfb', lw=1.5)
for x, l in [(6000, '6,000보'), (8000, '8,000보')]: ax.axvline(x, color=INK2, ls='--', lw=1); ax.text(x, len(kc) - 0.4, l, ha='center', fontsize=8, color=INK2)
for i, (_, r) in enumerate(kc.iterrows()):
    ax.text(8150, i, f"경로당→선착장 {r['경로당_선착장m']:,}m · 산책 {r['산책_8000보m'] / 1000:.1f}km", va='center', fontsize=8.5, color=INK)
ax.set_yticks(yy, kc['lab']); ax.set_xlim(0, 12500); ax.set_ylim(-2.2, len(kc) - 0.3); ax.set_xlabel('하루 걸음 수 (보폭 0.65m)'); grid(ax)
ax.legend(frameon=False, loc='lower right', fontsize=8)
ax.set_title('[6] 경로당 출발 건강 코스 (계단 없는 경로, 가까운 경로당 4곳)', loc='left', color=INK, fontsize=12)
fig.tight_layout(); fig.savefig(OUT + 'fig6b_kyungrodang_course.png'); plt.close(fig)
print('ok2')
