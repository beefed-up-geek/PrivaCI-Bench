'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GraphML → HTML (vis-network, physics-enabled)

- 의존성: networkx (pip install networkx)
- pyvis / jinja2 불필요 (CDN 기반 HTML 직접 생성)
- physics: enabled → 노드 자유 이동 (드래그 가능)
- subsume: 계층(파란색 실선)
- refer:   참조(주황색 점선)
- subsumedBy, referencedBy: 제외
- 노드 hover: content 툴팁(title)
"""

import json
from pathlib import Path
import networkx as nx

# ===== 경로 지정 =====
INPUT_GRAPHML = Path("law_tree/LawTree_HIPAA.graphml")         # 입력 .graphml
OUTPUT_HTML   = Path("law_tree/LawTree_HIPAA_move.html")  # 출력 html

# ===== 색상/스타일 =====
COLOR_NODE     = "#93c5fd"
COLOR_SUBSUME  = "#2563eb"   # 파란 실선
COLOR_REFER    = "#f59e0b"   # 주황 점선
NODE_SIZE      = 18

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Law Tree (Physics Enabled)</title>
<meta name="viewport" content="width=device-width, initial-scale=1" />
<style>
  html, body {{ height: 100%; margin: 0; background: #f8fafc; color: #111827; font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }}
  .wrap {{ max-width: 1200px; margin: 24px auto; padding: 0 12px; }}
  h1 {{ font-size: 20px; margin: 0 0 12px 0; font-weight: 600; }}
  #net {{ width: 100%; height: 80vh; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
  .legend {{ display:flex; gap:16px; align-items:center; margin: 10px 0 16px 0; font-size: 14px; }}
  .legend .item {{ display:inline-flex; align-items:center; gap:8px; }}
  .swatch {{ width:24px; height:4px; border-radius:2px; }}
</style>
</head>
<body>
  <div class="wrap">
    <h1>GDPR graph (physics: enabled, draggable)</h1>
    <div class="legend">
      <span class="item"><span class="swatch" style="background:{COLOR_SUBSUME}"></span> Hierarchy (subsume)</span>
      <span class="item"><span class="swatch" style="background:{COLOR_REFER}; border-bottom:1px dashed {COLOR_REFER}"></span> Reference (refer)</span>
    </div>
    <div id="net"></div>
  </div>

  <!-- vis-network CDN -->
  <script src="https://unpkg.com/vis-network@9.1.6/standalone/umd/vis-network.min.js"></script>
  <script>
    // 데이터 주입
    const nodes = new vis.DataSet({NODES_JSON});
    const edges = new vis.DataSet({EDGES_JSON});

    // 네트워크 옵션 (물리 ON)
    const options = {{
      physics: {{
        enabled: true,
        barnesHut: {{
          gravitationalConstant: -20000,
          springLength: 150,
          springConstant: 0.03,
          damping: 0.09,
          avoidOverlap: 0.1
        }},
        stabilization: {{
          iterations: 150,
          updateInterval: 25
        }}
      }},
      interaction: {{
        dragNodes: true,
        dragView: true,
        zoomView: true,
        hover: true
      }},
      nodes: {{
        shape: "dot",
        size: {NODE_SIZE},
        color: {{
          background: "{COLOR_NODE}",
          border: "#1e3a8a"
        }},
        font: {{
          size: 12,
          color: "#111827"
        }}
      }},
      edges: {{
        arrows: {{
          to: {{ enabled: true, scaleFactor: 0.8 }}
        }},
        smooth: {{
          enabled: true,
          type: "dynamic"
        }},
        width: 1.5
      }}
    }};

    const container = document.getElementById('net');
    const network = new vis.Network(container, {{ nodes, edges }}, options);

    // 참고) 필요하면 물리 토글도 가능:
    // network.setOptions({{ physics: {{ enabled: false }} }});
    // network.setOptions({{ physics: {{ enabled: true }} }});
  </script>
</body>
</html>
"""

def get_relation(edata: dict):
    return edata.get("relation") or edata.get("d4") or edata.get("label") or edata.get("type")

def parse_node_content(ndata: dict):
    raw = ndata.get("data") or ndata.get("d3")
    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
            return obj.get("content", "")
        except Exception:
            return raw
    return ""

def main():
    G = nx.read_graphml(str(INPUT_GRAPHML))

    # 노드 변환
    nodes = []
    for n, ndata in G.nodes(data=True):
        content = parse_node_content(ndata)
        nodes.append({
            "id": n,
            "label": n,
            "title": content,   # hover 툴팁
        })

    # 엣지 변환 (subsumedBy, referencedBy 제외)
    edges = []
    for u, v, edata in G.edges(data=True):
        rel = get_relation(edata)
        if not rel:
            continue
        rel = str(rel).lower()

        if rel == "subsume":
            edges.append({
                "from": u,
                "to": v,
                "color": {"color": COLOR_SUBSUME},
                "dashes": False
            })
        elif rel == "refer":
            edges.append({
                "from": u,
                "to": v,
                "color": {"color": COLOR_REFER},
                "dashes": True
            })
        else:
            # subsumedBy, referencedBy 등은 제외
            continue

    # HTML 빌드
    html = HTML_TEMPLATE.format(
        COLOR_SUBSUME=COLOR_SUBSUME,
        COLOR_REFER=COLOR_REFER,
        COLOR_NODE=COLOR_NODE,
        NODE_SIZE=NODE_SIZE,
        NODES_JSON=json.dumps(nodes, ensure_ascii=False),
        EDGES_JSON=json.dumps(edges, ensure_ascii=False),
    )

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(str(OUTPUT_HTML))

if __name__ == "__main__":
    main()
'''

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GraphML -> vis-network HTML 변환기
- 전체 노드의 1/10만 포함
- 엣지는 포함된 노드 사이의 것만 유지
- vis-network + Bootstrap + 로딩바 포함된 단일 HTML 생성
- 파일 상단 변수 또는 CLI 인자로 입력/출력 지정 가능
"""

import json
import random
import argparse
from pathlib import Path
import networkx as nx
from string import Template

# ====== 사용자 설정 (간단 사용 시 여기만 수정) ======
INPUT_GRAPHML  = "updated_kgs/role_kg_45k.graphml"     # 예: "mygraph.graphml"
OUTPUT_HTML    = "updated_kgs/role_kg_45k_mini.html"       # 예: "graph.html"
SAMPLE_FRACTION = 0.10               # 전체 노드 중 10%
RANDOM_SEED     = 42                 # 샘플 재현용
# ===================================================


# --- HTML 템플릿을 string.Template로 변경 ---
HTML_TEMPLATE = Template("""<!DOCTYPE html>
<html>
    <head>
        <meta charset="utf-8">
        
            <script src="lib/bindings/utils.js"></script>
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/dist/vis-network.min.css" integrity="sha512-WgxfT5LWjfszlPHXRmBWHkV2eceiWTOBvrKCNbdgDYTHrT2AeLCGbF4sZlZw3UMN3WtL0tGUoIAKsu8mllg/XA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
            <script src="https://cdnjs.cloudflare.com/ajax/libs/vis-network/9.1.2/dist/vis-network.min.js" integrity="sha512-LnvoEWDFrqGHlHmDD2101OrLcbsfkrzoSpvtSQtxK3RMnRV0eOkhhBN2dXHKRrUU8p2DGRTk35n4O8nWSVe1mQ==" crossorigin="anonymous" referrerpolicy="no-referrer"></script>
        
        <center>
          <h1></h1>
        </center>

        <link
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/css/bootstrap.min.css"
          rel="stylesheet"
          integrity="sha384-eOJMYsd53ii+scO/bJGFsiCZc+5NDVN2yr8+0RDqr0Ql0h+rP48ckxlpbzKgwra6"
          crossorigin="anonymous"
        />
        <script
          src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.0-beta3/dist/js/bootstrap.bundle.min.js"
          integrity="sha384-JEW9xMcG8R+pH31jmWH6WWP0WintQrMb4s7ZOdauHnUtxwoG2vI5DkLtS3qm9Ekf"
          crossorigin="anonymous"
        ></script>

        <style type="text/css">
             #mynetwork {
                 width: 100%;
                 height: 800px;
                 background-color: #ffffff;
                 border: 1px solid lightgray;
                 position: relative;
                 float: left;
             }
             #loadingBar {
                 position:absolute;
                 top:0px;
                 left:0px;
                 width: 100%;
                 height: 800px;
                 background-color:rgba(200,200,200,0.8);
                 -webkit-transition: all 0.5s ease;
                 -moz-transition: all 0.5s ease;
                 -ms-transition: all 0.5s ease;
                 -o-transition: all 0.5s ease;
                 transition: all 0.5s ease;
                 opacity:1;
             }
             #bar {
                 position:absolute;
                 top:0px;
                 left:0px;
                 width:20px;
                 height:20px;
                 margin:auto auto auto auto;
                 border-radius:11px;
                 border:2px solid rgba(30,30,30,0.05);
                 background: rgb(0, 173, 246);
                 box-shadow: 2px 0px 4px rgba(0,0,0,0.4);
             }
             #border {
                 position:absolute;
                 top:10px;
                 left:10px;
                 width:500px;
                 height:23px;
                 margin:auto auto auto auto;
                 box-shadow: 0px 0px 4px rgba(0,0,0,0.2);
                 border-radius:10px;
             }
             #text {
                 position:absolute;
                 top:8px;
                 left:530px;
                 width:30px;
                 height:50px;
                 margin:auto auto auto auto;
                 font-size:22px;
                 color: #000000;
             }
             div.outerBorder {
                 position:relative;
                 top:400px;
                 width:600px;
                 height:44px;
                 margin:auto auto auto auto;
                 border:8px solid rgba(0,0,0,0.1);
                 background: rgb(252,252,252);
                 background: -moz-linear-gradient(top,  rgba(252,252,252,1) 0%, rgba(237,237,237,1) 100%);
                 background: -webkit-gradient(linear, left top, left bottom, color-stop(0%,rgba(252,252,252,1)), color-stop(100%,rgba(237,237,237,1)));
                 background: -webkit-linear-gradient(top,  rgba(252,252,252,1) 0%,rgba(237,237,237,1) 100%);
                 background: -o-linear-gradient(top,  rgba(252,252,252,1) 0%,rgba(237,237,237,1) 100%);
                 background: -ms-linear-gradient(top,  rgba(252,252,252,1) 0%,rgba(237,237,237,1) 100%);
                 background: linear-gradient(to bottom,  rgba(252,252,252,1) 0%,rgba(237,237,237,1) 100%);
                 filter: progid:DXImageTransform.Microsoft.gradient( startColorstr='#fcfcfc', endColorstr='#ededed',GradientType=0 );
                 border-radius:72px;
                 box-shadow: 0px 0px 10px rgba(0,0,0,0.2);
             }
        </style>
    </head>

    <body>
        <div class="card" style="width: 100%">
            <div id="mynetwork" class="card-body"></div>
        </div>

        <div id="loadingBar">
          <div class="outerBorder">
            <div id="text">0%</div>
            <div id="border">
              <div id="bar"></div>
            </div>
          </div>
        </div>

        <script type="text/javascript">
              var edges;
              var nodes;
              var allNodes;
              var allEdges;
              var nodeColors;
              var originalNodes;
              var network;
              var container;
              var options, data;
              var filter = {
                  item : '',
                  property : '',
                  value : []
              };

              function drawGraph() {
                  var container = document.getElementById('mynetwork');

                  nodes = new vis.DataSet($nodes_json);
                  edges = new vis.DataSet($edges_json);

                  nodeColors = {};
                  allNodes = nodes.get({ returnType: "Object" });
                  for (nodeId in allNodes) {
                    nodeColors[nodeId] = allNodes[nodeId].color;
                  }
                  allEdges = edges.get({ returnType: "Object" });

                  data = {nodes: nodes, edges: edges};
                  var options = $options_json;

                  network = new vis.Network(container, data, options);

                  network.on("stabilizationProgress", function(params) {
                      document.getElementById('loadingBar').removeAttribute("style");
                      var maxWidth = 496;
                      var minWidth = 20;
                      var widthFactor = params.iterations/params.total;
                      var width = Math.max(minWidth,maxWidth * widthFactor);
                      document.getElementById('bar').style.width = width + 'px';
                      document.getElementById('text').innerHTML = Math.round(widthFactor*100) + '%';
                  });
                  network.once("stabilizationIterationsDone", function() {
                      document.getElementById('text').innerHTML = '100%';
                      document.getElementById('bar').style.width = '496px';
                      document.getElementById('loadingBar').style.opacity = 0;
                      setTimeout(function () {document.getElementById('loadingBar').style.display = 'none';}, 500);
                  });

                  return network;
              }
              drawGraph();
        </script>
    </body>
</html>
""")


DEFAULT_OPTIONS = {
    "configure": {"enabled": False},
    "edges": {
        "color": {"inherit": True},
        "smooth": {"enabled": True, "type": "dynamic"}
    },
    "interaction": {
        "dragNodes": True,
        "hideEdgesOnDrag": False,
        "hideNodesOnDrag": False
    },
    "physics": {
        "enabled": True,
        "stabilization": {
            "enabled": True,
            "fit": True,
            "iterations": 1000,
            "onlyDynamicEdges": False,
            "updateInterval": 50
        }
    }
}


def choose_node_label(node_id, attrs: dict):
    """
    GraphML에서 label로 쓸 필드를 탐색.
    우선순위: 'label', 'name', 'title' -> 없으면 node_id 문자열
    """
    for key in ("label", "name", "title"):
        if key in attrs and str(attrs[key]).strip():
            return str(attrs[key])
    return str(node_id)


def choose_edge_relation(attrs: dict):
    """
    엣지 관계명(tooltip 대용)으로 쓸 필드 선택.
    우선순위: 'label', 'type', 'relation' -> 없으면 빈 문자열
    """
    for key in ("label", "type", "relation"):
        if key in attrs and str(attrs[key]).strip():
            return str(attrs[key])
    return ""


def graphml_to_vis_data(
    g: nx.Graph,
    sample_fraction: float = 0.10,
    seed: int = 42
):
    """
    NetworkX Graph -> (nodes_list, edges_list)
    - nodes_list: [{id, label, color, shape}, ...]
    - edges_list: [{from, to, arrows?, relation?}, ...]
    - sample_fraction 비율로 노드 샘플링 후 유도된 서브그래프에 대해서만 export
    """
    rnd = random.Random(seed)

    all_nodes = list(g.nodes())
    n_total = len(all_nodes)
    if n_total == 0:
        return [], []

    k = max(1, int(round(n_total * sample_fraction)))
    # 재현성 있는 샘플링: 정렬 후 랜덤선택
    population = sorted(all_nodes, key=lambda x: str(x))
    sampled = set(rnd.sample(population, k))

    # 유도 서브그래프
    sub = g.subgraph(sampled).copy()

    # 노드 변환
    nodes = []
    for n, attrs in sub.nodes(data=True):
        node_dict = {
            "id": str(n),
            "label": choose_node_label(n, attrs),
            "color": attrs.get("color", "#97c2fc"),
            "shape": attrs.get("shape", "dot"),
        }
        nodes.append(node_dict)

    # 엣지 변환
    directed = isinstance(sub, (nx.DiGraph, nx.MultiDiGraph))
    edges = []
    if isinstance(sub, (nx.MultiDiGraph, nx.MultiGraph)):
        # 멀티그래프: key 포함
        for u, v, key, attrs in sub.edges(keys=True, data=True):
            e = {
                "from": str(u),
                "to": str(v),
                "relation": choose_edge_relation(attrs),
            }
            if directed:
                e["arrows"] = "to"
            edges.append(e)
    else:
        for u, v, attrs in sub.edges(data=True):
            e = {
                "from": str(u),
                "to": str(v),
                "relation": choose_edge_relation(attrs),
            }
            if directed:
                e["arrows"] = "to"
            edges.append(e)

    return nodes, edges


# --- 치환 함수 수정 ---
def build_html(nodes, edges, options=None):
    if options is None:
        opts = DEFAULT_OPTIONS
    else:
        opts = options
    html = HTML_TEMPLATE.substitute(
        nodes_json=json.dumps(nodes, ensure_ascii=False),
        edges_json=json.dumps(edges, ensure_ascii=False),
        options_json=json.dumps(opts, ensure_ascii=False),
    )
    return html


def main():
    parser = argparse.ArgumentParser(description="Convert GraphML to HTML (vis-network) with 10% node sampling.")
    parser.add_argument("--input", "-i", type=str, default=INPUT_GRAPHML, help="Input .graphml file path")
    parser.add_argument("--output", "-o", type=str, default=OUTPUT_HTML, help="Output .html file path")
    parser.add_argument("--frac", type=float, default=SAMPLE_FRACTION, help="Sampling fraction for nodes (default=0.10)")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help="Random seed (default=42)")
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)

    if not in_path.exists():
        raise FileNotFoundError(f"Input not found: {in_path}")

    # GraphML 로드 (유형 자동 감지)
    g = nx.read_graphml(in_path)

    nodes, edges = graphml_to_vis_data(g, sample_fraction=args.frac, seed=args.seed)
    html = build_html(nodes, edges, options=DEFAULT_OPTIONS)

    out_path.write_text(html, encoding="utf-8")
    print(f"[OK] Wrote HTML with {len(nodes)} nodes / {len(edges)} edges -> {out_path}")


if __name__ == "__main__":
    main()
