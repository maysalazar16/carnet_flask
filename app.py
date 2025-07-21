from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, send_file
from db import crear_base_datos, insertar_empleado, cargar_empleado, existe_codigo
from qr import generar_qr
from imagen import generar_carnet, combinar_anverso_reverso  # ✅ se agregó la función aquí
from datetime import date, timedelta, datetime
import os
import random
import traceback  # ✅ Agregado para debug
import pandas as pd  # ✅ NUEVO: Para manejar Excel
from werkzeug.utils import secure_filename  # ✅ NUEVO: Para archivos seguros

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

@app.route('/agregar', methods=['GET', 'POST'])
def agregar():
    if 'usuario' not in session or session['rol'] != 'admin':
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

        cargo = request.form.get('cargo', 'Empleado').strip()
        if cargo.lower() == 'instructor':
            primer_nombre = nombres.split()[0].lower()
            if primer_nombre.endswith("a"):
                cargo = "INSTRUCTORA"
            else:
                cargo = "INSTRUCTOR"

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
            'cargo': cargo,
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
            flash("Empleado registrado correctamente.")
            return redirect(url_for('dashboard_admin'))
        except ValueError as ve:
            flash(str(ve))
            return redirect(request.url)
        except Exception as e:
            flash(f"Error inesperado: {e}")
            return redirect(request.url)

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

# ✅ RUTA MEJORADA CON DEBUG SIN DAÑAR FUNCIONALIDAD ORIGINAL
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
        empleado = cargar_empleado(cedula_limpia)
        
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
        import sqlite3
        conn = sqlite3.connect('empleados.db')  # Ajustar nombre según tu DB
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
            # Crear plantilla con datos reales
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
                'Centro Red Tecnologica': [],
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
                data['Centro Red Tecnologica'].append('Centro de Biotecnología Industrial')
                data['Fecha Finalización del Programa'].append(empleado['fecha_vencimiento'])
            
            filename = f'empleados_sena_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            flash(f'✅ Se descargó la plantilla con {len(empleados)} empleados registrados', 'success')
            
        else:
            # Plantilla con datos de ejemplo si no hay empleados
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
                'Centro Red Tecnologica': [
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
        # Crear plantilla solo con cabeceras y una fila de ejemplo
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
            'Centro Red Tecnologica': ['Ejemplo: Centro de Biotecnología Industrial'],
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

# ================================================
# ✅ FUNCIONES AUXILIARES PARA EXCEL
# ================================================

def allowed_file(filename):
    """Verifica si el archivo tiene extensión permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['xlsx', 'xls']

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

if __name__ == "__main__":
    app.run(debug=True)