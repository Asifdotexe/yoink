import sys
from unittest.mock import patch

import pytest

from yoink.cli.main import main


def test_cli_help():
    with patch("sys.argv", ["yoink", "--help"]):
        try:
            main()
        except SystemExit as e:
            assert e.code == 0


def test_cli_raw(tmp_path):
    # Setup test file
    test_file = tmp_path / "foo.py"
    test_file.write_text("def run():\n    # Comment to be kept\n    pass")

    output_file = tmp_path / "output.md"

    # Run in --raw mode
    with patch("sys.argv", ["yoink", str(test_file), "-o", str(output_file), "--raw"]):
        main()

    assert output_file.exists()
    content = output_file.read_text()
    assert "# Comment to be kept" in content


def test_cli_max_size(tmp_path):
    # Setup test file that is relatively large (e.g., 5 KB)
    test_file = tmp_path / "large.py"
    # Write 5000 characters (approx 5 KB)
    test_file.write_text("a" * 5000)

    output_file = tmp_path / "output.md"

    # Run with --max-size 2 (2 KB limit, so 5 KB file should be skipped)
    with patch("sys.argv", ["yoink", str(test_file), "-o", str(output_file), "--max-size", "2"]):
        main()

    assert output_file.exists()
    content = output_file.read_text()
    assert "File skipped: size" in content
    assert "exceeds limit" in content


# ponytail: use parameterization to avoid duplicate test blocks
@pytest.mark.parametrize("flag", ["--no-visualize", "--no-visualise"])
def test_cli_no_visualize(tmp_path, flag):
    test_file = tmp_path / "simple.py"
    test_file.write_text("print('hello')")
    output_file = tmp_path / f"output_no_vis_{flag.replace('-', '')}.md"

    with patch("sys.argv", ["yoink", str(test_file), "-o", str(output_file), flag]):
        main()

    assert output_file.exists()
    content = output_file.read_text()
    assert "## FL" in content
    assert "## DT" not in content


@pytest.mark.parametrize("key", ["visualize", "visualise"])
def test_cli_config_visualize(tmp_path, key):
    test_file = tmp_path / "simple.py"
    test_file.write_text("print('hello')")
    config_file = tmp_path / ".yoinkconfig.json"
    config_file.write_text(f'{{"{key}": false}}')
    output_file = tmp_path / f"output_config_{key}.md"

    with patch("sys.argv", ["yoink", str(tmp_path), "-o", str(output_file), "-c", str(config_file)]):
        main()

    assert output_file.exists()
    content = output_file.read_text()
    assert "## FL" in content
    assert "## DT" not in content


def test_cli_default_visualize(tmp_path):
    test_file = tmp_path / "simple.py"
    test_file.write_text("print('hello')")
    output_file = tmp_path / "output_default.md"

    with patch("sys.argv", ["yoink", str(test_file), "-o", str(output_file)]):
        main()

    assert output_file.exists()
    content = output_file.read_text()
    assert "## FL" in content
    assert "## DT" in content


def test_cli_config_censor(tmp_path):
    test_file = tmp_path / "app.py"
    test_file.write_text("def connect_to_google():\n    return 'http://db.internal.net'")
    config_file = tmp_path / ".yoinkconfig.json"
    config_file.write_text('{"censor_words": ["Google"], "censor_domains": ["internal.net"]}')
    output_file = tmp_path / "output.md"

    with patch("sys.argv", ["yoink", str(test_file), "-o", str(output_file), "-c", str(config_file)]):
        main()

    assert output_file.exists()
    content = output_file.read_text()
    assert "Google" not in content
    assert "internal.net" not in content
    
    from yoink.core.shield import generate_pseudonym
    google_pseudo = generate_pseudonym("Google")
    assert f"connect_to_{google_pseudo}" in content


def test_cli_censor_tui_call():
    with patch("sys.argv", ["yoink", "censor", "tui"]), \
         patch("yoink.cli.tui.run_censor_tui") as mock_tui:
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
        mock_tui.assert_called_once()


def test_cli_censor_init_call():
    with patch("sys.argv", ["yoink", "censor", "init"]), \
         patch("yoink.cli.tui.run_censor_init") as mock_init:
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
        mock_init.assert_called_once()


def test_cli_censor_show_call():
    with patch("sys.argv", ["yoink", "censor", "show"]), \
         patch("yoink.cli.tui.run_censor_show") as mock_show:
        try:
            main()
        except SystemExit as e:
            assert e.code == 0
        mock_show.assert_called_once()




