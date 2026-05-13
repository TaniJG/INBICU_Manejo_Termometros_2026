from __future__ import annotations

from typing import Final

from .metrics import rango_minimo, rango_maximo


_INITIALIZED: bool = False

#Cargamos los tipos a las metricas de Prometheus para uso en grafana.
def init_rangos_from_db() -> None:
    global _INITIALIZED
    if _INITIALIZED:
        return

    from .models import TipoElemento

    for tipo in TipoElemento.objects.all():
        rango_minimo.labels(tipo_elemento=tipo.tipoElemento).set(tipo.minimoRango)
        rango_maximo.labels(tipo_elemento=tipo.tipoElemento).set(tipo.maximoRango)

    _INITIALIZED = True

