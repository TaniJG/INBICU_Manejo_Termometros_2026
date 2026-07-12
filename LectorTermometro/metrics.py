from prometheus_client import Gauge

temperatura_termometro = Gauge(
    'temperatura_termometro_celsius',
    'Lecturas de Temperatura por Termometro',
    ['id_termometro','tipo_elemento','descripcion_elemento']  # labels
)

rango_minimo = Gauge(
    'temperatura_rango_minimo',
    'Minimum allowed temperature by type',
    ['tipo_elemento']
)

rango_maximo = Gauge(
    'temperatura_rango_maximo',
    'Maximum allowed temperature by type',
    ['tipo_elemento']
)