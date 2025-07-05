from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import crear_base_datos, insertar_empleado, cargar_empleado, existe_codigo
from qr import generar_qr
from imagen import generar_carnet
from datetime import date, timedelta
import os
import random

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'

# Crear carpetas necesarias
os.makedirs("static/fotos", exist_ok=True)
os.makedirs("static/qr", exist_ok=True)
os.makedirs("static/carnets", exist_ok=True)

# Crear base de datos
crear_base_datos()

# Usuarios
usuarios = {
    "admin": {"clave": "admin123", "rol": "admin"},
    "aprendiz": {"clave": "aprendiz123", "rol": "aprendiz"}
}

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        clave = request.form['clave']
        if usuario in usuarios and usuarios[usuario]['clave'] == clave:
            session['usuario'] = usuario
            session['rol'] = usuarios[usuario]['rol']
            if session['rol'] == 'admin':
                return redirect(url_for('dashboard_admin'))
            else:
                return redirect(url_for('registro_aprendiz'))
        else:
            flash("Credenciales incorrectas")
    return render_template("login.html")

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard_admin():
    if 'usuario' not in session or session['rol'] != 'admin':
        return redirect(url_for('login'))
    return render_template("dashboard_admin.html", usuario=session['usuario'])

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

@app.route('/generar', methods=['GET', 'POST'])
def generar_carnet_web():
    if 'usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        cedula = request.form['cedula'].strip()
        empleado = cargar_empleado(cedula)
        if not empleado:
            flash("Empleado no encontrado.")
            return redirect(request.url)

        try:
            ruta_qr = generar_qr(empleado["cedula"])
            ruta_carnet = generar_carnet(empleado, ruta_qr)
            nombre_archivo = os.path.basename(ruta_carnet)
            return render_template("ver_carnet.html", carnet=nombre_archivo, empleado=empleado)
        except Exception as e:
            flash(f"Error al generar el carné: {e}")
            return redirect(request.url)

    return render_template("generar.html")

if __name__ == "__main__":
    app.run(debug=True)#