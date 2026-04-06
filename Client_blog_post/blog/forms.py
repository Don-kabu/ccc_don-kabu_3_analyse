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
        help_text='Séparez les tags avec des virgules (ex: maths, lecture, sciences).',
        label='Tags',
    )
    illustration_upload = forms.FileField(
        required=False,
        label='Image (upload)',
        widget=forms.ClearableFileInput(attrs={'accept': 'image/*', 'class': 'input'}),
    )

    class Meta:
        model = Article
        fields = [
            'title',
            'category',
            'illustration_url',
            'illustration_upload',
            'enable_analytics',
            'intro',
            'objectives',
            'content',
            'conclusion',
            'reflection_questions',
            'resources',
            'status',
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'input'}),
            'illustration_url': forms.URLInput(attrs={'class': 'input', 'placeholder': 'https://...'}),
            'enable_analytics': forms.CheckboxInput(attrs={'class': 'toggle-checkbox', 'id': 'id_enable_analytics'}),
            'title': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Titre de l\'article'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only title is required
        for name in self.fields:
            if name != 'title':
                self.fields[name].required = False

        if self.instance and self.instance.pk:
            self.fields['tags_csv'].initial = ', '.join(self.instance.tags.values_list('name', flat=True))
            if self.instance.illustration_upload:
                self.fields['illustration_upload'].initial = self.instance.illustration_upload

        rich_fields = {'intro', 'content', 'conclusion'}
        skip_class = {'illustration_upload', 'enable_analytics'}
        for name, field in self.fields.items():
            if name in skip_class:
                continue
            if name in rich_fields:
                field.widget.attrs.update({'class': 'input wysiwyg-source', 'data-rich': '1'})
            elif name not in ('illustration_url',):
                field.widget.attrs.update({'class': 'input'})

    def clean_intro(self):
        return sanitize_rich_html(self.cleaned_data.get('intro', ''))

    def clean_content(self):
        return sanitize_rich_html(self.cleaned_data.get('content', ''))

    def clean_conclusion(self):
        return sanitize_rich_html(self.cleaned_data.get('conclusion', ''))

    def save(self, commit=True):
        article = super().save(commit=False)
        illu_file = self.cleaned_data.get('illustration_upload')
        if illu_file:
            article.illustration_upload = illu_file
        if commit:
            article.save()
        raw_tags = self.cleaned_data.get('tags_csv', '')
        tag_names = [name.strip() for name in raw_tags.split(',') if name.strip()]
        tags = [Tag.objects.get_or_create(name=name)[0] for name in tag_names]
        if article.pk:
            article.tags.set(tags)
        return article


class ReaderCommentForm(forms.ModelForm):
    class Meta:
        model = ReaderComment
        fields = ['name', 'email', 'message']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs.update({'placeholder': 'Ton prénom', 'class': 'input', 'maxlength': '120'})
        self.fields['email'].required = False
        self.fields['email'].widget.attrs.update({'placeholder': 'exemple@mail.com (optionnel)', 'class': 'input'})
        self.fields['message'].widget.attrs.update({
            'placeholder': 'Pose ta question ou partage ton idée…',
            'class': 'input',
            'rows': 4,
            'maxlength': '1000',
            'id': 'id_comment_message',
        })
