from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_task(self, order_id):
    from orders.models import Order
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for confirmation email")
        return

    subject = f"Confirmación de pedido #{order.order_number}"
    context = {'order': order, 'site_url': settings.SITE_URL}

    text_message = render_to_string('orders/emails/order_confirmation_editorial.txt', context)
    html_message = render_to_string('orders/emails/order_confirmation_editorial.html', context)

    try:
        send_mail(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            html_message=html_message,
        )
        logger.info(f"Confirmation email sent for order {order.order_number}")
    except Exception as exc:
        logger.error(
            f"Failed to send confirmation email for order {order.order_number}: {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_cancellation_task(self, order_id):
    from orders.models import Order
    try:
        order = Order.objects.get(pk=order_id)
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found for cancellation email")
        return

    subject = f"Pedido cancelado #{order.order_number}"
    context = {'order': order, 'site_url': settings.SITE_URL}

    text_message = render_to_string('orders/emails/order_cancellation_editorial.txt', context)
    html_message = render_to_string('orders/emails/order_cancellation_editorial.html', context)

    try:
        send_mail(
            subject,
            text_message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            html_message=html_message,
        )
        logger.info(f"Cancellation email sent for order {order.order_number}")
    except Exception as exc:
        logger.error(
            f"Failed to send cancellation email for order {order.order_number}: {exc}",
            exc_info=True,
        )
        raise self.retry(exc=exc)
