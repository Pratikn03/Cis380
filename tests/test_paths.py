from uais_v.paths import CONFIG_DIR, DATA_DIR, PROJECT_ROOT


def test_paths_exist():
    assert PROJECT_ROOT.exists()
    assert DATA_DIR.exists()
    assert CONFIG_DIR.exists()
