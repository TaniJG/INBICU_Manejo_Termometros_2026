from django.urls import path
from django.http import HttpResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from . import views

def metrics_view(request):
    # Lazily initialize gauges on first scrape to avoid DB queries at startup.
    from .metrics_init import init_rangos_from_db

    init_rangos_from_db()
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


app_name = "LectorTermometro"
urlpatterns = [
    path("", views.RegistroTermometros.as_view(), name="listaTermometros"),
    #path("histogramas", views.histogramasTemperatura, name="histogramasTemperatura"),
    path("listaElementos", views.ListaDeElementos.as_view(), name="listaElementos"),
    path("listaTipos", views.ListaTiposDeElementos.as_view(), name="listaTipos"),
    path("crearElemento", views.CrearElemento.as_view(), name="crearElemento"),
    path("crearTipo", views.CrearTipo.as_view(), name="crearTipo"),
    path('upload/', views.upload_image, name='upload_image'),
    path('metricsT/', metrics_view),
]