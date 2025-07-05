import sqlite3
import os

DB_PATH = "carnet.db"

def crear_base_datos():
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
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
                foto TEXT
            )
        ''')
        conexion.commit()
    finally:
        conexion.close()

def insertar_empleado(datos):
    if existe_cedula(datos['cedula']):
        raise ValueError("La cédula ya está registrada.")

    if existe_codigo(datos['codigo']):
        raise ValueError("El código ya está registrado.")

    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('''
            INSERT INTO empleados (
                nombre, cedula, tipo_documento, cargo,
                codigo, fecha_emision, fecha_vencimiento,
                tipo_sangre, foto
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datos['nombre'],
            datos['cedula'],
            datos['tipo_documento'],
            datos['cargo'],
            datos['codigo'],
            datos['fecha_emision'],
            datos['fecha_vencimiento'],
            datos['tipo_sangre'],
            datos['foto']
        ))
        conexion.commit()
    finally:
        conexion.close()

def cargar_empleado(cedula):
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('SELECT * FROM empleados WHERE cedula = ?', (cedula,))
        fila = cursor.fetchone()
        if fila:
            columnas = [
                'id', 'nombre', 'cedula', 'tipo_documento', 'cargo',
                'codigo', 'fecha_emision', 'fecha_vencimiento',
                'tipo_sangre', 'foto'
            ]
            return dict(zip(columnas, fila))
        return None
    finally:
        conexion.close()

def existe_codigo(codigo):
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('SELECT 1 FROM empleados WHERE codigo = ?', (codigo,))
        resultado = cursor.fetchone()
        return resultado is not None
    finally:
        conexion.close()

def existe_cedula(cedula):
    try:
        conexion = sqlite3.connect(DB_PATH, timeout=10)
        cursor = conexion.cursor()
        cursor.execute('SELECT 1 FROM empleados WHERE cedula = ?', (cedula,))
        resultado = cursor.fetchone()
        return resultado is not None
    finally:
        conexion.close()