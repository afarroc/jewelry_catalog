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
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@jewelrycatalog.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

    # Verificar si el usuario ya existe
    if User.objects.filter(email=admin_email).exists():
        print(f"Usuario administrador '{admin_email}' ya existe")
        return

    # Crear usuario administrador
    try:
        # Para el modelo personalizado, necesitamos crear el usuario manualmente
        # ya que create_superuser espera username pero nuestro modelo usa email
        user = User.objects.create_user(
            username=admin_email,  # Usar email como username
            email=admin_email,
            password=admin_password,
            is_staff=True,
            is_superuser=True
        )
        print(f"Usuario administrador creado exitosamente:")
        print(f"  Email: {admin_email}")
        print(f"  Username: {admin_email}")
        print(f"  Password: {admin_password}")
        print("IMPORTANTE: Cambia la contraseña después del primer login")

    except Exception as e:
        print(f"Error creando usuario administrador: {e}")
        sys.exit(1)

if __name__ == '__main__':
    create_admin_user()