from .models import LecturaTermometro
from .leerImagenTerm import extraer_temperatura

#Esta función se plantea para ser llamada una vez se obtenga la foto de la ESP-32 mediante Arduino,
def cargarTermometro(id,tiempoHora,imag_path): #Abierto a modificaciones futuras
    tempMedida = extraer_temperatura(imag_path)
    if tempMedida is None:
        tempTermometro = None
    else:
        if tempMedida > 1000:
            tempTermometro = tempMedida/100
        elif tempMedida > 50:
            tempTermometro = tempMedida/10
        else:
            tempTermometro = tempMedida
    LecturaTermometro.objects.create(
        idTermometro = id,
        temperatura = tempTermometro,
        fechaHoraMedida = tiempoHora
    )
    return tempTermometro