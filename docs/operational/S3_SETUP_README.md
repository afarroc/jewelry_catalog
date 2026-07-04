# Configuración de S3 para Producción

## Problema Identificado
Las imágenes se están guardando en la base de datos pero **NO se están subiendo físicamente a S3** en producción.

## Solución Implementada

### 1. Variables de Entorno Requeridas
Configure las siguientes variables en **Render.com** (Environment Settings):

```bash
# Credenciales de AWS
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_STORAGE_BUCKET_NAME=management360
AWS_S3_REGION_NAME=us-east-2
```

### 2. Verificación de Configuración
Una vez configuradas las variables, acceda a:
```
https://your-domain.com/products/diagnostic/s3/
```

Esta página ejecutará pruebas automáticas para verificar:
- ✅ Variables de entorno configuradas
- ✅ Conectividad con S3
- ✅ Permisos de subida/descarga
- ✅ URLs de archivos generadas correctamente

### 3. Política del Bucket S3
Asegúrese de que su bucket `management360` tenga esta política:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::YOUR_ACCOUNT_ID:user/catalogo"
            },
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::management360",
                "arn:aws:s3:::management360/*"
            ]
        }
    ]
}
```

### 4. Permisos del Usuario IAM
El usuario IAM debe tener estos permisos:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::management360",
                "arn:aws:s3:::management360/*"
            ]
        }
    ]
}
```

### 5. Configuración CORS del Bucket
El bucket debe tener esta configuración CORS:

```json
[
    {
        "AllowedHeaders": ["*"],
        "AllowedMethods": ["GET", "PUT", "POST", "DELETE"],
        "AllowedOrigins": ["*"],
        "ExposeHeaders": []
    }
]
```

## Diagnóstico y Solución de Problemas

### Ejecutar Diagnóstico
1. Acceda a: `https://your-domain.com/products/diagnostic/s3/`
2. Revise los resultados de cada prueba
3. Corrija cualquier error identificado

### Logs de Debug
Los logs detallados se muestran en la consola de Render:
```
[S3] Configuring S3 storage with bucket: management360
[S3] AWS_ACCESS_KEY_ID configured: Yes
[S3] AWS_SECRET_ACCESS_KEY configured: Yes
[SUCCESS] Image uploaded successfully: ID=1, Title='test', File='uploads/2025/09/13/test.jpg', Size=12345 bytes
```

### Errores Comunes

#### ❌ "Access Denied" al acceder a archivos
**Solución:** Verificar política del bucket y permisos del usuario IAM

#### ❌ "No credentials found" en logs
**Solución:** Verificar que las variables de entorno estén configuradas en Render

#### ❌ "Invalid bucket name" en logs
**Solución:** Verificar que `AWS_STORAGE_BUCKET_NAME=management360`

#### ❌ Archivos se guardan en BD pero no en S3
**Solución:** Verificar conectividad S3 y permisos de escritura

## Estructura de Carpetas en S3

### Carpetas Automáticas
**NO es necesario crear carpetas manualmente en S3.** Django las crea automáticamente:

#### Para Productos (`upload_to='products/'`):
```
management360/
└── products/
    ├── imagen1.jpg
    ├── imagen2.png
    └── imagen3.gif
```

#### Para Imágenes Simples (`upload_to='uploads/%Y/%m/%d/'`):
```
management360/
└── uploads/
    ├── 2025/
    │   ├── 09/
    │   │   ├── 13/
    │   │   │   ├── imagen1.jpg
    │   │   │   └── imagen2.png
    │   │   └── 14/
    │   │       └── imagen3.gif
    │   └── 10/
    │       └── 01/
    │           └── imagen4.jpg
```

### Verificación de Carpetas
Ejecutar el script de diagnóstico:
```bash
python scripts/dev/test/test_s3.py
```

O acceder a la página de diagnóstico:
```
https://your-domain.com/products/diagnostic/s3/
```

## URLs de Acceso

### Desarrollo (Filesystem)
```
http://localhost:8000/media/uploads/2025/09/13/imagen.jpg
```

### Producción (S3)
```
https://management360.s3.amazonaws.com/uploads/2025/09/13/imagen.jpg
```

## Comandos de Verificación

### Ejecutar script de prueba localmente:
```bash
python test_s3.py
```

### Verificar configuración de Django:
```bash
python manage.py shell
from django.core.files.storage import default_storage
print(default_storage.__class__.__name__)
print(default_storage.bucket_name)
```

## Próximos Pasos

1. ✅ Configurar variables de entorno en Render
2. ✅ Ejecutar diagnóstico S3
3. ✅ Verificar que las imágenes se suban correctamente
4. ✅ Probar eliminación de archivos
5. ✅ Verificar URLs públicas de imágenes

## Contacto
Si persisten los problemas, revise los logs de Render y la configuración de AWS IAM.