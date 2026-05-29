import ollama
import re

#Esta parte del código permanece en caso de necesitarse a futuro
"""def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Upscale less aggressively
    gray = cv2.resize(gray, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)
    # CLAHE for better contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    # Lighter denoising
    gray = cv2.bilateralFilter(gray, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    # Lighter morphology
    kernel = np.ones((1,1), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    # Save for debug
    cv2.imwrite('processed_debug.jpg', thresh)
    print("Processed image saved as processed_debug.jpg")
    return thresh
"""
def extraer_temperatura(image_path):
    response = ollama.chat(
        model='glm-ocr',
        messages=[{
            'role':'user',
            'content': 'Text Recognition',
            'images':[image_path]
        }]
    )
    valorLeido = response['message']['content']
    valorTerm = re.sub(r'[^0-9.]', '', valorLeido)
    try:
        return float(valorTerm)
    except ValueError:
        print(f"[ERROR OCR] Invalid number: '{valorTerm}'")
        return None
#respuesta = extraer_temperatura("media\imagenesTermometros_uploads/2026/04/23/003_20260423_104924_testcam.jpg")
#print(respuesta)
