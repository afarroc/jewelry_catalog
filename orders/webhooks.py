from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import stripe
import logging

from orders.models import Order

logger = logging.getLogger(__name__)


@csrf_exempt
def stripe_webhook(request):
    """Handle Stripe webhooks."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        logger.error(f"Invalid webhook payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {str(e)}")
        return HttpResponse(status=400)

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        order_id = payment_intent.metadata.get('order_id')

        try:
            order = Order.objects.get(id=order_id)
            order.payment_status = True
            order.payment_date = timezone.now()
            order.save()
            logger.info(f"Payment succeeded for order {order.order_number}")
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found for payment intent {getattr(payment_intent, 'id', 'unknown')}")

    return HttpResponse(status=200)
