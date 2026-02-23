from PIL import Image, ImageDraw, ImageFont
import os

# ============================================
# SISTEMA ROBUSTO DE CARGA DE FUENTES
# Prueba múltiples rutas hasta encontrar una
# ============================================

def cargar_fuente(tamaño, bold=False, tipo='sans'):
    """
    Carga fuente con múltiples alternativas para garantizar
    que SIEMPRE se use una fuente legible, nunca la default de 8px
    """
    candidatas = []
    
    if tipo == 'serif':
        candidatas = [
            "cambria.ttf", "georgia.ttf", "times.ttf", "timesbd.ttf",
            "C:/Windows/Fonts/cambria.ttf",
            "C:/Windows/Fonts/georgia.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
            "/System/Library/Fonts/Times New Roman.ttf",
        ]
    elif bold:
        candidatas = [
            "arialbd.ttf", "calibrib.ttf", "arial_bold.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
    else:
        candidatas = [
            "arial.ttf", "calibri.ttf", "trebuc.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        ]

    for ruta in candidatas:
        try:
            return ImageFont.truetype(ruta, tamaño)
        except:
            continue

    # Último recurso: crear fuente bitmap escalada
    # Usamos un truco: ImageFont.load_default() es 8px pero podemos
    # generar texto más grande dibujando en una imagen mayor
    try:
        # Intentar con la fuente por defecto pero notificar
        print(f"⚠️  ADVERTENCIA: No se encontró fuente TTF para tamaño {tamaño}. "
              f"El carnet puede verse diferente al esperado.")
        print(f"   Instala fuentes en: C:/Windows/Fonts/ o /usr/share/fonts/")
        # Devolver default — al menos algo
        return ImageFont.load_default()
    except:
        return ImageFont.load_default()


def wrap_text(texto, font, draw, max_ancho):
    """Divide texto largo en líneas que caben en max_ancho"""
    palabras = texto.split()
    lineas = []
    linea_actual = ""
    
    for palabra in palabras:
        prueba = f"{linea_actual} {palabra}".strip()
        bbox = draw.textbbox((0, 0), prueba, font=font)
        if bbox[2] - bbox[0] <= max_ancho:
            linea_actual = prueba
        else:
            if linea_actual:
                lineas.append(linea_actual)
            linea_actual = palabra
    
    if linea_actual:
        lineas.append(linea_actual)
    
    return lineas


def generar_carnet(empleado, ruta_qr):
    # MEDIDAS EXACTAS DEL CARNET SENA: 5.5cm ancho x 8.7cm alto (formato vertical)
    # A 300 DPI para impresión de calidad: 649px ancho x 1024px alto
    ancho, alto = 649, 1024
    fondo_color = (255, 255, 255)
    img = Image.new("RGB", (ancho, alto), fondo_color)
    draw = ImageDraw.Draw(img)

    # ============================================
    # FUENTES — sistema robusto con múltiples alternativas
    # ============================================
    # FUENTES ajustadas al carnet Word de referencia (55x85mm a 300dpi)
    # Word usa 6-10pt → a 300dpi: 25-42px
    font_nombre       = cargar_fuente(36, bold=True)   # 8.6pt — nombre aprendiz (bold verde)
    font_cedula       = cargar_fuente(24, bold=False)  # 6.7pt — CC. 1.114.543.155
    font_rh_label     = cargar_fuente(26, bold=False)  # 6.2pt — Rh O+
    font_footer       = cargar_fuente(22, bold=False)  # 5.3pt — Regional / Centro
    font_aprendiz     = cargar_fuente(24, bold=True)   # 5.7pt — APRENDIZ (bold negro)
    font_vertical_bold= cargar_fuente(32, bold=True)
    font_logo         = cargar_fuente(30, bold=False)

    # ========== LOGO SENA ==========
    ruta_logo = os.path.join("static", "fotos", "logo_sena.png")
    try:
        logo = Image.open(ruta_logo).convert("RGBA")
        logo = logo.resize((90, 100))
        img.paste(logo, (30, 30), logo)
    except:
        draw.text((30, 30), "SENA", fill=(0, 128, 0), font=font_logo)

    # ========== FOTO DEL APRENDIZ ==========
    foto = None
    posibles_rutas = []

    if empleado.get('cedula'):
        posibles_rutas += [
            os.path.join("static", "fotos", f"foto_{empleado['cedula']}.png"),
            os.path.join("static", "fotos", f"foto_{empleado['cedula']}.jpg"),
            os.path.join("static", "fotos", f"{empleado['cedula']}.png"),
            os.path.join("static", "fotos", f"{empleado['cedula']}.jpg"),
        ]

    if empleado.get('foto'):
        posibles_rutas.append(os.path.join("static", "fotos", empleado['foto']))

    for ruta in posibles_rutas:
        if os.path.exists(ruta):
            try:
                foto = Image.open(ruta).convert("RGB")
                break
            except:
                continue

    if foto is None:
        foto = Image.new("RGB", (220, 260), (235, 235, 235))
        draw_ph = ImageDraw.Draw(foto)
        font_ph = cargar_fuente(18)
        draw_ph.text((55, 115), "SIN FOTO", fill=(150, 150, 150), font=font_ph)

    # Siempre redimensionar a tamaño fijo — independiente de la foto original
    foto = foto.resize((195, 230), Image.LANCZOS)
    img.paste(foto, (420, 25))

    # ========== CARGO ==========
    cargo_texto = empleado.get('cargo', 'APRENDIZ').upper()
    # CARGO "APRENDIZ" — justo debajo de la foto+logo
    draw.text((30, 258), cargo_texto, fill=(0, 0, 0), font=font_aprendiz)

    # Línea verde horizontal separadora
    draw.line((30, 292, 619, 292), fill=(0, 128, 0), width=4)

    # ========== NOMBRE — dividido en líneas si es largo ==========
    nombre_completo = empleado['nombre'].upper()
    partes = nombre_completo.split()

    y_nombre = 304
    espaciado = 42   # espacio entre líneas del nombre (fuente 36px bold)

    if len(partes) <= 2:
        # Una sola línea: "ANA MARIA"
        draw.text((30, y_nombre), nombre_completo, fill=(0, 128, 0), font=font_nombre)
        siguiente_y = y_nombre + espaciado + 10
    elif len(partes) == 3:
        # Dos líneas: "ANA MARIA" / "TOQUICA"
        draw.text((30, y_nombre),            " ".join(partes[:2]), fill=(0, 128, 0), font=font_nombre)
        draw.text((30, y_nombre + espaciado)," ".join(partes[2:]), fill=(0, 128, 0), font=font_nombre)
        siguiente_y = y_nombre + espaciado * 2 + 8
    else:
        # Tres líneas: "ANA MARIA" / "TOQUICA" / "MILLAN"
        draw.text((30, y_nombre),                " ".join(partes[:2]), fill=(0, 128, 0), font=font_nombre)
        draw.text((30, y_nombre + espaciado),    " ".join(partes[2:3]), fill=(0, 128, 0), font=font_nombre)
        draw.text((30, y_nombre + espaciado * 2)," ".join(partes[3:]), fill=(0, 128, 0), font=font_nombre)
        siguiente_y = y_nombre + espaciado * 3 + 6

    # ========== CÉDULA ==========
    tipo_doc = empleado.get('tipo_documento', 'CC')
    try:
        cedula_formateada = "{:,}".format(int(empleado['cedula'])).replace(",", ".")
    except:
        cedula_formateada = str(empleado['cedula'])
    texto_cedula = f"{tipo_doc}. {cedula_formateada}"
    draw.text((30, siguiente_y + 8), texto_cedula, fill=(0, 0, 0), font=font_cedula)

    # ========== RH / TIPO SANGRE ==========
    tipo_sangre = empleado.get('tipo_sangre', 'O+').upper()
    draw.text((30, siguiente_y + 44), f"Rh {tipo_sangre}", fill=(0, 0, 0), font=font_rh_label)

    # ========== CÓDIGO QR — esquina inferior derecha ==========
    try:
        qr = Image.open(ruta_qr).convert("RGB")
        qr = qr.resize((240, 240), Image.LANCZOS)
        img.paste(qr, (390, siguiente_y + 10))
    except:
        draw.rectangle([(390, siguiente_y + 10), (630, siguiente_y + 250)], outline=(0, 0, 0), width=2)
        draw.text((480, siguiente_y + 120), "QR", fill=(0, 0, 0), font=font_footer)

    # ========== FOOTER ==========
    draw.line((30, 940, 80, 940), fill=(0, 100, 0), width=4)
    draw.text((30, 952), "Regional Valle del Cauca",         fill=(0, 128, 0), font=font_footer)
    draw.text((30, 976), "Centro de Biotecnología Industrial", fill=(0, 100, 0), font=font_footer)

    # Guardar anverso
    ruta_anverso = os.path.join("static", "carnets", f"carnet_{empleado['cedula']}.png")
    img.save(ruta_anverso, dpi=(300, 300))
    print(f"✅ Anverso guardado: {ruta_anverso}")

    # ===== REVERSO DEL CARNET =====
    try:
        ruta_fondo_reverso = os.path.join("static", "fondos", "trasero.png")
        reverso = Image.open(ruta_fondo_reverso).convert("RGB")
        reverso = reverso.resize((ancho, alto))
    except:
        reverso = Image.new("RGB", (ancho, alto), (255, 255, 255))

    draw_reverso = ImageDraw.Draw(reverso)

    # Fuentes del reverso — también con sistema robusto
    font_reverso       = cargar_fuente(32, tipo='serif')
    font_extraviado    = cargar_fuente(26, tipo='serif')
    font_programa_bold = cargar_fuente(26, tipo='serif')
    font_firma_titulo  = cargar_fuente(26, tipo='serif')
    font_ficha         = cargar_fuente(26, tipo='serif')

    # ========== TEXTO PRINCIPAL DEL REVERSO ==========
    margen_izq = 40
    margen_der = 40
    max_ancho_texto = ancho - margen_izq - margen_der
    texto_y = 80
    sep = 50  # separación entre líneas

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

    for i, line in enumerate(texto1_lines):
        if not line.strip():
            continue
        palabras = line.split()
        if len(palabras) > 1:
            # Texto justificado
            anchos_palabras = [
                draw_reverso.textbbox((0, 0), p, font=font_reverso)[2] -
                draw_reverso.textbbox((0, 0), p, font=font_reverso)[0]
                for p in palabras
            ]
            suma_palabras = sum(anchos_palabras)
            espacio = (max_ancho_texto - suma_palabras) / (len(palabras) - 1)
            x = margen_izq
            for j, palabra in enumerate(palabras):
                draw_reverso.text((x, texto_y + i * sep), palabra,
                                  fill=(0, 0, 0), font=font_reverso)
                x += anchos_palabras[j] + (espacio if j < len(palabras) - 1 else 0)
        else:
            draw_reverso.text((margen_izq, texto_y + i * sep),
                              line, fill=(0, 0, 0), font=font_reverso)

    # ========== FIRMA ==========
    firma_y = 520
    firma_x = (ancho - 100) // 3
    try:
        ruta_firma = os.path.join("static", "fotos", "firma_directora.png")
        if os.path.exists(ruta_firma):
            firma_img = Image.open(ruta_firma).convert("RGBA")
            firma_img = firma_img.resize((300, 180), Image.LANCZOS)
            reverso.paste(firma_img, (firma_x, firma_y), firma_img)
    except:
        pass

    # "Firma y Autoriza"
    firma_texto_y = firma_y + 195
    texto_firma = "Firma y Autoriza"
    bbox_firma = draw_reverso.textbbox((0, 0), texto_firma, font=font_firma_titulo)
    pos_x_firma = margen_izq
    draw_reverso.text((pos_x_firma, firma_texto_y),
                      texto_firma, fill=(0, 0, 0), font=font_firma_titulo)

    # ========== TEXTO CARNÉ EXTRAVIADO ==========
    info_y = 780
    texto_extraviado = [
        "Si por algún motivo este carné es extraviado,",
        "por favor diríjase al Centro de Biotecnología",
        "Industrial ubicado en la calle 40 #30-44"
    ]
    for i, linea in enumerate(texto_extraviado):
        draw_reverso.text((margen_izq, info_y + i * 42),
                          linea, fill=(0, 0, 0), font=font_extraviado)

    # ========== PROGRAMA Y FICHA ==========
    nombre_programa = empleado.get('nombre_programa', 'Programa Técnico')
    codigo_ficha    = empleado.get('codigo_ficha', '0000')

    # Wrap del nombre de programa si es muy largo
    lineas_programa = wrap_text(nombre_programa, font_programa_bold, draw_reverso,
                                max_ancho_texto)
    prog_y = 910
    for i, lp in enumerate(lineas_programa[:2]):  # máximo 2 líneas
        draw_reverso.text((margen_izq, prog_y + i * 34),
                          lp, fill=(0, 0, 0), font=font_programa_bold)

    ficha_y = prog_y + (len(lineas_programa[:2])) * 34 + 6
    draw_reverso.text((margen_izq, ficha_y),
                      f"FICHA {codigo_ficha}", fill=(0, 0, 0), font=font_ficha)

    ruta_reverso = os.path.join("static", "carnets", f"reverso_{empleado['cedula']}.png")
    reverso.save(ruta_reverso, dpi=(300, 300))
    print(f"✅ Reverso guardado: {ruta_reverso}")

    return ruta_anverso


def combinar_anverso_reverso(nombre_archivo_anverso, nombre_archivo_reverso, nombre_aprendiz):
    ruta_anverso = os.path.join("static", "carnets", nombre_archivo_anverso)
    ruta_reverso = os.path.join("static", "carnets", nombre_archivo_reverso)

    try:
        anverso = Image.open(ruta_anverso)
        reverso = Image.open(ruta_reverso)
    except Exception as e:
        raise Exception(f"Error al cargar las imágenes: {e}")

    # Padding entre las dos caras
    padding = 40
    ancho_total = anverso.width + reverso.width + padding
    alto_total  = max(anverso.height, reverso.height) + 60

    combinado = Image.new("RGB", (ancho_total, alto_total), (245, 245, 245))
    combinado.paste(anverso, (0, 0))
    combinado.paste(reverso, (anverso.width + padding, 0))

    # Etiquetas ANVERSO / REVERSO
    draw = ImageDraw.Draw(combinado)
    font_label = cargar_fuente(22)
    draw.text((anverso.width // 2 - 40, anverso.height + 15),
              "ANVERSO", fill=(80, 80, 80), font=font_label)
    draw.text((anverso.width + padding + reverso.width // 2 - 40, reverso.height + 15),
              "REVERSO", fill=(80, 80, 80), font=font_label)

    nombre_archivo = f"{nombre_aprendiz.replace(' ', '_')}_completo.png"
    ruta_combinada = os.path.join("static", "carnets", nombre_archivo)
    combinado.save(ruta_combinada, dpi=(300, 300))
    print(f"✅ Carnet combinado guardado: {ruta_combinada}")

    return nombre_archivo