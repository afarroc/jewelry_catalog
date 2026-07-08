from django.template.loader import render_to_string
from django.conf import settings
import requests
import os
import logging

logger = logging.getLogger(__name__)

ZOHO_TOKEN_URL = "https://accounts.zoho.com/oauth/v2/token"
ZOHO_MAIL_URL = "https://mail.zoho.com/api/accounts/{account_id}/messages"

ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN")
ZOHO_SENDER_EMAIL = os.getenv("ZOHO_SENDER_EMAIL")
ZOHO_ACCOUNT_ID = os.getenv("ZOHO_ACCOUNT_ID") or os.getenv("ZOHO_USER_ID")


def _get_zoho_access_token():
    if not all([ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET, ZOHO_REFRESH_TOKEN]):
        raise RuntimeError("Faltan variables de entorno de Zoho: ZOHO_CLIENT_ID, ZOHO_CLIENT_SECRET o ZOHO_REFRESH_TOKEN")
    response = requests.post(
        ZOHO_TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "client_id": ZOHO_CLIENT_ID,
            "client_secret": ZOHO_CLIENT_SECRET,
            "refresh_token": ZOHO_REFRESH_TOKEN,
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    access_token = payload.get("access_token")
    if not access_token:
        raise RuntimeError(f"Zoho no devolvió access_token: {payload}")
    return access_token


def _send_zoho_mail(to_email, subject, html_content, text_content):
    if not all([ZOHO_SENDER_EMAIL, ZOHO_ACCOUNT_ID]):
        raise RuntimeError("Faltan variables de entorno de Zoho: ZOHO_SENDER_EMAIL o ZOHO_ACCOUNT_ID")

    access_token = _get_zoho_access_token()
    url = ZOHO_MAIL_URL.format(account_id=ZOHO_ACCOUNT_ID)
    headers = {
        "Authorization": f"Zoho-oauthtoken {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "fromAddress": ZOHO_SENDER_EMAIL,
        "toAddress": to_email,
        "subject": subject,
        "content": html_content,
        "mailFormat": "html",
    }
    if text_content:
        payload["content"] = html_content
    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def _send_order_confirmation_email(order_id):
    from orders.models import Order
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for confirmation email")
        return

    subject = f"Confirmación de pedido #{order.order_number}"
    context = {'order': order, 'site_url': settings.SITE_URL}

    html_message = render_to_string('orders/emails/order_confirmation_editorial.html', context)
    text_message = render_to_string('orders/emails/order_confirmation_editorial.txt', context)

    try:
        r = _send_zoho_mail(order.user.email, subject, html_message, text_message)
        logger.info(f"Confirmation email sent for order {order.order_number}: {r}")
    except Exception as exc:
        logger.error(
            f"Failed to send confirmation email for order {order.order_number}: {exc}",
            exc_info=True,
        )
        raise


def _send_order_cancellation_email(order_id):
    from orders.models import Order
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for cancellation email")
        return

    subject = f"Pedido cancelado #{order.order_number}"
    context = {'order': order, 'site_url': settings.SITE_URL}

    html_message = render_to_string('orders/emails/order_cancellation_editorial.html', context)
    text_message = render_to_string('orders/emails/order_cancellation_editorial.txt', context)

    try:
        r = _send_zoho_mail(order.user.email, subject, html_message, text_message)
        logger.info(f"Cancellation email sent for order {order.order_number}: {r}")
    except Exception as exc:
        logger.error(
            f"Failed to send cancellation email for order {order.order_number}: {exc}",
            exc_info=True,
        )
        raise
