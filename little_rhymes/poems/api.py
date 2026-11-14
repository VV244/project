from rest_framework import generics, serializers
from rest_framework.exceptions import ValidationError
from .models import Poem
from .forms import PoemFilterForm
from .services import filter_poems

class PoemSerializer(serializers.ModelSerializer):
    language = serializers.CharField(source='language.native_name')
    language_code = serializers.CharField(source='language.code')
    text_direction = serializers.CharField(source='language.text_direction')
    classes = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    categories = serializers.SlugRelatedField(many=True, read_only=True, slug_field='name')
    url = serializers.CharField(source='get_absolute_url')

    class Meta:
        model = Poem
        fields = ['id', 'title', 'slug', 'url', 'language', 'language_code', 'text_direction', 'classes', 'categories', 'author', 'poem_text', 'short_description', 'thumbnail', 'illustration', 'audio_file', 'video_url', 'rights_statement']

class PoemListAPI(generics.ListAPIView):
    serializer_class = PoemSerializer

    def get_queryset(self):
        form = PoemFilterForm(self.request.GET)
        if not form.is_valid():
            raise ValidationError(form.errors)
        queryset = filter_poems(Poem.objects.published().with_relations(), form.cleaned_data)
        ids = self.request.GET.get('ids')
        if ids is not None:
            values = ids.split(',')
            if len(values) > 100 or not all(v.isdecimal() and len(v) <= 18 for v in values):
                raise ValidationError({'ids': 'Supply at most 100 comma-separated numeric IDs.'})
            queryset = queryset.filter(pk__in=values)
        return queryset

class PoemDetailAPI(generics.RetrieveAPIView):
    serializer_class = PoemSerializer
    queryset = Poem.objects.published().with_relations()
    lookup_field = 'slug'
