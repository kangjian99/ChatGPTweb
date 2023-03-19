import re
import markdown

def generate_markdown_message(text):
    if text.startswith("\n\n"):
        text = text[2:]
    pattern = r'#{2,6}(?!\w)|\*\*[\s\S]*?\*\*|\*[\s\S]*?\*|\||^-{1,}\s|(?<!\S)```(?!\S)'
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