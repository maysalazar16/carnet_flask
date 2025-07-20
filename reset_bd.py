import os
import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

# Configuración de Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carnets.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelo actualizado con todos los campos requeridos
class Aprendiz(db.Model):
    __tablename__ = 'aprendices'
    
    id = db.Column(db.Integer, primary_key=True)
    nis = db.Column(db.String(20), nullable=False, unique=True)
    primer_apellido = db.Column(db.String(100), nullable=False)
    segundo_apellido = db.Column(db.String(100), nullable=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo_documento = db.Column(db.String(20), nullable=False, default='CC')
    numero_documento = db.Column(db.String(20), nullable=False, unique=True)
    tipo_sangre = db.Column(db.String(5), nullable=False, default='O+')
    nombre_programa = db.Column(db.String(200), nullable=False)
    codigo_ficha = db.Column(db.String(20), nullable=False)
    centro_red_tecnologica = db.Column(db.String(200), nullable=False)
    fecha_finalizacion_programa = db.Column(db.Date, nullable=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)

def reset_database():
    # Eliminar base de datos existente si existe
    if os.path.exists('carnets.db'):
        os.remove('carnets.db')
        print("✅ Base de datos anterior eliminada")
    
    # Crear nueva base de datos
    with app.app_context():
        db.create_all()
        print("✅ Nueva base de datos creada exitosamente")
        
        # Agregar algunos datos de ejemplo
        ejemplos = [
            Aprendiz(
                nis="12345678901",
                primer_apellido="GRANADOS",
                segundo_apellido="CORONADO",
                nombre="VICTOR JAVIER",
                tipo_documento="CC",
                numero_documento="1113684867",
                tipo_sangre="B+",
                nombre_programa="Análisis y Desarrollo de Sistemas de Información",
                codigo_ficha="2024001",
                centro_red_tecnologica="Centro de Biotecnología Industrial",
                fecha_finalizacion_programa=date(2024, 12, 15)
            ),
            Aprendiz(
                nis="12345678902",
                primer_apellido="RODRIGUEZ",
                segundo_apellido="LOPEZ",
                nombre="MARIA ALEJANDRA",
                tipo_documento="CC",
                numero_documento="87654321",
                tipo_sangre="O+",
                nombre_programa="Biotecnología Industrial",
                codigo_ficha="2024002",
                centro_red_tecnologica="Centro de Biotecnología Industrial",
                fecha_finalizacion_programa=date(2025, 6, 30)
            ),
            Aprendiz(
                nis="12345678903",
                primer_apellido="MARTINEZ",
                segundo_apellido="SILVA",
                nombre="CARLOS ANDRES",
                tipo_documento="TI",
                numero_documento="11223344",
                tipo_sangre="A-",
                nombre_programa="Gestión Empresarial",
                codigo_ficha="2024003",
                centro_red_tecnologica="Centro de Biotecnología Industrial",
                fecha_finalizacion_programa=date(2024, 11, 20)
            )
        ]
        
        for aprendiz in ejemplos:
            db.session.add(aprendiz)
        
        db.session.commit()
        print("✅ Datos de ejemplo agregados")
        print(f"\n🎯 Se crearon {len(ejemplos)} aprendices de ejemplo")
        
        # Verificar que se crearon correctamente
        total = Aprendiz.query.count()
        print(f"📊 Total de aprendices en la base de datos: {total}")

if __name__ == '__main__':
    reset_database()
    print("\n🎉 ¡Listo! Ahora puedes ejecutar: python app.py")
    print("🔗 Ve a: http://localhost:5000")
    print("💡 Los botones de generar carnet ya deberían funcionar correctamente")
