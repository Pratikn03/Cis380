from app.services.decision_engine import make_decision


def test_make_decision_blocks_on_high_fraud():
    out = make_decision(cyber_risk=0.0, behavior_risk=0.0, fraud_risk=0.86)
    assert out.decision == "BLOCK"
    assert out.reason_code == "FRAUD_HIGH"


def test_make_decision_step_up_on_combined_risk():
    out = make_decision(cyber_risk=0.71, behavior_risk=0.61, fraud_risk=0.1)
    assert out.decision == "STEP_UP_AUTH"


def test_make_decision_allows_low_risk():
    out = make_decision(cyber_risk=0.2, behavior_risk=0.2, fraud_risk=0.2)
    assert out.decision == "ALLOW"
