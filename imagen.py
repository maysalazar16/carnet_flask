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
        font_nombre = ImageFont.truetype("arial.ttf", 42)                    # Nombre: ARIAL (igual)
        font_cedula = ImageFont.truetype("calibri.ttf", 32)                  # CC: SANS-SERIF (Calibri)
        font_rh_label = ImageFont.truetype("trebuc.ttf", 28)                 # Rh: TREBUCHET MS
        font_rh_tipo = ImageFont.truetype("trebuc.ttf", 85)                  # Tipo sangre: TREBUCHET MS
        font_footer = ImageFont.truetype("arial.ttf", 28)                    # Regional: ARIAL (igual)
        font_vertical = ImageFont.truetype("arial.ttf", 25)
        font_vertical_bold = ImageFont.truetype("arialbd.ttf", 35)
        font_logo = ImageFont.truetype("arial.ttf", 36)
    except:
        font_nombre = font_cedula = font_rh_label = font_rh_tipo = font_footer = font_vertical = font_vertical_bold = font_logo = ImageFont.load_default()

    # Cargar imagen del logo SENA - MÁS PEQUEÑO
    ruta_logo = os.path.join("static", "fotos", "logo_sena.png")
    try:
        logo = Image.open(ruta_logo).convert("RGBA")
        logo = logo.resize((130, 140))  # Logo más pequeño (antes era 260x250)
        img.paste(logo, (65, 75), logo)
    except:
        draw.text((40, 75), "SENA", fill=(0, 128, 0), font=font_logo)

    # ========== SECCIÓN DE LA FOTO ==========
    foto_encontrada = False
    foto = None
    
    posibles_rutas = []
    
    if empleado.get('cedula'):
        posibles_rutas.append(os.path.join("static", "fotos", f"foto_{empleado['cedula']}.png"))
        posibles_rutas.append(os.path.join("static", "fotos", f"foto_{empleado['cedula']}.jpg"))
    
    if empleado.get('foto'):
        posibles_rutas.append(os.path.join("static", "fotos", empleado['foto']))
        if not empleado['foto'].endswith(('.png', '.jpg', '.jpeg')):
            posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['foto']}.png"))
            posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['foto']}.jpg"))
    
    if empleado.get('cedula'):
        posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['cedula']}.png"))
        posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['cedula']}.jpg"))
        posibles_rutas.append(os.path.join("static", "fotos", f"{empleado['cedula']}.jpeg"))
    
    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            try:
                foto = Image.open(ruta).convert("RGB")
                foto_encontrada = True
                break
            except:
                continue
    
    if not foto_encontrada:
        try:
            from procesamiento_fotos import obtener_ruta_foto_final
            ruta_foto_final = obtener_ruta_foto_final(empleado['cedula'])
            if ruta_foto_final and os.path.exists(ruta_foto_final):
                foto = Image.open(ruta_foto_final).convert("RGB")
                foto_encontrada = True
        except:
            pass
    
    if not foto_encontrada:
        foto = Image.new("RGB", (220, 270), (240, 240, 240))
        draw_placeholder = ImageDraw.Draw(foto)
        try:
            font_placeholder = ImageFont.truetype("arial.ttf", 20)
        except:
            font_placeholder = ImageFont.load_default()
        draw_placeholder.text((60, 120), "SIN FOTO", fill=(150, 150, 150), font=font_placeholder)
    
    foto = foto.resize((220, 260))
    img.paste(foto, (399, 40)) #posicionamiento a la derecha 

    # Texto "APRENDIZ" HORIZONTAL debajo del logo, SOBRE la línea verde - EN COLOR NEGRO Y NEGRILLA
    cargo_texto = empleado.get('cargo', 'APRENDIZ').upper()
    try:
        font_aprendiz = ImageFont.truetype("arialbd.ttf", 26)  # NEGRILLA
    except:
        font_aprendiz = ImageFont.load_default()
    
    # Colocar APRENDIZ debajo del logo más pequeño, sobre la línea verde
    draw.text((40, 270), cargo_texto, fill=(0, 0, 0), font=font_aprendiz)

    # Línea verde horizontal - CON GROSOR PERO SIN TOCAR LOS BORDES
    draw.line((40, 310, 624, 310), fill=(0, 128, 0), width=7)  # width aumenta el grosor de la linea verde 

    # NOMBRES
    nombre_completo = empleado['nombre'].upper()
    if len(nombre_completo) > 16:
        partes = nombre_completo.split()
        linea1 = " ".join(partes[:2])
        linea2 = " ".join(partes[2:])
        draw.text((40, 325 + 20 ), linea1, fill=(0, 128, 0), font=font_nombre)
        if linea2:
            draw.text((40, 375 + 20), linea2, fill=(0, 128, 0), font=font_nombre)
        siguiente_y = 435
    else:
        draw.text((15, 325), nombre_completo, fill=(0, 128, 0), font=font_nombre)
        siguiente_y = 375

   
    # CÉDULA CON TIPO DE DOCUMENTO (TI, CC, etc.)
    tipo_doc = empleado.get('tipo_documento', 'CC')
    cedula_formateada = "{:,}".format(int(empleado['cedula'])).replace(",", ".")
    texto_completo_cedula = f"{tipo_doc}. {cedula_formateada}"
    draw.text((40, siguiente_y + 50), texto_completo_cedula, fill=(0, 0, 0), font=font_cedula)

    # RH y TIPO DE SANGRE
    rh_y = siguiente_y + 140
    tipo_sangre = empleado['tipo_sangre'].upper()
    texto_rh_completo = f"Rh {tipo_sangre}"
    draw.text((40, rh_y-40), texto_rh_completo, fill=(0, 0, 0), font=font_rh_label)

    # CÓDIGO QR
    try:
        qr = Image.open(ruta_qr).convert("RGB")
        qr = qr.resize((370, 370))
        img.paste(qr, (260, 470))
    except:
        draw.rectangle([(320, 430), (620, 730)], outline=(0, 0, 0), width=2)
        draw.text((420, 570), "QR CODE", fill=(0, 0, 0), font=font_footer)

    # LÍNEA VERDE ANTES DEL FOOTER (igual que la de arriba)
    draw.line((40, 900, 100, 900), fill=(0, 100, 0), width=7)
    
    # INFORMACIÓN REGIONAL - TODO EN VERDE Y EN DOS LÍNEAS
    footer_y = 870
    draw.text((40, footer_y + 50), "Regional Valle del Cauca", fill=(0, 128, 0), font=font_footer)
    draw.text((40, footer_y + 90), "Centro de Biotecnología Industrial", fill=(0, 100, 0), font=font_footer)

    # Guardar anverso
    ruta_anverso = os.path.join("static", "carnets", f"carnet_{empleado['cedula']}.png")
    img.save(ruta_anverso, dpi=(300, 300))

    # ===== REVERSO DEL CARNET =====
    try:
        ruta_fondo_reverso = os.path.join("static", "fondos", "trasero.png")
        reverso = Image.open(ruta_fondo_reverso).convert("RGB")
        reverso = reverso.resize((ancho, alto))
    except:
        reverso = Image.new("RGB", (ancho, alto), (255, 255, 255))
    
    draw_reverso = ImageDraw.Draw(reverso)

    try:
        font_reverso = ImageFont.truetype("cambria.ttf", 28)  # LETRA GRANDE
        font_programa = ImageFont.truetype("arialbd.ttf", 18)
        font_fecha = ImageFont.truetype("arial.ttf", 16)
    except:
        try:
            font_reverso = ImageFont.truetype("arial.ttf", 28)
            font_programa = ImageFont.truetype("arialbd.ttf", 18)
            font_fecha = ImageFont.truetype("arial.ttf", 16)
        except:
            font_reverso = font_programa = font_fecha = ImageFont.load_default()

    # CUADRO PRINCIPAL (solo variables)
    cuadro_x, cuadro_y = 40, 50
    cuadro_ancho, cuadro_alto = 560, 400

    # MÁRGENES IGUALES A IZQUIERDA Y DERECHA
    margen_izquierdo = 40
    margen_derecho = 40
    ancho_texto_disponible = ancho - margen_izquierdo - margen_derecho

    # PRIMER TEXTO - LETRA GRANDE
    texto1_y = cuadro_y + 30
    texto1_lines = [
        "Este carné identifica a quien lo porta,",
        "únicamente para el cumplimiento de sus",
        "funciones y para la obtención de los",
        "servicios que el SENA presta a sus",
        "aprendices, funcionarios y/o contratistas.",
        "Se solicita a las autoridades civiles y militares",
        "prestarle toda la colaboración para su",
        "desempeño."
    ]
    
    # DIBUJAR EL TEXTO CENTRADO
    separacion_lineas = 45  # Separación entre líneas

    for i, line in enumerate(texto1_lines):
        if line.strip():  # Solo si la línea no está vacía
            # Justificar el texto (distribuir espacios)
            palabras = line.split()
            if len(palabras) > 1:
                # Calcular ancho total de palabras sin espacios
                ancho_palabras = sum([draw_reverso.textbbox((0, 0), palabra, font=font_reverso)[2] - 
                                    draw_reverso.textbbox((0, 0), palabra, font=font_reverso)[0] 
                                    for palabra in palabras])
                # Espacio disponible para distribuir entre palabras
                espacio_total = ancho_texto_disponible - ancho_palabras
                espacio_entre_palabras = espacio_total / (len(palabras) - 1) if len(palabras) > 1 else 0
                
                # Dibujar cada palabra con el espaciado calculado
                x_actual = margen_izquierdo
                for palabra in palabras:
                    draw_reverso.text((x_actual, texto1_y + (i * separacion_lineas)), palabra, fill=(0, 0, 0), font=font_reverso)
                    bbox_palabra = draw_reverso.textbbox((0, 0), palabra, font=font_reverso)
                    ancho_palabra = bbox_palabra[2] - bbox_palabra[0]
                    x_actual += ancho_palabra + espacio_entre_palabras
            else:
                # Si solo hay una palabra, centrarla
                draw_reverso.text((margen_izquierdo, texto1_y + (i * separacion_lineas)), line, fill=(0, 0, 0), font=font_reverso)
    
    # ========== SECCIÓN INFERIOR DEL REVERSO ==========
    
    # FIRMA
    firma_y = alto - 300
    
    # TEXTO "FIRMA Y AUTORIZA" CENTRADO
    try:
        font_firma_titulo = ImageFont.truetype("cambria.ttf", 22)
    except:
        font_firma_titulo = font_reverso
    
    firma_texto_y = firma_y - 50
    texto_firma = "Firma y Autoriza"
    bbox_firma = draw_reverso.textbbox((0, 0), texto_firma, font=font_firma_titulo)
    ancho_firma = bbox_firma[2] - bbox_firma[0]
    pos_x_firma = (ancho - ancho_firma) // 2
    draw_reverso.text((pos_x_firma, firma_texto_y), texto_firma, fill=(0, 0, 0), font=font_firma_titulo)
    
    # IMAGEN DE FIRMA CENTRADA
    try:
        ruta_firma = os.path.join("static", "fotos", "firma_directora.png")
        if os.path.exists(ruta_firma):
            firma_img = Image.open(ruta_firma).convert("RGBA")
            firma_img = firma_img.resize((200, 100))
            pos_firma_x = (ancho - 200) // 2
            pos_firma_y = firma_texto_y + 35
            reverso.paste(firma_img, (pos_firma_x, pos_firma_y), firma_img)
    except:
        pass
    
    # TEXTO SOBRE CARNÉ EXTRAVIADO (CENTRADO)
    try:
        font_extraviado = ImageFont.truetype("cambria.ttf", 20)
    except:
        font_extraviado = font_fecha
    
    info_y = firma_texto_y + 150
    texto_extraviado = [
        "Si por algún motivo este carné es extraviado,",
        "por favor diríjase al Centro de Biotecnología",
        "Industrial ubicado en la calle 40 #30-44"
    ]
    
    for i, linea in enumerate(texto_extraviado):
        bbox_linea = draw_reverso.textbbox((0, 0), linea, font=font_extraviado)
        ancho_linea = bbox_linea[2] - bbox_linea[0]
        pos_x_linea = (ancho - ancho_linea) // 2
        draw_reverso.text((pos_x_linea, info_y + (i * 25)), linea, fill=(0, 0, 0), font=font_extraviado)
    
    # NOMBRE DEL PROGRAMA (CENTRADO)
    nombre_programa = empleado.get('nombre_programa', 'Programa Técnico')
    programa_y = info_y + 100
    try:
        font_programa_bold = ImageFont.truetype("arialbd.ttf", 20)
    except:
        font_programa_bold = font_programa
    
    bbox_programa = draw_reverso.textbbox((0, 0), nombre_programa, font=font_programa_bold)
    ancho_programa = bbox_programa[2] - bbox_programa[0]
    pos_x_programa = (ancho - ancho_programa) // 2
    draw_reverso.text((pos_x_programa, programa_y), nombre_programa, fill=(0, 0, 0), font=font_programa_bold)
    
    # FICHA (CENTRADO Y NEGRILLA)
    codigo_ficha = empleado.get('codigo_ficha', '0000')
    ficha_y = programa_y + 35
    ficha_text = f"FICHA {codigo_ficha}"
    try:
        font_ficha = ImageFont.truetype("arialbd.ttf", 20)
    except:
        font_ficha = font_programa
    
    bbox_ficha = draw_reverso.textbbox((0, 0), ficha_text, font=font_ficha)
    ancho_ficha = bbox_ficha[2] - bbox_ficha[0]
    pos_x_ficha = (ancho - ancho_ficha) // 2
    draw_reverso.text((pos_x_ficha, ficha_y), ficha_text, fill=(0, 0, 0), font=font_ficha)

    ruta_reverso = os.path.join("static", "carnets", f"reverso_{empleado['cedula']}.png")
    reverso.save(ruta_reverso, dpi=(300, 300))

    return ruta_anverso


def combinar_anverso_reverso(nombre_archivo_anverso, nombre_archivo_reverso, nombre_aprendiz):
    ruta_anverso = os.path.join("static", "carnets", nombre_archivo_anverso)
    ruta_reverso = os.path.join("static", "carnets", nombre_archivo_reverso)

    try:
        anverso = Image.open(ruta_anverso)
        reverso = Image.open(ruta_reverso)
    except Exception as e:
        raise Exception(f"Error al cargar las imágenes: {e}")

    ancho_total = anverso.width + reverso.width + 40
    alto_total = max(anverso.height, reverso.height) + 60

    combinado = Image.new("RGB", (ancho_total, alto_total), (245, 245, 245))
    
    combinado.paste(anverso, (0, 0))
    combinado.paste(reverso, (anverso.width + 40, 0))

    draw = ImageDraw.Draw(combinado)
    try:
        font_label = ImageFont.truetype("arial.ttf", 18)
    except:
        font_label = ImageFont.load_default()
    
    draw.text((anverso.width//2 - 40, anverso.height + 20), "ANVERSO", fill=(0, 0, 0), font=font_label)
    draw.text((anverso.width + 40 + reverso.width//2 - 40, reverso.height + 20), "REVERSO", fill=(0, 0, 0), font=font_label)

    nombre_archivo = f"{nombre_aprendiz.replace(' ', '_')}_completo.png"
    ruta_combinada = os.path.join("static", "carnets", nombre_archivo)
    combinado.save(ruta_combinada, dpi=(300, 300))

    return nombre_archivo