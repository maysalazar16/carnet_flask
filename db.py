import sqlite3
import os

DB_PATH = "carnet.db"

def crear_base_datos():
    """Crea la base de datos con todas las columnas necesarias"""
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        
        # ✅ TABLA ACTUALIZADA CON TODOS LOS CAMPOS SENA + nivel_formacion
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS empleados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                cedula TEXT NOT NULL UNIQUE,
                tipo_documento TEXT NOT NULL,
                cargo TEXT NOT NULL,
                codigo TEXT NOT NULL UNIQUE,
                fecha_emision TEXT NOT NULL,
                fecha_vencimiento TEXT NOT NULL,
                tipo_sangre TEXT NOT NULL,
                foto TEXT,
                nis TEXT,
                primer_apellido TEXT,
                segundo_apellido TEXT,
                nombre_programa TEXT,
                codigo_ficha TEXT,
                centro TEXT,
                nivel_formacion TEXT DEFAULT 'Técnico'
            )
        ''')
        conexion.commit()
        print("✅ Base de datos creada correctamente")
        
        # ✅ AGREGAR COLUMNAS NUEVAS SI NO EXISTEN (para bases de datos existentes)
        agregar_columnas_sena(cursor)
        conexion.commit()
        
    except Exception as e:
        print(f"❌ Error creando base de datos: {e}")
    finally:
        conexion.close()

def agregar_columnas_sena(cursor):
    """Agrega las nuevas columnas SENA si no existen"""
    nuevas_columnas = [
        'nis TEXT',
        'primer_apellido TEXT',
        'segundo_apellido TEXT',
        'nombre_programa TEXT',
        'codigo_ficha TEXT',
        'centro TEXT',
        'nivel_formacion TEXT DEFAULT "Técnico"'  # 🆕 NUEVA COLUMNA
    ]
    
    for columna in nuevas_columnas:
        try:
            cursor.execute(f'ALTER TABLE empleados ADD COLUMN {columna}')
            print(f"✅ Columna agregada: {columna}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"⚠️ Columna ya existe: {columna.split()[0]}")
            else:
                print(f"❌ Error agregando columna {columna}: {e}")

def insertar_empleado(datos):
    """Inserta un empleado con todos los campos SENA"""
    if existe_cedula(datos['cedula']):
        raise ValueError("La cédula ya está registrada.")

    if existe_codigo(datos['codigo']):
        raise ValueError("El código ya está registrado.")

    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        
        # ✅ INSERT ACTUALIZADO CON TODOS LOS CAMPOS SENA + nivel_formacion
        cursor.execute('''
            INSERT INTO empleados (
                nombre, cedula, tipo_documento, cargo,
                codigo, fecha_emision, fecha_vencimiento,
                tipo_sangre, foto, nis, primer_apellido,
                segundo_apellido, nombre_programa, codigo_ficha, centro, nivel_formacion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datos['nombre'],
            datos['cedula'],
            datos['tipo_documento'],
            datos['cargo'],
            datos['codigo'],
            datos['fecha_emision'],
            datos['fecha_vencimiento'],
            datos['tipo_sangre'],
            datos['foto'],
            datos.get('nis', ''),
            datos.get('primer_apellido', ''),
            datos.get('segundo_apellido', ''),
            datos.get('nombre_programa', ''),
            datos.get('codigo_ficha', ''),
            datos.get('centro', 'Centro de Biotecnología Industrial'),
            datos.get('nivel_formacion', 'Técnico')  # 🆕 NUEVO CAMPO
        ))
        conexion.commit()
        print(f"✅ Empleado {datos['nombre']} insertado correctamente - Nivel: {datos.get('nivel_formacion', 'Técnico')}")
        
    except Exception as e:
        print(f"❌ Error insertando empleado: {e}")
        raise e
    finally:
        conexion.close()

def cargar_empleado(cedula):
    """Carga un empleado por cédula con todos los campos"""
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('SELECT * FROM empleados WHERE cedula = ?', (cedula,))
        fila = cursor.fetchone()
        if fila:
            # ✅ COLUMNAS ACTUALIZADAS CON CAMPOS SENA + nivel_formacion
            columnas = [
                'id', 'nombre', 'cedula', 'tipo_documento', 'cargo',
                'codigo', 'fecha_emision', 'fecha_vencimiento',
                'tipo_sangre', 'foto', 'nis', 'primer_apellido',
                'segundo_apellido', 'nombre_programa', 'codigo_ficha', 'centro', 'nivel_formacion'
            ]
            empleado = dict(zip(columnas, fila))
            # Asegurar que nivel_formacion tenga un valor por defecto
            if not empleado.get('nivel_formacion'):
                empleado['nivel_formacion'] = 'Técnico'
            return empleado
        return None
    except Exception as e:
        print(f"❌ Error cargando empleado: {e}")
        return None
    finally:
        conexion.close()

def obtener_todos_empleados():
    """Obtiene todos los empleados de la base de datos"""
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('SELECT * FROM empleados ORDER BY fecha_emision DESC')
        filas = cursor.fetchall()
        
        empleados = []
        if filas:
            columnas = [
                'id', 'nombre', 'cedula', 'tipo_documento', 'cargo',
                'codigo', 'fecha_emision', 'fecha_vencimiento',
                'tipo_sangre', 'foto', 'nis', 'primer_apellido',
                'segundo_apellido', 'nombre_programa', 'codigo_ficha', 'centro', 'nivel_formacion'
            ]
            for fila in filas:
                empleado = dict(zip(columnas, fila))
                # Asegurar que nivel_formacion tenga un valor por defecto
                if not empleado.get('nivel_formacion'):
                    empleado['nivel_formacion'] = 'Técnico'
                empleados.append(empleado)
        
        return empleados
        
    except Exception as e:
        print(f"❌ Error obteniendo empleados: {e}")
        return []
    finally:
        conexion.close()

def existe_codigo(codigo):
    """Verifica si un código ya existe"""
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('SELECT 1 FROM empleados WHERE codigo = ?', (codigo,))
        resultado = cursor.fetchone()
        return resultado is not None
    except Exception as e:
        print(f"❌ Error verificando código: {e}")
        return False
    finally:
        conexion.close()

def existe_cedula(cedula):
    """Verifica si una cédula ya existe"""
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('SELECT 1 FROM empleados WHERE cedula = ?', (cedula,))
        resultado = cursor.fetchone()
        return resultado is not None
    except Exception as e:
        print(f"❌ Error verificando cédula: {e}")
        return False
    finally:
        conexion.close()

def actualizar_empleado(cedula, datos):
    """Actualiza los datos de un empleado existente"""
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        
        cursor.execute('''
            UPDATE empleados SET
                nombre = ?, tipo_documento = ?, cargo = ?,
                fecha_vencimiento = ?, tipo_sangre = ?, foto = ?,
                nis = ?, primer_apellido = ?, segundo_apellido = ?,
                nombre_programa = ?, codigo_ficha = ?, centro = ?, nivel_formacion = ?
            WHERE cedula = ?
        ''', (
            datos['nombre'],
            datos['tipo_documento'],
            datos['cargo'],
            datos['fecha_vencimiento'],
            datos['tipo_sangre'],
            datos['foto'],
            datos.get('nis', ''),
            datos.get('primer_apellido', ''),
            datos.get('segundo_apellido', ''),
            datos.get('nombre_programa', ''),
            datos.get('codigo_ficha', ''),
            datos.get('centro', ''),
            datos.get('nivel_formacion', 'Técnico'),  # 🆕 NUEVO CAMPO
            cedula
        ))
        conexion.commit()
        print(f"✅ Empleado con cédula {cedula} actualizado")
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando empleado: {e}")
        return False
    finally:
        conexion.close()

def eliminar_empleado(cedula):
    """Elimina un empleado por cédula"""
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('DELETE FROM empleados WHERE cedula = ?', (cedula,))
        conexion.commit()
        
        if cursor.rowcount > 0:
            print(f"✅ Empleado con cédula {cedula} eliminado")
            return True
        else:
            print(f"⚠️ No se encontró empleado con cédula {cedula}")
            return False
            
    except Exception as e:
        print(f"❌ Error eliminando empleado: {e}")
        return False
    finally:
        conexion.close()

def obtener_estadisticas():
    """Obtiene estadísticas básicas de la base de datos"""
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        
        # Total empleados
        cursor.execute('SELECT COUNT(*) FROM empleados')
        total = cursor.fetchone()[0]
        
        # Empleados por cargo
        cursor.execute('SELECT cargo, COUNT(*) FROM empleados GROUP BY cargo')
        por_cargo = dict(cursor.fetchall())
        
        # 🆕 Empleados por nivel de formación
        cursor.execute('SELECT nivel_formacion, COUNT(*) FROM empleados GROUP BY nivel_formacion')
        por_nivel = dict(cursor.fetchall())
        
        # Empleados registrados hoy
        from datetime import date
        hoy = date.today().strftime("%Y-%m-%d")
        cursor.execute('SELECT COUNT(*) FROM empleados WHERE fecha_emision = ?', (hoy,))
        hoy_count = cursor.fetchone()[0]
        
        return {
            'total': total,
            'por_cargo': por_cargo,
            'por_nivel_formacion': por_nivel,  # 🆕 NUEVA ESTADÍSTICA
            'registrados_hoy': hoy_count
        }
        
    except Exception as e:
        print(f"❌ Error obteniendo estadísticas: {e}")
        return {'total': 0, 'por_cargo': {}, 'por_nivel_formacion': {}, 'registrados_hoy': 0}
    finally:
        conexion.close()

# ✅ FUNCIÓN PARA MIGRAR DATOS EXISTENTES (OPCIONAL)
def migrar_base_datos():
    """
    Función para migrar una base de datos antigua a la nueva estructura
    Solo ejecutar si tienes datos importantes que no quieres perder
    """
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        
        # Verificar si existe la tabla antigua
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='empleados'")
        if cursor.fetchone():
            print("🔄 Migrando base de datos existente...")
            agregar_columnas_sena(cursor)
            conexion.commit()
            print("✅ Migración completada")
        else:
            print("📋 Creando nueva base de datos...")
            crear_base_datos()
            
    except Exception as e:
        print(f"❌ Error en migración: {e}")
    finally:
        conexion.close()

# 🆕 NUEVA FUNCIÓN: Verificar estructura de la base de datos
def verificar_estructura_db():
    """
    Verifica que la base de datos tenga todos los campos necesarios
    """
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        
        cursor.execute("PRAGMA table_info(empleados)")
        columnas = cursor.fetchall()
        
        print("🔍 ESTRUCTURA ACTUAL DE LA BASE DE DATOS:")
        print("-" * 50)
        
        campos_esperados = [
            'id', 'nombre', 'cedula', 'tipo_documento', 'cargo', 'codigo',
            'fecha_emision', 'fecha_vencimiento', 'tipo_sangre', 'foto',
            'nis', 'primer_apellido', 'segundo_apellido', 'nombre_programa',
            'codigo_ficha', 'centro', 'nivel_formacion'
        ]
        
        campos_existentes = [col[1] for col in columnas]
        
        for campo in campos_esperados:
            if campo in campos_existentes:
                print(f"✅ {campo}")
            else:
                print(f"❌ {campo} - FALTA")
        
        # Verificar específicamente nivel_formacion
        if 'nivel_formacion' in campos_existentes:
            print("\n🎯 ¡Campo 'nivel_formacion' encontrado! La base de datos está lista.")
        else:
            print("\n⚠️ Falta el campo 'nivel_formacion'. Ejecutando actualización...")
            agregar_columnas_sena(cursor)
            conexion.commit()
            print("✅ Campo 'nivel_formacion' agregado exitosamente")
            
    except Exception as e:
        print(f"❌ Error verificando estructura: {e}")
    finally:
        conexion.close()

# 🆕 NUEVA FUNCIÓN: Actualizar empleados existentes para que tengan nivel_formacion
def actualizar_empleados_sin_nivel():
    """
    Actualiza empleados existentes que no tienen nivel_formacion definido
    """
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        
        # Buscar empleados sin nivel_formacion o con valor NULL
        cursor.execute("SELECT cedula, nombre FROM empleados WHERE nivel_formacion IS NULL OR nivel_formacion = ''")
        empleados_sin_nivel = cursor.fetchall()
        
        if empleados_sin_nivel:
            print(f"🔄 Actualizando {len(empleados_sin_nivel)} empleados sin nivel de formación...")
            
            # Asignar 'Técnico' por defecto
            cursor.execute("UPDATE empleados SET nivel_formacion = 'Técnico' WHERE nivel_formacion IS NULL OR nivel_formacion = ''")
            conexion.commit()
            
            print("✅ Empleados actualizados con nivel 'Técnico' por defecto")
            
            for cedula, nombre in empleados_sin_nivel:
                print(f"   - {nombre} (Cédula: {cedula})")
        else:
            print("✅ Todos los empleados ya tienen nivel de formación definido")
            
    except Exception as e:
        print(f"❌ Error actualizando empleados: {e}")
    finally:
        conexion.close()

# ✅ EJECUTAR VERIFICACIÓN Y ACTUALIZACIÓN AL IMPORTAR
if __name__ == "__main__":
    print("🚀 INICIALIZANDO BASE DE DATOS...")
    crear_base_datos()
    verificar_estructura_db()
    actualizar_empleados_sin_nivel()
    print("✅ Base de datos inicializada correctamente con nivel_formacion")
else:
    # Cuando se importe desde app.py, verificar silenciosamente
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=5)
        cursor = conexion.cursor()
        cursor.execute("PRAGMA table_info(empleados)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'nivel_formacion' not in columnas:
            print("🔄 Agregando campo nivel_formacion...")
            agregar_columnas_sena(cursor)
            conexion.commit()
            print("✅ Campo nivel_formacion agregado")
        
        conexion.close()
    except:
        pass  # Silenciosamente continuar si hay problemas