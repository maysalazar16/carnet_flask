from PIL import Image, ImageDraw, ImageFont
import os

def generar_carnet(empleado, ruta_qr):
    ancho, alto = 400, 600
    fondo_color = (255, 255, 255)
    img = Image.new("RGB", (ancho, alto), fondo_color)
    draw = ImageDraw.Draw(img)

    # Cargar imagen del logo
    ruta_logo = os.path.join("static", "fotos", "logo_sena.png")
    logo = Image.open(ruta_logo).convert("RGBA")
    logo = logo.resize((130, 130))
    img.paste(logo, (20, 30), logo)

    # Cargar foto del empleado
    ruta_foto = os.path.join("static", "fotos", empleado['foto'])
    try:
        foto = Image.open(ruta_foto).convert("RGB")
    except Exception as e:
        raise Exception(f"No se pudo cargar la foto: {e}")
    foto = foto.resize((120, 150))
    img.paste(foto, (250, 30))

    # Cargar código QR
    qr = Image.open(ruta_qr).convert("RGB")
    qr = qr.resize((180, 180))
    img.paste(qr, (200, 290))

    # Cargar fuentes
    font_path = "arial.ttf"
    try:
        font_nombre = ImageFont.truetype(font_path, 16)
        font_cedula = ImageFont.truetype(font_path, 14)
        font_rh = ImageFont.truetype(font_path, 50)
        font_normal = ImageFont.truetype(font_path, 18)
        font_footer = ImageFont.truetype(font_path, 18)
        font_vertical = ImageFont.truetype(font_path, 22)
    except:
        font_nombre = ImageFont.load_default()
        font_cedula = ImageFont.load_default()
        font_rh = ImageFont.load_default()
        font_normal = ImageFont.load_default()
        font_footer = ImageFont.load_default()
        font_vertical = ImageFont.load_default()

    # Texto vertical (APRENDIZ) de abajo hacia arriba
    cargo_img = Image.new("RGBA", (150, 160), (255, 255, 255, 0))
    draw_cargo = ImageDraw.Draw(cargo_img)
    cargo = empleado['cargo'].upper()
    draw_cargo.text((0, 0), cargo, font=font_vertical, fill=(0, 0, 0))
    cargo_img = cargo_img.rotate(90, expand=True)  # Rota para que inicie desde abajo hacia arriba
    img.paste(cargo_img, (370, 30), cargo_img)

    # Línea verde horizontal
    draw.line((20, 200, 380, 200), fill=(0, 128, 0), width=3)

    # Nombres y apellidos separados
    nombre = empleado['nombre'].upper()
    nombre_partes = nombre.split()
    nombres = " ".join(nombre_partes[:2])
    apellidos = " ".join(nombre_partes[2:]) if len(nombre_partes) > 2 else ""

    draw.text((25, 210), nombres, fill=(0, 128, 0), font=font_nombre)
    draw.text((25, 235), apellidos, fill=(0, 128, 0), font=font_nombre)

    # Cédula formateada
    cedula = "{:,}".format(int(empleado['cedula'])).replace(",", ".")
    draw.text((25, 260), cedula, fill=(80, 80, 80), font=font_cedula)

    # RH
    draw.text((25, 300), "RH", fill=(0, 0, 0), font=font_normal)
    draw.text((25, 335), empleado['tipo_sangre'].upper(), fill=(120, 120, 120), font=font_rh)

    # Pie de página
    draw.text((25, 520), "Regional Valle", fill=(100, 100, 100), font=font_footer)
    draw.text((25, 545), "Centro de Biotecnología", fill=(0, 128, 0), font=font_footer)
    draw.text((25, 570), "Industrial", fill=(0, 128, 0), font=font_footer)

    # Guardar imagen
    ruta_guardar = os.path.join("static", "carnets", f"carnet_{empleado['cedula']}.png")
    img.save(ruta_guardar)
    return ruta_guardar