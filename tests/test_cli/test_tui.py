import json
from pathlib import Path
from unittest.mock import patch
import pytest
from yoink.cli.tui import run_censor_tui


def test_tui_flow_toggle_and_save(tmp_path):
    config_file = tmp_path / ".yoinkconfig.json"
    
    # Mock inputs:
    # 4: Toggle pseudonym masking (auto-saves config)
    # 0: Exit
    inputs = ["4", "0"]
    
    with patch("builtins.input", side_effect=inputs):
        with pytest.raises(SystemExit) as e:
            run_censor_tui(config_file, tmp_path)
        assert e.value.code == 0

    assert config_file.exists()
    with open(config_file, "r") as f:
        data = json.load(f)
    assert data["pseudonym_masking"] is False


def test_tui_flow_add_words_and_save(tmp_path):
    config_file = tmp_path / ".yoinkconfig.json"
    
    # Mock inputs:
    # 1: Add words (auto-saves config)
    # "Google, Microsoft"
    # 0: Exit
    inputs = ["1", "Google, Microsoft", "0"]
    
    with patch("builtins.input", side_effect=inputs):
        with pytest.raises(SystemExit) as e:
            run_censor_tui(config_file, tmp_path)
        assert e.value.code == 0

    assert config_file.exists()
    with open(config_file, "r") as f:
        data = json.load(f)
    assert "Google" in data["censor_words"]
    assert "Microsoft" in data["censor_words"]


def test_censor_init_flow(tmp_path):
    config_file = tmp_path / ".yoinkconfig.json"
    
    # 1. Censor word: Theseus, then Enter
    # 2. Censor domain: internal.net, then Enter
    # 3. Enable pseudonym masking: Y
    inputs = ["Theseus", "", "internal.net", "", "y"]
    
    from yoink.cli.tui import run_censor_init
    with patch("builtins.input", side_effect=inputs):
        run_censor_init(config_file)
        
    assert config_file.exists()
    with open(config_file, "r") as f:
        data = json.load(f)
    assert "Theseus" in data["censor_words"]
    assert "internal.net" in data["censor_domains"]
    assert data["pseudonym_masking"] is True


def test_censor_show_flow(tmp_path, capsys):
    config_file = tmp_path / ".yoinkconfig.json"
    config_file.write_text(
        '{"censor_words": ["Theseus"], "censor_domains": ["internal.net"], "pseudonym_masking": true}'
    )
    
    from yoink.cli.tui import run_censor_show
    run_censor_show(config_file)
    
    captured = capsys.readouterr()
    assert "Active Masking Rules" in captured.out
    assert "Theseus" in captured.out
    assert "internal.net" in captured.out
    
    # Check that deterministic pseudonym appears in show
    from yoink.core.shield import generate_pseudonym
    pseudo = generate_pseudonym("Theseus")
    assert pseudo in captured.out
