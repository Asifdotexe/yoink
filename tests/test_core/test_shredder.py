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


def test_hash_comment_stripping():
    code = """
# This is a comment
name: test
  # Nested comment
value: 123  # Inline comment
"""
    expected = """name: test
value: 123"""
    result = shred_code(code, "config.yml", strip_comments=True, strip_whitespace=True)
    assert result.strip() == expected.strip()


def test_dockerfile_comment_stripping():
    code = """
# Build stage
FROM python:3.10-slim
# Install curl
RUN apt-get update && apt-get install -y curl
"""
    expected = """FROM python:3.10-slim
RUN apt-get update && apt-get install -y curl"""
    result = shred_code(code, "Dockerfile", strip_comments=True, strip_whitespace=True)
    assert result.strip() == expected.strip()


def test_license_header_stripping():
    # Test stripping python copyright header
    code = """# Copyright (c) 2026 Asif Sayyed
# All rights reserved.
# Licensed under MIT License.

def foo():
    return 42
"""
    expected = """def foo():
    return 42"""
    result = shred_code(code, "main.py", strip_comments=True, strip_whitespace=True)
    assert result.strip() == expected.strip()

    # Test stripping C-style block comment header
    code_c = """/*
 * Copyright (C) 2026 Asif Sayyed. All Rights Reserved.
 * Unauthorized copying of this file is strictly prohibited.
 * Written by Asif Sayyed <asifdotexe@gmail.com>.
 */

#include <stdio.h>
"""
    expected_c = """#include <stdio.h>"""
    result_c = shred_code(code_c, "main.c", strip_comments=True, strip_whitespace=True)
    assert result_c.strip() == expected_c.strip()


