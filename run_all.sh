#!/usr/bin/env bash
# 전체 분석 재현 (프로젝트 루트에서 실행). 원자료는 data/README.md 참고.
# access_osm.py, kyungrodang_courses.py 는 OpenStreetMap(Overpass)에 접속하므로 인터넷이 필요함.
set -euo pipefail
cd "$(dirname "$0")"

python3 analysis/build_timetable.py            # 한강버스 시간표 정형화
python3 analysis/timetable_metrics.py          # 기대대기·여의도 환승대기
python3 analysis/diagnosis.py                  # 원인 분해(배차 몫·불규칙 몫·교차 정차)
python3 analysis/scenarios.py                  # 통근 시나리오 + 가중치 민감도
python3 analysis/demand_signals.py             # 휴일 쏠림 지수(2026·2025)
python3 analysis/optimize_timetable.py         # 12척 제약 격자 전수탐색(약 1분)
python3 analysis/elderly.py                    # 평일 낮 고령층 집중도
python3 analysis/access_osm.py                 # 계단 없는 보행 경로 (인터넷 필요)
python3 analysis/final_tables.py               # 선착장 진단표·요금 시나리오·건강 코스(역 기준)
python3 analysis/subway_tfi.py                 # 지하철 TFI
python3 analysis/compare_subway.py             # 한강버스 vs 지하철
python3 analysis/kyungrodang_courses.py        # 경로당 출발 건강 코스 (인터넷 필요)
python3 analysis/min_transfer_sensitivity.py   # 최소 환승시간 2/3/5분 민감도
python3 analysis/elderly_speed_sensitivity.py  # 고령층 보행속도 민감도
python3 analysis/figures.py                    # 그래프
