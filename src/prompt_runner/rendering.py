"""Markdown to HTML rendering for email delivery."""

import markdown


# Email-friendly HTML template with inline CSS
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
{content}
</body>
</html>"""

# Inline CSS for markdown elements (email clients strip <style> tags)
# Order matters: longer tags must be processed before shorter ones to avoid
# partial matches (e.g., <pre before <p, <blockquote before <b)
INLINE_STYLES = [
    ("<h1>", '<h1 style="font-size: 24px; font-weight: 600; margin: 24px 0 16px 0; border-bottom: 1px solid #eee; padding-bottom: 8px;">'),
    ("<h2>", '<h2 style="font-size: 20px; font-weight: 600; margin: 20px 0 12px 0;">'),
    ("<h3>", '<h3 style="font-size: 16px; font-weight: 600; margin: 16px 0 8px 0;">'),
    ("<pre>", '<pre style="background-color: #f6f8fa; padding: 16px; border-radius: 6px; overflow-x: auto; margin: 0 0 16px 0;">'),
    ("<p>", '<p style="margin: 0 0 16px 0;">'),
    ("<ul>", '<ul style="margin: 0 0 16px 0; padding-left: 24px;">'),
    ("<ol>", '<ol style="margin: 0 0 16px 0; padding-left: 24px;">'),
    ("<li>", '<li style="margin: 4px 0;">'),
    ("<code>", '<code style="font-family: SFMono-Regular, Consolas, Monaco, monospace; font-size: 14px;">'),
    ("<code ", '<code style="font-family: SFMono-Regular, Consolas, Monaco, monospace; font-size: 14px;" '),
    ("<blockquote>", '<blockquote style="margin: 0 0 16px 0; padding: 0 16px; border-left: 4px solid #ddd; color: #666;">'),
    ("<table>", '<table style="border-collapse: collapse; margin: 0 0 16px 0; width: 100%;">'),
    ("<th>", '<th style="border: 1px solid #ddd; padding: 8px 12px; background-color: #f6f8fa; text-align: left;">'),
    ("<td>", '<td style="border: 1px solid #ddd; padding: 8px 12px;">'),
]


def markdown_to_html(content: str) -> str:
    """Convert markdown content to email-friendly HTML.

    Uses the markdown library with extensions for fenced code blocks,
    tables, and newline-to-break conversion. Output is wrapped in an
    HTML template with inline CSS for email client compatibility.

    Args:
        content: Markdown-formatted text content.

    Returns:
        HTML string ready for email delivery.
    """
    # Convert markdown to HTML with useful extensions
    md = markdown.Markdown(extensions=["fenced_code", "tables", "nl2br"])
    html_content = md.convert(content)

    # Apply inline styles for email compatibility
    for tag, styled_tag in INLINE_STYLES:
        html_content = html_content.replace(tag, styled_tag)

    return HTML_TEMPLATE.format(content=html_content)
