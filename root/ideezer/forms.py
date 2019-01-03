from django import forms


class UploadLibraryForm(forms.Form):
    file = forms.FileField()
