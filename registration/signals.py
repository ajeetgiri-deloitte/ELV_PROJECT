from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.db import models
from utils.file_cleaner import sanitize_file

@receiver(pre_save)
def sanitize_uploaded_files(sender, instance, **kwargs):
    # Skip Django internal models
    if sender._meta.app_label in ['admin', 'contenttypes', 'sessions', 'auth']:
        return

    for field in instance._meta.fields:
        if isinstance(field, models.FileField):
            file = getattr(instance, field.name)
            if file:
                setattr(instance, field.name, sanitize_file(file))
