import pytest


def test_distilbert_forward_smoke():
    torch = pytest.importorskip("torch")
    pytest.importorskip("transformers")

    from uais_v.models.nlp_text_model import DistilBERTClassifier

    # Avoid downloading large HF weights during tests.
    model = DistilBERTClassifier("distilbert-base-uncased", num_labels=2, from_scratch=True)
    input_ids = torch.randint(0, int(model.config.vocab_size), (2, 8))
    attention_mask = torch.ones_like(input_ids)
    out = model(input_ids, attention_mask)
    assert out.shape == (2, 2)
