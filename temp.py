'''#!/usr/bin/env python3
"""
HF_cache/ 이하 모든 하위 폴더의 *.arrow 파일을 찾아
같은 디렉터리에 같은 이름의 .jsonl 로 저장합니다.

예)
HF_cache/cases/GDPR/data-00000-of-00001.arrow
 -> HF_cache/cases/GDPR/data-00000-of-00001.jsonl
"""

import os
import json
import sys

ROOT = "HF_cache"   # 루트 디렉터리 (필요하면 변경)

# 옵션
OVERWRITE = False   # True로 하면 기존 jsonl를 덮어씀

# 가용한 로더 선택 (datasets 우선, 없으면 pyarrow 사용)
_loader = None
try:
    from datasets import Dataset
    def _load_arrow(path):
        # datasets는 단일 .arrow 파일을 직접 읽을 수 있습니다.
        return Dataset.from_file(path)
    _loader = "datasets"
except Exception:
    try:
        import pyarrow as pa
        import pyarrow.ipc as pa_ipc
        def _load_arrow(path):
            # pyarrow로 .arrow 파일을 스트림 읽기
            with pa.memory_map(path, "r") as source:
                reader = pa_ipc.RecordBatchFileReader(source)
                table = reader.read_all()
            return table  # pyarrow.Table 반환
        _loader = "pyarrow"
    except Exception:
        print("ERROR: 'datasets' 또는 'pyarrow' 중 최소 하나가 필요합니다.", file=sys.stderr)
        sys.exit(1)

def convert_arrow_to_jsonl(arrow_path: str, jsonl_path: str):
    """단일 .arrow 파일을 jsonl로 변환"""
    print(f"  -> Converting: {os.path.basename(arrow_path)}  ->  {os.path.basename(jsonl_path)}  (loader={_loader})")

    if _loader == "datasets":
        ds = _load_arrow(arrow_path)  # datasets.Dataset
        # 스트리밍으로 라인 바이 라인 저장
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for ex in ds:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        print(f"     Saved {len(ds)} lines")

    elif _loader == "pyarrow":
        table = _load_arrow(arrow_path)  # pyarrow.Table
        # 테이블을 행 단위로 변환 (대용량도 안전하게 처리)
        # pyarrow.Table.to_pylist()는 메모리 부담이 커질 수 있으므로
        # RecordBatch 단위로 순회
        count = 0
        with open(jsonl_path, "w", encoding="utf-8") as f:
            # Table은 여러 RecordBatch로 구성될 수 있음
            # to_batches()로 배치 단위 접근
            for batch in table.to_batches():
                # 각 배치를 pylist로 변환 후 라인 쓰기
                for row in batch.to_pylist():
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    count += 1
        print(f"     Saved {count} lines")
    else:
        raise RuntimeError("Unknown loader selected")

def main():
    if not os.path.isdir(ROOT):
        print(f"ERROR: '{ROOT}' 디렉터리가 없습니다. 스크립트를 루트에서 실행 중인지 확인하세요.", file=sys.stderr)
        sys.exit(1)

    arrow_files = []
    for dirpath, _, filenames in os.walk(ROOT):
        for fn in filenames:
            if fn.endswith(".arrow"):
                arrow_files.append(os.path.join(dirpath, fn))

    if not arrow_files:
        print("변환할 .arrow 파일을 찾지 못했습니다.")
        return

    print(f"총 {len(arrow_files)}개의 .arrow 파일을 변환합니다.\n")

    for arrow_path in sorted(arrow_files):
        jsonl_path = os.path.splitext(arrow_path)[0] + ".jsonl"

        # 덮어쓰기 옵션
        if os.path.exists(jsonl_path) and not OVERWRITE:
            print(f"[SKIP] 이미 존재: {jsonl_path}")
            continue

        try:
            print(f"Processing: {arrow_path}")
            convert_arrow_to_jsonl(arrow_path, jsonl_path)
        except Exception as e:
            print(f"[ERROR] 변환 실패: {arrow_path}\n        -> {e}", file=sys.stderr)

    print("\nDone.")

if __name__ == "__main__":
    main()
'''
import os
import networkx as nx
from pyvis.network import Network

import os
import networkx as nx
from pyvis.network import Network

LAW_TREE_DIR = "updated_kgs"

# PyVis에서 예약/충돌 가능 키
RESERVED_NODE_KEYS = {"id"}
RESERVED_EDGE_KEYS = {"source", "target", "from", "to", "id", "label"}  # ← label도 제거해서 표시 안 됨

# 관계명이 들어있을 법한 키 후보들(GraphML마다 다를 수 있음)
RELATION_KEYS = ("relation", "rel", "type", "name", "edge_type", "predicate", "label")

def sanitize_attrs(attrs: dict, reserved: set):
    if not attrs:
        return {}
    return {k: v for k, v in attrs.items() if k not in reserved}

def get_relation(attrs: dict) -> str | None:
    """여러 후보 키 중에서 관계명을 추출(소문자/트리밍)"""
    if not attrs:
        return None
    for k in RELATION_KEYS:
        if k in attrs and isinstance(attrs[k], str):
            return attrs[k].strip().lower()
    return None

for file in os.listdir(LAW_TREE_DIR):
    if not file.endswith(".graphml"):
        continue

    graphml_path = os.path.join(LAW_TREE_DIR, file)
    html_path = os.path.join(LAW_TREE_DIR, os.path.splitext(file)[0] + ".html")
    print(f"Processing {graphml_path} -> {html_path}")

    # 1) 그래프 로드
    G = nx.read_graphml(graphml_path)

    # 2) PyVis 네트워크 생성
    net = Network(height="800px", width="100%", directed=G.is_directed())

    # 3) 노드 추가
    for n, attrs in G.nodes(data=True):
        safe_attrs = sanitize_attrs(attrs, RESERVED_NODE_KEYS)
        if "label" not in safe_attrs:
            safe_attrs["label"] = str(n)
        net.add_node(str(n), **safe_attrs)

    # 4) 엣지 추가: subsume만 남기고, is subsumed by 및 그 외는 제외
    def edge_keep(attrs: dict) -> bool:
        rel = get_relation(attrs)
        return rel == "subsume"  # 이외( None 포함 )는 전부 제거

    if G.is_multigraph():
        for u, v, key, attrs in G.edges(keys=True, data=True):
            if not edge_keep(attrs):
                continue
            safe_attrs = sanitize_attrs(attrs, RESERVED_EDGE_KEYS)
            # title도 굳이 넣지 않음 (툴팁 비표시 원하면)
            net.add_edge(str(u), str(v), **safe_attrs)
    else:
        for u, v, attrs in G.edges(data=True):
            if not edge_keep(attrs):
                continue
            safe_attrs = sanitize_attrs(attrs, RESERVED_EDGE_KEYS)
            net.add_edge(str(u), str(v), **safe_attrs)

    # (선택) 물리 레이아웃 on/off
    net.toggle_physics(True)

    # 5) HTML 저장
    net.write_html(html_path, open_browser=False)

print("Done!")
