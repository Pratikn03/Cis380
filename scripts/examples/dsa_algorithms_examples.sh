#!/usr/bin/env bash
set -eo pipefail

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

echo
echo "Graph traversal (BFS/DFS) example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/bfs" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 4,
    "edges": [{"u":0,"v":1,"w":1},{"u":1,"v":2,"w":2},{"u":2,"v":3,"w":3},{"u":0,"v":3,"w":10}],
    "start": 0,
    "directed": false
  }' | python -m json.tool

curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/dfs" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 4,
    "edges": [{"u":0,"v":1,"w":1},{"u":1,"v":2,"w":2},{"u":2,"v":3,"w":3},{"u":0,"v":3,"w":10}],
    "start": 0,
    "directed": false
  }' | python -m json.tool

echo
echo "Shortest paths (Dijkstra) example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/shortest-paths" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 4,
    "edges": [{"u":0,"v":1,"w":1},{"u":1,"v":2,"w":2},{"u":2,"v":3,"w":3},{"u":0,"v":3,"w":10}],
    "source": 0,
    "directed": false
  }' | python -m json.tool

echo
echo "Minimum spanning tree example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/mst" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 4,
    "edges": [{"u":0,"v":1,"w":1},{"u":1,"v":2,"w":2},{"u":2,"v":3,"w":3},{"u":0,"v":3,"w":10}]
  }' | python -m json.tool

echo
echo "SCC example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/scc" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 4,
    "edges": [{"u":0,"v":1,"w":1},{"u":1,"v":2,"w":1},{"u":2,"v":0,"w":1},{"u":2,"v":3,"w":1}]
  }' | python -m json.tool

echo
echo "Segment tree (range min) example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/segment-tree-min" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "values": [5,3,8],
    "ops": [
      {"type":"min","l":0,"r":2},
      {"type":"set","l":1,"r":1,"value":6},
      {"type":"min","l":0,"r":2}
    ]
  }' | python -m json.tool

echo
echo "Shortest paths (Bellman-Ford) example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/shortest-paths/bellman-ford" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 3,
    "edges": [{"u":0,"v":1,"w":1},{"u":1,"v":2,"w":2},{"u":0,"v":2,"w":10}],
    "source": 0,
    "directed": true
  }' | python -m json.tool

echo
echo "Shortest paths (Floyd-Warshall) example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/shortest-paths/floyd-warshall" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 3,
    "edges": [{"u":0,"v":1,"w":1},{"u":1,"v":2,"w":2},{"u":0,"v":2,"w":10}],
    "directed": true
  }' | python -m json.tool

echo
echo "Shortest paths (0-1 BFS) example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/shortest-paths/zero-one-bfs" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "n": 3,
    "edges": [{"u":0,"v":1,"w":0},{"u":1,"v":2,"w":1},{"u":0,"v":2,"w":1}],
    "source": 0,
    "directed": false
  }' | python -m json.tool

echo
echo "Trie example"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/trie" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{
    "operations": [
      {"op":"insert","text":"cat"},
      {"op":"search","text":"cat"},
      {"op":"search","text":"car"},
      {"op":"starts_with","text":"ca"},
      {"op":"delete","text":"cat"},
      {"op":"search","text":"cat"}
    ]
  }' | python -m json.tool

echo
echo "DP examples"
curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/dp" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{"method":"lis","nums":[10,9,2,5,3,7,101,18]}' | python -m json.tool

curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/dp" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{"method":"knapsack","weights":[2,3,4],"values":[4,5,6],"capacity":5}' | python -m json.tool

curl -sS -X POST "${BASE_URL}/api/dsa/algorithms/dp" \
  -H "Content-Type: application/json" \
  "${AUTH_HEADER[@]}" \
  -d '{"method":"coin_change","coins":[1,2,5],"amount":11}' | python -m json.tool
