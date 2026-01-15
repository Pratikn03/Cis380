#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_HEADER=()
if [ -n "${AUTH_TOKEN:-}" ]; then
  AUTH_HEADER=(-H "Authorization: Bearer ${AUTH_TOKEN}")
fi

echo "LCA example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/lca" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 7,
    "edges": [{"u":0,"v":1},{"u":0,"v":2},{"u":1,"v":3},{"u":1,"v":4},{"u":2,"v":5},{"u":2,"v":6}],
    "root": 0,
    "queries": [{"u":3,"v":4},{"u":3,"v":5},{"u":5,"v":6},{"u":2,"v":6}]
  }' | python -m json.tool

echo
echo "Segment tree example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/segment-tree" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "values": [1,2,3,4,5],
    "ops": [
      {"type":"sum","l":0,"r":4},
      {"type":"add","l":1,"r":3,"value":2},
      {"type":"sum","l":0,"r":4},
      {"type":"sum","l":2,"r":2}
    ]
  }' | python -m json.tool

echo
echo "Min-cost max flow example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/min-cost-max-flow" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 4,
    "edges": [
      {"u":0,"v":1,"cap":2,"cost":1},
      {"u":0,"v":2,"cap":1,"cost":5},
      {"u":1,"v":2,"cap":1,"cost":0},
      {"u":1,"v":3,"cap":1,"cost":2},
      {"u":2,"v":3,"cap":2,"cost":1}
    ],
    "source": 0,
    "sink": 3
  }' | python -m json.tool
