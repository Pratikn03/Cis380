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
