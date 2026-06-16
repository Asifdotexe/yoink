from pathlib import Path
import tempfile
from yoink.core.scanner import get_files_to_process

def test_scanner_traversal():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create some files
        (temp_path / "foo.py").write_text("print('foo')", encoding="utf-8")
        (temp_path / "bar.js").write_text("console.log('bar')", encoding="utf-8")
        (temp_path / "ignored.pyc").write_text("", encoding="utf-8")
        
        # Create ignored dir
        git_dir = temp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("", encoding="utf-8")
        
        # Scan
        files = get_files_to_process(temp_path)
        rel_files = [f.relative_to(temp_path).as_posix() for f in files]
        
        assert "foo.py" in rel_files
        assert "bar.js" in rel_files
        assert "ignored.pyc" not in rel_files
        assert ".git/config" not in rel_files
