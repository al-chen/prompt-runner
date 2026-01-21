"""Tests for markdown to HTML rendering."""

import pytest

from prompt_runner.rendering import markdown_to_html


class TestMarkdownToHtml:
    """Tests for the markdown_to_html function."""

    def test_headers_convert_to_html_tags(self):
        """Headers should convert to h1, h2, h3 with inline styles."""
        content = "# Heading 1\n\n## Heading 2\n\n### Heading 3"
        result = markdown_to_html(content)

        assert "<h1" in result and "Heading 1</h1>" in result
        assert "<h2" in result and "Heading 2</h2>" in result
        assert "<h3" in result and "Heading 3</h3>" in result

    def test_bold_and_italic(self):
        """Bold and italic formatting should work."""
        content = "This is **bold** and this is *italic*."
        result = markdown_to_html(content)

        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_unordered_list(self):
        """Unordered lists should convert to ul/li."""
        content = "- Item 1\n- Item 2\n- Item 3"
        result = markdown_to_html(content)

        assert "<ul" in result
        assert "<li" in result
        assert "Item 1</li>" in result
        assert "Item 2</li>" in result
        assert "Item 3</li>" in result

    def test_ordered_list(self):
        """Ordered lists should convert to ol/li."""
        content = "1. First\n2. Second\n3. Third"
        result = markdown_to_html(content)

        assert "<ol" in result
        assert "<li" in result
        assert "First</li>" in result
        assert "Second</li>" in result

    def test_fenced_code_block(self):
        """Fenced code blocks should convert to pre/code."""
        content = "```python\nprint('hello')\n```"
        result = markdown_to_html(content)

        assert "<pre" in result
        assert "<code" in result
        assert "print" in result

    def test_inline_code(self):
        """Inline code should convert to code tags."""
        content = "Use the `print()` function."
        result = markdown_to_html(content)

        assert "<code" in result
        assert "print()</code>" in result

    def test_output_wrapped_in_html_template(self):
        """Output should be wrapped in HTML template with doctype and body."""
        content = "Hello world"
        result = markdown_to_html(content)

        assert "<!DOCTYPE html>" in result
        assert "<html>" in result
        assert "<body" in result
        assert "</body>" in result
        assert "</html>" in result

    def test_inline_styles_applied(self):
        """HTML elements should have inline styles for email compatibility."""
        content = "# Header\n\nParagraph\n\n- List item"
        result = markdown_to_html(content)

        # Check that style attributes are present
        assert 'style="' in result
        # Check specific style properties exist
        assert "font-family:" in result
        assert "margin:" in result

    def test_table_rendering(self):
        """Tables should render with proper HTML and styles."""
        content = "| Col 1 | Col 2 |\n|-------|-------|\n| A | B |"
        result = markdown_to_html(content)

        assert "<table" in result
        assert "<th" in result
        assert "<td" in result
        assert "Col 1</th>" in result
        assert "A</td>" in result

    def test_newlines_convert_to_breaks(self):
        """Newlines within paragraphs should convert to br tags (nl2br)."""
        content = "Line 1\nLine 2"
        result = markdown_to_html(content)

        assert "<br" in result
