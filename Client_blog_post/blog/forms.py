from django import forms
import bleach
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Article, ReaderComment, Tag


ALLOWED_HTML_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's',
    'h2', 'h3', 'blockquote',
    'ul', 'ol', 'li',
    'a', 'img',
]

ALLOWED_HTML_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'title'],
}

ALLOWED_HTML_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_rich_html(value):
    if not value:
        return ''
    cleaned = bleach.clean(
        value,
        tags=ALLOWED_HTML_TAGS,
        attributes=ALLOWED_HTML_ATTRIBUTES,
        protocols=ALLOWED_HTML_PROTOCOLS,
        strip=True,
    )
    return bleach.linkify(cleaned)


class AuthorSignupForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, max_length=150, label='Prenom')
    last_name = forms.CharField(required=True, max_length=150, label='Nom')

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        placeholders = {
            'username': 'nom.auteur',
            'first_name': 'Prenom',
            'last_name': 'Nom',
            'email': 'auteur@example.com',
            'password1': 'Mot de passe',
            'password2': 'Confirmation du mot de passe',
        }
        for name, field in self.fields.items():
            field.widget.attrs.update({'placeholder': placeholders.get(name, field.label), 'class': 'input'})

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Un compte avec cet email existe deja.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user


class ArticleForm(forms.ModelForm):
    tags_csv = forms.CharField(
        required=False,
        help_text='Separez les tags avec des virgules (ex: maths, lecture, sciences).',
        label='Tags',
    )

    class Meta:
        model = Article
        fields = [
            'title',
            'illustration_url',
            'intro',
            'objectives',
            'content',
            'conclusion',
            'reflection_questions',
            'resources',
            'status',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['tags_csv'].initial = ', '.join(self.instance.tags.values_list('name', flat=True))

        rich_fields = {'intro', 'content', 'conclusion'}
        for name, field in self.fields.items():
            if name in rich_fields:
                field.widget.attrs.update({'class': 'input wysiwyg-source', 'data-rich': '1'})
            else:
                field.widget.attrs.update({'class': 'input'})

    def clean_intro(self):
        return sanitize_rich_html(self.cleaned_data.get('intro', ''))

    def clean_content(self):
        return sanitize_rich_html(self.cleaned_data.get('content', ''))

    def clean_conclusion(self):
        return sanitize_rich_html(self.cleaned_data.get('conclusion', ''))

    def save(self, commit=True):
        article = super().save(commit=commit)
        raw_tags = self.cleaned_data.get('tags_csv', '')
        tag_names = [name.strip() for name in raw_tags.split(',') if name.strip()]
        tags = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
        if article.pk:
            article.tags.set(tags)
        return article


class ReaderCommentForm(forms.ModelForm):
    class Meta:
        model = ReaderComment
        fields = ['name', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'Ton prenom', 'class': 'input'})
        self.fields['message'].widget.attrs.update({'placeholder': 'Pose ta question ou partage ton idee', 'class': 'input', 'rows': 4})
