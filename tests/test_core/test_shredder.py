from yoink.core.shredder import shred_code

def test_python_comment_stripping():
    code = """
def foo():
    # This is a comment
    x = 1
    y = "hello # world"
    \"\"\"This is a docstring\"\"\"
    return x
"""
    expected = """def foo():
    x = 1
    y = "hello # world"
    return x"""
    
    result = shred_code(code, ".py", strip_comments=True, strip_whitespace=True)
    assert result.strip() == expected.strip()

def test_c_comment_stripping():
    code = """
// Some C-style comment
#include <stdio.h>
int main() {
    /* Multi-line
       comment */
    printf("Hello // World\\n");
    return 0;
}
"""
    expected = """#include <stdio.h>
int main() {
    printf("Hello // World\\n");
    return 0;
}"""
    result = shred_code(code, ".c", strip_comments=True, strip_whitespace=True)
    assert result.strip() == expected.strip()
