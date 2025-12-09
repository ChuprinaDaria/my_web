from django import forms


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
    nickname = forms.CharField(max_length=80)
    text = forms.CharField(widget=forms.Textarea)
    website = forms.CharField(required=False)

    def clean_website(self):
        value = self.cleaned_data.get("website", "")
        if value:
            raise forms.ValidationError("Неприпустиме значення.")
        return value

    def clean_text(self):
        value = self.cleaned_data.get("text", "")
        lower = value.lower()
        for word in BAD_WORDS:
            if word in lower:
                raise forms.ValidationError("Текст містить заборонені слова.")
        return value


