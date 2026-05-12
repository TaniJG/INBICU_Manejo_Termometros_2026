from django.apps import AppConfig


class LectortermometroConfig(AppConfig):
    name = 'LectorTermometro'
    default_auto_field = 'django.db.models.BigAutoField'
    def ready(self):
        from .metrics import rango_minimo, rango_maximo
        from .models import TipoElemento
        for tipo in TipoElemento.objects.all():
            rango_minimo.labels(tipo_elemento=tipo.tipoElemento).set(tipo.minimoRango)
            rango_maximo.labels(tipo_elemento=tipo.tipoElemento).set(tipo.maximoRango)