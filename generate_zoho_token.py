#!/usr/bin/env python
"""
Generador de Refresh Token de Zoho Mail para el flujo OAuth2.
Uso:
    python generate_zoho_token.py
"""
import os
import sys
import requests
from urllib.parse import urlencode

from dotenv import load_dotenv

load_dotenv()

ZOHO_AUTH_URL = "https://accounts.zoho.com/oauth/v2/auth"
ZOHO_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
REDIRECT_URI = "https://onrender.com"
SCOPES = "ZohoMail.messages.CREATE,ZohoMail.messages.UPDATE"

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")


def main():
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET:
        print(
            "ERROR: Faltan ZOHO_CLIENT_ID o ZOHO_CLIENT_SECRET en .env.\n"
            "Agrega esas variables y volve a ejecutar el script."
        )
        sys.exit(1)

    params = {
        "client_id": ZOHO_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
        "access_type": "offline",
    }
    auth_url = f"{ZOHO_AUTH_URL}?{urlencode(params)}"

    print("=" * 60)
    print("GENERADOR DE REFRESH TOKEN - ZOHO MAIL")
    print("=" * 60)
    print(f"Redirect URI registrada: {REDIRECT_URI}")
    print(f"Scopes: {SCOPES}")
    print()
    print("1. Abri esta URL en el navegador:")
    print(auth_url)
    print()
    print("2. Aceptá los permisos en la consola de Zoho.")
    print("3. Cuando Zoho redirija a:", REDIRECT_URI)
    print("   copiá la URL completa de la barra de direcciones del navegador.")
    print()

    raw_input = input("Pegá acá la URL de redirección o solo el 'code' y presioná Enter: ").strip()
    if not raw_input:
        print("No ingresaste nada. Abortando.")
        sys.exit(1)

    if raw_input.startswith("http"):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(raw_input)
        query = parse_qs(parsed.query)
        code = query.get("code", [""])[0]
        if not code:
            print("La URL pegada no contiene el parámetro 'code'.")
            print("Verificá haber autorizado correctamente en Zoho.")
            sys.exit(1)
        print("Código extraído de la URL correctamente.")
    else:
        code = raw_input

    print()
    print(f"Código a usar: {code}")

    print()
    print("Intercambiando código por refresh token...")
    try:
        response = requests.post(
            ZOHO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "client_id": ZOHO_CLIENT_ID,
                "client_secret": ZOHO_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code,
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        print(f"ERROR en la solicitud a Zoho: {exc}")
        if hasattr(exc, "response") and exc.response is not None:
            print(exc.response.text)
        sys.exit(1)

    refresh_token = payload.get("refresh_token")
    if not refresh_token:
        print("ERROR: Zoho no devolvió refresh_token.")
        print("Respuesta:", payload)
        sys.exit(1)

    print()
    print("=" * 60)
    print("REFRESH TOKEN GENERADO")
    print("=" * 60)
    print(refresh_token)
    print()
    print("Agregá esta variable en Render Environment y en tu .env local:")
    print(f"ZOHO_REFRESH_TOKEN={refresh_token}")
    print()
    print("Variables adicionales que necesitas configurar:")
    print("- ZOHO_CLIENT_ID")
    print("- ZOHO_CLIENT_SECRET")
    print("- ZOHO_SENDER_EMAIL")
    print("- ZOHO_ACCOUNT_ID")


if __name__ == "__main__":
    main()
