from django import forms
from django.utils.translation import gettext_lazy as _


BAD_WORDS = [
    "хуй",
    "пизд",
    "бляд",
    "сука",
    "ебан",
    "fuck",
    "shit",
    "bitch",
]


class BlogCommentForm(forms.Form):
    nickname = forms.CharField(
        max_length=80,
        label=_("Nickname"),
        widget=forms.TextInput(attrs={
            'class': 'comment-input',
            'placeholder': _('Enter your nickname'),
            'required': True,
        })
    )
    text = forms.CharField(
        label=_("Comment"),
        widget=forms.Textarea(attrs={
            'class': 'comment-textarea',
            'placeholder': _('Write your comment here...'),
            'rows': 5,
            'required': True,
        })
    )
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError(_("Invalid value."))
        return value

    def clean_text(self):
        value = self.cleaned_data.get("text", "")
        lower = value.lower()
        for word in BAD_WORDS:
            if word in lower:
                raise forms.ValidationError(_("Text contains prohibited words."))
        return value


