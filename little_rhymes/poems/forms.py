from django import forms
from .models import Language, ClassLevel, Category

class PoemFilterForm(forms.Form):
    q = forms.CharField(required=False, max_length=120, label='Search poems', widget=forms.TextInput(attrs={'placeholder': 'A title, a topic, a little wonder…', 'type': 'search'}))
    language = forms.ModelChoiceField(required=False, queryset=Language.objects.filter(is_active=True), to_field_name='slug', empty_label='All languages')
    class_level = forms.ModelChoiceField(required=False, queryset=ClassLevel.objects.filter(is_active=True), to_field_name='slug', empty_label='All classes', label='Class')
    category = forms.ModelChoiceField(required=False, queryset=Category.objects.filter(is_active=True), to_field_name='slug', empty_label='All categories')
    sort = forms.ChoiceField(required=False, choices=[('newest', 'Newest first'), ('title', 'Title A–Z'), ('oldest', 'Oldest first'), ('featured', 'Featured first')], initial='newest')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-select' if isinstance(field, forms.ChoiceField) else 'form-control'
