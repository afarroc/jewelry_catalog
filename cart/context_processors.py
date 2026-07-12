from .models import Cart
from .cart import CartSession

def cart(request):
    """Make the cart available globally in templates."""
    user = getattr(request, 'user', None)
    if user and user.is_authenticated:
        # Use database cart for authenticated users
        cart, created = Cart.objects.get_or_create(user=request.user)
        return {'cart': cart}
    else:
        # Use session cart for anonymous users
        cart_session = CartSession(request)
        return {'cart': cart_session}