from django.contrib import admin

from .models import Ideia, Link, Prompt, Video

for modelo in (Prompt, Ideia, Link, Video):
    admin.site.register(modelo)
