import sys
from unittest.mock import patch
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
