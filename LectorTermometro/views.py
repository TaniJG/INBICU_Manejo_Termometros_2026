from django.shortcuts import render
from django import forms
from .models import LecturaTermometro, ElementoMedido, TipoElemento
from django.views import generic
import datetime as date
from django.conf import settings
from django.db.models import F, Q
import plotly.express as px
import pandas as pd
# Create your views here.
from django.http import HttpResponse,JsonResponse
import pandas as pd
import numpy as np
import os
from django.views.decorators.csrf import csrf_exempt
from .cargarMedida import cargarTermometro
from PIL import Image


#Agregar modificar, al menos para tipos???
class ListaDeElementos(generic.ListView):
    model = ElementoMedido
    template_name = 'LectorTermometro/listaElementos.html'
class ListaTiposDeElementos(generic.ListView):
    model = TipoElemento
    template_name = 'LectorTermometro/listaTipos.html'

class CrearElemento(generic.CreateView):
    model = ElementoMedido
    template_name = 'LectorTermometro/crearElemento.html'
    success_url = "/listaElementos"
    fields =["idElemento","tipoElemento"]
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['idElemento'].label = 'Id del Elemento'
        form.fields['tipoElemento'].label = 'Tipo de Elemento'
        choices = [('', '')] + list(TipoElemento.objects.values_list('tipoElemento', 'tipoElemento'))
        form.fields['tipoElemento'].widget = forms.Select(choices=choices)
        return form
class CrearTipo(generic.CreateView):
    model = TipoElemento
    template_name = 'LectorTermometro/crearTipo.html'
    success_url = "/listaTipos"
    fields = ["tipoElemento","minimoRango","maximoRango"]
    def get_form(self, form_class=None):
        form = super().get_form(form_class)  # Get form instance
        form.fields['tipoElemento'].label = 'Tipo de Elemento'
        form.fields['minimoRango'].label = 'Temperatura Mínima Aceptable (°C)'
        form.fields['maximoRango'].label = 'Temperatura Máxima Aceptable (°C)'
        return form

class RegistroTermometros(generic.ListView):
    model = LecturaTermometro
    template_name = 'LectorTermometro/listaTermometros.html'
    def get_queryset(self):
        fechaMedida = self.request.GET.get('q','')
        #Busqueda por día
        if fechaMedida:
            fechaFormateada = date.datetime.strptime(fechaMedida, '%Y-%m-%d').date()
            return self.model.objects.filter(fechaHoraMedida__date=fechaFormateada)
        return self.model.objects.all()
    def get_context_data(self, **kwargs): #Creamos tuplas a partir de los datos y el estado, para asegurar si se cumple el rango
        context = super().get_context_data(**kwargs)
        estadoMedidas = []
        for medida in context['object_list']:
            idElem= medida.idTermometro
            elementoM = ElementoMedido.objects.filter(idElemento = idElem).first()
            if elementoM is None or medida.temperatura is None:
                cumpleRango = False  # or None
            else:
                cumpleRango = enRango(elementoM.tipoElemento, medida.temperatura)
            estadoMedidas.append(cumpleRango)
        context['medidas_con_estado'] = zip(context["object_list"],estadoMedidas)
        return context
def enRango(tipo,temperatura):
    if temperatura is None:
        return False
    tipoElem = TipoElemento.objects.get(tipoElemento = tipo)
    cumple_rango = (temperatura >= tipoElem.minimoRango) and (temperatura <= tipoElem.maximoRango)
    return cumple_rango
#AREA DONDE SOLIAN ESTAR LAS VIEWS DE HISTOGRAMAS
#View que deberia obtern imagen de ESP32 (prototipo, no pensada para totalidad)
@csrf_exempt
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('photo'):
        idTermometro = request.POST.get('id', 'unknown')
        fecha = date.datetime.now()
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'imagenesTermometros_uploads', fecha.strftime('%Y/%m/%d'))
        os.makedirs(upload_dir, exist_ok=True)
        
        photo = request.FILES['photo']
        filename = f"{idTermometro}_{fecha.strftime('%Y%m%d_%H%M%S')}_{photo.name}"
        filepath = os.path.join(upload_dir, filename)
        
        print(f"[DEBUG] Saving {photo.name} ({photo.size} bytes) as {filepath}")
        
        # ALWAYS SAVE FILE FIRST
        raw_bytes = b''.join(chunk for chunk in photo.chunks())
        try:
            if len(raw_bytes) == 400 * 296 * 2:
                print(f"[DEBUG] RGB565 detected ({len(raw_bytes)} bytes)")
                img = Image.frombytes('RGB', (400, 296), raw_bytes, 'raw', 'BGR565')
                filepath = filepath.rsplit('.', 1)[0] + '_rgb565.jpg'
                img.save(filepath, 'JPEG', quality=85)
                print(f"[DEBUG] RGB565 converted to {filepath}")
            else:
                print(f"[DEBUG] JPEG/other ({len(raw_bytes)} bytes)")
                with open(filepath, 'wb') as f:
                    f.write(raw_bytes)  # Use collected bytes
            print(f"[DEBUG] File saved successfully")
        except Exception as save_err:
            print(f"[ERROR] Save failed: {save_err}")
            return JsonResponse({'status': 'error', 'message': f'Save failed: {str(save_err)}'})
        
        # NOW extract temp - NO DELETE ON FAIL
        temp_val = None
        try:
            print(f"[DEBUG] Calling cargarTermometro on {filepath}")
            tempeCargada = cargarTermometro(idTermometro, fecha, filepath)
            temp_val = float(tempeCargada) if tempeCargada is not None else None
            print(f"[DEBUG] OCR temp: {tempeCargada} → {temp_val}")
        except Exception as ocr_err:
            print(f"[WARN] OCR failed but file kept: {ocr_err}")
            temp_val = None  # Keep file, mark temp null
        
        return JsonResponse({
            'status': 'ok', 
            'filename': filename, 
            'path': filepath.replace(str(settings.BASE_DIR), ''),  # Relative path
            'temp': temp_val
        })
    
    return JsonResponse({'status': 'error', 'message': 'POST with photo required'})