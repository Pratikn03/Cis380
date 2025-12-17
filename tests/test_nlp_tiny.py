import pytest


def test_distilbert_forward_smoke():
    torch = pytest.importorskip("torch")  # noqa: F841
    transformers = pytest.importorskip("transformers")  # noqa: F841
    from uais_v.models.nlp_text_model import DistilBERTClassifier, get_tokenizer

    try:
        tokenizer = get_tokenizer("distilbert-base-uncased")
    except OSError as exc:
        pytest.skip(f"HuggingFace model download unavailable offline: {exc}")
    enc = tokenizer("hello world", return_tensors="pt")

    try:
        model = DistilBERTClassifier("distilbert-base-uncased", num_labels=2)
    except OSError as exc:
        pytest.skip(f"HuggingFace model download unavailable offline: {exc}")
    out = model(enc["input_ids"], enc["attention_mask"])
    assert out.shape[1] == 2
