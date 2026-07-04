#!/usr/bin/env python
"""
Script para probar la conexión S3 con las credenciales actuales
Ejecuta: python test_s3_connection.py
"""
import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_s3_connection():
    print("🔗 Probando conexión S3...")
    print("=" * 50)

    # Obtener credenciales
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME', 'management360')
    region = os.getenv('AWS_S3_REGION_NAME', 'us-east-2')

    print(f"Access Key: {'***' + access_key[-4:] if access_key else 'None'}")
    print(f"Secret Key: {'***' + secret_key[-4:] if secret_key else 'None'}")
    print(f"Bucket: {bucket_name}")
    print(f"Region: {region}")
    print()

    if not access_key or not secret_key:
        print("❌ Credenciales faltantes")
        return False

    try:
        # Crear cliente S3
        print("🔌 Creando cliente S3...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

        # Probar conexión listando buckets
        print("📋 Listando buckets...")
        response = s3_client.list_buckets()

        buckets = [bucket['Name'] for bucket in response['Buckets']]
        print(f"✅ Buckets encontrados: {len(buckets)}")
        for bucket in buckets:
            print(f"   - {bucket}")

        # Verificar si nuestro bucket existe
        if bucket_name in buckets:
            print(f"✅ Bucket '{bucket_name}' encontrado")

            # Listar objetos en el bucket
            print(f"📁 Listando objetos en {bucket_name}...")
            try:
                objects_response = s3_client.list_objects_v2(Bucket=bucket_name, MaxKeys=10)
                objects = objects_response.get('Contents', [])

                if objects:
                    print(f"✅ Encontrados {len(objects)} objetos:")
                    for obj in objects[:5]:  # Mostrar primeros 5
                        print(f"   - {obj['Key']} ({obj['Size']} bytes)")
                    if len(objects) > 5:
                        print(f"   ... y {len(objects) - 5} más")
                else:
                    print("ℹ️  Bucket vacío")

            except ClientError as e:
                print(f"❌ Error listando objetos: {e}")

            # Probar subida de archivo de prueba
            print("⬆️  Probando subida de archivo...")
            test_content = b"Test file from diagnostic script"
            test_key = "diagnostic/test_connection.txt"

            try:
                s3_client.put_object(
                    Bucket=bucket_name,
                    Key=test_key,
                    Body=test_content,
                    ContentType='text/plain'
                )
                print("✅ Archivo de prueba subido exitosamente")

                # Limpiar archivo de prueba
                s3_client.delete_object(Bucket=bucket_name, Key=test_key)
                print("🗑️  Archivo de prueba eliminado")

            except ClientError as e:
                print(f"❌ Error en subida de prueba: {e}")

        else:
            print(f"❌ Bucket '{bucket_name}' no encontrado")
            print("Buckets disponibles:")
            for bucket in buckets:
                print(f"   - {bucket}")

        print("\n🎉 Conexión S3 exitosa!")
        return True

    except NoCredentialsError:
        print("❌ Error de credenciales: No se encontraron credenciales válidas")
        return False
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ Error de AWS ({error_code}): {error_message}")

        if error_code == 'InvalidAccessKeyId':
            print("💡 La Access Key ID no es válida")
        elif error_code == 'SignatureDoesNotMatch':
            print("💡 La Secret Access Key no es válida")
        elif error_code == 'AccessDenied':
            print("💡 Credenciales válidas pero sin permisos suficientes")
        elif error_code == 'NoSuchBucket':
            print("💡 El bucket no existe")

        return False
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        print(f"Tipo de error: {type(e).__name__}")
        return False

if __name__ == '__main__':
    success = test_s3_connection()
    if success:
        print("\n✅ S3 está configurado correctamente")
        print("El sistema debería funcionar con S3 en producción")
    else:
        print("\n❌ Problemas con la configuración de S3")
        print("Revisa las credenciales y permisos IAM")