import pytest


def test_resnet_forward_smoke():
    torch = pytest.importorskip("torch")
    torchvision = pytest.importorskip("torchvision")
    from uais_v.models.vision_resnet import VisionConfig, build_resnet_classifier

    cfg = VisionConfig(model_name="resnet18", num_classes=2, pretrained=False)
    model = build_resnet_classifier(cfg)
    x = torch.randn(1, 3, 224, 224)
    out = model(x)
    assert out.shape == (1, 2)
