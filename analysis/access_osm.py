"""③ 인접역 → 선착장 보행 경로: 일반(계단 허용) vs 계단 없는 경로(highway=steps 제거). OpenStreetMap(OSMnx).
출발점: 일반 = 선착장에 가장 가까운 지하철 출입구, 계단 없음 = 역 반경 400m 안에서 선착장에 가장 가까운 엘리베이터(없으면 출입구 중 wheelchair=yes, 그것도 없으면 일반 출입구로 두고 표시)."""
import json, time, math
import numpy as np, pandas as pd, networkx as nx, osmnx as ox, requests

ox.settings.use_cache = True; ox.settings.cache_folder = 'data/osm_cache'; ox.settings.requests_timeout = 180
OVP = 'https://overpass-api.de/api/interpreter'
PIERS = {'마곡': (37.57503, 126.84395, '양천향교'), '망원': (37.55461, 126.89443, '마포구청'),
         '여의도': (37.52844, 126.93513, '여의나루'), '압구정': (37.52666, 127.01649, '압구정'),
         '옥수': (37.53880, 127.01797, '옥수'), '서울숲': (37.53778, 127.04093, '서울숲'),
         '뚝섬': (37.52881, 127.06647, '자양'), '잠실': (37.51877, 127.08478, '잠실새내')}

import hashlib, os
def overpass(q, tries=10):
    fp = f"data/osm_cache/q_{hashlib.md5(q.encode()).hexdigest()}.json"
    if os.path.exists(fp): return json.load(open(fp))
    for i in range(tries):
        r = requests.post(OVP, data={'data': q}, headers={'User-Agent': 'hangang-recipe-research'}, timeout=200)
        if r.status_code == 200:
            el = r.json()['elements']; os.makedirs('data/osm_cache', exist_ok=True); json.dump(el, open(fp, 'w')); return el
        time.sleep(20)
    raise RuntimeError('overpass failed')

def hav(a, b):
    R = 6371000; p1, p2 = map(math.radians, (a[0], b[0])); dl = math.radians(b[1] - a[1]); dp = p2 - p1
    return 2 * R * math.asin(math.sqrt(math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))

def station_points(name, pier):
    q = f'''[out:json][timeout:90];
    node["railway"="station"]["name"~"^{name}"](around:3000,{pier[0]},{pier[1]})->.s;
    (node(around.s:400)["railway"="subway_entrance"]; node(around.s:400)["highway"="elevator"];);
    out body; .s out body;'''
    el = overpass(q)
    st = [e for e in el if e['tags'].get('railway') == 'station']
    ent = [e for e in el if e['tags'].get('railway') == 'subway_entrance']
    elv = [e for e in el if e['tags'].get('highway') == 'elevator'
           or e['tags'].get('wheelchair') == 'yes']
    return st, ent, elv

def has_steps(d):
    hw = d.get('highway'); return 'steps' in (hw if isinstance(hw, list) else [hw])

rows = []
for pier, (lat, lon, stn) in PIERS.items():
    st, ent, elv = station_points(stn, (lat, lon))
    if not ent and not st: rows.append(dict(선착장=pier, 인접역=stn, 비고='역 좌표 없음')); continue
    near = lambda pts: min(pts, key=lambda e: hav((e['lat'], e['lon']), (lat, lon)))
    o_gen = near(ent) if ent else near(st)
    o_sf, sf_src = (near(elv), '엘리베이터') if elv else (o_gen, '출입구(엘리베이터 미확인)')
    dist = int(hav((o_gen['lat'], o_gen['lon']), (lat, lon)) + 900)
    G = ox.graph_from_point((lat, lon), dist=dist, network_type='walk', retain_all=False)
    Gsf = G.copy(); Gsf.remove_edges_from([(u, v, k) for u, v, k, d in G.edges(keys=True, data=True) if has_steps(d)])
    def L(Gx, o):
        # 출발점에서 도달 가능한 노드 중 '경로거리 + 선착장까지 직선 간격'이 최소인 지점. 간격이 크면 OSM에서 선착장까지 연결이 끊긴 것
        n = ox.distance.nearest_nodes(Gx, o['lon'], o['lat'])
        dd = nx.single_source_dijkstra_path_length(Gx, n, weight='length')
        gaps = {v: hav((Gx.nodes[v]['y'], Gx.nodes[v]['x']), (lat, lon)) for v in dd}
        gmin = min(gaps.values())
        best = min((v for v in dd if gaps[v] <= gmin + 20), key=lambda v: dd[v])   # 선착장에 가장 가까이 닿는 지점들 중 최단
        gap = gaps[best]
        return dd[best] + gap, gap
    (lg, gg), (ls, gs) = L(G, o_gen), L(Gsf, o_sf)
    rows.append(dict(선착장=pier, 인접역=stn, 일반출발=o_gen['tags'].get('ref', o_gen['tags'].get('name', '')),
                     일반경로m=lg, 일반_미연결간격m=gg, 계단없음출발=sf_src, 계단없는경로m=ls, 계단없음_미연결간격m=gs,
                     직선거리m=hav((o_gen['lat'], o_gen['lon']), (lat, lon)),
                     계단구간수=sum(has_steps(d) for _, _, d in G.edges(data=True))))
    print(rows[-1], flush=True)
df = pd.DataFrame(rows).set_index('선착장')
df['유아차추가m'] = df['계단없는경로m'] - df['일반경로m']
df.to_csv('data/access_paths.csv', encoding='utf-8-sig'); print(df.round(0).to_string())
