import cv2
import pytesseract
from pytesseract import Output

# Ruta a tesseract (ajusta si es necesario)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Cargar imagen
img = cv2.imread("example.png")
if img is None:
    raise FileNotFoundError("Imagen no encontrada.")

h, w = img.shape[:2]

# Regiones definidas (x1, y1, x2, y2)
regions = {
    # "hp": (4, 23, w - 2, 34),
    # "mp": (60, 37, w - 58, 51),
    "target_name": (40, 55, w - 40, 67),
}


def preprocess(region_img):
    # Inversión
    invert = cv2.bitwise_not(region_img)
    # Aumentar contraste
    contrast = cv2.convertScaleAbs(invert, alpha=5, beta=-10)
    # Escala de grises
    gray = cv2.cvtColor(contrast, cv2.COLOR_BGR2GRAY)
    # Binarización
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return thresh


# OCR por región
for key, (x1, y1, x2, y2) in regions.items():
    cropped = img[y1:y2, x1:x2]
    processed = preprocess(cropped)
    text = pytesseract.image_to_string(processed, config="--psm 7")

    print(f"{key.upper()}: {text if text else '(n/detectado)'}")
    # Si quieres ver la región:
    cv2.imwrite(f"debug_{key}.png", processed)


# cv2.waitKey(0)
# cv2.destroyAllWindows()
