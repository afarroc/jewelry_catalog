from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, DetailView, ListView
from django.conf import settings
from decimal import Decimal
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from cart.models import Cart, CartItem
from .models import Order, OrderItem
from .forms import CheckoutForm
from .serializers import (
    OrderSerializer, OrderListSerializer,
    OrderCreateSerializer, OrderItemSerializer
)
from django.views.decorators.http import require_POST
import logging
import stripe

logger = logging.getLogger('orders')
api_logger = logging.getLogger('api')

# Constants
DEFAULT_SHIPPING_COST = Decimal('5.00')
TAX_RATE = Decimal('0.08')  # 8%
stripe.api_key = settings.STRIPE_SECRET_KEY
def checkout(request):
    """Handle the checkout process and order creation."""
    from cart.cart import CartSession

    # Get cart for authenticated or anonymous users
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            logger.info(f"Cart found with {cart.total_items} items (ID: {cart.id})")
        except Cart.DoesNotExist:
            logger.warning(f"No cart found for user {request.user.id}")
            messages.error(request, "Your shopping cart was not found")
            return redirect('home:index')
    else:
        cart = CartSession(request)
        logger.info(f"Session cart found with {cart.total_items} items")

    if cart.total_items == 0:
        logger.warning("Empty cart detected during checkout")
        messages.warning(request, "Your cart is empty")
        return redirect('cart:cart_detail')

    # For anonymous users, require login before checkout
    if not request.user.is_authenticated:
        messages.info(request, "Please log in or create an account to complete your purchase.")
        return redirect(f"{settings.LOGIN_URL}?next={request.path}")

    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        
        if form.is_valid():
            if not request.POST.get('agree_terms'):
                messages.error(request, "You must accept the terms and conditions")
                return redirect('orders:checkout')

            try:
                with transaction.atomic():
                    # Create and validate order
                    order = form.save(commit=False)
                    order.user = request.user
                    order.subtotal = cart.subtotal
                    order.shipping_cost = DEFAULT_SHIPPING_COST
                    order.tax = (cart.subtotal * TAX_RATE).quantize(Decimal('0.01'))
                    order.total = (order.subtotal + order.shipping_cost + order.tax).quantize(Decimal('0.01'))

                    # Validate payment method
                    payment_method = form.cleaned_data.get('payment_method')
                    if payment_method not in dict(Order.PAYMENT_CHOICES).keys():
                        raise ValueError("Invalid payment method selected")

                    order.save()

                    # Create order items - handle both cart types
                    if hasattr(cart, 'items'):  # Database cart
                        for cart_item in cart.items.all():
                            OrderItem.objects.create(
                                order=order,
                                product=cart_item.product,
                                quantity=cart_item.quantity,
                                price=cart_item.product.price
                            )
                    else:  # Session cart
                        for item in cart:
                            OrderItem.objects.create(
                                order=order,
                                product=item['product'],
                                quantity=item['quantity'],
                                price=item['product'].price
                            )

                    # Process payment based on selected method
                    if payment_method == 'credit_card':
                        try:
                            intent = stripe.PaymentIntent.create(
                                amount=int(order.total * 100),
                                currency='usd',
                                metadata={
                                    'order_id': order.id,
                                    'user_id': request.user.id,
                                    'payment_method': payment_method
                                },
                                description=f"Order #{order.order_number}"
                            )
                            
                            if settings.DEBUG:
                                stripe.PaymentIntent.confirm(
                                    intent.id,
                                    payment_method='pm_card_visa'
                                )
                            
                            order.payment_status = True
                            order.payment_date = timezone.now()
                            order.save()
                            
                        except stripe.error.StripeError as e:
                            logger.error(f"Stripe payment failed: {str(e)}")
                            messages.error(request, f"Payment processing failed: {e.user_message}")
                            return redirect('orders:checkout')
                            
                    elif payment_method == 'paypal':
                        # PayPal processing would go here
                        order.payment_status = True
                        order.payment_date = timezone.now()
                        order.save()
                    
                    # Clear cart and send confirmation
                    cart.clear()
                    send_order_confirmation(order)
                    
                    messages.success(request, "Your order has been placed successfully!")
                    return redirect('orders:order_confirmation', order_id=order.id)

            except Exception as e:
                logger.error(f"Checkout failed: {str(e)}", exc_info=True)
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('orders:checkout')
                
        else:
            logger.warning(f"Form validation failed: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'title': 'Checkout',
        'cart': cart,
        'form': form,
        'tax': (cart.subtotal * TAX_RATE).quantize(Decimal('0.01')),
        'shipping_cost': DEFAULT_SHIPPING_COST,
        'total': (cart.subtotal + DEFAULT_SHIPPING_COST + (cart.subtotal * TAX_RATE)).quantize(Decimal('0.01')),
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY
    }
    
    return render(request, 'orders/checkout_editorial.html', context)

@csrf_exempt
@login_required
def create_order_ajax(request):
    """AJAX endpoint for order creation."""
    if request.method == 'POST':
        try:
            cart = Cart.objects.get(user=request.user)
            form = CheckoutForm(request.POST, user=request.user)
            
            if form.is_valid():
                with transaction.atomic():
                    # Create order
                    order = form.save(commit=False)
                    order.user = request.user
                    order.subtotal = cart.subtotal
                    order.shipping_cost = DEFAULT_SHIPPING_COST
                    order.tax = (cart.subtotal * TAX_RATE).quantize(Decimal('0.01'))
                    order.total = (order.subtotal + order.shipping_cost + order.tax).quantize(Decimal('0.01'))
                    order.save()

                    # Create order items
                    for cart_item in cart.items.all():
                        OrderItem.objects.create(
                            order=order,
                            product=cart_item.product,
                            quantity=cart_item.quantity,
                            price=cart_item.product.price
                        )

                    # Create Stripe PaymentIntent
                    intent = stripe.PaymentIntent.create(
                        amount=int(order.total * 100),  # Amount in cents
                        currency='usd',
                        metadata={
                            'order_id': order.id,
                            'user_id': request.user.id
                        },
                        description=f"Order #{order.order_number}"
                    )

                    return JsonResponse({
                        'success': True,
                        'order_id': order.id,
                        'client_secret': intent.client_secret
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.as_json()
                }, status=400)
                
        except Exception as e:
            logger.error(f"Order creation failed: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=500)
    
    return JsonResponse({'success': False}, status=405)

def process_order(request, cart, form):
    """Process and create a new order (legacy fallback)."""
    with transaction.atomic():
        # Create order
        order = form.save(commit=False)
        order.user = request.user
        order.subtotal = cart.subtotal
        order.shipping_cost = DEFAULT_SHIPPING_COST
        order.tax = (cart.subtotal * TAX_RATE).quantize(Decimal('0.01'))
        order.total = (order.subtotal + order.shipping_cost + order.tax).quantize(Decimal('0.01'))
        order.save()

        # Create order items
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )

        # Process payment
        if not process_payment(order):
            raise Exception("Payment processing failed")

        # Update order status
        order.payment_status = True
        order.payment_date = timezone.now()
        order.save()

        # Clear cart
        cart.clear()

        # Send confirmation
        send_order_confirmation(order)
        
        messages.success(request, "Your order has been placed successfully!")
        logger.info(f"Order {order.order_number} created successfully")
        return redirect('orders:order_confirmation', order_id=order.id)

class OrderConfirmationView(DetailView):
    """Class-based view for order confirmation page."""
    model = Order
    template_name = 'orders/confirmation_editorial.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Only show orders for the current user."""
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context['title'] = f'Confirmación #{order.order_number}'
        return context


class OrderHistoryView(ListView):
    """Class-based view for order history."""
    model = Order
    template_name = 'orders/history_editorial.html'
    context_object_name = 'page_obj'
    paginate_by = 10

    def get_queryset(self):
        """Only show orders for the current user."""
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Historial de pedidos'
        return context


class OrderDetailView(DetailView):
    """Class-based view for order details."""
    model = Order
    template_name = 'orders/detail_editorial.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Only show orders for the current user."""
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context['title'] = f'Pedido #{order.order_number}'
        context['active_statuses'] = ['processing', 'shipped', 'delivered']
        context['shipped_statuses'] = ['shipped', 'delivered']
        return context


class OrderInvoiceView(DetailView):
    """Class-based view for order invoice."""
    model = Order
    template_name = 'orders/invoice_editorial.html'
    context_object_name = 'order'

    def get_queryset(self):
        """Only show orders for the current user."""
        return Order.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        context['title'] = f'Factura #{order.order_number}'
        return context


class TermsAndConditionsView(TemplateView):
    """Class-based view for terms and conditions page."""
    template_name = 'orders/legal/terms_editorial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Términos y condiciones'
        return context


# Legacy function-based views for backward compatibility
@login_required
def order_confirmation(request, order_id):
    """Legacy function-based view for order confirmation."""
    view = OrderConfirmationView.as_view()
    return view(request, pk=order_id)

@login_required
def order_history(request):
    """Legacy function-based view for order history."""
    view = OrderHistoryView.as_view()
    return view(request)

@login_required
def order_detail(request, order_id):
    """Legacy function-based view for order detail."""
    view = OrderDetailView.as_view()
    return view(request, pk=order_id)

@login_required
def order_invoice(request, order_id):
    """Legacy function-based view for order invoice."""
    view = OrderInvoiceView.as_view()
    return view(request, pk=order_id)

@login_required
@require_POST
def cancel_order(request, order_id):
    """Handle order cancellation request."""
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if order.status not in ['pending', 'processing']:
        messages.error(request, "This order cannot be cancelled at this stage")
        logger.warning(f"Cancel attempt for non-cancellable order {order.order_number}")
        return redirect('orders:order_detail', order_id=order.id)

    try:
        with transaction.atomic():
            # Create Stripe refund if payment was processed
            if order.payment_status:
                try:
                    payment_intents = stripe.PaymentIntent.list(
                        metadata={'order_id': order.id}
                    )
                    for intent in payment_intents.auto_paging_iter():
                        stripe.Refund.create(
                            payment_intent=intent.id,
                            reason='requested_by_customer'
                        )
                except Exception as e:
                    logger.error(f"Stripe refund failed: {str(e)} (IGNORED in DEBUG mode)")
                    if not settings.DEBUG:
                        raise

            order.status = 'cancelled'
            order.save()
            try:
                send_order_cancellation(order)
            except Exception as e:
                logger.error(f"Order cancellation email failed: {str(e)} (IGNORED in DEBUG mode)")
                if not settings.DEBUG:
                    raise
            messages.success(request, "Order has been cancelled successfully")
            logger.info(f"Order {order.order_number} cancelled by user")
    except Exception as e:
        if settings.DEBUG:
            messages.success(request, "Order has been cancelled successfully (with ignored errors)")
            logger.warning(f"Order cancelled with ignored error in DEBUG: {str(e)}")
        else:
            messages.error(request, "Failed to cancel order")
            logger.error(f"Order cancellation failed: {str(e)}")

    return redirect('orders:order_history')

@login_required
@require_POST
def delete_order(request, order_id):
    """Delete an order permanently (only if pending or processing and belongs to user)."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status not in ['pending', 'processing']:
        messages.error(request, "This order cannot be deleted at this stage.")
        return redirect('orders:order_detail', order_id=order.id)
    try:
        order.delete()
        messages.success(request, "Order deleted successfully.")
        logger.info(f"Order {order.order_number} deleted by user {request.user.id}")
    except Exception as e:
        messages.error(request, "Failed to delete order.")
        logger.error(f"Order deletion failed: {str(e)}")
    return redirect('orders:order_history')

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
        logger.error(f"Invalid payload: {str(e)}")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {str(e)}")
        return HttpResponse(status=400)

    # Handle payment success
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
            logger.error(f"Order {order_id} not found for payment intent {payment_intent.id}")

    return HttpResponse(status=200)

# Helper Functions
def process_payment(order):
    """Process payment through Stripe."""
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(order.total * 100),
            currency='usd',
            metadata={
                'order_id': order.id,
                'user_id': order.user.id
            },
            description=f"Order #{order.order_number}"
        )
        logger.info(f"Payment processed for order {order.order_number}")
        return True
    except stripe.error.StripeError as e:
        logger.error(f"Payment failed for order {order.order_number}: {str(e)}")
        return False

def send_order_confirmation(order):
    """Send order confirmation email."""
    subject = f"Order Confirmation #{order.order_number}"
    context = {'order': order}
    
    text_message = render_to_string('orders/emails/order_confirmation.txt', context)
    html_message = render_to_string('orders/emails/order_confirmation.html', context)
    
    send_mail(
        subject,
        text_message,
        'orders@fantasyjewelry.com',
        [order.user.email],
        html_message=html_message
    )
    logger.info(f"Confirmation email sent for order {order.order_number}")

def send_order_cancellation(order):
    """Send order cancellation email."""
    subject = f"Order Cancelled #{order.order_number}"
    context = {'order': order}
    
    text_message = render_to_string('orders/emails/cancellation.txt', context)
    html_message = render_to_string('orders/emails/cancellation.html', context)
    
    send_mail(
        subject,
        text_message,
        'support@fantasyjewelry.com',
        [order.user.email],
        html_message=html_message
    )
    logger.info(f"Cancellation email sent for order {order.order_number}")
    
class TermsAndConditionsView(TemplateView):
    """Class-based view for terms and conditions page."""
    template_name = 'orders/legal/terms_editorial.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Términos y condiciones'
        return context


def terms_and_conditions(request):
    """Legacy function-based view for backward compatibility."""
    view = TermsAndConditionsView.as_view()
    return view(request)


# API Views
class OrderPagination(PageNumberPagination):
    """Custom pagination for orders."""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class OrderListAPIView(generics.ListCreateAPIView):
    """API view for listing and creating orders."""
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = OrderPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_fields = ['status', 'payment_status']
    search_fields = ['order_number']
    ordering_fields = ['created_at', 'updated_at', 'total']
    ordering = ['-created_at']

    def get_queryset(self):
        """Return orders for the current user."""
        return Order.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        """Use different serializer for create vs list."""
        if self.request.method == 'POST':
            return OrderCreateSerializer
        return OrderListSerializer

    def perform_create(self, serializer):
        """Create order for the current user."""
        serializer.save(user=self.request.user)


class OrderDetailAPIView(generics.RetrieveUpdateAPIView):
    """API view for retrieving and updating orders."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_number'

    def get_queryset(self):
        """Return orders for the current user."""
        return Order.objects.filter(user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_order_api(request, order_number):
    """API endpoint for cancelling orders."""
    try:
        order = Order.objects.get(
            order_number=order_number,
            user=request.user
        )

        if order.status not in ['pending', 'processing']:
            return Response(
                {'error': 'Order cannot be cancelled at this stage'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cancel order logic (similar to existing cancel_order view)
        order.status = 'cancelled'
        order.save()

        serializer = OrderSerializer(order)
        return Response(serializer.data)

    except Order.DoesNotExist:
        return Response(
            {'error': 'Order not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_history_api(request):
    """API endpoint for order history."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = OrderPagination()
    paginated_orders = paginator.paginate_queryset(orders, request)
    serializer = OrderListSerializer(paginated_orders, many=True, context={'request': request})

    return paginator.get_paginated_response(serializer.data)