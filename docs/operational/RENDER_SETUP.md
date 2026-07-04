# 🚀 Configuración de Render para S3

## Problema Actual
El diagnóstico muestra que el sistema está usando **FileSystemStorage** (almacenamiento local) en lugar de **S3Boto3Storage** (S3).

## ✅ Solución: Configurar Variables de Entorno

### Paso 1: Verificar Variables Actuales
Ejecuta este comando para ver el estado actual:
```bash
python test_env.py
```

### Paso 2: Configurar Variables en Render

#### Opción A: Dashboard de Render (Recomendado)
1. Ve a [dashboard.render.com](https://dashboard.render.com)
2. Selecciona tu servicio **jewelry-catalog**
3. Ve a la pestaña **"Environment"**
4. Haz clic en **"Add Environment Variable"**
5. Agrega estas variables:

```
AWS_ACCESS_KEY_ID = tu_access_key_aqui
AWS_SECRET_ACCESS_KEY = tu_secret_key_aqui
AWS_STORAGE_BUCKET_NAME = management360
AWS_S3_REGION_NAME = us-east-2
```

#### Opción B: Render CLI
```bash
# Instalar Render CLI si no lo tienes
npm install -g render-cli

# Configurar variables
render env set AWS_ACCESS_KEY_ID tu_access_key_aqui
render env set AWS_SECRET_ACCESS_KEY tu_secret_key_aqui
render env set AWS_STORAGE_BUCKET_NAME management360
render env set AWS_S3_REGION_NAME us-east-2
```

### Paso 3: Redeploy
Después de configurar las variables:
1. Ve al dashboard de Render
2. Selecciona tu servicio
3. Haz clic en **"Manual Deploy"** → **"Deploy latest commit"**

### Paso 4: Verificar Configuración
Después del redeploy:
1. Ve a `/products/diagnostic/s3/`
2. Deberías ver:
   - ✅ **Storage Type:** `S3Boto3Storage`
   - ✅ **Bucket:** `management360`
   - ✅ **Todas las pruebas en verde**

## 🔍 Logs de Verificación

### En Desarrollo (Local)
```bash
python manage.py runserver
# Busca logs que empiecen con [S3]
```

### En Producción (Render)
```bash
# En el dashboard → Service → Logs
# O usando CLI:
render logs --app jewelry-catalog-kpoy
```

### Logs Esperados Después de la Configuración:
```
[S3] === S3 CONFIGURATION CHECK ===
[S3] AWS_ACCESS_KEY_ID: 'AKIA...' (length: 20)
[S3] AWS_SECRET_ACCESS_KEY: '***wxyz' (length: 40)
[S3] AWS_STORAGE_BUCKET_NAME: 'management360'
[S3] AWS_S3_REGION_NAME: 'us-east-2'
[S3] ✅ All credentials present - configuring S3 storage
[S3] ✅ S3 storage configured successfully
[S3] Media URL: https://management360.s3.amazonaws.com/
```

## 🐛 Troubleshooting

### ❌ **Problema Detectado: Política IAM Vacía**

La política del grupo de usuario IAM está **completamente vacía**:
```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "Statement1",
			"Effect": "Allow",
			"Action": [],      // <- VACÍO
			"Resource": []     // <- VACÍO
		}
	]
}
```

### ✅ **Solución: Actualizar Política IAM**

#### **Paso 1: Ir a AWS IAM Console**
1. Ve a [console.aws.amazon.com/iam](https://console.aws.amazon.com/iam)
2. Ve a **"Groups"**
3. Selecciona el grupo del usuario
4. Ve a **"Permissions"** → **"Inline policies"**
5. Edita o crea una nueva política inline

#### **Paso 2: Política Correcta para S3**
Reemplaza la política vacía con esta:

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

#### **Paso 3: Verificar en AWS**
Después de actualizar la política:
1. Ve a **"Users"** → selecciona tu usuario
2. Ve a **"Permissions"**
3. Deberías ver los permisos S3 listados

### 🔄 **Después de Corregir IAM**

1. **Configura variables en Render** (como indiqué antes)
2. **Redeploy** el servicio
3. **Verifica** que aparezca en logs:
   ```
   [S3] ✅ All credentials present - configuring S3 storage
   [S3] ✅ S3 storage configured successfully
   ```

### 📋 **Verificación de Permisos IAM**

#### **Permisos Requeridos:**
- ✅ `s3:GetObject` - Leer archivos
- ✅ `s3:PutObject` - Subir archivos
- ✅ `s3:DeleteObject` - Eliminar archivos
- ✅ `s3:ListBucket` - Listar contenido del bucket

#### **Recursos Específicos:**
- ✅ `arn:aws:s3:::management360` - El bucket
- ✅ `arn:aws:s3:::management360/*` - Todos los archivos dentro del bucket

### 🚨 **Si Sigue Sin Funcionar:**

1. **Verifica que la política se aplicó:**
   ```bash
   # En AWS CLI (si lo tienes instalado)
   aws sts get-caller-identity
   aws s3 ls s3://management360/
   ```

2. **Revisa los logs de Render:**
   ```
   [S3] ❌ Error message from AWS
   ```

3. **Verifica región del bucket:**
   - El bucket debe estar en `us-east-2`
   - Las credenciales deben ser para la misma región

### Si Hay Errores de Conexión S3:
1. **Verifica credenciales de AWS:**
   - Access Key debe ser válida
   - Secret Key debe ser correcta
   - Usuario IAM debe tener permisos para el bucket

2. **Verifica bucket:**
   - Bucket `management360` debe existir
   - Región debe ser `us-east-2`
   - Política del bucket debe permitir acceso

## 📋 Checklist Final

- [ ] Variables de entorno configuradas en Render
- [ ] Redeploy completado
- [ ] Diagnóstico muestra S3Boto3Storage
- [ ] Subida de imágenes funciona
- [ ] URLs de imágenes apuntan a S3
- [ ] Logs muestran configuración correcta

## 🎯 Resultado Esperado

Después de la configuración correcta:
- ✅ **Storage:** S3Boto3Storage
- ✅ **URLs:** `https://management360.s3.amazonaws.com/...`
- ✅ **Archivos:** Se guardan en S3
- ✅ **Acceso:** Público (con política correcta del bucket)

¡El sistema estará completamente configurado para producción con S3!