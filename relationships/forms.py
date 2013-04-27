from django import forms
from django.db.models import Q

from .models import RelationshipStatus


class RelationshipStatusAdminForm(forms.ModelForm):
    class Meta:
        model = RelationshipStatus

    def duplicate_slug_check(self, status_slug):
        status_qs = RelationshipStatus.objects.filter(
            Q(from_slug=status_slug) |
            Q(to_slug=status_slug) |
            Q(symmetrical_slug=status_slug)
        )

        if self.instance.pk:
            status_qs = status_qs.exclude(pk=self.instance.pk)

        if status_qs.exists():
            raise forms.ValidationError('"%s" slug already in use on %s' %
                (status_slug, unicode(status_qs[0])))

    def clean_from_slug(self):
        self.duplicate_slug_check(self.cleaned_data['from_slug'])
        return self.cleaned_data['from_slug']

    def clean_to_slug(self):
        self.duplicate_slug_check(self.cleaned_data['to_slug'])
        return self.cleaned_data['to_slug']

    def clean_symmetrical_slug(self):
        self.duplicate_slug_check(self.cleaned_data['symmetrical_slug'])
        return self.cleaned_data['symmetrical_slug']

    def clean(self):
        if self.errors:
            return self.cleaned_data

        if self.cleaned_data['from_slug'] == self.cleaned_data['to_slug'] or \
           self.cleaned_data['to_slug'] == self.cleaned_data['symmetrical_slug'] or \
           self.cleaned_data['symmetrical_slug'] == self.cleaned_data['from_slug']:
            raise forms.ValidationError('from, to, and symmetrical slugs must be different')

        return self.cleaned_data
