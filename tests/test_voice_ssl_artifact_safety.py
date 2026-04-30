import json

import pytest

from scripts.voice.ssl_utils import ensure_compatible_label_map, resolve_trainer_eval_sampler


def test_ensure_compatible_label_map_rejects_stale_output_dir(tmp_path):
    output_dir = tmp_path / "voice_ssl"
    output_dir.mkdir()
    (output_dir / "label_map.json").write_text(
        json.dumps(
            {
                "label2id": {
                    "angry": 0,
                    "happy": 1,
                    "neutral": 2,
                    "sad": 3,
                }
            }
        ),
        encoding="utf-8",
    )

    expected = {
        "angry": 0,
        "disgust": 1,
        "happy": 2,
        "neutral": 3,
        "sad": 4,
    }

    with pytest.raises(SystemExit, match="stale SSL voice output directory"):
        ensure_compatible_label_map(output_dir, expected, resume_from_checkpoint=None)


def test_ensure_compatible_label_map_allows_matching_output_dir(tmp_path):
    output_dir = tmp_path / "voice_ssl"
    output_dir.mkdir()
    expected = {"angry": 0, "happy": 1}
    (output_dir / "label_map.json").write_text(
        json.dumps({"label2id": expected}),
        encoding="utf-8",
    )

    ensure_compatible_label_map(output_dir, expected, resume_from_checkpoint=None)


def test_resolve_trainer_eval_sampler_supports_private_transformers_api():
    dataset = object()

    class TrainerWithPrivateSampler:
        def _get_eval_sampler(self, eval_dataset):
            return ("private", eval_dataset)

    assert resolve_trainer_eval_sampler(TrainerWithPrivateSampler(), dataset) == (
        "private",
        dataset,
    )
