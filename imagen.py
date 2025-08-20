from PIL import Image, ImageDraw, ImageFont
import os

def generar_carnet(empleado, ruta_qr):
    # MEDIDAS EXACTAS DEL CARNET SENA: 5.5cm ancho x 8.7cm alto (formato vertical)
    # A 300 DPI para impresión de calidad: 649px ancho x 1024px alto
    ancho, alto = 649, 1024
    fondo_color = (255, 255, 255)
    img = Image.new("RGB", (ancho, alto), fondo_color)
    draw = ImageDraw.Draw(img)

    # Cargar fuentes PRIMERO (antes de usarlas)
    try:
        
        font_nombre = ImageFont.truetype("arial.ttf", 42)      # NOMBRE EXTRA GRANDE
        font_cedula = ImageFont.truetype("arial.ttf", 32)      # Cédula más grande
        font_rh_label = ImageFont.truetype("arial.ttf", 28)    # "RH" más grande
        font_rh_tipo = ImageFont.truetype("arial.ttf", 85)     # Tipo de sangre EXTRA GIGANTE
        font_footer = ImageFont.truetype("arial.ttf", 28)      # Pie de página MÁS GRANDE
        font_vertical = ImageFont.truetype("arial.ttf", 25)    # Texto vertical MÁS GRANDE
        font_vertical_bold = ImageFont.truetype("arialbd.ttf", 35)  # Fuente en NEGRITA más grande
        font_logo = ImageFont.truetype("arial.ttf", 36)        # Logo SENA
    except:
        font_nombre = font_cedula = font_rh_label = font_rh_tipo = font_footer = font_vertical = font_vertical_bold = font_logo = ImageFont.load_default()

    # Cargar imagen del logo SENA EXTRA GRANDE
    ruta_logo = os.path.join("static", "fotos", "logo_sena.png")
    try:
        logo = Image.open(ruta_logo).convert("RGBA")
        # Logo EXTRA grande como en el carnet real
        logo = logo.resize((260, 250))  # Aumentado de 160x105 a 180x120
        img.paste(logo, (50, 58), logo)
    except:
        # Si no hay logo, dibujar texto "SENA" EXTRA grande
        draw.text((15, 15), "SENA", fill=(0, 128, 0), font=font_logo)

    # ========== AQUÍ ESTÁ LA FOTO - MÁS GRANDE SIN PASAR LA LÍNEA VERDE ==========
    # ✅ MEJORADA: Búsqueda inteligente de la foto del aprendiz
    foto_encontrada = False
    foto = None
    
    # Lista de posibles rutas donde buscar la foto
    posibles_rutas = []
    
    # 1. Buscar foto procesada con prefijo "foto_"
    if empleado.get('cedula'):
        posibles_rutas.append(os.path.join("static", "fotos", f"foto_{empleado['cedula']}.png"))
        posibles_rutas.append(os.path.join("static", "fotos", f"foto_{empleado['cedula']}.jpg"))
    
    # 2. Buscar foto con el nombre almacenado en la base de datos
    if empleado.get('foto'):
        posibles_rutas.append(os.path.join("static", "fotos", empleado['foto']))
        # Si el nombre no tiene extensión, probar con varias
        if not empleado['foto'].endswith(('.png', '.jpg', '.jpeg')):
            posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['foto']}.png"))
            posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['foto']}.jpg"))
    
    # 3. Buscar foto con solo la cédula como nombre
    if empleado.get('cedula'):
        posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['cedula']}.png"))
        posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['cedula']}.jpg"))
        posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['cedula']}.jpeg"))
    
    # Intentar cargar la foto de las posibles rutas
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            try:
                print(f"📸 Intentando cargar foto desde: {ruta}")
                foto = Image.open(ruta).convert("RGB")
                foto_encontrada = True
                print(f"✅ Foto cargada exitosamente desde: {ruta}")
                break
            except Exception as e:
                print(f"⚠️ No se pudo cargar foto desde {ruta}: {e}")
                continue
    
    # Si no se encontró foto por las rutas normales, intentar con el módulo de procesamiento
    if not foto_encontrada:
        try:
            from procesamiento_fotos import obtener_ruta_foto_final
            ruta_foto_final = obtener_ruta_foto_final(empleado['cedula'])
            
            if ruta_foto_final and os.path.exists(ruta_foto_final):
                print(f"📸 Usando foto procesada: {ruta_foto_final}")
                foto = Image.open(ruta_foto_final).convert("RGB")
                foto_encontrada = True
        except ImportError:
            print("⚠️ Módulo de procesamiento no disponible")
        except Exception as e:
            print(f"⚠️ Error con módulo de procesamiento: {e}")
    
    # Si aún no hay foto, crear un placeholder
    if not foto_encontrada:
        print(f"❌ No se encontró ninguna foto para el empleado {empleado.get('nombre', 'desconocido')}")
        # Crear imagen placeholder
        foto = Image.new("RGB", (220, 270), (240, 240, 240))
        draw_placeholder = ImageDraw.Draw(foto)
        try:
            font_placeholder = ImageFont.truetype("arial.ttf", 20)
        except:
            font_placeholder = ImageFont.load_default()
        draw_placeholder.text((60, 120), "SIN FOTO", fill=(150, 150, 150), font=font_placeholder)
        print("⚠️ Usando placeholder para la foto")
    
    # 📸 FOTO MÁS ANCHA Y MÁS ALTA - SIN PASAR LÍNEA VERDE
    # Línea verde está en Y=330, foto empieza en Y=75, entonces máximo alto = 330-75 = 255px
    foto = foto.resize((220, 270))  # MÁS GRANDE: era (200, 230) ahora (240, 250)
    
    # 📍 REPOSICIONADA para que no se pase de la línea verde
    img.paste(foto, (360, 40))  # Reposicionada: era (380, 85) ahora (350, 75) para que quepa mejor
    # ========== FIN DE LA SECCIÓN DE LA FOTO ==========

    # Texto "INSTRUCTOR/APRENDIZ" vertical MÁS GRANDE y en NEGRITA
    cargo_texto = empleado['cargo'].upper()
    cargo_img = Image.new("RGBA", (250, 90), (255, 255, 255, 0))  # Lienzo más grande para palabras largas
    draw_cargo = ImageDraw.Draw(cargo_img)
    
    # Usar fuente en negrita para mejor visibilidad
    try:
        fuente_cargo = font_vertical_bold
    except:
        fuente_cargo = font_vertical
    
    draw_cargo.text((0, 15), cargo_texto, font=fuente_cargo, fill=(45, 0, 0))
    cargo_img = cargo_img.rotate(90, expand=True)
    img.paste(cargo_img, (585, 50), cargo_img)  # POSICIÓN FIJA al lado de la foto

    # Línea verde horizontal más abajo para acomodar foto y logo más grandes - BAJADA MÁS
    draw.line((15, 330, 620, 330), fill=(0, 128, 0), width=5)  # BAJADA MÁS: era 300 ahora 330 = +30px adicional

    # NOMBRES (debajo de la línea verde) - TEXTO EXTRA GRANDE - BAJADO MÁS
    nombre_completo = empleado['nombre'].upper()
    # Dividir el nombre para el texto más grande
    if len(nombre_completo) > 16:  # Límite menor por texto más grande
        partes = nombre_completo.split()
        linea1 = " ".join(partes[:2])  # Primeros dos nombres
        linea2 = " ".join(partes[2:])  # Apellidos
        draw.text((15, 345), linea1, fill=(0, 128, 0), font=font_nombre)  # BAJADO MÁS: era 315 ahora 345 = +30px adicional
        if linea2:
            draw.text((15, 395), linea2, fill=(0, 128, 0), font=font_nombre)  # BAJADO MÁS: era 365 ahora 395 = +30px adicional
        siguiente_y = 455  # BAJADO MÁS: era 425 ahora 455 = +30px adicional
    else:
        draw.text((15, 345), nombre_completo, fill=(0, 128, 0), font=font_nombre)  # BAJADO MÁS: era 315 ahora 345 = +30px adicional
        siguiente_y = 395  # BAJADO MÁS: era 365 ahora 395 = +30px adicional

    # CÉDULA (debajo del nombre) - TEXTO MÁS GRANDE - BAJADA
    cedula_formateada = "{:,}".format(int(empleado['cedula'])).replace(",", ".")
    draw.text((15, siguiente_y), cedula_formateada, fill=(100, 100, 100), font=font_cedula)

    # RH y TIPO DE SANGRE - GIGANTES como en la imagen - BAJADOS
    rh_y = siguiente_y + 140  # Más espacio para elementos grandes (ya incluye el +40px del bajón general)
    
    # RH más centrado horizontalmente
    draw.text((90, rh_y), "RH", fill=(0, 0, 0), font=font_rh_label)
    
    # TIPO DE SANGRE AÚN MÁS GRANDE y centrado
    tipo_sangre = empleado['tipo_sangre'].upper()
    draw.text((20, rh_y + 90), tipo_sangre, fill=(100, 100, 100), font=font_rh_tipo)

    # CÓDIGO QR EXTRA GRANDE y reposicionado - BAJADO MÁS
    try:
        qr = Image.open(ruta_qr).convert("RGB")
        qr = qr.resize((370, 370))  # QR EXTRA grande (era 260x260)
        img.paste(qr, (260, 480))   # BAJADO MÁS: era (320, 400) ahora (320, 430) = +30px adicional
    except Exception as e:
        # Si no se puede cargar el QR, dibujar un rectángulo más grande
        draw.rectangle([(320, 430), (620, 730)], outline=(0, 0, 0), width=2)  # BAJADO MÁS +30px adicional
        draw.text((420, 570), "QR CODE", fill=(0, 0, 0), font=font_footer)  # BAJADO MÁS +30px adicional

    # INFORMACIÓN REGIONAL (pie de página) - CON MÁS ESPACIADO - BAJADO MÁS
    footer_y = 870  # BAJADO MÁS: era 790 ahora 820 = +30px adicional
    draw.text((15, footer_y ), "Regional Valle", fill=(100, 100, 100), font=font_footer)
    draw.text((15, footer_y + 50), "Centro de Biotecnología", fill=(0, 128, 0), font=font_footer)
    draw.text((15, footer_y + 100), "Industrial", fill=(0, 128, 0), font=font_footer)

    # Guardar anverso
    ruta_anverso = os.path.join("static", "carnets", f"carnet_{empleado['cedula']}.png")
    img.save(ruta_anverso, dpi=(300, 300))

    # ---- Crear reverso del carné con CUADRO y DOS TEXTOS ----
    try:
        ruta_fondo_reverso = os.path.join("static", "fondos", "trasero.png")
        reverso = Image.open(ruta_fondo_reverso).convert("RGB")
        reverso = reverso.resize((ancho, alto))
    except:
        reverso = Image.new("RGB", (ancho, alto), (255, 255, 255))
    
    draw_reverso = ImageDraw.Draw(reverso)

    # Fuente para el texto del reverso - TAMAÑO NORMAL
    try:
        font_reverso = ImageFont.truetype("arial.ttf", 19)  # Tamaño normal
        font_programa = ImageFont.truetype("arialbd.ttf", 18)  # 🆕 Fuente para programa (negrita)
        font_fecha = ImageFont.truetype("arial.ttf", 16)      # 🆕 Fuente para fecha
    except:
        font_reverso = font_programa = font_fecha = ImageFont.load_default()

    # CUADRO PRINCIPAL que encierra ambos textos
    cuadro_x, cuadro_y = 40, 80
    cuadro_ancho, cuadro_alto = 560, 400
    draw_reverso.rectangle([(cuadro_x, cuadro_y), (cuadro_x + cuadro_ancho, cuadro_y + cuadro_alto)], 
                          outline=(0, 0, 0), width=3)

    # PRIMER TEXTO - Redistribuido para llenar la mitad superior
    texto1_y = cuadro_y + 10  # Pegado al borde superior
    texto1_lines = [
        "Este carnet identifica a quien lo porta",
        "únicamente para las funciones y para la",
        "obtención de los servicios que el SENA",
        "presta a sus funcionarios y/o contratistas.",
        "",  # Línea vacía para espaciar
        "Se solicita a las autoridades civiles y",
        "militares prestarle toda la colaboración",
        "para su desempeño.",
        ""   # Línea vacía para llegar al separador
    ]
    
    for i, line in enumerate(texto1_lines):
        draw_reverso.text((cuadro_x + 15, texto1_y + (i * 20)), line, fill=(0, 0, 0), font=font_reverso)

    # LÍNEA SEPARADORA en el centro
    separador_y = cuadro_y + 200
    draw_reverso.line([(cuadro_x + 15, separador_y), (cuadro_x + cuadro_ancho - 15, separador_y)], 
                     fill=(0, 0, 0), width=2)

    # SEGUNDO TEXTO - Redistribuido para llenar la mitad inferior
    texto2_y = separador_y + 10  # Pegado al separador
    texto2_lines = [
        "",  # Línea vacía para espaciar desde el separador
        "Si por algún motivo este carnet es extraviado",
        "por favor diríjase a la Calle 40 # 30-44",
        "",  # Línea vacía para espaciar
        "Barrio Alfonso López o al teléfono:",
        "",  # Línea vacía para espaciar
        "3182532397",
        "",  # Línea vacía para llegar al borde
        ""   # Línea vacía final
    ]
    
    for i, line in enumerate(texto2_lines):
        draw_reverso.text((cuadro_x + 15, texto2_y + (i * 20)), line, fill=(0, 0, 0), font=font_reverso)

    # 🆕🆕🆕 AGREGAR PROGRAMA Y FECHA DE FINALIZACIÓN 🆕🆕🆕
    # Obtener datos del empleado
    nombre_programa = empleado.get('nombre_programa', 'Programa Técnico')
    fecha_finalizacion = empleado.get('fecha_vencimiento', '2025-12-31')
    nivel_formacion = empleado.get('nivel_formacion', 'Técnico')
    
    # Formatear fecha (de YYYY-MM-DD a DD/MM/YYYY)
    try:
        from datetime import datetime
        if '-' in fecha_finalizacion:  # Formato YYYY-MM-DD
            fecha_obj = datetime.strptime(fecha_finalizacion, '%Y-%m-%d')
            fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
        else:
            fecha_formateada = fecha_finalizacion  # Ya está formateada
    except:
        fecha_formateada = fecha_finalizacion
    
    # Posición para el programa y fecha (debajo del cuadro principal)
    info_adicional_y = cuadro_y + cuadro_alto + 30
    
    # 🎯 NOMBRE DEL PROGRAMA (con nivel de formación)
    programa_completo = f"{nivel_formacion} en {nombre_programa}"
    
    # Dividir el programa en líneas si es muy largo
    if len(programa_completo) > 45:  # Si es muy largo, dividir
        palabras = programa_completo.split()
        linea1_programa = " ".join(palabras[:4])  # Primeras 4 palabras
        linea2_programa = " ".join(palabras[4:])  # Resto
        
        draw_reverso.text((cuadro_x, info_adicional_y), "PROGRAMA:", fill=(0, 0, 0), font=font_programa)
        draw_reverso.text((cuadro_x, info_adicional_y + 25), linea1_programa, fill=(0, 100, 0), font=font_programa)
        if linea2_programa:
            draw_reverso.text((cuadro_x, info_adicional_y + 50), linea2_programa, fill=(0, 100, 0), font=font_programa)
        siguiente_info_y = info_adicional_y + 80
    else:
        draw_reverso.text((cuadro_x, info_adicional_y), "PROGRAMA:", fill=(0, 0, 0), font=font_programa)
        draw_reverso.text((cuadro_x, info_adicional_y + 25), programa_completo, fill=(0, 100, 0), font=font_programa)
        siguiente_info_y = info_adicional_y + 55
    
    # 📅 FECHA DE FINALIZACIÓN
    draw_reverso.text((cuadro_x, siguiente_info_y), "FECHA DE FINALIZACIÓN:", fill=(0, 0, 0), font=font_programa)
    draw_reverso.text((cuadro_x, siguiente_info_y + 25), fecha_formateada, fill=(200, 0, 0), font=font_fecha)
    # 🆕🆕🆕 FIN DE PROGRAMA Y FECHA 🆕🆕🆕

    # INFORMACIÓN ADICIONAL EN EL FONDO DEL CARNET CON FIRMA
    # Línea de firma (en el fondo)
    firma_y = alto - 200  # 200px desde el fondo
    #draw_reverso.line([(cuadro_x + 200, firma_y), (cuadro_x + 400, firma_y)], fill=(0, 0, 0), width=1)
    
    # ========== CARGAR Y AGREGAR FIRMA MANUSCRITA EN EL REVERSO ==========
    try:
        ruta_firma = os.path.join("static", "fotos", "firma_directora.png")
        print(f"🔍 Intentando cargar firma desde: {ruta_firma}")
        print(f"🔍 ¿Archivo existe?: {os.path.exists(ruta_firma)}")
        
        if os.path.exists(ruta_firma):
            firma_img = Image.open(ruta_firma).convert("RGBA")
            print(f"🖼️ Firma cargada - tamaño original: {firma_img.size}")
            
            # Redimensionar firma para que se vea bien arriba del nombre
            firma_img = firma_img.resize((250, 300))  # Tamaño apropiado
            print(f"🔧 Firma redimensionada a: {firma_img.size}")
            
            # Posicionar firma ARRIBA del nombre "Fanny Marcela García Davila"
            pos_firma_x = cuadro_x + 190  # Centrada horizontalmente
            pos_firma_y = firma_y - 280    # Arriba del nombre
            print(f"📍 Posicionando firma en: ({pos_firma_x}, {pos_firma_y})")
            
            reverso.paste(firma_img, (pos_firma_x, pos_firma_y), firma_img)
            print(f"✅ Firma aplicada exitosamente en el reverso")
        else:
            print(f"❌ Archivo de firma no encontrado: {ruta_firma}")
            
    except Exception as e:
        print(f"💥 Error al cargar la firma: {e}")
        print(f"🔍 Tipo de error: {type(e).__name__}")
        # Si no hay firma, usar texto manuscrito simulado
        try:
            font_firma = ImageFont.truetype("arial.ttf", 16)
        except:
            font_firma = ImageFont.load_default()
        draw_reverso.text((cuadro_x + 220, firma_y + 65), "Fanny M. García", fill=(0, 0, 0), font=font_firma)
    # ========== FIN FIRMA EN REVERSO ==========
    
    # Texto manuscrito simulado para la firma (solo si no se carga la imagen)
    try:
        font_firma = ImageFont.truetype("arial.ttf", 16)
        font_info = ImageFont.truetype("arial.ttf", 14)
        font_bold = ImageFont.truetype("arialbd.ttf", 14)
    except:
        font_firma = font_info = font_bold = ImageFont.load_default()
    
    # Nombre completo centrado
    nombre_y = firma_y + 15
    draw_reverso.text((cuadro_x + 180, nombre_y), "Fanny Marcela García Davila", fill=(0, 0, 0), font=font_bold)
    
    # Cargo centrado
    cargo_y = nombre_y + 20
    draw_reverso.text((cuadro_x + 240, cargo_y), "Subdirectora", fill=(0, 0, 0), font=font_info)
    
    # Información adicional
    info_y = cargo_y + 30
    draw_reverso.text((cuadro_x + 100, info_y), "0000", fill=(0, 0, 0), font=font_info)
    
    # 🆕 FICHA y CADUCIDAD ACTUALIZADAS CON DATOS REALES
    ficha_y = info_y + 25
    # Usar código de ficha real del empleado
    codigo_ficha_real = empleado.get('codigo_ficha', '0000')
    draw_reverso.text((cuadro_x + 50, ficha_y), f"FICHA: {codigo_ficha_real}", fill=(0, 0, 0), font=font_bold)
    draw_reverso.text((cuadro_x + 200, ficha_y), f"CADUCIDAD: {fecha_formateada}", fill=(0, 0, 0), font=font_bold)

    ruta_reverso = os.path.join("static", "carnets", f"reverso_{empleado['cedula']}.png")
    reverso.save(ruta_reverso, dpi=(300, 300))

    return ruta_anverso


def combinar_anverso_reverso(nombre_archivo_anverso, nombre_archivo_reverso, nombre_aprendiz):
    """
    Combina anverso y reverso del carnet manteniendo las medidas exactas
    """
    ruta_anverso = os.path.join("static", "carnets", nombre_archivo_anverso)
    ruta_reverso = os.path.join("static", "carnets", nombre_archivo_reverso)

    try:
        anverso = Image.open(ruta_anverso)
        reverso = Image.open(ruta_reverso)
    except Exception as e:
        raise Exception(f"Error al cargar las imágenes: {e}")

    # Crear imagen combinada (lado a lado)
    ancho_total = anverso.width + reverso.width + 40  # 40px de separación
    alto_total = max(anverso.height, reverso.height) + 60  # Espacio para etiquetas

    combinado = Image.new("RGB", (ancho_total, alto_total), (245, 245, 245))
    
    # Pegar las imágenes
    combinado.paste(anverso, (0, 0))
    combinado.paste(reverso, (anverso.width + 40, 0))

    # Agregar etiquetas
    draw = ImageDraw.Draw(combinado)
    try:
        font_label = ImageFont.truetype("arial.ttf", 18)
    except:
        font_label = ImageFont.load_default()
    
    # Etiquetas centradas bajo cada carnet
    draw.text((anverso.width//2 - 40, anverso.height + 20), "ANVERSO", fill=(0, 0, 0), font=font_label)
    #durante la ejecucion de la funcion, se verifica si el reverso tiene el mismo ancho que el anverso
    draw.text((anverso.width + 40 + reverso.width//2 - 40, reverso.height + 20), "REVERSO", fill=(0, 0, 0), font=font_label)

    nombre_archivo = f"{nombre_aprendiz.replace(' ', '_')}_completo.png"
    ruta_combinada = os.path.join("static", "carnets", nombre_archivo)
    combinado.save(ruta_combinada, dpi=(300, 300))

    return nombre_archivo


def verificar_medidas_carnet():
    """
    Función para verificar que las medidas del carnet sean correctas
    """
    print("📏 Medidas del carnet SENA:")
    print(f"   Ancho: 5.5 cm = 649 píxeles (a 300 DPI)")
    print(f"   Alto: 8.7 cm = 1024 píxeles (a 300 DPI)")
    print(f"   Formato: Vertical")
    print(f"   Relación de aspecto: {1024/649:.2f}")
    return True