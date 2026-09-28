from django import forms


class MarkdownEditorWidget(forms.Textarea):
    """Textarea with a small toolbar, image upload and a live server-rendered preview."""

    template_name = "admin/widgets/markdown_editor.html"

    def __init__(self, attrs=None):
        super().__init__(attrs={"rows": 24, "dir": "auto", **(attrs or {})})

    class Media:
        css = {"all": ["css/code.css", "admin/markdown-editor.css"]}
        js = ["admin/markdown-editor.js"]
