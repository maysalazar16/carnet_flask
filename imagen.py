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
        font_nombre = ImageFont.truetype("arial.ttf", 42)
        font_cedula = ImageFont.truetype("arial.ttf", 32)
        font_rh_label = ImageFont.truetype("arial.ttf", 28)
        font_rh_tipo = ImageFont.truetype("arial.ttf", 85)
        font_footer = ImageFont.truetype("arial.ttf", 28)
        font_vertical = ImageFont.truetype("arial.ttf", 25)
        font_vertical_bold = ImageFont.truetype("arialbd.ttf", 35)
        font_logo = ImageFont.truetype("arial.ttf", 36)
    except:
        font_nombre = font_cedula = font_rh_label = font_rh_tipo = font_footer = font_vertical = font_vertical_bold = font_logo = ImageFont.load_default()

    # Cargar imagen del logo SENA EXTRA GRANDE
    ruta_logo = os.path.join("static", "fotos", "logo_sena.png")
    try:
        logo = Image.open(ruta_logo).convert("RGBA")
        logo = logo.resize((260, 250))
        img.paste(logo, (50, 58), logo)
    except:
        draw.text((15, 15), "SENA", fill=(0, 128, 0), font=font_logo)

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
    
    foto = foto.resize((220, 270))
    img.paste(foto, (360, 40))

    # Texto "INSTRUCTOR/APRENDIZ" vertical
    cargo_texto = empleado['cargo'].upper()
    cargo_img = Image.new("RGBA", (250, 90), (255, 255, 255, 0))
    draw_cargo = ImageDraw.Draw(cargo_img)
    
    try:
        fuente_cargo = font_vertical_bold
    except:
        fuente_cargo = font_vertical
    
    draw_cargo.text((0, 15), cargo_texto, font=fuente_cargo, fill=(45, 0, 0))
    cargo_img = cargo_img.rotate(90, expand=True)
    img.paste(cargo_img, (585, 50), cargo_img)

    # Línea verde horizontal
    draw.line((15, 330, 620, 330), fill=(0, 128, 0), width=5)

    # NOMBRES
    nombre_completo = empleado['nombre'].upper()
    if len(nombre_completo) > 16:
        partes = nombre_completo.split()
        linea1 = " ".join(partes[:2])
        linea2 = " ".join(partes[2:])
        draw.text((15, 345), linea1, fill=(0, 128, 0), font=font_nombre)
        if linea2:
            draw.text((15, 395), linea2, fill=(0, 128, 0), font=font_nombre)
        siguiente_y = 455
    else:
        draw.text((15, 345), nombre_completo, fill=(0, 128, 0), font=font_nombre)
        siguiente_y = 395

    # CÉDULA
    cedula_formateada = "{:,}".format(int(empleado['cedula'])).replace(",", ".")
    draw.text((15, siguiente_y), cedula_formateada, fill=(100, 100, 100), font=font_cedula)

    # RH y TIPO DE SANGRE
    rh_y = siguiente_y + 140
    draw.text((90, rh_y), "RH", fill=(0, 0, 0), font=font_rh_label)
    tipo_sangre = empleado['tipo_sangre'].upper()
    draw.text((20, rh_y + 90), tipo_sangre, fill=(100, 100, 100), font=font_rh_tipo)

    # CÓDIGO QR
    try:
        qr = Image.open(ruta_qr).convert("RGB")
        qr = qr.resize((370, 370))
        img.paste(qr, (260, 480))
    except:
        draw.rectangle([(320, 430), (620, 730)], outline=(0, 0, 0), width=2)
        draw.text((420, 570), "QR CODE", fill=(0, 0, 0), font=font_footer)

    # INFORMACIÓN REGIONAL
    footer_y = 870
    draw.text((15, footer_y), "Regional Valle", fill=(100, 100, 100), font=font_footer)
    draw.text((15, footer_y + 50), "Centro de Biotecnología", fill=(0, 128, 0), font=font_footer)
    draw.text((15, footer_y + 100), "Industrial", fill=(0, 128, 0), font=font_footer)

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
        font_reverso = ImageFont.truetype("arial.ttf", 19)
        font_programa = ImageFont.truetype("arialbd.ttf", 18)
        font_fecha = ImageFont.truetype("arial.ttf", 16)
    except:
        font_reverso = font_programa = font_fecha = ImageFont.load_default()

    # CUADRO PRINCIPAL
    cuadro_x, cuadro_y = 40, 80
    cuadro_ancho, cuadro_alto = 560, 400
    draw_reverso.rectangle([(cuadro_x, cuadro_y), (cuadro_x + cuadro_ancho, cuadro_y + cuadro_alto)], 
                          outline=(0, 0, 0), width=3)

    # PRIMER TEXTO
    texto1_y = cuadro_y + 10
    texto1_lines = [
        "Este carnet identifica a quien lo porta",
        "únicamente para las funciones y para la",
        "obtención de los servicios que el SENA",
        "presta a sus funcionarios y/o contratistas.",
        "",
        "Se solicita a las autoridades civiles y",
        "militares prestarle toda la colaboración",
        "para su desempeño.",
        ""
    ]
    
    for i, line in enumerate(texto1_lines):
        draw_reverso.text((cuadro_x + 15, texto1_y + (i * 20)), line, fill=(0, 0, 0), font=font_reverso)

    # LÍNEA SEPARADORA
    separador_y = cuadro_y + 200
    draw_reverso.line([(cuadro_x + 15, separador_y), (cuadro_x + cuadro_ancho - 15, separador_y)], 
                     fill=(0, 0, 0), width=2)

    # SEGUNDO TEXTO
    texto2_y = separador_y + 10
    texto2_lines = [
        "",
        "Si por algún motivo este carnet es extraviado",
        "por favor diríjase a la Calle 40 # 30-44",
        "",
        "Barrio Alfonso López o al teléfono:",
        "",
        "3182532397",
        "",
        ""
    ]
    
    for i, line in enumerate(texto2_lines):
        draw_reverso.text((cuadro_x + 15, texto2_y + (i * 20)), line, fill=(0, 0, 0), font=font_reverso)

    # FIRMA
    firma_y = alto - 200
    
    try:
        ruta_firma = os.path.join("static", "fotos", "firma_directora.png")
        if os.path.exists(ruta_firma):
            firma_img = Image.open(ruta_firma).convert("RGBA")
            firma_img = firma_img.resize((250, 300))
            pos_firma_x = cuadro_x + 190
            pos_firma_y = firma_y - 280
            reverso.paste(firma_img, (pos_firma_x, pos_firma_y), firma_img)
    except:
        pass
    
    try:
        font_firma = ImageFont.truetype("arial.ttf", 16)
        font_info = ImageFont.truetype("arial.ttf", 14)
        font_bold = ImageFont.truetype("arialbd.ttf", 14)
        font_nombre_subdirectora = ImageFont.truetype("arialbd.ttf", 18)  # NUEVO: más grande
    except:
        font_firma = font_info = font_bold = font_nombre_subdirectora = ImageFont.load_default()
        
    
    
    # Nombre
    nombre_y = firma_y + 15
    draw_reverso.text((cuadro_x + 180, nombre_y), "Fanny Marcela García Davila", fill=(0, 0, 0), font=font_bold)
    
    # Cargo
    cargo_y = nombre_y + 20
    draw_reverso.text((cuadro_x + 240, cargo_y), "Subdirectora", fill=(0, 0, 0), font=font_info)
    
    # ===== CAMBIOS SOLICITADOS =====
    # Obtener datos
    nombre_programa = empleado.get('nombre_programa', 'Programa Técnico')
    fecha_vencimiento = empleado.get('fecha_vencimiento', '2025-12-31')
    codigo_ficha = empleado.get('codigo_ficha', '0000')
    
    # Formatear fecha
    try:
        from datetime import datetime
        if '-' in fecha_vencimiento:
            fecha_obj = datetime.strptime(fecha_vencimiento, '%Y-%m-%d')
            fecha_formateada = fecha_obj.strftime('%d/%m/%Y')
        else:
            fecha_formateada = fecha_vencimiento
    except:
        fecha_formateada = fecha_vencimiento
    
    info_y = cargo_y + 30
    
    # 1. SOLO EL NOMBRE DEL PROGRAMA (sin "Técnico en" ni "Tecnólogo en")
    draw_reverso.text((cuadro_x + 100, info_y), nombre_programa, fill=(0, 0, 0), font=font_info)
    
    # 2. FICHA y CADUCIDAD en líneas separadas
    ficha_y = info_y + 25
    draw_reverso.text((cuadro_x + 50, ficha_y), f"FICHA: {codigo_ficha}", fill=(0, 0, 0), font=font_bold)
    
    # CADUCIDAD debajo de FICHA
    caducidad_y = ficha_y + 25
    draw_reverso.text((cuadro_x + 50, caducidad_y), f"CADUCIDAD: {fecha_formateada}", fill=(0, 0, 0), font=font_bold)

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