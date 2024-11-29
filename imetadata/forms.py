from django import forms
from django.core.exceptions import ValidationError
import os

class ImageUploadForm(forms.Form):
    image = forms.ImageField()

    def clean_image(self):
        image = self.cleaned_data.get('image')

        # Validate file extension
        valid_extensions = ['.jpg', '.jpeg', '.png']
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in valid_extensions:
            raise ValidationError("Unsupported file extension. Please upload a .jpg, .jpeg, or .png file.")

        # Optional: Validate file MIME type
        valid_mime_types = ['image/jpeg', 'image/png']
        if image.content_type not in valid_mime_types:
            raise ValidationError("Unsupported file type. Please upload a valid image.")

        return image
