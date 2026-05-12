from .models import LecturaTermometro
from .leerImagenTerm import extraer_temperatura

#Esta función se plantea para ser llamada una vez se obtenga la foto de la ESP-32 mediante Arduino,
# pero no estoy seguro si la misma tendra el tiempo y hora aparte o si tendre que extraerlos de la imagen
def cargarTermometro(id,tiempoHora,imag_path): #Abierto a modificaciones futuras
    tempMedida = extraer_temperatura(imag_path)
    if not tempMedida:
        tempTermometro = None
    else:
        if tempMedida > 1000:
            tempTermometro = tempMedida/100
        elif tempMedida > 60:
            tempTermometro = tempMedida/10
        else:
            tempTermometro = tempMedida
    LecturaTermometro.objects.create(
        idTermometro = id,
        temperatura = tempTermometro,
        fechaHoraMedida = tiempoHora
    )
    return tempMedida