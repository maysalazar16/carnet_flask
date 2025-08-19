from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
import os
import cv2

def procesar_foto_carnet(ruta_imagen, ruta_salida, ancho_carnet=300, alto_carnet=400):
    """
    Procesa una foto para carnet:
    1. Convierte a proporción 3:4
    2. Ajusta al tamaño del carnet
    3. Cambia el fondo a blanco automáticamente
    
    Args:
        ruta_imagen: Ruta de la imagen original
        ruta_salida: Ruta donde guardar la imagen procesada
        ancho_carnet: Ancho en píxeles para el carnet (default: 300px)
        alto_carnet: Alto en píxeles para el carnet (default: 400px)
    """
    try:
        print(f"🖼️ Procesando foto: {ruta_imagen}")
        
        # 1. Abrir la imagen
        imagen = Image.open(ruta_imagen)
        
        # 2. Convertir a RGB si es necesario
        if imagen.mode != 'RGB':
            imagen = imagen.convert('RGB')
            print("✅ Convertida a RGB")
        
        # 3. Mejorar la calidad de la imagen
        imagen = mejorar_calidad_imagen(imagen)
        
        # 4. Remover el fondo y ponerlo blanco
        imagen_sin_fondo = remover_fondo_simple(imagen)
        
        # 5. Redimensionar manteniendo proporción 3:4
        imagen_redimensionada = redimensionar_3x4(imagen_sin_fondo, ancho_carnet, alto_carnet)
        
        # 6. Aplicar mejoras finales
        imagen_final = aplicar_mejoras_finales(imagen_redimensionada)
        
        # 7. Guardar la imagen procesada
        imagen_final.save(ruta_salida, 'JPEG', quality=95, optimize=True)
        
        print(f"✅ Foto procesada guardada en: {ruta_salida}")
        print(f"📏 Dimensiones finales: {imagen_final.size}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error procesando foto: {str(e)}")
        return False

def mejorar_calidad_imagen(imagen):
    """Mejora la calidad básica de la imagen"""
    try:
        # Mejorar contraste ligeramente
        enhancer_contrast = ImageEnhance.Contrast(imagen)
        imagen = enhancer_contrast.enhance(1.1)
        
        # Mejorar nitidez ligeramente
        enhancer_sharpness = ImageEnhance.Sharpness(imagen)
        imagen = enhancer_sharpness.enhance(1.1)
        
        # Mejorar brillo si está muy oscura
        enhancer_brightness = ImageEnhance.Brightness(imagen)
        imagen = enhancer_brightness.enhance(1.05)
        
        return imagen
    except:
        return imagen

def remover_fondo_simple(imagen):
    """
    Intenta remover el fondo y ponerlo blanco usando técnicas simples
    """
    try:
        # Convertir PIL a numpy array para OpenCV
        imagen_np = np.array(imagen)
        
        # Convertir RGB a BGR para OpenCV
        imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
        
        # Método 1: Detección de bordes para encontrar la persona
        gray = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)
        
        # Aplicar blur para suavizar
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detectar bordes
        edges = cv2.Canny(blurred, 50, 150)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Encontrar el contorno más grande (probablemente la persona)
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Crear máscara
            mask = np.zeros(gray.shape, np.uint8)
            cv2.fillPoly(mask, [largest_contour], 255)
            
            # Suavizar la máscara
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            
            # Aplicar la máscara a la imagen original
            resultado = imagen_bgr.copy()
            
            # Poner fondo blanco donde la máscara es 0
            resultado[mask == 0] = [255, 255, 255]
            
            # Convertir de BGR a RGB y luego a PIL
            resultado_rgb = cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB)
            return Image.fromarray(resultado_rgb)
        else:
            # Si no se detectan contornos, aplicar método alternativo
            return remover_fondo_por_color(imagen)
            
    except Exception as e:
        print(f"⚠️ Error en remoción de fondo avanzada, usando método simple: {e}")
        return remover_fondo_por_color(imagen)

def remover_fondo_por_color(imagen):
    """
    Método alternativo: Remover fondo basado en colores predominantes en los bordes
    """
    try:
        # Convertir a array numpy
        img_array = np.array(imagen)
        
        # Obtener dimensiones
        height, width = img_array.shape[:2]
        
        # Analizar colores en los bordes (probablemente fondo)
        borde_superior = img_array[0:10, :].reshape(-1, 3)
        borde_inferior = img_array[height-10:height, :].reshape(-1, 3)
        borde_izquierdo = img_array[:, 0:10].reshape(-1, 3)
        borde_derecho = img_array[:, width-10:width].reshape(-1, 3)
        
        # Combinar todos los bordes
        colores_borde = np.vstack([borde_superior, borde_inferior, borde_izquierdo, borde_derecho])
        
        # Calcular color promedio del borde (probablemente el fondo)
        color_fondo = np.mean(colores_borde, axis=0).astype(int)
        
        print(f"🎨 Color de fondo detectado: {color_fondo}")
        
        # Crear máscara para píxeles similares al color de fondo
        tolerancia = 40  # Ajustable según necesidad
        
        # Calcular diferencia de color
        diff = np.abs(img_array - color_fondo).sum(axis=2)
        mask = diff < tolerancia
        
        # Aplicar fondo blanco
        resultado = img_array.copy()
        resultado[mask] = [255, 255, 255]  # Blanco
        
        return Image.fromarray(resultado)
        
    except Exception as e:
        print(f"⚠️ Error en remoción por color, devolviendo imagen original: {e}")
        return imagen

def redimensionar_3x4(imagen, ancho_objetivo, alto_objetivo):
    """
    Redimensiona la imagen manteniendo proporción 3:4 y ajustando al tamaño del carnet
    """
    # Calcular las dimensiones para proporción 3:4
    # Si el carnet es 300x400, la proporción es 3:4
    
    # Obtener dimensiones actuales
    ancho_actual, alto_actual = imagen.size
    
    # Calcular nueva proporción 3:4
    proporcion_objetivo = ancho_objetivo / alto_objetivo  # 300/400 = 0.75 (3:4)
    proporcion_actual = ancho_actual / alto_actual
    
    if proporcion_actual > proporcion_objetivo:
        # Imagen muy ancha, ajustar por alto
        nuevo_alto = alto_actual
        nuevo_ancho = int(nuevo_alto * proporcion_objetivo)
        # Recortar desde el centro
        left = (ancho_actual - nuevo_ancho) // 2
        imagen_recortada = imagen.crop((left, 0, left + nuevo_ancho, nuevo_alto))
    else:
        # Imagen muy alta, ajustar por ancho
        nuevo_ancho = ancho_actual
        nuevo_alto = int(nuevo_ancho / proporcion_objetivo)
        # Recortar desde arriba (para mantener la cara)
        top = max(0, (alto_actual - nuevo_alto) // 4)  # Recortar más desde abajo
        imagen_recortada = imagen.crop((0, top, nuevo_ancho, top + nuevo_alto))
    
    # Redimensionar a tamaño final
    imagen_final = imagen_recortada.resize((ancho_objetivo, alto_objetivo), Image.Resampling.LANCZOS)
    
    print(f"📏 Redimensionado de {imagen.size} a {imagen_final.size}")
    
    return imagen_final

def aplicar_mejoras_finales(imagen):
    """
    Aplica mejoras finales a la imagen para carnet
    """
    try:
        # Suavizar ligeramente para eliminar ruido
        imagen = imagen.filter(ImageFilter.SMOOTH_MORE)
        
        # Ajustar contraste final
        enhancer = ImageEnhance.Contrast(imagen)
        imagen = enhancer.enhance(1.05)
        
        return imagen
    except:
        return imagen

def validar_imagen(ruta_imagen):
    """
    Valida que la imagen sea procesable
    """
    try:
        with Image.open(ruta_imagen) as img:
            # Verificar que no esté corrupta
            img.verify()
        
        # Abrir de nuevo para usar (verify() cierra la imagen)
        imagen = Image.open(ruta_imagen)
        
        # Verificar dimensiones mínimas
        ancho, alto = imagen.size
        if ancho < 200 or alto < 200:
            return False, "La imagen es muy pequeña (mínimo 200x200 píxeles)"
        
        # Verificar tamaño de archivo (máximo 10MB)
        tamaño_archivo = os.path.getsize(ruta_imagen)
        if tamaño_archivo > 10 * 1024 * 1024:  # 10MB
            return False, "El archivo es muy grande (máximo 10MB)"
        
        return True, "Imagen válida"
        
    except Exception as e:
        return False, f"Error validando imagen: {str(e)}"

# Función principal para usar en el app.py
def procesar_foto_aprendiz(archivo_foto, cedula, carpeta_fotos="static/fotos"):
    """
    Función principal para procesar fotos de aprendices
    
    Args:
        archivo_foto: Objeto de archivo de Flask
        cedula: Cédula del aprendiz
        carpeta_fotos: Carpeta donde guardar las fotos
    
    Returns:
        tuple: (éxito, nombre_archivo, mensaje)
    """
    try:
        # Crear carpeta si no existe
        os.makedirs(carpeta_fotos, exist_ok=True)
        
        # Obtener extensión del archivo
        extension = os.path.splitext(archivo_foto.filename)[1].lower()
        if extension not in ['.jpg', '.jpeg', '.png']:
            return False, None, "Formato de archivo no válido. Use JPG o PNG"
        
        # Nombres de archivos
        nombre_temp = f"temp_{cedula}{extension}"
        nombre_final = f"{cedula}.jpg"  # Siempre guardar como JPG
        
        ruta_temp = os.path.join(carpeta_fotos, nombre_temp)
        ruta_final = os.path.join(carpeta_fotos, nombre_final)
        
        # Guardar archivo temporal
        archivo_foto.save(ruta_temp)
        
        # Validar imagen
        es_valida, mensaje_validacion = validar_imagen(ruta_temp)
        if not es_valida:
            os.remove(ruta_temp)
            return False, None, mensaje_validacion
        
        # Procesar la imagen
        exito = procesar_foto_carnet(ruta_temp, ruta_final, ancho_carnet=300, alto_carnet=400)
        
        # Eliminar archivo temporal
        if os.path.exists(ruta_temp):
            os.remove(ruta_temp)
        
        if exito:
            return True, nombre_final, "Foto procesada correctamente"
        else:
            return False, None, "Error procesando la foto"
            
    except Exception as e:
        # Limpiar archivos temporales en caso de error
        if 'ruta_temp' in locals() and os.path.exists(ruta_temp):
            os.remove(ruta_temp)
            
        return False, None, f"Error inesperado: {str(e)}"

# Función para instalar dependencias si no están disponibles
def verificar_dependencias():
    """
    Verifica e informa sobre las dependencias necesarias
    """
    dependencias = {
        'PIL': True,
        'numpy': True,
        'cv2': True
    }
    
    try:
        import cv2
    except ImportError:
        dependencias['cv2'] = False
        print("⚠️ OpenCV no está instalado. Instalar con: pip install opencv-python")
    
    try:
        import numpy
    except ImportError:
        dependencias['numpy'] = False
        print("⚠️ NumPy no está instalado. Instalar con: pip install numpy")
    
    try:
        from PIL import Image
    except ImportError:
        dependencias['PIL'] = False
        print("⚠️ Pillow no está instalado. Instalar con: pip install Pillow")
    
    return all(dependencias.values())

if __name__ == "__main__":
    print("🧪 Probando procesador de fotos...")
    verificar_dependencias()