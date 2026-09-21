from django.contrib import admin

from .models import Ideia, Link, Prompt

for modelo in (Prompt, Ideia, Link):
    admin.site.register(modelo)
