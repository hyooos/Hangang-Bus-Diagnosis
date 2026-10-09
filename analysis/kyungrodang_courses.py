"""⑥ 경로당 출발 건강 코스. 경로당 좌표 = 전국마을회관및경로당표준데이터(서울 12개 구 제공, 강서·강남 포함).
경로당 → 출발 선착장: OSM 계단 없는 보행 최단거리(마곡·압구정은 OSM 경로가 공식 도보거리와 ±10% 이내로 검증된 선착장).
배 → 도착 선착장 → 공원 산책 → 도착역(공식 도보거리). 귀가는 지하철(걸음 수 제외)."""
import math, numpy as np, pandas as pd, networkx as nx, osmnx as ox
ox.settings.use_cache = True; ox.settings.cache_folder = 'data/osm_cache'; ox.settings.requests_timeout = 180
def hav(a, b):
    R = 6371000; p1, p2 = map(math.radians, (a[0], b[0])); dl = math.radians(b[1] - a[1]); dp = p2 - p1
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))
def has_steps(d):
    hw = d.get('highway'); return 'steps' in (hw if isinstance(hw, list) else [hw])

k = pd.read_csv('data/kyungrodang_standard_seoul.csv', encoding='utf-8-sig')
k = k[(k.BUSI_COD_NM == '영업') & (k.FLCT_TYP.astype(str).str.contains('경로당'))].dropna(subset=['LAT', 'LOT'])
ORIG = {'마곡': ((37.57503, 126.84395), '강서구'), '압구정': ((37.52666, 127.01649), '강남구')}
# 코스: 출발 선착장 → 도착 선착장, 배 위 시간(현행 시간표), 평일 낮 출발편, 도착 선착장→도착역 공식 도보거리
COURSE = {'마곡': [('여의도', 48, '11:20·12:20·13:20·14:20·15:00·15:30·16:00·17:00', '여의나루', 230)],
          '압구정': [('뚝섬', 39, '14:07·16:12·17:02', '자양', 190), ('여의도', 29, '12:55·14:55', '여의나루', 230)]}
STRIDE = 0.65; R = 1500
rows = []
for pier, ((lat, lon), gu) in ORIG.items():
    cand = k[k.INSTT_NM.str.contains(gu)].copy()
    cand['직선m'] = [hav((a, b), (lat, lon)) for a, b in zip(cand.LAT, cand.LOT)]
    cand = cand[cand['직선m'] <= R]
    import time
    for i in range(12):
        ox.settings.overpass_url = ['https://overpass-api.de/api', 'https://overpass.private.coffee/api', 'https://maps.mail.ru/osm/tools/overpass/api'][i % 3]
        try: G = ox.graph_from_point((lat, lon), dist=R + 600, network_type='walk'); break
        except Exception as e: print('retry', i, type(e).__name__, flush=True); time.sleep(30)
    G.remove_edges_from([(u, v, kk) for u, v, kk, d in G.edges(keys=True, data=True) if has_steps(d)])
    # 선착장 접속점: 선착장에 가장 가까운 노드(마곡·압구정은 간격 66~108m → 간격을 직선으로 더함)
    pn = ox.distance.nearest_nodes(G, lon, lat); gap = hav((G.nodes[pn]['y'], G.nodes[pn]['x']), (lat, lon))
    dist = nx.single_source_dijkstra_path_length(G, pn, weight='length')
    for _, r in cand.iterrows():
        n = ox.distance.nearest_nodes(G, r.LOT, r.LAT)
        if n not in dist: continue
        d = dist[n] + gap + hav((G.nodes[n]['y'], G.nodes[n]['x']), (r.LAT, r.LOT))
        for dest, ivt, deps, stn, egress in COURSE[pier]:
            base = d + egress
            rows.append(dict(출발선착장=pier, 경로당=r.FLCT_NM, 주소=r.LCTN_ROAD_NM_ADDR or r.LCTN_LOTNO_ADDR,
                             경로당_선착장m=round(d), 도착=dest, 배위분=ivt, 평일낮출발=deps, 도착역=stn,
                             기본걸음=round(base / STRIDE), 산책_6000보m=max(0, round(6000 * STRIDE - base)),
                             산책_8000보m=max(0, round(8000 * STRIDE - base))))
df = pd.DataFrame(rows).sort_values(['출발선착장', '도착', '경로당_선착장m'])
df.to_csv('results/kyungrodang_courses.csv', index=False, encoding='utf-8-sig')
summ = df.groupby(['출발선착장', '도착']).agg(경로당수=('경로당', 'nunique'), 최단m=('경로당_선착장m', 'min'),
        중앙m=('경로당_선착장m', 'median'), 산책8000_중앙m=('산책_8000보m', 'median'),
        걸어서1km이내=('경로당_선착장m', lambda s: int((s <= 1000).sum())))
summ.to_csv('results/kyungrodang_course_summary.csv', encoding='utf-8-sig')
pd.set_option('display.width', 250)
print(summ.to_string()); print(df.groupby(['출발선착장', '도착']).head(5).to_string())
