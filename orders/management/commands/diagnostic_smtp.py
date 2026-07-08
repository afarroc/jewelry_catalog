"""
Diagnóstico de SMTP para producción.
Uso:
    python manage.py diagnostic_smtp
"""
import sys
import smtplib
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Diagnóstico de SMTP: muestra configuración y prueba envío real."

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("DIAGNÓSTICO SMTP")
        self.stdout.write("=" * 60)

        backend = getattr(settings, 'EMAIL_BACKEND', 'NOT SET')
        host = getattr(settings, 'EMAIL_HOST', 'NOT SET')
        port = getattr(settings, 'EMAIL_PORT', 'NOT SET')
        use_tls = getattr(settings, 'EMAIL_USE_TLS', 'NOT SET')
        user = getattr(settings, 'EMAIL_HOST_USER', 'NOT SET')
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'NOT SET')

        self.stdout.write(f"EMAIL_BACKEND : {backend}")
        self.stdout.write(f"EMAIL_HOST     : {host}")
        self.stdout.write(f"EMAIL_PORT     : {port}")
        self.stdout.write(f"EMAIL_USE_TLS  : {use_tls}")
        self.stdout.write(f"EMAIL_HOST_USER: {user}")
        self.stdout.write(f"DEFAULT_FROM   : {default_from}")
        self.stdout.write("-" * 60)

        if backend == 'django.core.mail.backends.console.EmailBackend':
            self.stdout.write(
                self.style.WARNING(
                    "BACKEND ES CONSOLE: no se enviará correo real. "
                    "Verifica EMAIL_BACKEND en variables de entorno."
                )
            )
            logger.error("DIAGNOSTIC_SMTP: backend es console.EmailBackend, no se enviará correo real.")
            sys.exit(1)

        if not host or not user:
            self.stdout.write(
                self.style.ERROR(
                    f"Faltan variables críticas: host={host}, user={user}"
                )
            )
            logger.error(f"DIAGNOSTIC_SMTP: faltan variables EMAIL_HOST={host} o EMAIL_HOST_USER={user}")
            sys.exit(1)

        self.stdout.write("Probando conexión SMTP...")
        try:
            server = smtplib.SMTP(host, port, timeout=10)
            server.ehlo()
            if use_tls:
                server.starttls()
                server.ehlo()
            server.login(user, "***")
            self.stdout.write(self.style.SUCCESS("Login SMTP exitoso."))
            logger.info("DIAGNOSTIC_SMTP: login SMTP exitoso.")
            server.quit()
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error de conexión/login SMTP: {exc}"))
            logger.error("DIAGNOSTIC_SMTP: error de conexión/login SMTP.", exc_info=True)
            sys.exit(1)

        self.stdout.write("Enviando correo de prueba...")
        subject = "[DIAGNÓSTICO SMTP] Prueba de envío"
        message = (
            "Este es un correo de diagnóstico generado automáticamente "
            "desde jewelry_catalog para verificar la entrega."
        )
        try:
            sent = send_mail(
                subject=subject,
                message=message,
                from_email=default_from,
                recipient_list=[default_from],
                fail_silently=False,
            )
            if sent >= 1:
                self.stdout.write(self.style.SUCCESS(f"Correo enviado correctamente (sent={sent})."))
                logger.info(f"DIAGNOSTIC_SMTP: correo enviado correctamente (sent={sent}).")
            else:
                self.stdout.write(self.style.WARNING(f"send_mail retornó sent={sent}"))
                logger.warning(f"DIAGNOSTIC_SMTP: send_mail retornó sent={sent}.")
        except Exception as exc:
            self.stdout.write(self.style.ERROR(f"Error al enviar correo: {exc}"))
            logger.error("DIAGNOSTIC_SMTP: error al enviar correo.", exc_info=True)
            sys.exit(1)

        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("DIAGNÓSTICO SMTP FINALIZADO"))
        self.stdout.write("=" * 60)
