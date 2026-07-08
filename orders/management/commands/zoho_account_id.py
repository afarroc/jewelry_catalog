"""
Comando para obtener el accountId de Zoho Mail necesario para enviar correos.
Uso:
    python manage.py zoho_account_id
"""
import requests
import os
from django.core.management.base import BaseCommand
from django.conf import settings

from orders.tasks import _get_zoho_access_token


class Command(BaseCommand):
    help = "Obtiene el accountId de Zoho Mail listando las cuentas del usuario autenticado."

    def handle(self, *args, **options):
        try:
            access_token = _get_zoho_access_token()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"No se pudo obtener el access token: {exc}"))
            return

        url = "https://mail.zoho.com/api/accounts"
        headers = {
            "Authorization": f"Zoho-oauthtoken {access_token}",
            "Accept": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Error al consultar cuentas de Zoho: {exc}"))
            return

        data = payload.get("data", [])
        if not data:
            self.stderr.write(self.style.WARNING("Zoho no devolvió cuentas asociadas al token."))
            return

        self.stdout.write("Cuentas encontradas:")
        for account in data:
            self.stdout.write(
                f"- accountId={account.get('accountId')} | email={account.get('primaryEmailAddress')} | zuid={account.get('zuid')}"
            )
