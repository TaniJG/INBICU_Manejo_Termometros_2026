from django.contrib import admin

from .models import LecturaTermometro, ElementoMedido, TipoElemento

admin.site.register(LecturaTermometro)
admin.site.register(ElementoMedido)
admin.site.register(TipoElemento)

# Register your models here.
