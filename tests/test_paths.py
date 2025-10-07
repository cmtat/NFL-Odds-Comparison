from nfl_betting_model.config import paths


def test_project_paths_exist():
    assert paths.data_raw.exists()
    assert paths.data_staging.exists()
    assert paths.data_features.exists()
