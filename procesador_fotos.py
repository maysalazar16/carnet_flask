from PIL import Image, ImageFilter, ImageEnhance, ImageOps, ImageDraw
import numpy as np
import os
import cv2

def procesar_foto_carnet(ruta_imagen, ruta_salida, ancho_carnet=220, alto_carnet=270):
    """
    Procesa una foto para carnet SENA:
    1. Convierte a proporción correcta para el carnet
    2. Ajusta al tamaño del carnet (220x270 para tu imagen.py)
    3. Cambia el fondo a blanco automáticamente SIN tocar la ropa
    
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
        
        # 4. MEJORADO: Remover el fondo ULTRA conservador
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
    ULTRA CONSERVADOR: Solo elimina fondo por detección de color de bordes
    NO toca la ropa ni el cuerpo
    """
    try:
        # 1. Intentar con rembg primero (el más preciso)
        try:
            from rembg import remove
            print("🎯 Usando rembg (método más preciso)...")
            
            import io
            img_byte_arr = io.BytesIO()
            imagen.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            output = remove(img_byte_arr)
            imagen_sin_fondo = Image.open(io.BytesIO(output))
            
            if imagen_sin_fondo.mode == 'RGBA':
                fondo_blanco = Image.new('RGB', imagen_sin_fondo.size, 'white')
                fondo_blanco.paste(imagen_sin_fondo, mask=imagen_sin_fondo.split()[3])
                print("✅ Fondo removido con rembg (preciso)")
                return fondo_blanco
            else:
                return imagen_sin_fondo
                
        except ImportError:
            print("⚠️ rembg no disponible, usando método conservador...")
            return remover_fondo_solo_bordes(imagen)
            
    except Exception as e:
        print(f"⚠️ Error, usando método de respaldo: {e}")
        return remover_fondo_solo_bordes(imagen)

def remover_fondo_solo_bordes(imagen):
    """
    NUEVO: Método ULTRA conservador - solo elimina el color del borde
    """
    try:
        imagen_np = np.array(imagen)
        imagen_bgr = cv2.cvtColor(imagen_np, cv2.COLOR_RGB2BGR)
        
        height, width = imagen_bgr.shape[:2]
        
        # Detectar color dominante SOLO en las esquinas (fondo real)
        corner_size = 30
        
        # Tomar muestras solo de las 4 esquinas
        esquinas = []
        esquinas.extend(imagen_bgr[0:corner_size, 0:corner_size].reshape(-1, 3))  # Esquina superior izquierda
        esquinas.extend(imagen_bgr[0:corner_size, width-corner_size:width].reshape(-1, 3))  # Superior derecha
        esquinas.extend(imagen_bgr[height-corner_size:height, 0:corner_size].reshape(-1, 3))  # Inferior izquierda
        esquinas.extend(imagen_bgr[height-corner_size:height, width-corner_size:width].reshape(-1, 3))  # Inferior derecha
        
        esquinas = np.array(esquinas)
        color_fondo = np.mean(esquinas, axis=0).astype(int)
        
        print(f"🎨 Color de fondo detectado (BGR): {color_fondo}")
        
        # Crear máscara solo para ese color específico con tolerancia ALTA
        tolerance = 60  # Muy alta para ser conservador
        lower = np.maximum(0, color_fondo - tolerance)
        upper = np.minimum(255, color_fondo + tolerance)
        
        # Máscara: True donde está el fondo
        mask_fondo = cv2.inRange(imagen_bgr, lower, upper)
        
        # IMPORTANTE: Erosionar la máscara para NO tocar los bordes de la persona
        kernel_erode = np.ones((5, 5), np.uint8)
        mask_fondo = cv2.erode(mask_fondo, kernel_erode, iterations=3)  # Erosión fuerte
        
        # Invertir máscara (True donde está la persona)
        mask_persona = cv2.bitwise_not(mask_fondo)
        
        # IMPORTANTE: Dilatar la máscara de la persona para incluir TODO
        kernel_dilate = np.ones((20, 20), np.uint8)
        mask_persona = cv2.dilate(mask_persona, kernel_dilate, iterations=3)  # Dilatación fuerte
        
        # Suavizar MUCHO los bordes
        mask_persona = cv2.GaussianBlur(mask_persona, (31, 31), 0)
        
        # Aplicar: fondo blanco, persona original
        resultado = np.ones_like(imagen_bgr) * 255  # Fondo blanco
        mask3d = cv2.cvtColor(mask_persona, cv2.COLOR_GRAY2BGR) / 255.0
        resultado = (imagen_bgr * mask3d + resultado * (1 - mask3d)).astype(np.uint8)
        
        resultado_rgb = cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB)
        print("✅ Fondo removido SOLO por color de bordes (ultra conservador)")
        return Image.fromarray(resultado_rgb)
        
    except Exception as e:
        print(f"⚠️ Error en método conservador: {e}")
        # Si todo falla, devolver imagen original
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
            return False, None, f"Ya existe una foto cargada para la cédula {cedula}. Elimínala primero si deseas cargar otra."
        
        # Crear carpeta si no existe
        os.makedirs(carpeta_fotos, exist_ok=True)
        
        # Obtener extensión del archivo
        extension = os.path.splitext(archivo_foto.filename)[1].lower()
        if extension not in ['.jpg', '.jpeg', '.png']:
            return False, None, "Formato de archivo no válido. Use JPG o PNG"
        
        # Nombres de archivos
        nombre_temp = f"temp_{cedula}{extension}"
        # IMPORTANTE: Guardar como foto_{cedula}.png para que imagen.py lo encuentre
        nombre_final = f"foto_{cedula}.png"
        
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
            print("🔧 Procesando imagen para eliminar fondo...")
            exito = procesar_foto_carnet(ruta_temp, ruta_final, ancho_carnet=220, alto_carnet=270)  
        
        # Eliminar archivo temporal
        if os.path.exists(ruta_temp):
            os.remove(ruta_temp)
        
        if exito:
            print(f"✅ Foto guardada como: {nombre_final}")
            return True, nombre_final, "Foto procesada correctamente (solo fondo eliminado, ropa intacta)"
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
        'rembg': False
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
        dependencias['rembg'] = True
        print("✅ rembg disponible - se usará para MEJOR remoción de fondo (recomendado)")
    except ImportError:
        print("💡 RECOMENDADO: Instalar rembg para mejor precisión: pip install rembg")
        print("   (El sistema funcionará sin rembg pero con menor precisión)")
    
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
    print("=" * 70)
    print("🎓 PROCESADOR DE FOTOS PARA CARNETS SENA")
    print("=" * 70)
    print("CARACTERÍSTICAS ULTRA CONSERVADORAS:")
    print("✅ Solo elimina FONDO (detectado por color de esquinas)")
    print("✅ NO toca ropa, brazos, ni cuerpo")
    print("✅ Erosiona máscara de fondo y dilata máscara de persona")
    print("✅ Bordes suavizados para transición natural")
    print("✅ Usa rembg si está disponible (más preciso)")
    print("✅ Dimensiones finales: 220x270 píxeles (compatibles con carnet)")
    print("=" * 70)
    
    if verificar_dependencias():
        print("\n✅ Dependencias básicas instaladas correctamente")
        print("\n💡 Para probar con una imagen:")
        print('   python procesador_fotos.py "ruta/a/tu/imagen.jpg"')
        
        import sys
        if len(sys.argv) > 1:
            probar_procesamiento(sys.argv[1])
    else:
        print("\n❌ Faltan dependencias críticas.")
        print("Instala: pip install opencv-python numpy Pillow")
        print("Opcional (mejor precisión): pip install rembg")