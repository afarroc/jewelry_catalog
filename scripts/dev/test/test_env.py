#!/usr/bin/env python
"""
Script para verificar las variables de entorno de AWS en Render
Ejecuta: python test_env.py
"""
import os

def check_aws_env():
    print("🔍 Verificando variables de entorno AWS...")
    print("=" * 50)

    # Variables requeridas
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_STORAGE_BUCKET_NAME',
        'AWS_S3_REGION_NAME'
    ]

    all_present = True

    for var in required_vars:
        value = os.getenv(var)
        if value:
            if 'SECRET' in var:
                # No mostrar el valor completo de la secret key
                display_value = f"***{value[-4:]}" if len(value) > 4 else "***"
            else:
                display_value = value

            print(f"✅ {var}: {display_value} (length: {len(value)})")
        else:
            print(f"❌ {var}: NOT SET")
            all_present = False

    print("=" * 50)

    if all_present:
        print("🎉 Todas las variables de AWS están configuradas correctamente!")
        print("El sistema debería usar S3 para almacenar archivos.")
    else:
        print("⚠️  Faltan variables de entorno de AWS.")
        print("El sistema usará almacenamiento local como fallback.")
        print("\nPara configurar S3:")
        print("1. Ve al dashboard de Render")
        print("2. Selecciona tu servicio")
        print("3. Ve a Environment")
        print("4. Agrega las variables faltantes")

    # Información adicional
    print("\n📋 Información del entorno:")
    print(f"Python path: {os.sys.executable}")
    print(f"Current directory: {os.getcwd()}")

    # Verificar si estamos en Render
    render_env = os.getenv('RENDER')
    if render_env:
        print(f"Render environment: {render_env}")
    else:
        print("Not running on Render (development environment)")

if __name__ == '__main__':
    check_aws_env()