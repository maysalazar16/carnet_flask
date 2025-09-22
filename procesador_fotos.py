from PIL import Image, ImageFilter, ImageEnhance, ImageDraw
import numpy as np
import os
import cv2

def procesar_foto_carnet(ruta_imagen, ruta_salida, ancho_carnet=220, alto_carnet=270):
    """Conserva TODA la persona, elimina SOLO el fondo"""
    try:
        print(f"[1/3] Abriendo: {ruta_imagen}")
        imagen = Image.open(ruta_imagen).convert('RGB')
        
        print("[2/3] Analizando...")
        fondo_es_blanco = detectar_fondo_blanco(imagen)
        
        if fondo_es_blanco:
            print("[✓] FONDO BLANCO - SIN CAMBIOS")
            resultado = imagen
        else:
            print("[!] Eliminando fondo (conservando persona completa)...")
            resultado = eliminar_solo_fondo(imagen)
        
        print("[3/3] Ajustando tamaño...")
        final = redimensionar_para_carnet(resultado, ancho_carnet, alto_carnet)
        
        final.save(ruta_salida, 'PNG', quality=100)
        print(f"[EXITO] {ruta_salida}")
        return True
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def detectar_fondo_blanco(imagen):
    """Detecta si el fondo es blanco"""
    try:
        img_array = np.array(imagen)
        h, w = img_array.shape[:2]
        
        # Muestras de los bordes
        b = 50
        muestras = []
        muestras.extend(img_array[0:b, :].reshape(-1, 3))
        muestras.extend(img_array[h-b:h, :].reshape(-1, 3))
        muestras.extend(img_array[:, 0:b].reshape(-1, 3))
        muestras.extend(img_array[:, w-b:w].reshape(-1, 3))
        
        promedio = np.mean(muestras, axis=0)
        es_blanco = all(promedio > 240)
        
        print(f"    Fondo: {'BLANCO' if es_blanco else 'COLOR'} (RGB: {promedio.astype(int)})")
        return es_blanco
        
    except:
        return False

def eliminar_solo_fondo(imagen):
    """Elimina SOLO el fondo, preserva TODO lo demás"""
    try:
        from rembg import remove
        import io
        
        print("    Procesando...")
        
        # Convertir imagen a bytes
        buffer = io.BytesIO()
        imagen.save(buffer, format='PNG')
        buffer.seek(0)
        
        # rembg SIN alpha matting - más preciso, conserva TODO
        output_bytes = remove(buffer.read())
        
        # Convertir resultado
        resultado = Image.open(io.BytesIO(output_bytes))
        
        if resultado.mode == 'RGBA':
            # Crear fondo blanco
            blanco = Image.new('RGB', resultado.size, (255, 255, 255))
            
            # Usar el canal alpha tal cual lo da rembg
            # NO modificar - rembg ya detectó correctamente la persona
            alpha = resultado.split()[3]
            
            # Pegar sobre fondo blanco
            blanco.paste(resultado, (0, 0), alpha)
            
            print("    Fondo eliminado (persona intacta)")
            return blanco
        else:
            return resultado.convert('RGB')
            
    except ImportError:
        print("    rembg no instalado")
        return eliminar_fondo_simple(imagen)
    except Exception as e:
        print(f"    Error: {e}")
        return eliminar_fondo_simple(imagen)

def eliminar_fondo_simple(imagen):
    """Método alternativo simple"""
    try:
        img_array = np.array(imagen)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        
        h, w = img_bgr.shape[:2]
        
        # Detectar color del fondo
        b = 40
        muestras = []
        muestras.extend(img_bgr[0:b, :].reshape(-1, 3))
        muestras.extend(img_bgr[h-b:h, :].reshape(-1, 3))
        muestras.extend(img_bgr[:, 0:b].reshape(-1, 3))
        muestras.extend(img_bgr[:, w-b:w].reshape(-1, 3))
        
        color = np.median(muestras, axis=0).astype(int)
        
        # Crear máscara
        tol = 50
        mask_fondo = cv2.inRange(img_bgr, color - tol, color + tol)
        mask_persona = cv2.bitwise_not(mask_fondo)
        
        # Suavizar solo un poco
        mask_persona = cv2.GaussianBlur(mask_persona, (5, 5), 0)
        
        # Aplicar
        resultado = np.ones_like(img_bgr) * 255
        mask_3d = cv2.cvtColor(mask_persona, cv2.COLOR_GRAY2BGR) / 255.0
        resultado = (img_bgr * mask_3d + resultado * (1 - mask_3d)).astype(np.uint8)
        
        return Image.fromarray(cv2.cvtColor(resultado, cv2.COLOR_BGR2RGB))
        
    except:
        return imagen

def redimensionar_para_carnet(imagen, ancho, alto):
    w, h = imagen.size
    ratio = ancho / alto
    ratio_actual = w / h
    
    if ratio_actual > ratio:
        nuevo_h = h
        nuevo_w = int(h * ratio)
        left = (w - nuevo_w) // 2
        imagen = imagen.crop((left, 0, left + nuevo_w, nuevo_h))
    else:
        nuevo_w = w
        nuevo_h = int(w / ratio)
        top = max(0, (h - nuevo_h) // 4)
        imagen = imagen.crop((0, top, nuevo_w, top + nuevo_h))
    
    return imagen.resize((ancho, alto), Image.Resampling.LANCZOS)

def validar_imagen(ruta):
    try:
        with Image.open(ruta) as img:
            img.verify()
        img = Image.open(ruta)
        if img.size[0] < 200 or img.size[1] < 200:
            return False, "Muy pequeña"
        if os.path.getsize(ruta) > 10485760:
            return False, "Muy grande"
        return True, "OK"
    except:
        return False, "Invalida"

def verificar_si_foto_existe(cedula, carpeta="static/fotos"):
    for nombre in [f"foto_{cedula}.png", f"foto_{cedula}.jpg", f"{cedula}.png", f"{cedula}.jpg"]:
        if os.path.exists(os.path.join(carpeta, nombre)):
            return True, os.path.join(carpeta, nombre)
    return False, None

def procesar_foto_aprendiz(archivo_foto, cedula, carpeta_fotos="static/fotos"):
    try:
        print("\n" + "="*70)
        print(f"PROCESANDO - {cedula}")
        print("="*70)
        
        existe, _ = verificar_si_foto_existe(cedula, carpeta_fotos)
        if existe:
            return False, None, f"Ya existe foto para {cedula}"
        
        os.makedirs(carpeta_fotos, exist_ok=True)
        
        ext = os.path.splitext(archivo_foto.filename)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png']:
            return False, None, "Formato invalido"
        
        temp = f"temp_{cedula}{ext}"
        final = f"foto_{cedula}.png"
        ruta_temp = os.path.join(carpeta_fotos, temp)
        ruta_final = os.path.join(carpeta_fotos, final)
        
        archivo_foto.save(ruta_temp)
        
        valida, msg = validar_imagen(ruta_temp)
        if not valida:
            os.remove(ruta_temp)
            return False, None, msg
        
        exito = procesar_foto_carnet(ruta_temp, ruta_final, 220, 270)
        
        if os.path.exists(ruta_temp):
            os.remove(ruta_temp)
        
        if exito:
            print("="*70 + "\n")
            return True, final, "Foto procesada correctamente"
        else:
            return False, None, "Error al procesar"
            
    except Exception as e:
        print(f"[ERROR] {e}")
        if 'ruta_temp' in locals() and os.path.exists(ruta_temp):
            os.remove(ruta_temp)
        return False, None, str(e)

if __name__ == "__main__":
    print("PROCESADOR SENA - Preserva persona completa, elimina solo fondo")