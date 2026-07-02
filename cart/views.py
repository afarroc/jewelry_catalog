from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from products.models import Product
from .models import Cart, CartItem
from .cart import CartSession
import logging

logger = logging.getLogger(__name__)

def get_cart(request):
    """Get cart for authenticated or anonymous users."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        return cart
    else:
        return CartSession(request)

def cart_detail(request):
    """Display the contents of the shopping cart."""
    cart = get_cart(request)
    context = {
        'title': 'Shopping Cart',
        'cart': cart,
    }
    return render(request, 'cart/cart_detail_editorial.html', context)

def cart_add(request, product_id):
    """Add a product to the cart or increment quantity."""
    if request.method != 'POST':
        return redirect('products:product_list')

    product = get_object_or_404(Product, id=product_id, available=True)
    cart = get_cart(request)

    quantity = int(request.POST.get('quantity', 1))

    if quantity > product.stock:
        messages.warning(request, f"Only {product.stock} available in stock.")
        quantity = product.stock

    cart.add_product(product, quantity)
    messages.success(request, f"Added {product.name} to your cart.")
    logger.info(f"Product {product.id} added to cart for user {request.user if request.user.is_authenticated else 'anonymous'}")

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Added {product.name} to your cart.",
            'cart_total': cart.total_items
        })

    return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))

def cart_remove(request, product_id):
    """Remove a product from the cart."""
    if request.method != 'POST':
        return redirect('cart:cart_detail')

    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)

    cart.remove_product(product)
    messages.success(request, f"Removed {product.name} from your cart.")
    logger.info(f"Product {product.id} removed from cart for user {request.user if request.user.is_authenticated else 'anonymous'}")

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Removed {product.name} from your cart.",
            'cart_total': cart.total_items
        })

    return redirect('cart:cart_detail')

def cart_update(request, product_id):
    """Update the quantity of a product in the cart."""
    if request.method != 'POST':
        return redirect('cart:cart_detail')

    product = get_object_or_404(Product, id=product_id, available=True)
    cart = get_cart(request)

    quantity = int(request.POST.get('quantity', 1))

    if quantity <= 0:
        return cart_remove(request, product_id)

    if quantity > product.stock:
        messages.warning(request, f"Only {product.stock} available in stock.")
        quantity = product.stock

    # Handle update differently for authenticated vs anonymous users
    if request.user.is_authenticated:
        cart_item = get_object_or_404(CartItem, cart=cart, product=product)
        cart_item.quantity = quantity
        cart_item.save()
    else:
        # For session cart, override quantity
        cart.add(product, quantity, override_quantity=True)

    messages.success(request, f"Updated {product.name} quantity.")
    logger.info(f"Cart updated - Product {product.id} quantity set to {quantity} for user {request.user if request.user.is_authenticated else 'anonymous'}")

    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Updated {product.name} quantity.",
            'cart_total': cart.total_items
        })

    return redirect('cart:cart_detail')

def cart_clear(request):
    """Remove all items from the cart."""
    if request.method != 'POST':
        return redirect('cart:cart_detail')

    cart = get_cart(request)
    cart.clear()
    messages.success(request, "Your cart has been cleared.")
    logger.info(f"Cart cleared by user {request.user if request.user.is_authenticated else 'anonymous'}")

    return redirect('cart:cart_detail')

# AJAX endpoints for cart operations
def cart_add_ajax(request, product_id):
    """AJAX endpoint to add product to cart."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    try:
        product = get_object_or_404(Product, id=product_id, available=True)
        cart = get_cart(request)

        quantity = int(request.POST.get('quantity', 1))

        if quantity > product.stock:
            return JsonResponse({
                'success': False,
                'error': f"Only {product.stock} available in stock."
            })

        cart.add_product(product, quantity)

        return JsonResponse({
            'success': True,
            'message': f"Added {product.name} to your cart.",
            'cart_total': cart.total_items
        })

    except Exception as e:
        logger.error(f"Error adding product to cart: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred'})

def cart_update_ajax(request, product_id):
    """AJAX endpoint to update product quantity in cart."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    try:
        product = get_object_or_404(Product, id=product_id, available=True)
        cart = get_cart(request)

        quantity = int(request.POST.get('quantity', 1))

        if quantity <= 0:
            cart.remove_product(product)
            return JsonResponse({
                'success': True,
                'message': f"Removed {product.name} from your cart.",
                'cart_total': cart.total_items
            })

        if quantity > product.stock:
            return JsonResponse({
                'success': False,
                'error': f"Only {product.stock} available in stock."
            })

        # Handle update differently for authenticated vs anonymous users
        if request.user.is_authenticated:
            cart_item = get_object_or_404(CartItem, cart=cart, product=product)
            cart_item.quantity = quantity
            cart_item.save()
        else:
            cart.add(product, quantity, override_quantity=True)

        return JsonResponse({
            'success': True,
            'message': f"Updated {product.name} quantity.",
            'cart_total': cart.total_items
        })

    except Exception as e:
        logger.error(f"Error updating cart: {str(e)}")
        return JsonResponse({'success': False, 'error': 'An error occurred'})