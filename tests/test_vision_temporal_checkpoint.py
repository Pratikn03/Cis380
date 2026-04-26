from app.api.vision_temporal import _checkpoint_state_dict


def test_checkpoint_state_dict_unwraps_training_checkpoint() -> None:
    state = {"layer.weight": object()}
    checkpoint = {"state_dict": state, "clip_len": 16, "size": 224}

    assert _checkpoint_state_dict(checkpoint) is state


def test_checkpoint_state_dict_preserves_raw_state_dict() -> None:
    state = {"layer.weight": object()}

    assert _checkpoint_state_dict(state) is state
