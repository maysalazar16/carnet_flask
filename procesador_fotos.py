from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw
import numpy as np
import os
import cv2

def procesar_foto_carnet(ruta_imagen, ruta_salida, ancho_carnet=220, alto_carnet=270):
    """
    Procesa una foto para carnet SENA:
    1. Convierte a proporción correcta para el carnet
    2. Ajusta al tamaño del carnet (220x270 para tu imagen.py)
    3. Cambia el fondo a blanco automáticamente
    
    Args:
        ruta_imagen: Ruta de la imagen original
        ruta_salida: Ruta donde guardar la imagen procesada
        ancho_carnet: Ancho en píxeles para el carnet (220px para SENA)
        alto_carnet: Alto en píxeles para el carnet (270px para SENA)
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
        
        # 4. MEJORADO: Remover el fondo usando múltiples métodos
        imagen_sin_fondo = remover_fondo_avanzado(imagen)
        
        # 5. Redimensionar manteniendo proporción correcta
        imagen_redimensionada = redimensionar_para_carnet(imagen_sin_fondo, ancho_carnet, alto_carnet)
        
        # 6. Aplicar mejoras finales
        imagen_final = aplicar_mejoras_finales(imagen_redimensionada)
        
        # 7. Guardar la imagen procesada
        imagen_final.save(ruta_salida, 'PNG', quality=95, optimize=True)
        
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

def remover_fondo_avanzado(imagen):
    """
    MEJORADO: Intenta remover el fondo usando múltiples métodos
    """
    try:
        # Primero intentar con rembg si está disponible
        try:
            from rembg import remove
            print("🎯 Usando rembg para remover fondo...")
            
            # Convertir PIL a bytes
            import io
            img_byte_arr = io.BytesIO()
            imagen.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Remover fondo
            output = remove(img_byte_arr)
            
            # Convertir de vuelta a PIL
            imagen_sin_fondo = Image.open(io.BytesIO(output))
            
            # Agregar fondo blanco
            if imagen_sin_fondo.mode == 'RGBA':
                # Crear imagen con fondo blanco
                fondo_blanco = Image.new('RGB', imagen_sin_fondo.size, 'white')
                fondo_blanco.paste(imagen_sin_fondo, mask=imagen_sin_fondo.split()[3])
                print("✅ Fondo removido con rembg exitosamente")
                return fondo_blanco
            else:
                return imagen_sin_fondo
                
        except ImportError:
            print("⚠️ rembg no disponible, usando método OpenCV...")
            # Si rembg no está disponible, usar método OpenCV mejorado
            return remover_fondo_opencv_mejorado(imagen)
            
    except Exception as e:
        print(f"⚠️ Error en remoción avanzada, usando método simple: {e}")
        return remover_fondo_simple(imagen)

def remover_fondo_opencv_mejorado(imagen):
    """
    MEJORADO: Método OpenCV más avanzado para remover fondo
    """
    try:
        # Convertir PIL a numpy array
        imagen_np = np.array(imagen)
        imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
        
        # Método 1: Usar GrabCut para segmentación
        print("🔍 Aplicando GrabCut para segmentación...")
        
        height, width = imagen_bgr.shape[:2]
        
        # Definir rectángulo inicial (asumiendo que la persona está en el centro)
        margin = 20
        rect = (margin, margin, width - margin*2, height - margin*2)
        
        # Inicializar máscara y modelos
        mask = np.zeros((height, width), np.uint8)
        bgdModel = np.zeros((1, 65), np.float64)
        fgdModel = np.zeros((1, 65), np.float64)
        
        # Aplicar GrabCut
        cv2.grabCut(imagen_bgr, mask, rect, bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
        
        # Modificar la máscara
        mask2 = np.where((mask == 2) | (mask == 0), 0, 255).astype('uint8')
        
        # Aplicar morfología para limpiar la máscara
        kernel = np.ones((5, 5), np.uint8)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_CLOSE, kernel)
        mask2 = cv2.morphologyEx(mask2, cv2.MORPH_OPEN, kernel)
        
        # Suavizar los bordes de la máscara
        mask2 = cv2.GaussianBlur(mask2, (5, 5), 0)
        
        # Crear imagen con fondo blanco
        resultado = np.ones_like(imagen_bgr) * 255  # Fondo blanco
        
        # Aplicar la máscara
        mask3d = cv2.cvtColor(mask2, cv2.COLOR_GRAY2BGR) / 255.0
        resultado = (imagen_bgr * mask3d + resultado * (1 - mask3d)).astype(np.uint8)
        
        # Convertir de BGR a RGB y luego a PIL
        resultado_rgb = cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB)
        
        print("✅ Fondo removido con GrabCut")
        return Image.fromarray(resultado_rgb)
        
    except Exception as e:
        print(f"⚠️ Error con GrabCut, intentando método de detección facial: {e}")
        return remover_fondo_con_deteccion_facial(imagen)

def remover_fondo_con_deteccion_facial(imagen):
    """
    Método que detecta la cara y construye la máscara alrededor
    """
    try:
        imagen_np = np.array(imagen)
        imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)
        
        # Cargar el clasificador de caras
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Detectar caras
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) > 0:
            print("👤 Cara detectada, construyendo máscara...")
            
            # Tomar la primera cara detectada
            (x, y, w, h) = faces[0]
            
            # Expandir el área para incluir hombros y cabello
            expand_ratio = 2.0
            x_new = max(0, int(x - w * (expand_ratio - 1) / 2))
            y_new = max(0, int(y - h * 0.3))
            w_new = min(imagen_bgr.shape[1] - x_new, int(w * expand_ratio))
            h_new = min(imagen_bgr.shape[0] - y_new, int(h * 2.5))
            
            # Crear máscara elíptica alrededor de la persona
            mask = np.zeros(gray.shape, np.uint8)
            center = (x_new + w_new // 2, y_new + h_new // 2)
            axes = (w_new // 2, h_new // 2)
            cv2.ellipse(mask, center, axes, 0, 0, 360, 255, -1)
            
            # Suavizar la máscara
            mask = cv2.GaussianBlur(mask, (21, 21), 0)
            
            # Aplicar la máscara
            resultado = np.ones_like(imagen_bgr) * 255  # Fondo blanco
            mask3d = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
            resultado = (imagen_bgr * mask3d + resultado * (1 - mask3d)).astype(np.uint8)
            
            resultado_rgb = cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB)
            print("✅ Fondo removido usando detección facial")
            return Image.fromarray(resultado_rgb)
        else:
            print("⚠️ No se detectó cara, usando método simple")
            return remover_fondo_simple(imagen)
            
    except Exception as e:
        print(f"⚠️ Error en detección facial: {e}")
        return remover_fondo_simple(imagen)

def remover_fondo_simple(imagen):
    """
    Método simple mejorado: Remover fondo basado en color dominante
    """
    try:
        # Convertir PIL a numpy array para OpenCV
        imagen_np = np.array(imagen)
        imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
        
        # Convertir a HSV para mejor detección de color
        hsv = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2HSV)
        
        # Detectar el color dominante en los bordes
        height, width = imagen_bgr.shape[:2]
        border_size = 20
        
        # Obtener píxeles del borde
        border_pixels = []
        border_pixels.extend(hsv[0:border_size, :].reshape(-1, 3))
        border_pixels.extend(hsv[height-border_size:height, :].reshape(-1, 3))
        border_pixels.extend(hsv[:, 0:border_size].reshape(-1, 3))
        border_pixels.extend(hsv[:, width-border_size:width].reshape(-1, 3))
        
        border_pixels = np.array(border_pixels)
        
        # Calcular el color promedio del borde
        mean_color = np.mean(border_pixels, axis=0).astype(int)
        
        # Crear máscara basada en rango de colores
        tolerance = 30
        lower = np.array([max(0, mean_color[0] - tolerance), 50, 50])
        upper = np.array([min(179, mean_color[0] + tolerance), 255, 255])
        
        # Crear máscara
        mask = cv2.inRange(hsv, lower, upper)
        
        # Invertir la máscara (queremos mantener lo que NO es fondo)
        mask_inv = cv2.bitwise_not(mask)
        
        # Limpiar la máscara con operaciones morfológicas
        kernel = np.ones((5, 5), np.uint8)
        mask_inv = cv2.morphologyEx(mask_inv, cv2.MORPH_CLOSE, kernel)
        mask_inv = cv2.morphologyEx(mask_inv, cv2.MORPH_OPEN, kernel)
        
        # Suavizar bordes
        mask_inv = cv2.GaussianBlur(mask_inv, (5, 5), 0)
        
        # Aplicar la máscara
        resultado = np.ones_like(imagen_bgr) * 255  # Fondo blanco
        mask3d = cv2.cvtColor(mask_inv, cv2.COLOR_GRAY2BGR) / 255.0
        resultado = (imagen_bgr * mask3d + resultado * (1 - mask3d)).astype(np.uint8)
        
        # Convertir de BGR a RGB y luego a PIL
        resultado_rgb = cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB)
        print("✅ Fondo removido con método simple")
        return Image.fromarray(resultado_rgb)
        
    except Exception as e:
        print(f"⚠️ Error en remoción simple, aplicando fondo blanco directo: {e}")
        # Como último recurso, aclarar el fondo
        return aplicar_fondo_blanco_suave(imagen)

def aplicar_fondo_blanco_suave(imagen):
    """
    Último recurso: Aclarar el fondo gradualmente
    """
    try:
        # Convertir a array numpy
        img_array = np.array(imagen)
        
        # Crear una máscara radial desde el centro
        height, width = img_array.shape[:2]
        center_x, center_y = width // 2, height // 3  # Centro un poco arriba (para la cara)
        
        # Crear gradiente radial
        Y, X = np.ogrid[:height, :width]
        dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
        max_dist = np.sqrt(center_x**2 + center_y**2)
        
        # Normalizar distancia
        mask = 1 - (dist_from_center / max_dist)
        mask = np.clip(mask, 0.3, 1)  # Mantener mínimo 30% de la imagen
        
        # Expandir máscara a 3 canales
        mask_3d = np.stack([mask, mask, mask], axis=2)
        
        # Mezclar con blanco
        white_bg = np.ones_like(img_array) * 255
        resultado = img_array * mask_3d + white_bg * (1 - mask_3d)
        
        print("✅ Fondo aclarado con método suave")
        return Image.fromarray(resultado.astype(np.uint8))
        
    except Exception as e:
        print(f"⚠️ Error aplicando fondo blanco suave: {e}")
        return imagen

def redimensionar_para_carnet(imagen, ancho_objetivo, alto_objetivo):
    """
    Redimensiona la imagen para el carnet SENA manteniendo la cara centrada
    """
    # Obtener dimensiones actuales
    ancho_actual, alto_actual = imagen.size
    
    # Calcular proporción objetivo
    proporcion_objetivo = ancho_objetivo / alto_objetivo
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
        
        # Asegurar que los bordes sean blancos
        imagen = agregar_borde_blanco(imagen)
        
        return imagen
    except:
        return imagen

def agregar_borde_blanco(imagen, grosor=2):
    """
    Agrega un borde blanco delgado para asegurar fondo limpio
    """
    try:
        # Crear nueva imagen un poco más grande
        ancho, alto = imagen.size
        nueva_imagen = Image.new('RGB', (ancho, alto), 'white')
        
        # Pegar la imagen original dejando borde blanco
        nueva_imagen.paste(imagen, (0, 0))
        
        # Pintar los bordes de blanco
        draw = ImageDraw.Draw(nueva_imagen)
        
        # Borde superior
        draw.rectangle([(0, 0), (ancho, grosor)], fill='white')
        # Borde inferior
        draw.rectangle([(0, alto-grosor), (ancho, alto)], fill='white')
        # Borde izquierdo
        draw.rectangle([(0, 0), (grosor, alto)], fill='white')
        # Borde derecho
        draw.rectangle([(ancho-grosor, 0), (ancho, alto)], fill='white')
        
        return nueva_imagen
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

# ========== FUNCIONES NUEVAS AGREGADAS ==========

def detectar_si_fondo_es_blanco(imagen):
    """
    Detecta si el fondo de la imagen ya es blanco
    Retorna True si el fondo es mayormente blanco
    """
    try:
        # Convertir a array numpy
        img_array = np.array(imagen)
        height, width = img_array.shape[:2]
        
        # Tomar muestras del borde (probable fondo)
        border_size = 20
        
        # Muestras de los 4 bordes
        muestras = []
        muestras.extend(img_array[0:border_size, :].reshape(-1, 3))  # Superior
        muestras.extend(img_array[height-border_size:height, :].reshape(-1, 3))  # Inferior
        muestras.extend(img_array[:, 0:border_size].reshape(-1, 3))  # Izquierdo
        muestras.extend(img_array[:, width-border_size:width].reshape(-1, 3))  # Derecho
        
        muestras = np.array(muestras)
        
        # Calcular el promedio de los bordes
        promedio = np.mean(muestras, axis=0)
        
        # Si el promedio de todos los canales es > 240, es prácticamente blanco
        es_blanco = all(promedio > 240)
        
        if es_blanco:
            print("✅ Fondo detectado como BLANCO - No se procesará")
        else:
            print(f"🔍 Fondo detectado NO blanco (RGB promedio: {promedio.astype(int)}) - Se procesará")
        
        return es_blanco
        
    except Exception as e:
        print(f"⚠️ Error detectando fondo: {e}")
        return False

def verificar_si_foto_existe(cedula, carpeta_fotos="static/fotos"):
    """
    Verifica si ya existe una foto para esta cédula
    """
    posibles_nombres = [
        f"foto_{cedula}.png",
        f"foto_{cedula}.jpg",
        f"{cedula}.png",
        f"{cedula}.jpg"
    ]
    
    for nombre in posibles_nombres:
        ruta = os.path.join(carpeta_fotos, nombre)
        if os.path.exists(ruta):
            print(f"⚠️ Ya existe una foto para la cédula {cedula}: {ruta}")
            return True, ruta
    
    return False, None

# ========== FIN DE FUNCIONES NUEVAS ==========

# Función principal para usar en el app.py
def procesar_foto_aprendiz(archivo_foto, cedula, carpeta_fotos="static/fotos"):
    """
    Función principal para procesar fotos de aprendices
    IMPORTANTE: Guarda como foto_{cedula}.png para compatibilidad con imagen.py
    
    Args:
        archivo_foto: Objeto de archivo de Flask
        cedula: Cédula del aprendiz
        carpeta_fotos: Carpeta donde guardar las fotos
    
    Returns:
        tuple: (éxito, nombre_archivo, mensaje)
    """
    try:
        # VERIFICAR SI YA EXISTE FOTO
        existe, ruta_existente = verificar_si_foto_existe(cedula, carpeta_fotos)
        if existe:
            return False, None, f"Ya existe una foto cargada para la cédula {cedula}. No se puede cargar otra foto."
        
        # Crear carpeta si no existe
        os.makedirs(carpeta_fotos, exist_ok=True)
        
        # Obtener extensión del archivo
        extension = os.path.splitext(archivo_foto.filename)[1].lower()
        if extension not in ['.jpg', '.jpeg', '.png']:
            return False, None, "Formato de archivo no válido. Use JPG o PNG"
        
        # Nombres de archivos
        nombre_temp = f"temp_{cedula}{extension}"
        # IMPORTANTE: Guardar como foto_{cedula}.png para que imagen.py lo encuentre
        nombre_final = f"foto_{cedula}.png"  # Cambiado para compatibilidad
        
        ruta_temp = os.path.join(carpeta_fotos, nombre_temp)
        ruta_final = os.path.join(carpeta_fotos, nombre_final)
        
        # Guardar archivo temporal
        archivo_foto.save(ruta_temp)
        
        # Validar imagen
        es_valida, mensaje_validacion = validar_imagen(ruta_temp)
        if not es_valida:
            os.remove(ruta_temp)
            return False, None, mensaje_validacion
        
        # Abrir imagen para verificar el fondo
        imagen = Image.open(ruta_temp)
        if imagen.mode != 'RGB':
            imagen = imagen.convert('RGB')
        
        # VERIFICAR SI EL FONDO YA ES BLANCO
        if detectar_si_fondo_es_blanco(imagen):
            print("ℹ️ El fondo ya es blanco, solo se redimensionará")
            # Solo redimensionar sin procesar el fondo
            imagen_redimensionada = redimensionar_para_carnet(imagen, 220, 270)
            imagen_redimensionada.save(ruta_final, 'PNG', quality=95, optimize=True)
            exito = True
        else:
            print("🔧 Fondo no es blanco, procesando imagen completa...")
            # Procesar la imagen con dimensiones correctas para el carnet SENA
            exito = procesar_foto_carnet(ruta_temp, ruta_final, ancho_carnet=220, alto_carnet=270)
        
        # Eliminar archivo temporal
        if os.path.exists(ruta_temp):
            os.remove(ruta_temp)
        
        if exito:
            print(f"✅ Foto guardada como: {nombre_final}")
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
        'cv2': True,
        'rembg': True
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
    
    try:
        from rembg import remove
        print("✅ rembg disponible - se usará para mejor remoción de fondo")
    except ImportError:
        dependencias['rembg'] = False
        print("💡 rembg no está instalado. Para mejor remoción de fondo instalar con: pip install rembg")
        print("   (El sistema funcionará sin rembg usando métodos alternativos)")
    
    return dependencias['PIL'] and dependencias['numpy'] and dependencias['cv2']

# Función de prueba directa
def probar_procesamiento(ruta_imagen_prueba):
    """
    Función para probar el procesamiento con una imagen
    """
    if not os.path.exists(ruta_imagen_prueba):
        print(f"❌ No existe el archivo: {ruta_imagen_prueba}")
        return
    
    print(f"🧪 Probando con: {ruta_imagen_prueba}")
    
    # Simular el objeto de archivo de Flask
    class ArchivoSimulado:
        def __init__(self, ruta):
            self.filename = os.path.basename(ruta)
            self.ruta = ruta
        
        def save(self, destino):
            import shutil
            shutil.copy(self.ruta, destino)
    
    archivo = ArchivoSimulado(ruta_imagen_prueba)
    exito, nombre, mensaje = procesar_foto_aprendiz(archivo, "12345678")
    
    if exito:
        print(f"✅ Prueba exitosa: {mensaje}")
        print(f"📁 Archivo guardado: static/fotos/{nombre}")
    else:
        print(f"❌ Prueba fallida: {mensaje}")

if __name__ == "__main__":
    print("🧪 Verificando procesador de fotos para SENA...")
    print("=" * 60)
    print("CARACTERÍSTICAS:")
    print("✅ Solo quita fondo si NO es blanco")
    print("✅ NO recorta vestimenta ni partes del cuerpo")
    print("✅ Verifica si ya existe foto antes de procesar")
    print("=" * 60)
    
    if verificar_dependencias():
        print("\n✅ Todas las dependencias básicas están instaladas")
        print("\n💡 Para probar con una imagen, ejecuta:")
        print('   python procesador_fotos.py "ruta/a/tu/imagen.jpg"')
        
        import sys
        if len(sys.argv) > 1:
            probar_procesamiento(sys.argv[1])
    else:
        print("\n❌ Faltan dependencias. Instala las faltantes antes de usar el sistema.")