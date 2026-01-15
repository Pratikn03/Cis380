from fastapi.testclient import TestClient

from app.main import app


def test_dsa_lca_api():
    client = TestClient(app)
    payload = {
        "n": 7,
        "edges": [
            {"u": 0, "v": 1},
            {"u": 0, "v": 2},
            {"u": 1, "v": 3},
            {"u": 1, "v": 4},
            {"u": 2, "v": 5},
            {"u": 2, "v": 6},
        ],
        "root": 0,
        "queries": [
            {"u": 3, "v": 4},
            {"u": 3, "v": 5},
            {"u": 5, "v": 6},
            {"u": 2, "v": 6},
        ],
    }
    resp = client.post("/api/dsa/algorithms/lca", json=payload)
    assert resp.status_code == 200
    assert resp.json()["lca"] == [1, 0, 2, 2]


def test_dsa_segment_tree_api():
    client = TestClient(app)
    payload = {
        "values": [1, 2, 3, 4, 5],
        "ops": [
            {"type": "sum", "l": 0, "r": 4},
            {"type": "add", "l": 1, "r": 3, "value": 2},
            {"type": "sum", "l": 0, "r": 4},
            {"type": "sum", "l": 2, "r": 2},
        ],
    }
    resp = client.post("/api/dsa/algorithms/segment-tree", json=payload)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results == [
        {"op_index": 0, "value": 15.0},
        {"op_index": 2, "value": 21.0},
        {"op_index": 3, "value": 5.0},
    ]


def test_dsa_min_cost_max_flow_api():
    client = TestClient(app)
    payload = {
        "n": 4,
        "edges": [
            {"u": 0, "v": 1, "cap": 2, "cost": 1},
            {"u": 0, "v": 2, "cap": 1, "cost": 5},
            {"u": 1, "v": 2, "cap": 1, "cost": 0},
            {"u": 1, "v": 3, "cap": 1, "cost": 2},
            {"u": 2, "v": 3, "cap": 2, "cost": 1},
        ],
        "source": 0,
        "sink": 3,
    }
    resp = client.post("/api/dsa/algorithms/min-cost-max-flow", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["flow"] == 3
    assert data["cost"] == 11


def test_dsa_graph_algorithms_api():
    client = TestClient(app)
    edges = [
        {"u": 0, "v": 1, "w": 1},
        {"u": 1, "v": 2, "w": 2},
        {"u": 2, "v": 3, "w": 3},
        {"u": 0, "v": 3, "w": 10},
    ]

    bfs_resp = client.post(
        "/api/dsa/algorithms/bfs",
        json={"n": 4, "edges": edges, "start": 0, "directed": False},
    )
    assert bfs_resp.status_code == 200
    assert bfs_resp.json()["distances"] == [0, 1, 2, 1]

    dfs_resp = client.post(
        "/api/dsa/algorithms/dfs",
        json={"n": 4, "edges": edges, "start": 0, "directed": False},
    )
    assert dfs_resp.status_code == 200
    assert dfs_resp.json()["order"][0] == 0

    dijkstra_resp = client.post(
        "/api/dsa/algorithms/shortest-paths",
        json={"n": 4, "edges": edges, "source": 0, "directed": False},
    )
    assert dijkstra_resp.status_code == 200
    distances = dijkstra_resp.json()["distances"]
    assert distances[3] == 6.0

    mst_resp = client.post(
        "/api/dsa/algorithms/mst",
        json={"n": 4, "edges": edges},
    )
    assert mst_resp.status_code == 200
    assert mst_resp.json()["total_weight"] == 6.0

    scc_edges = [
        {"u": 0, "v": 1, "w": 1},
        {"u": 1, "v": 2, "w": 1},
        {"u": 2, "v": 0, "w": 1},
        {"u": 2, "v": 3, "w": 1},
    ]
    scc_resp = client.post(
        "/api/dsa/algorithms/scc",
        json={"n": 4, "edges": scc_edges},
    )
    assert scc_resp.status_code == 200
    components = scc_resp.json()["components"]
    assert any(set(comp) == {0, 1, 2} for comp in components)


def test_dsa_segment_tree_min_api():
    client = TestClient(app)
    payload = {
        "values": [5, 3, 8],
        "ops": [
            {"type": "min", "l": 0, "r": 2},
            {"type": "set", "l": 1, "r": 1, "value": 6},
            {"type": "min", "l": 0, "r": 2},
        ],
    }
    resp = client.post("/api/dsa/algorithms/segment-tree-min", json=payload)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results == [
        {"op_index": 0, "value": 3.0},
        {"op_index": 2, "value": 5.0},
    ]


def test_dsa_shortest_path_variants_api():
    client = TestClient(app)
    edges = [
        {"u": 0, "v": 1, "w": 1},
        {"u": 1, "v": 2, "w": 2},
        {"u": 0, "v": 2, "w": 10},
    ]
    bellman_resp = client.post(
        "/api/dsa/algorithms/shortest-paths/bellman-ford",
        json={"n": 3, "edges": edges, "source": 0, "directed": True},
    )
    assert bellman_resp.status_code == 200
    bellman_data = bellman_resp.json()
    assert bellman_data["distances"][2] == 3.0
    assert bellman_data["negative_cycle"] is False

    floyd_resp = client.post(
        "/api/dsa/algorithms/shortest-paths/floyd-warshall",
        json={"n": 3, "edges": edges, "directed": True},
    )
    assert floyd_resp.status_code == 200
    floyd_data = floyd_resp.json()
    assert floyd_data["distances"][0][2] == 3.0

    zero_one_edges = [
        {"u": 0, "v": 1, "w": 0},
        {"u": 1, "v": 2, "w": 1},
        {"u": 0, "v": 2, "w": 1},
    ]
    zero_one_resp = client.post(
        "/api/dsa/algorithms/shortest-paths/zero-one-bfs",
        json={"n": 3, "edges": zero_one_edges, "source": 0, "directed": False},
    )
    assert zero_one_resp.status_code == 200
    assert zero_one_resp.json()["distances"] == [0.0, 0.0, 1.0]


def test_dsa_trie_api():
    client = TestClient(app)
    payload = {
        "operations": [
            {"op": "insert", "text": "cat"},
            {"op": "search", "text": "cat"},
            {"op": "search", "text": "car"},
            {"op": "starts_with", "text": "ca"},
            {"op": "delete", "text": "cat"},
            {"op": "search", "text": "cat"},
        ]
    }
    resp = client.post("/api/dsa/algorithms/trie", json=payload)
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert results == [
        {"op_index": 0, "op": "insert", "result": True},
        {"op_index": 1, "op": "search", "result": True},
        {"op_index": 2, "op": "search", "result": False},
        {"op_index": 3, "op": "starts_with", "result": True},
        {"op_index": 4, "op": "delete", "result": True},
        {"op_index": 5, "op": "search", "result": False},
    ]


def test_dsa_dp_api():
    client = TestClient(app)
    lis_resp = client.post(
        "/api/dsa/algorithms/dp",
        json={"method": "lis", "nums": [10, 9, 2, 5, 3, 7, 101, 18]},
    )
    assert lis_resp.status_code == 200
    assert lis_resp.json()["result"] == 4

    knapsack_resp = client.post(
        "/api/dsa/algorithms/dp",
        json={
            "method": "knapsack",
            "weights": [2, 3, 4],
            "values": [4, 5, 6],
            "capacity": 5,
        },
    )
    assert knapsack_resp.status_code == 200
    assert knapsack_resp.json()["result"] == 9

    coin_resp = client.post(
        "/api/dsa/algorithms/dp",
        json={"method": "coin_change", "coins": [1, 2, 5], "amount": 11},
    )
    assert coin_resp.status_code == 200
    assert coin_resp.json()["result"] == 3
