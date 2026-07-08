#!/usr/bin/env python
"""
Generador de Refresh Token de Zoho Mail para el flujo OAuth2.
Uso:
    python generate_zoho_token.py
"""
import os
import sys
import socket
import threading
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs

import requests
from dotenv import load_dotenv

load_dotenv()

ZOHO_AUTH_URL = "https://accounts.zoho.com/oauth/v2/auth"
ZOHO_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
REDIRECT_URI = "http://localhost:8080/callback"
SCOPES = "ZohoMail.messages.CREATE,ZohoMail.messages.UPDATE,ZohoMail.accounts.READ"

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")


class _CallbackHandler(BaseHTTPRequestHandler):
    server_code = None

    def do_GET(self):
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        _CallbackHandler.server_code = query.get("code", [""])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Token capture completed</h1><p>You can close this tab.</p></body></html>"
        )

    def log_message(self, format, *args):
        pass


def _wait_for_code(port=8080, timeout=120):
    server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    print(f"Esperando autorizacion en http://127.0.0.1:{port}/callback ...")
    deadline = time.time() + timeout
    while _CallbackHandler.server_code is None and time.time() < deadline:
        time.sleep(0.5)

    server.shutdown()
    return _CallbackHandler.server_code


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
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Scopes: {SCOPES}")
    print()
    print("Antes de continuar, confirmar en Zoho:")
    print("  Authorized Redirect URIs:")
    print(f"  {REDIRECT_URI}")
    print()
    input("Presiona Enter para abrir el navegador...")
    webbrowser.open(auth_url)

    code = _wait_for_code()
    if not code:
        print("No se capturo el codigo de autorizacion. Abortando.")
        sys.exit(1)

    print()
    print("Intercambiando codigo por refresh token...")
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
        print("ERROR: Zoho no devolvio refresh_token.")
        print("Respuesta:", payload)
        sys.exit(1)

    print()
    print("=" * 60)
    print("REFRESH TOKEN GENERADO")
    print("=" * 60)
    print(refresh_token)
    print()
    print("Agregar en Render Environment y en tu .env local:")
    print(f"ZOHO_REFRESH_TOKEN={refresh_token}")
    print()
    print("Verificar tambien:")
    print("- ZOHO_CLIENT_ID")
    print("- ZOHO_CLIENT_SECRET")
    print("- ZOHO_SENDER_EMAIL")
    print("- ZOHO_ACCOUNT_ID")


if __name__ == "__main__":
    main()
