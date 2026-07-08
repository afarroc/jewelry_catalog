#!/usr/bin/env python
"""
Script para crear usuario administrador de manera segura
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jewelry_catalog.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import User

def create_admin_user():
    """
    Crea usuario administrador si no existe
    """
    from accounts.models import User

    # Obtener credenciales de variables de entorno
    admin_user = os.getenv('ADMIN_USER')
    admin_email = os.getenv('ADMIN_EMAIL')
    admin_password = os.getenv('ADMIN_PASSWORD')

    if not all([admin_user, admin_email, admin_password]):
        print("ERROR: Faltan variables de entorno ADMIN_USER, ADMIN_EMAIL y/o ADMIN_PASSWORD.")
        print("Definelas en tu .env o en el entorno de ejecucion antes de correr este script.")
        sys.exit(1)

    # Verificar si el usuario ya existe
    if User.objects.filter(email=admin_email).exists():
        print(f"Usuario administrador '{admin_email}' ya existe")
        return

    # Crear usuario administrador
    try:
        user = User.objects.create_superuser(
            username=admin_user,
            email=admin_email,
            password=admin_password,
        )
        print(f"Usuario administrador creado exitosamente:")
        print(f"  Username: {admin_user}")
        print(f"  Email: {admin_email}")
        print(f"  Password: {admin_password}")
        print("IMPORTANTE: Cambia la contraseña después del primer login")

    except Exception as e:
        print(f"Error creando usuario administrador: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin_user()