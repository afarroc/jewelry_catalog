#!/bin/bash
# Script de construcción para Render

set -e  # Salir si hay algún error

echo "Iniciando construcción de la aplicación..."

# Instalar dependencias
echo "Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# Verificar instalación de dependencias críticas
echo "Verificando dependencias críticas..."
python3 -c "import django; print('Django OK')"
python3 -c "import gunicorn; print('Gunicorn OK')"
python3 -c "import whitenoise; print('WhiteNoise OK')"

# Crear directorios necesarios
echo "Creando directorios necesarios..."
mkdir -p staticfiles media logs

# Configurar variables de entorno
echo "Configurando variables de entorno..."
export DJANGO_SETTINGS_MODULE=jewelry_catalog.settings
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Verificar configuración de Django
echo "Verificando configuración de Django..."
python3 manage.py check --deploy

# Ejecutar migraciones
echo "Ejecutando migraciones de base de datos..."
python3 manage.py makemigrations --noinput
python3 manage.py migrate --noinput

# Recolectar archivos estáticos (FORZAR en producción)
echo "Procesando archivos estáticos..."
echo "DEBUG variable: '$DEBUG'"
echo "Current working directory: $(pwd)"
echo "Python path: $PYTHONPATH"
echo "Django settings module: $DJANGO_SETTINGS_MODULE"

# FORZAR ejecución de collectstatic en Render (producción)
echo "🔧 FORZANDO ejecución de collectstatic en producción..."
echo "✅ Ejecutando collectstatic con compresión..."

# Verificar que el directorio static existe y tiene archivos
if [ -d "static" ]; then
    STATIC_SOURCE_COUNT=$(find static -type f | wc -l)
    echo "Directorio static encontrado con $STATIC_SOURCE_COUNT archivos"

    # Mostrar archivos encontrados
    echo "Archivos estáticos encontrados:"
    find static -type f -name "*.css" | head -5 | sed 's/^/  CSS: /'
    find static -type f -name "*.js" | head -5 | sed 's/^/  JS: /'
    find static -type f -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" -o -name "*.svg" | head -5 | sed 's/^/  IMG: /'
else
    echo "❌ Error: Directorio static no encontrado"
    echo "Asegúrate de que los archivos estáticos estén en el directorio 'static/'"
    exit 1
fi

# Crear directorio staticfiles si no existe
mkdir -p staticfiles

# Ejecutar collectstatic con opciones optimizadas
echo "Ejecutando collectstatic..."
echo "Comando: python3 manage.py collectstatic --noinput --clear --verbosity=1"

# Limpiar staticfiles completamente antes de collectstatic para forzar copia de banners
echo "🧹 Limpiando staticfiles completamente..."
echo "Contenido antes de limpiar:"
ls -la staticfiles/ 2>/dev/null || echo "staticfiles no existe o está vacío"

# Forzar eliminación completa
rm -rf staticfiles
mkdir -p staticfiles

echo "Contenido después de limpiar:"
ls -la staticfiles/

python3 manage.py collectstatic --noinput --verbosity=1

# Verificar el código de salida de collectstatic
COLLECTSTATIC_EXIT_CODE=$?
echo "Collectstatic exit code: $COLLECTSTATIC_EXIT_CODE"

# Verificar inmediatamente qué se copió
echo "Contenido de staticfiles inmediatamente después de collectstatic:"
find staticfiles -name "*.jpg" -o -name "banner*" | head -10

    # Verificar resultado
    if [ -d "staticfiles" ]; then
        STATIC_COUNT=$(find staticfiles -type f | wc -l)
        STATIC_SIZE=$(du -sh staticfiles 2>/dev/null | cut -f1)
        echo "✅ Collectstatic completado exitosamente"
        echo "📁 Archivos estáticos procesados: $STATIC_COUNT archivos"
        echo "📏 Tamaño total: ${STATIC_SIZE:-desconocido}"
        echo "📍 Ubicación: $(pwd)/staticfiles"

        # Verificar que se crearon los archivos principales
        if [ -f "staticfiles/admin/css/base.css" ]; then
            echo "✅ Archivos de Django Admin incluidos"
        fi

        if [ -d "staticfiles/css" ] && [ -d "staticfiles/js" ]; then
            echo "✅ Archivos CSS y JS del proyecto incluidos"
        fi

        # Verificar banners específicamente
        if [ -d "staticfiles/images/banners" ]; then
            BANNER_COUNT=$(find staticfiles/images/banners -type f | wc -l)
            echo "✅ Banners encontrados: $BANNER_COUNT archivos"
            ls -la staticfiles/images/banners/
        else
            echo "❌ ERROR: Directorio de banners no encontrado en staticfiles"
        fi

        # Mostrar archivos generados
        echo "Archivos generados en staticfiles:"
        find staticfiles -name "*.css" | wc -l | sed 's/^/  CSS: /'
        find staticfiles -name "*.js" | wc -l | sed 's/^/  JS: /'
        find staticfiles -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.gif" -o -name "*.svg" \) | wc -l | sed 's/^/  Imágenes: /'

        # Listar estructura de staticfiles
        echo "Estructura de staticfiles:"
        find staticfiles -type d | head -10

        # Verificar permisos
        echo "Permisos del directorio staticfiles:"
        ls -la staticfiles/

        # Verificación FINAL de banners
        echo "🔍 VERIFICACIÓN FINAL DE BANNERS:"
        if [ -d "staticfiles/images/banners" ]; then
            BANNER_FINAL_COUNT=$(find staticfiles/images/banners -type f | wc -l)
            echo "✅ Banners en staticfiles: $BANNER_FINAL_COUNT archivos"
            ls -la staticfiles/images/banners/

            # Verificar archivos específicos
            if [ -f "staticfiles/images/banners/banner.jpg" ]; then
                echo "✅ banner.jpg: COPIADO correctamente"
            else
                echo "❌ banner.jpg: NO se copió"
            fi

            if [ -f "staticfiles/images/banners/banner1.jpg" ]; then
                echo "✅ banner1.jpg: COPIADO correctamente"
            else
                echo "❌ banner1.jpg: NO se copió"
            fi
        else
            echo "❌ ERROR CRÍTICO: Directorio de banners NO existe en staticfiles"
            echo "Esto causará que los banners no se carguen en producción"
        fi

    else
        echo "❌ Error: Directorio staticfiles no creado"
        echo "Revisa la configuración de STATIC_ROOT en settings.py"
        exit 1
    fi

echo "✅ Collectstatic completado - archivos estáticos listos para producción"
echo "🎯 Los banners deberían cargar correctamente ahora"

# Crear usuario administrador
echo "Creando usuario administrador..."
python3 scripts/admin/create_superuser.py

echo "Construcción completada exitosamente!"