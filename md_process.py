import re
import markdown
import html

def is_html(text):
    html_pattern = re.compile(r'<[^>]+>')
    return bool(html_pattern.search(text))

def generate_markdown_message(text):
    if text.startswith("\n\n"):
        text = text[2:]
        
    if is_html(text):
        escaped_text = html.escape(text) # 将HTML标签转换为实体
        text = f"<pre>{escaped_text}</pre>"
        return text

    pattern = r'#{2,6}(?!\w)|\*\*[\s\S]*?\*\*|\*[\s\S]*?\*|\||^-{1,}\s|```'
    is_markdown = re.search(pattern, text) # 先判断是否markdown
    is_codeblock = bool('```' in text)
    if is_markdown:
        text = text.replace("\n\n\n", "\n\n")
        if is_codeblock:
            text = text.replace("#", "%35%")
        markdown_message = markdown.markdown(text, extensions=["tables", "nl2br"]) # 将返回的字符串转换为Markdown格式的HTML标记
        if is_codeblock:
            markdown_message = markdown_message.replace("%35%", "#")
        return markdown_message
    else:
        text = text.replace("\n", "<br>")
        return text