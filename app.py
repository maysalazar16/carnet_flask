from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, send_file, jsonify
from db import crear_base_datos, insertar_empleado, cargar_empleado, existe_codigo
from qr import generar_qr
from imagen import generar_carnet, combinar_anverso_reverso  # ✅ se agregó la función aquí
from datetime import date, timedelta, datetime
import os
import random
import traceback  # ✅ Agregado para debug
import pandas as pd  # ✅ NUEVO: Para manejar Excel
from werkzeug.utils import secure_filename  # ✅ NUEVO: Para archivos seguros
import sqlite3  # ✅ NUEVO: Para la funcionalidad de cargar plantilla

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

# ✅ NUEVAS CONFIGURACIONES PARA EXCEL
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Crear carpetas necesarias
os.makedirs("static/fotos", exist_ok=True)
os.makedirs("static/qr", exist_ok=True)
os.makedirs("static/carnets", exist_ok=True)
os.makedirs("uploads", exist_ok=True)  # ✅ NUEVA: Para archivos Excel

# Crear base de datos
crear_base_datos()

# Usuarios mejorados con múltiples credenciales
usuarios = {
    "admin": {"clave": "admin123", "rol": "admin"},
    "aprendiz": {"clave": "aprendiz123", "rol": "aprendiz"},
    # ✅ Credenciales adicionales para login mejorado
    "sena": {"clave": "sena2024", "rol": "admin"},
    "usuario": {"clave": "123456", "rol": "admin"}
}
                                                                                                                              
@app.route('/')
def index():
    # Si ya está logueado, redirigir según el rol
    if 'usuario' in session:
        if session.get('rol') == 'admin':
            return redirect(url_for('dashboard_admin'))
        elif session.get('rol') == 'aprendiz':
            return redirect(url_for('dashboard_aprendiz'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # ✅ Mejorado para soportar ambos nombres de campo
        usuario = request.form.get('usuario', '').strip() or request.form.get('clave', '').strip()
        clave = request.form.get('password', '').strip() or request.form.get('clave', '').strip()

        print(f"Intento de login - Usuario: {usuario}, Clave: {clave}")  # Para debug

        # ✅ Validación mejorada con múltiples credenciales
        if usuario in usuarios and usuarios[usuario]["clave"] == clave:
            session['usuario'] = usuario
            session['rol'] = usuarios[usuario]["rol"]
            flash(f'¡Bienvenido {usuario}! Has iniciado sesión correctamente.', 'success')
            
            # Redirigir según el rol
            if session['rol'] == 'admin':
                return redirect(url_for('dashboard_admin'))
            elif session['rol'] == 'aprendiz':
                return redirect(url_for('dashboard_aprendiz'))
        else:
            flash("Usuario o contraseña incorrectos. Intenta de nuevo.", 'error')
            return render_template('login.html', error='Credenciales incorrectas')

    return render_template('login.html')

# ✅ Nueva ruta de logout mejorada
@app.route('/logout')
def logout():
    usuario = session.get('usuario', 'Usuario')
    session.clear()
    flash(f'Has cerrado sesión exitosamente. ¡Hasta pronto {usuario}!', 'info')
    return redirect(url_for('login'))

# ✅ Ruta POST de logout mantenida para compatibilidad
@app.route('/logout', methods=['POST'])
def logout_post():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@app.route('/dashboard_admin')
def dashboard_admin():
    if 'usuario' not in session or session['rol'] != 'admin':
        flash('Debes iniciar sesión como administrador para acceder.', 'error')
        return redirect(url_for('login'))
    return render_template("dashboard_admin.html", usuario=session['usuario'])

@app.route('/dashboard_aprendiz')
def dashboard_aprendiz():
    if 'usuario' not in session or session['rol'] != 'aprendiz':
        flash('Debes iniciar sesión como aprendiz para acceder.', 'error')
        return redirect(url_for('login'))
    return render_template("dashboard_aprendiz.html", usuario=session['usuario'])

# 🔥🔥🔥 FUNCIÓN AGREGAR ARREGLADA QUE SÍ FUNCIONA 🔥🔥🔥
@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    print(f"🔥🔥🔥 RUTA AGREGAR ACCEDIDA - MÉTODO: {request.method}")
    
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))

    hoy = date.today()
    vencimiento = hoy + timedelta(days=365)

    if request.method == 'POST':
        try:
            print("🔥 PROCESANDO FORMULARIO...")
            print("🔥 DATOS RECIBIDOS:", dict(request.form))
            print("🔥 ARCHIVOS RECIBIDOS:", dict(request.files))
            
            # ✅ OBTENER CAMPOS BÁSICOS OBLIGATORIOS
            nis = request.form.get('nis', '').strip()
            primer_apellido = request.form.get('primer_apellido', '').strip().upper()
            segundo_apellido = request.form.get('segundo_apellido', '').strip().upper()
            nombres = request.form.get('nombres', '').strip().upper()
            tipo_documento = request.form.get('tipo_documento', '').strip()
            cedula = request.form.get('cedula', '').strip()
            tipo_sangre = request.form.get('tipo_sangre', '').strip().upper()
            fecha_vencimiento = request.form.get('fecha_vencimiento', '').strip()
            nombre_programa = request.form.get('nombre_programa', '').strip()
            codigo_ficha = request.form.get('codigo_ficha', '').strip()
            
            print(f"🔥 CAMPOS EXTRAÍDOS: NIS={nis}, Nombres={nombres}, Primer Apellido={primer_apellido}")
            
            # ✅ VALIDACIONES BÁSICAS
            if not all([nis, primer_apellido, nombres, tipo_documento, cedula, tipo_sangre, fecha_vencimiento, nombre_programa, codigo_ficha]):
                flash("❌ Todos los campos obligatorios deben estar completos.", 'error')
                print("❌ VALIDACIÓN FALLIDA - Campos faltantes")
                return render_template('agregar.html', fecha_hoy=hoy.strftime("%Y-%m-%d"), fecha_vencimiento=vencimiento.strftime("%Y-%m-%d"))
            
            # ✅ CONSTRUIR NOMBRE COMPLETO
            apellidos = f"{primer_apellido} {segundo_apellido}".strip()
            nombre_completo = f"{nombres} {apellidos}".strip()
            centro = "Centro de Biotecnología Industrial"
            cargo = 'APRENDIZ'
            
            print(f"🔥 NOMBRE COMPLETO: {nombre_completo}")
            
            # ✅ GENERAR CÓDIGO ÚNICO
            iniciales = ''.join([parte[0] for parte in nombre_completo.split() if parte])
            codigo = None
            for _ in range(10):
                codigo_temp = f"{iniciales}{random.randint(1000, 9999)}"
                if not existe_codigo(codigo_temp):
                    codigo = codigo_temp
                    break
            
            if not codigo:
                flash("❌ No se pudo generar un código único.", 'error')
                print("❌ ERROR GENERANDO CÓDIGO")
                return render_template('agregar.html', fecha_hoy=hoy.strftime("%Y-%m-%d"), fecha_vencimiento=vencimiento.strftime("%Y-%m-%d"))
            
            print(f"🔥 CÓDIGO GENERADO: {codigo}")
            
            # ✅ MANEJAR FOTO OBLIGATORIA
            archivo_foto = request.files.get('foto')
            nombre_archivo_foto = None
            
            if archivo_foto and archivo_foto.filename != '':
                extension = os.path.splitext(archivo_foto.filename)[1]
                nombre_archivo_foto = f"{cedula}{extension}"
                ruta_guardar = os.path.join('static/fotos', nombre_archivo_foto)
                archivo_foto.save(ruta_guardar)
                print(f"🔥 FOTO GUARDADA: {nombre_archivo_foto}")
            else:
                flash("❌ Debe subir una foto.", 'error')
                print("❌ FOTO FALTANTE")
                return render_template('agregar.html', fecha_hoy=hoy.strftime("%Y-%m-%d"), fecha_vencimiento=vencimiento.strftime("%Y-%m-%d"))
            
            # ✅ PREPARAR DATOS PARA INSERTAR
            datos = {
                'nombre': nombre_completo,
                'cedula': cedula,
                'tipo_documento': tipo_documento,
                'cargo': cargo,
                'codigo': codigo,
                'fecha_emision': hoy.strftime("%Y-%m-%d"),
                'fecha_vencimiento': fecha_vencimiento,
                'tipo_sangre': tipo_sangre,
                'foto': nombre_archivo_foto,
                'nis': nis,
                'primer_apellido': primer_apellido,
                'segundo_apellido': segundo_apellido,
                'nombre_programa': nombre_programa,
                'codigo_ficha': codigo_ficha,
                'centro': centro
            }
            
            print("🔥 DATOS PREPARADOS PARA INSERTAR:")
            for key, value in datos.items():
                print(f"   {key}: {value}")
            
            # ✅ INSERTAR EN BASE DE DATOS
            print("🔥 INSERTANDO EN BASE DE DATOS...")
            insertar_empleado(datos)
            print("🔥 ✅ EMPLEADO INSERTADO CORRECTAMENTE")
            
            # ✅ MENSAJE DE ÉXITO Y REDIRECCIÓN
            flash(f"✅ ¡Empleado {nombre_completo} registrado correctamente!", 'success')
            return redirect(url_for('agregar'))
            
        except Exception as e:
            print(f"🔥 ❌ ERROR COMPLETO: {str(e)}")
            print(f"🔥 ❌ TRACEBACK: {traceback.format_exc()}")
            flash(f"❌ Error al guardar: {str(e)}", 'error')
            return render_template('agregar.html', fecha_hoy=hoy.strftime("%Y-%m-%d"), fecha_vencimiento=vencimiento.strftime("%Y-%m-%d"))
    
    # ✅ GET REQUEST - MOSTRAR FORMULARIO
    print("🔥 MOSTRANDO FORMULARIO GET")
    return render_template('agregar.html', fecha_hoy=hoy.strftime("%Y-%m-%d"), fecha_vencimiento=vencimiento.strftime("%Y-%m-%d"))

@app.route('/registro', methods=['GET', 'POST'])
def registro_aprendiz():
    if 'usuario' not in session or session['rol'] != 'aprendiz':
        return redirect(url_for('login'))

    hoy = date.today()
    vencimiento = hoy + timedelta(days=365)

    if request.method == 'POST':
        nombres = request.form['nombres'].strip().upper()
        apellidos = request.form['apellidos'].strip().upper()
        nombre = f"{nombres} {apellidos}"
        tipo_documento = request.form['tipo_documento']
        cedula = request.form['cedula'].strip()
        tipo_sangre = request.form['tipo_sangre'].strip().upper()
        fecha_vencimiento = request.form['fecha_vencimiento'].strip()

        iniciales = ''.join([parte[0] for parte in (nombres + ' ' + apellidos).split() if parte])
        for _ in range(10):
            codigo = f"{iniciales}{random.randint(1000, 9999)}"
            if not existe_codigo(codigo):
                break
        else:
            flash("No se pudo generar un código único. Intente nuevamente.")
            return redirect(request.url)

        datos = {
            'nombre': nombre,
            'cedula': cedula,
            'tipo_documento': tipo_documento,
            'cargo': 'Aprendiz',
            'codigo': codigo,
            'fecha_emision': hoy.strftime("%Y-%m-%d"),
            'fecha_vencimiento': fecha_vencimiento,
            'tipo_sangre': tipo_sangre,
            'foto': None
        }

        archivo_foto = request.files['foto']
        if archivo_foto and archivo_foto.filename != '':
            nombre_archivo = datos['cedula'] + os.path.splitext(archivo_foto.filename)[1]
            ruta_guardar = os.path.join('static/fotos', nombre_archivo)
            archivo_foto.save(ruta_guardar)
            datos['foto'] = nombre_archivo
        else:
            flash("Debe subir una foto.")
            return redirect(request.url)

        try:
            insertar_empleado(datos)
            flash("Datos registrados correctamente.")
            return redirect(url_for('logout'))
        except ValueError as ve:
            flash(str(ve))
            return redirect(request.url)
        except Exception as e:
            flash(f"Error inesperado: {e}")
            return redirect(request.url)

    return render_template("registro_aprendiz.html", usuario=session['usuario'], fecha_hoy=hoy.strftime("%Y-%m-%d"), fecha_vencimiento=vencimiento.strftime("%Y-%m-%d"))

# ✅ NUEVA RUTA PARA AGREGAR EMPLEADOS CON CAMPOS SENA (MANTENIDA PARA COMPATIBILIDAD)
@app.route('/agregar_empleado', methods=['GET', 'POST'])
def agregar_empleado():
    """Nueva ruta para agregar empleados con todos los campos del SENA"""
    if 'usuario' not in session or session['rol'] != 'admin':
        flash('Debes iniciar sesión como administrador para acceder.', 'error')
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            # Obtener todos los campos del formulario SENA
            nis = request.form.get('nis', '').strip()
            primer_apellido = request.form.get('primer_apellido', '').strip().upper()
            segundo_apellido = request.form.get('segundo_apellido', '').strip().upper()
            nombre = request.form.get('nombre', '').strip().upper()
            tipo_documento = request.form.get('tipo_documento', '').strip()
            numero_documento = request.form.get('numero_documento', '').strip()
            tipo_sangre = request.form.get('tipo_sangre', '').strip().upper()
            nombre_programa = request.form.get('nombre_programa', '').strip()
            codigo_ficha = request.form.get('codigo_ficha', '').strip()
            # ✅ CENTRO FIJO
            centro = "Centro de Biotecnología Industrial"
            fecha_finalizacion = request.form.get('fecha_finalizacion', '').strip()
            
            # Validaciones básicas (sin red_tecnologica)
            if not all([nis, primer_apellido, nombre, tipo_documento, numero_documento, 
                       tipo_sangre, nombre_programa, codigo_ficha, fecha_finalizacion]):
                flash('Todos los campos obligatorios deben estar completos.', 'error')
                return render_template('agregar_empleado.html')
            
            # Construir nombre completo
            nombre_completo = f"{nombre} {primer_apellido}"
            if segundo_apellido:
                nombre_completo += f" {segundo_apellido}"
            
            # Generar código único si no se proporcionó
            codigo_generado = request.form.get('codigo', '').strip()
            if not codigo_generado:
                iniciales = ''.join([parte[0] for parte in nombre_completo.split() if parte])
                for _ in range(10):
                    codigo_generado = f"{iniciales}{random.randint(1000, 9999)}"
                    if not existe_codigo(codigo_generado):
                        break
                else:
                    flash("No se pudo generar un código único. Intente nuevamente.", 'error')
                    return render_template('agregar_empleado.html')
            
            # Preparar datos para la base de datos (compatible con estructura existente)
            hoy = date.today()
            datos = {
                'nombre': nombre_completo,
                'cedula': numero_documento,
                'tipo_documento': tipo_documento,
                'cargo': 'APRENDIZ',  # Por defecto para SENA
                'codigo': codigo_generado,
                'fecha_emision': hoy.strftime("%Y-%m-%d"),
                'fecha_vencimiento': fecha_finalizacion,
                'tipo_sangre': tipo_sangre,
                'foto': None,
                # Campos adicionales SENA (sin red_tecnologica)
                'nis': nis,
                'primer_apellido': primer_apellido,
                'segundo_apellido': segundo_apellido,
                'nombre_programa': nombre_programa,
                'codigo_ficha': codigo_ficha,
                'centro': centro
            }
            
            # Manejar foto
            archivo_foto = request.files.get('foto')
            if archivo_foto and archivo_foto.filename != '':
                nombre_archivo = datos['cedula'] + os.path.splitext(archivo_foto.filename)[1]
                ruta_guardar = os.path.join('static/fotos', nombre_archivo)
                archivo_foto.save(ruta_guardar)
                datos['foto'] = nombre_archivo
            else:
                flash("Debe subir una foto.", 'error')
                return render_template('agregar_empleado.html')
            
            # Insertar en base de datos (usa tu función existente)
            insertar_empleado(datos)
            flash(f"Empleado {nombre_completo} registrado correctamente en el sistema SENA.", 'success')
            return redirect(url_for('dashboard_admin'))
            
        except ValueError as ve:
            flash(str(ve), 'error')
            return render_template('agregar_empleado.html')
        except Exception as e:
            print(f"Error en agregar_empleado: {e}")
            flash(f"Error inesperado: {e}", 'error')
            return render_template('agregar_empleado.html')
    
    # GET request - mostrar formulario
    return render_template('agregar_empleado.html')

# ✅ FUNCIÓN PARA BUSCAR EMPLEADOS CON DATOS COMPLETOS SENA
def buscar_empleado_completo(cedula):
    """
    Busca un empleado por cédula en la base de datos con todos los campos del SENA
    """
    try:
        conn = sqlite3.connect('carnet.db')
        cursor = conn.cursor()
        
        # Buscar con todos los campos SENA
        cursor.execute("""
            SELECT nombre, cedula, tipo_documento, cargo, codigo, 
                   fecha_emision, fecha_vencimiento, tipo_sangre, foto,
                   nis, primer_apellido, segundo_apellido, 
                   nombre_programa, codigo_ficha, centro
            FROM empleados 
            WHERE cedula = ? 
            ORDER BY fecha_emision DESC
            LIMIT 1
        """, (cedula,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            empleado = {
                'nombre': row[0],
                'cedula': row[1],
                'tipo_documento': row[2] or 'CC',
                'cargo': row[3] or 'APRENDIZ',
                'codigo': row[4],
                'fecha_emision': row[5],
                'fecha_vencimiento': row[6],
                'tipo_sangre': row[7] or 'O+',
                'foto': row[8],
                # Campos adicionales del SENA
                'nis': row[9] or 'N/A',
                'primer_apellido': row[10] or '',
                'segundo_apellido': row[11] or '',
                'nombre_programa': row[12] or 'Programa Técnico',
                'codigo_ficha': row[13] or 'N/A',
                'centro': row[14] or 'Centro de Biotecnología Industrial'
            }
            
            print(f"✅ Empleado encontrado con datos SENA: {empleado['nombre']}")
            print(f"📋 NIS: {empleado['nis']} | Programa: {empleado['nombre_programa']}")
            
            return empleado
        else:
            print(f"❌ No se encontró empleado con cédula: {cedula}")
            return None
            
    except Exception as e:
        print(f"❌ Error buscando empleado: {e}")
        return None

# ✅ RUTA MEJORADA CON DEBUG SIN DAÑAR FUNCIONALIDAD ORIGINAL - MODIFICADA PARA USAR LA NUEVA FUNCIÓN
@app.route('/generar', methods=['GET', 'POST'])
def generar_carnet_web():
    print("🚀 Ruta /generar accedida")
    print(f"📋 Método: {request.method}")
    
    if 'usuario' not in session or session.get('rol') != 'admin':
        print("❌ Sin autorización - redirigiendo a login")
        return redirect(url_for('login'))
    
    print(f"✅ Usuario autorizado: {session.get('usuario')}")

    if request.method == 'POST':
        print("📝 Procesando POST request")
        print(f"📊 Form data completo: {dict(request.form)}")
        
        cedula = request.form.get('cedula', '').strip()
        print(f"🔍 Cédula recibida: '{cedula}'")
        
        if not cedula:
            print("❌ Cédula vacía")
            flash("Por favor ingresa un número de cédula.", 'error')
            return render_template("generar.html")
        
        # Limpiar cédula de cualquier formato
        cedula_limpia = ''.join(filter(str.isdigit, cedula))
        print(f"🧹 Cédula limpia: '{cedula_limpia}'")
        
        if len(cedula_limpia) < 7 or len(cedula_limpia) > 10:
            print(f"❌ Cédula inválida - longitud: {len(cedula_limpia)}")
            flash("La cédula debe tener entre 7 y 10 dígitos.", 'error')
            return render_template("generar.html")
        
        print(f"🔎 Buscando empleado con cédula: {cedula_limpia}")
        # ✅ CAMBIO PRINCIPAL: Usar la nueva función que busca con datos completos SENA
        empleado = buscar_empleado_completo(cedula_limpia)
        
        if not empleado:
            print(f"❌ Empleado no encontrado para cédula: {cedula_limpia}")
            flash(f"No se encontró un empleado con la cédula {cedula_limpia}.", 'error')
            return render_template("generar.html")
        
        print(f"✅ Empleado encontrado: {empleado.get('nombre', 'Sin nombre')}")
        
        try:
            print("🎯 Generando QR...")
            ruta_qr = generar_qr(empleado["cedula"])
            print(f"✅ QR generado: {ruta_qr}")
            
            print("🖼️ Generando carnet...")
            ruta_carnet = generar_carnet(empleado, ruta_qr)
            print(f"✅ Carnet generado: {ruta_carnet}")
            
            nombre_archivo = os.path.basename(ruta_carnet)
            print(f"📄 Nombre archivo: {nombre_archivo}")
            
            # ✅ Combinar anverso y reverso aquí (nombre está en empleado['nombre'])
            print("🔗 Combinando anverso y reverso...")
            reverso_path = f"reverso_{empleado['cedula']}.png"  # Nombre del reverso esperado
            archivo_combinado = combinar_anverso_reverso(nombre_archivo, reverso_path, empleado['nombre'])
            print(f"✅ Archivo combinado: {archivo_combinado}")
            
            print("🎉 ¡Carnet generado exitosamente!")
            flash(f"Carnet generado exitosamente para {empleado['nombre']}", 'success')
            return render_template("ver_carnet.html", carnet=archivo_combinado, empleado=empleado)
            
        except Exception as e:
            print(f"💥 Error al generar carnet: {e}")
            print(f"🔍 Tipo de error: {type(e).__name__}")
            print(f"📚 Traceback completo: {traceback.format_exc()}")
            flash(f"Error al generar el carné: {str(e)}", 'error')
            return render_template("generar.html")
    
    print("📄 Mostrando formulario GET")
    return render_template("generar.html")

# ✅ NUEVA RUTA PARA DESCARGAR EL CARNÉ
@app.route('/descargar_carnet/<path:carnet>')
def descargar_carnet(carnet):
    return send_from_directory('static/carnets', carnet, as_attachment=True)

# ================================================
# ✅ NUEVAS FUNCIONES PARA PLANTILLA EXCEL
# ================================================

def obtener_todos_empleados():
    """Función para obtener todos los empleados de la base de datos"""
    try:
        conn = sqlite3.connect('carnet.db')  # ✅ CAMBIAR A carnet.db
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT nombre, cedula, tipo_documento, cargo, codigo, 
                   fecha_emision, fecha_vencimiento, tipo_sangre, foto
            FROM empleados
        """)
        
        empleados = []
        for row in cursor.fetchall():
            empleado = {
                'nombre': row[0],
                'cedula': row[1],
                'tipo_documento': row[2],
                'cargo': row[3],
                'codigo': row[4],
                'fecha_emision': row[5],
                'fecha_vencimiento': row[6],
                'tipo_sangre': row[7],
                'foto': row[8]
            }
            empleados.append(empleado)
        
        conn.close()
        return empleados
        
    except Exception as e:
        print(f"Error obteniendo empleados: {e}")
        return []

@app.route('/descargar_plantilla')
def descargar_plantilla():
    """Genera plantilla Excel con datos reales de empleados registrados"""
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))
    
    try:
        # Obtener empleados registrados
        empleados = obtener_todos_empleados()
        
        if empleados:
            # Crear plantilla con datos reales (SIN red tecnológica)
            data = {
                'NIS': [],
                'Primer Apellido': [],
                'Segundo Apellido': [],
                'Nombre': [],
                'Tipo de documento': [],
                'Número de documento': [],
                'Tipo de Sangre': [],
                'Nombre del Programa': [],
                'Código de Ficha': [],
                'Centro': [],
                'Fecha Finalización del Programa': []
            }
            
            # Llenar con datos reales
            for empleado in empleados:
                # Dividir nombre completo en partes
                partes_nombre = empleado['nombre'].split()
                if len(partes_nombre) >= 3:
                    nombres = partes_nombre[0]
                    primer_apellido = partes_nombre[1]
                    segundo_apellido = ' '.join(partes_nombre[2:])
                elif len(partes_nombre) == 2:
                    nombres = partes_nombre[0]
                    primer_apellido = partes_nombre[1]
                    segundo_apellido = ''
                else:
                    nombres = empleado['nombre']
                    primer_apellido = ''
                    segundo_apellido = ''
                
                data['NIS'].append(empleado['codigo'])  # Usar código como NIS
                data['Primer Apellido'].append(primer_apellido)
                data['Segundo Apellido'].append(segundo_apellido)
                data['Nombre'].append(nombres)
                data['Tipo de documento'].append(empleado['tipo_documento'])
                data['Número de documento'].append(empleado['cedula'])
                data['Tipo de Sangre'].append(empleado['tipo_sangre'])
                data['Nombre del Programa'].append(f"Programa {empleado['cargo']}")
                data['Código de Ficha'].append(empleado['codigo'])
                data['Centro'].append('Centro de Biotecnología Industrial')
                data['Fecha Finalización del Programa'].append(empleado['fecha_vencimiento'])
            
            filename = f'empleados_sena_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            flash(f'✅ Se descargó la plantilla con {len(empleados)} empleados registrados', 'success')
            
        else:
            # Plantilla con datos de ejemplo si no hay empleados (SIN red tecnológica)
            data = {
                'NIS': ['12345678901', '12345678902', '12345678903'],
                'Primer Apellido': ['PEREZ', 'GARCIA', 'MARTINEZ'],
                'Segundo Apellido': ['LOPEZ', 'RODRIGUEZ', 'SILVA'],
                'Nombre': ['JUAN CARLOS', 'MARIA ALEJANDRA', 'CARLOS ANDRES'],
                'Tipo de documento': ['CC', 'CC', 'TI'],
                'Número de documento': ['12345678', '87654321', '11223344'],
                'Tipo de Sangre': ['O+', 'A-', 'B+'],
                'Nombre del Programa': [
                    'Análisis y Desarrollo de Sistemas de Información',
                    'Biotecnología Industrial',
                    'Gestión Empresarial'
                ],
                'Código de Ficha': ['2024001', '2024002', '2024003'],
                'Centro': [
                    'Centro de Biotecnología Industrial',
                    'Centro de Biotecnología Industrial',
                    'Centro de Biotecnología Industrial'
                ],
                'Fecha Finalización del Programa': ['31/12/2024', '30/06/2025', '15/11/2024']
            }
            filename = 'plantilla_empleados_sena.xlsx'
            flash('📋 Se descargó la plantilla con datos de ejemplo (no hay empleados registrados)', 'info')
        
        # Crear DataFrame y archivo Excel
        df = pd.DataFrame(data)
        temp_file = filename
        df.to_excel(temp_file, index=False, sheet_name='Empleados SENA')
        
        return send_file(temp_file, as_attachment=True, download_name=filename)
        
    except Exception as e:
        print(f"Error generando plantilla: {e}")
        flash(f'Error al generar la plantilla: {str(e)}', 'error')
        return redirect(url_for('dashboard_admin'))

@app.route('/descargar_plantilla_vacia')
def descargar_plantilla_vacia():
    """Genera una plantilla vacía solo con cabeceras para importar nuevos datos"""
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))
    
    try:
        # Crear plantilla solo con cabeceras y una fila de ejemplo (SIN red tecnológica)
        data = {
            'NIS': ['Ejemplo: 12345678901'],
            'Primer Apellido': ['Ejemplo: PEREZ'],
            'Segundo Apellido': ['Ejemplo: LOPEZ'],
            'Nombre': ['Ejemplo: JUAN CARLOS'],
            'Tipo de documento': ['CC, TI, CE, PEP, PPT'],
            'Número de documento': ['Ejemplo: 12345678'],
            'Tipo de Sangre': ['O+, O-, A+, A-, B+, B-, AB+, AB-'],
            'Nombre del Programa': ['Ejemplo: Análisis y Desarrollo de Sistemas'],
            'Código de Ficha': ['Ejemplo: 2024001'],
            'Centro': ['Centro de Biotecnología Industrial'],
            'Fecha Finalización del Programa': ['Formato: DD/MM/AAAA']
        }
        
        df = pd.DataFrame(data)
        temp_file = 'plantilla_vacia_sena.xlsx'
        df.to_excel(temp_file, index=False, sheet_name='Nueva Importación')
        
        flash('📋 Plantilla vacía descargada. Elimina la fila de ejemplo antes de cargar datos.', 'info')
        return send_file(temp_file, as_attachment=True, download_name='plantilla_vacia_sena.xlsx')
        
    except Exception as e:
        print(f"Error generando plantilla vacía: {e}")
        flash(f'Error al generar la plantilla vacía: {str(e)}', 'error')
        return redirect(url_for('dashboard_admin'))

# ✅ NUEVA RUTA: CARGAR PLANTILLA EXCEL - LA FUNCIONALIDAD PRINCIPAL
@app.route('/cargar_plantilla', methods=['GET', 'POST'])
def cargar_plantilla():
    """Ruta para cargar empleados desde archivo Excel"""
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        return render_template('cargar_plantilla.html')
    
    if request.method == 'POST':
        try:
            # Verificar si se subió un archivo
            if 'excel_file' not in request.files:
                return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo'})
            
            file = request.files['excel_file']
            if file.filename == '':
                return jsonify({'success': False, 'message': 'No se seleccionó ningún archivo'})
            
            # Verificar extensión del archivo
            if not file.filename.lower().endswith(('.xlsx', '.xls')):
                return jsonify({'success': False, 'message': 'El archivo debe ser un Excel (.xlsx o .xls)'})
            
            # Leer el archivo Excel
            try:
                # Leer el Excel con pandas
                df = pd.read_excel(file, engine='openpyxl')
                
                # Verificar que tenga las columnas necesarias
                columnas_requeridas = [
                    'NIS', 'Primer Apellido', 'Segundo Apellido', 'Nombre', 
                    'Tipo de documento', 'Número de documento', 'Tipo de Sangre', 
                    'Nombre del Programa', 'Código de Ficha', 'Centro', 
                    'Fecha Finalización del Programa'
                ]
                
                columnas_faltantes = []
                for col in columnas_requeridas:
                    if col not in df.columns:
                        columnas_faltantes.append(col)
                
                if columnas_faltantes:
                    return jsonify({
                        'success': False, 
                        'message': f'Faltan las siguientes columnas: {", ".join(columnas_faltantes)}'
                    })
                
                # Procesar cada fila del Excel
                created_count = 0
                updated_count = 0
                error_count = 0
                errors = []
                
                # Conectar a la base de datos
                conn = sqlite3.connect('carnet.db')
                cursor = conn.cursor()
                
                for index, row in df.iterrows():
                    try:
                        # Limpiar y preparar los datos
                        nis = str(row['NIS']).strip() if pd.notna(row['NIS']) else ''
                        primer_apellido = str(row['Primer Apellido']).strip().upper() if pd.notna(row['Primer Apellido']) else ''
                        segundo_apellido = str(row['Segundo Apellido']).strip().upper() if pd.notna(row['Segundo Apellido']) else ''
                        nombre = str(row['Nombre']).strip().upper() if pd.notna(row['Nombre']) else ''
                        tipo_documento = str(row['Tipo de documento']).strip() if pd.notna(row['Tipo de documento']) else ''
                        numero_documento = str(row['Número de documento']).strip() if pd.notna(row['Número de documento']) else ''
                        tipo_sangre = str(row['Tipo de Sangre']).strip().upper() if pd.notna(row['Tipo de Sangre']) else ''
                        programa = str(row['Nombre del Programa']).strip() if pd.notna(row['Nombre del Programa']) else ''
                        codigo_ficha = str(row['Código de Ficha']).strip() if pd.notna(row['Código de Ficha']) else ''
                        centro = str(row['Centro']).strip() if pd.notna(row['Centro']) else 'Centro de Biotecnología Industrial'
                        fecha_finalizacion = str(row['Fecha Finalización del Programa']).strip() if pd.notna(row['Fecha Finalización del Programa']) else ''
                        
                        # Validar datos mínimos requeridos
                        if not all([nis, primer_apellido, nombre, numero_documento]):
                            errors.append(f"Fila {index + 2}: Faltan datos obligatorios (NIS, Primer Apellido, Nombre, Número de documento)")
                            error_count += 1
                            continue
                        
                        # Construir nombre completo
                        nombre_completo = f"{nombre} {primer_apellido}"
                        if segundo_apellido:
                            nombre_completo += f" {segundo_apellido}"
                        
                        # Verificar si el empleado ya existe (por número de documento)
                        cursor.execute("SELECT * FROM empleados WHERE cedula = ?", (numero_documento,))
                        empleado_existente = cursor.fetchone()
                        
                        # Generar código único si no existe
                        iniciales = ''.join([parte[0] for parte in nombre_completo.split() if parte])
                        codigo_generado = None
                        for _ in range(10):
                            codigo_temp = f"{iniciales}{random.randint(1000, 9999)}"
                            cursor.execute("SELECT codigo FROM empleados WHERE codigo = ?", (codigo_temp,))
                            if not cursor.fetchone():
                                codigo_generado = codigo_temp
                                break
                        
                        if not codigo_generado:
                            errors.append(f"Fila {index + 2}: No se pudo generar código único")
                            error_count += 1
                            continue
                        
                        # Preparar datos para insertar/actualizar
                        hoy = date.today()
                        
                        if empleado_existente:
                            # Actualizar empleado existente
                            cursor.execute("""
                                UPDATE empleados SET 
                                    nombre = ?, tipo_documento = ?, cargo = ?, codigo = ?,
                                    fecha_emision = ?, fecha_vencimiento = ?, tipo_sangre = ?,
                                    nis = ?, primer_apellido = ?, segundo_apellido = ?,
                                    nombre_programa = ?, codigo_ficha = ?, centro = ?
                                WHERE cedula = ?
                            """, (
                                nombre_completo, tipo_documento, 'APRENDIZ', codigo_generado,
                                hoy.strftime("%Y-%m-%d"), fecha_finalizacion, tipo_sangre,
                                nis, primer_apellido, segundo_apellido,
                                programa, codigo_ficha, centro,
                                numero_documento
                            ))
                            updated_count += 1
                        else:
                            # Crear nuevo empleado
                            cursor.execute("""
                                INSERT INTO empleados (
                                    nombre, cedula, tipo_documento, cargo, codigo,
                                    fecha_emision, fecha_vencimiento, tipo_sangre, foto,
                                    nis, primer_apellido, segundo_apellido,
                                    nombre_programa, codigo_ficha, centro
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                nombre_completo, numero_documento, tipo_documento, 
                                'APRENDIZ', codigo_generado, hoy.strftime("%Y-%m-%d"), 
                                fecha_finalizacion, tipo_sangre, None,
                                nis, primer_apellido, segundo_apellido,
                                programa, codigo_ficha, centro
                            ))
                            created_count += 1
                        
                        # Confirmar la transacción para cada empleado
                        conn.commit()
                        
                    except Exception as e:
                        error_count += 1
                        errors.append(f"Fila {index + 2}: Error al procesar - {str(e)}")
                        print(f"Error procesando fila {index + 2}: {str(e)}")
                        continue
                
                # Cerrar conexión
                conn.close()
                
                # Preparar respuesta
                response_data = {
                    'success': True,
                    'created': created_count,
                    'updated': updated_count,
                    'errors': error_count,
                    'message': f'Procesamiento completado. {created_count} empleados creados, {updated_count} actualizados.'
                }
                
                if errors:
                    response_data['error_details'] = errors[:10]  # Solo mostrar los primeros 10 errores
                
                return jsonify(response_data)
                
            except Exception as e:
                print(f"Error leyendo Excel: {str(e)}")
                return jsonify({'success': False, 'message': f'Error al leer el archivo Excel: {str(e)}'})
                
        except Exception as e:
            print(f"Error general: {str(e)}")
            return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'})

# ================================================
# ✅ FUNCIONES AUXILIARES PARA EXCEL
# ================================================

def allowed_file(filename):
    """Verifica si el archivo tiene extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

# ✅ FUNCIÓN AUXILIAR PARA ACTUALIZAR BASE DE DATOS (OPCIONAL)
# Solo ejecutar si quieres agregar las nuevas columnas a tu DB existente

def actualizar_base_datos_sena():
    """
    Función opcional para agregar nuevas columnas SENA a la base de datos existente
    Solo ejecutar UNA VEZ si quieres guardar los campos adicionales
    """
    try:
        conn = sqlite3.connect('carnet.db')  # ✅ USAR carnet.db
        cursor = conn.cursor()
        
        # Agregar nuevas columnas si no existen (SIN red_tecnologica)
        nuevas_columnas = [
            'nis TEXT',
            'primer_apellido TEXT',
            'segundo_apellido TEXT', 
            'nombre_programa TEXT',
            'codigo_ficha TEXT',
            'centro TEXT'
        ]
        
        for columna in nuevas_columnas:
            try:
                cursor.execute(f'ALTER TABLE empleados ADD COLUMN {columna}')
                print(f"✅ Columna agregada: {columna}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️ Columna ya existe: {columna}")
                else:
                    print(f"❌ Error agregando columna {columna}: {e}")
        
        conn.commit()
        conn.close()
        print("✅ Base de datos actualizada correctamente")
        
    except Exception as e:
        print(f"❌ Error actualizando base de datos: {e}")

# ✅ Nuevas rutas adicionales para compatibilidad con el login mejorado
@app.route('/dashboard_menu')
def dashboard_menu():
    """Ruta adicional para el menú del dashboard"""
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    if session.get('rol') == 'admin':
        return redirect(url_for('dashboard_admin'))
    elif session.get('rol') == 'aprendiz':
        return redirect(url_for('dashboard_aprendiz'))
    else:
        return redirect(url_for('login'))

# ✅ RUTAS ADICIONALES PARA VERIFICAR CARNETS
@app.route('/verificar')
def verificar():
    """Ruta para verificar carnets"""
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('verificar.html')

@app.route('/verificar_carnet', methods=['POST'])
def verificar_carnet():
    """Procesar verificación de carnet por código QR"""
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    try:
        codigo_qr = request.form.get('codigo_qr', '').strip()
        
        if not codigo_qr:
            flash("Ingresa un código para verificar.", 'error')
            return redirect(url_for('verificar'))
        
        # Buscar empleado por código QR (que generalmente es la cédula)
        empleado = cargar_empleado(codigo_qr)
        
        if empleado:
            flash(f"✅ Carnet VÁLIDO - {empleado['nombre']}", 'success')
            return render_template('verificar.html', empleado=empleado, valido=True)
        else:
            flash("❌ Carnet NO VÁLIDO - No se encontró en el sistema", 'error')
            return render_template('verificar.html', valido=False)
            
    except Exception as e:
        print(f"Error verificando carnet: {e}")
        flash("Error al verificar el carnet.", 'error')
        return redirect(url_for('verificar'))

# ✅ RUTA PARA VER CARNETS GENERADOS
@app.route('/ver_carnet')
def ver_carnet():
    """Ruta para mostrar carnets generados"""
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    return render_template('ver_carnet.html')

# ✅ RUTA PARA CONFIGURACIÓN DEL SISTEMA
@app.route('/configuracion')
def configuracion():
    """Ruta para configuración del sistema"""
    if 'usuario' not in session or session.get('rol') != 'admin':
        flash('Acceso denegado. Solo administradores.', 'error')
        return redirect(url_for('login'))
    return render_template('configuracion.html')

# ✅ RUTA PARA REPORTES
@app.route('/reportes')
def reportes():
    """Ruta para generar reportes del sistema"""
    if 'usuario' not in session or session.get('rol') != 'admin':
        flash('Acceso denegado. Solo administradores.', 'error')
        return redirect(url_for('login'))
    
    try:
        # Obtener estadísticas básicas
        empleados = obtener_todos_empleados()
        total_empleados = len(empleados)
        
        # Contar por cargo
        cargos = {}
        for emp in empleados:
            cargo = emp.get('cargo', 'Sin cargo')
            cargos[cargo] = cargos.get(cargo, 0) + 1
        
        # Empleados registrados hoy
        hoy = date.today().strftime("%Y-%m-%d")
        empleados_hoy = len([emp for emp in empleados if emp.get('fecha_emision') == hoy])
        
        estadisticas = {
            'total_empleados': total_empleados,
            'empleados_hoy': empleados_hoy,
            'cargos': cargos,
            'empleados': empleados
        }
        
        return render_template('reportes.html', stats=estadisticas)
        
    except Exception as e:
        print(f"Error generando reportes: {e}")
        flash('Error al generar reportes.', 'error')
        return redirect(url_for('dashboard_admin'))

# ✅ MANEJO DE ERRORES 404
@app.errorhandler(404)
def pagina_no_encontrada(e):
    return render_template('404.html'), 404

# ✅ MANEJO DE ERRORES 500
@app.errorhandler(500)
def error_interno(e):
    return render_template('500.html'), 500

# ✅ Descomenta la siguiente línea SOLO UNA VEZ para actualizar tu DB
actualizar_base_datos_sena()

if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)