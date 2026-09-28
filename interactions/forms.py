from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    # Honeypot: hidden from humans with CSS; bots that fill every field get rejected.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={
        "autocomplete": "off", "tabindex": "-1", "class": "hp-field", "aria-hidden": "true",
    }))

    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": "دیدگاه خود را بنویسید...", "maxlength": 3000}),
        }
        labels = {"body": ""}

    def clean_body(self):
        body = self.cleaned_data["body"].strip()
        if len(body) < 2:
            raise forms.ValidationError("دیدگاه خیلی کوتاه است.")
        return body

    def is_spam_trap(self):
        return bool(self.cleaned_data.get("website"))


class CommentEditForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "maxlength": 3000})}
        labels = {"body": ""}
