import ollama
import re

def extraer_temperatura(image_path):
    try:
        # Añadimos el parámetro options para cortar alucinaciones
        response = ollama.chat(
            model='glm-ocr',
            messages=[{
                'role': 'user',
                'content': 'Identify the temperature value shown in the display. Output ONLY the number, nothing else.',
                'images': [image_path]
            }],
            options={
                'num_predict': 10,       # Fuerza al modelo a detenerse tras 10 tokens (caracteres/palabras)
            }
        )
        
        valorLeido = response['message']['content'].strip()
        print(f"[DEBUG OCR] Respuesta cruda de Ollama: '{valorLeido}'")
        
        match = re.search(r'-?\d+(?:\.\d+)?', valorLeido.replace(',', '.'))

        if match:
            return float(match.group(0))
        
        print(f"[WARN OCR] No se pudo parsear un número de: '{valorLeido}'")
        return None
        
    except Exception as e:
        print(f"[SYSTEM ERROR OCR] Error en la llamada a Ollama: {e}")
        return None