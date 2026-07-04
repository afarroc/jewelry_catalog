#!/bin/bash
# Script de configuración para desarrollo local
# NO ejecuta collectstatic para desarrollo rápido

set -e

echo "Configurando entorno de desarrollo..."

# Instalar dependencias
echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar dependencias críticas
echo "Verificando dependencias..."
python -c "import django; print('Django OK')"
python -c "import pymysql; print('PyMySQL OK')"

# Configurar variables de entorno para desarrollo
echo "Configurando entorno de desarrollo..."
export DJANGO_SETTINGS_MODULE=jewelry_catalog.settings
export DEBUG=True
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Crear directorios necesarios
echo "Creando directorios..."
mkdir -p media

# Verificar configuración
echo "Verificando configuración de Django..."
python manage.py check

# Ejecutar migraciones
echo "Ejecutando migraciones..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Crear usuario administrador si no existe
echo "Verificando usuario administrador..."
python create_superuser.py

echo ""
echo "🎉 Entorno de desarrollo configurado!"
echo ""
echo "Para iniciar el servidor:"
echo "  python manage.py runserver"
echo ""
echo "Notas importantes:"
echo "• DEBUG=True (modo desarrollo)"
echo "• Archivos estáticos se sirven desde /static/"
echo "• No se ejecuta collectstatic (más rápido para desarrollo)"
echo "• Base de datos: MySQL local"