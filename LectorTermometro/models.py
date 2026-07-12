from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# Create your models here.
class LecturaTermometro(models.Model):
    idTermometro = models.CharField(max_length=10)
    temperatura = models.FloatField(null=True)
    fechaHoraMedida = models.DateTimeField(auto_now_add=True)

@receiver(post_save, sender=LecturaTermometro)
def actualizar_temperatura(sender, instance, **kwargs):
    if instance.temperatura is not None:
        from .metrics import temperatura_termometro
        try:
            elemento = ElementoMedido.objects.get(idElemento=instance.idTermometro)
            tipo = elemento.tipoElemento
            descripcion = elemento.descripElemento
        except ElementoMedido.DoesNotExist:
            tipo = "desconocido"
            descripcion = "desconocido"

        temperatura_termometro.labels(
            id_termometro=instance.idTermometro,
            tipo_elemento=tipo,
            descripcion_elemento=descripcion
        ).set(instance.temperatura)


@receiver(post_delete, sender=LecturaTermometro)
def borrar_temperatura(sender, instance, **kwargs):
    if instance.temperatura is None:
        return

    from .metrics import temperatura_termometro

    try:
        elemento = ElementoMedido.objects.get(idElemento=instance.idTermometro)
        tipo = elemento.tipoElemento
        descripcion = elemento.descripElemento
    except ElementoMedido.DoesNotExist:
        tipo = "desconocido"
        descripcion = "desconocido"

    temperatura_termometro.remove(
        id_termometro=instance.idTermometro,
        tipo_elemento=tipo,
        descripcion_elemento=descripcion,
    )



class ElementoMedido(models.Model):
    idElemento = models.CharField(max_length=10)
    descripElemento = models.CharField(max_length=20, default="")
    tipoElemento = models.CharField(max_length=15)


class TipoElemento(models.Model):
    tipoElemento = models.CharField(max_length=15)
    minimoRango = models.FloatField(default=10)
    maximoRango = models.FloatField(default=20)

@receiver(post_save, sender=TipoElemento)
@receiver(post_delete, sender=TipoElemento)
def sync_rangos(sender, instance=None, **kwargs):
    from .metrics import rango_minimo, rango_maximo
    # Clear and reload all ranges
    rango_minimo.clear()
    rango_maximo.clear()
    for tipo in TipoElemento.objects.all():
        rango_minimo.labels(tipo_elemento=tipo.tipoElemento).set(tipo.minimoRango)
        rango_maximo.labels(tipo_elemento=tipo.tipoElemento).set(tipo.maximoRango)