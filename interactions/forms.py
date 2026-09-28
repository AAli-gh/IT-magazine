from django import forms

from .models import Comment


class CommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 3, "placeholder": "دیدگاه خود را بنویسید..."}),
        }
        labels = {"body": ""}
