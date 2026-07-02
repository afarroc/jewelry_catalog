from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserLoginForm, ProfileUpdateForm
import logging

logger = logging.getLogger(__name__)

def register(request):
    """Handle user registration."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            
            # Log the user in after registration
            login(request, user)
            messages.success(request, f'Account created for {username}!')
            logger.info(f"New user registered: {username}")
            return redirect('home:index')
        else:
            logger.warning(f"Registration failed for {request.POST.get('username')}")
    else:
        form = UserRegisterForm()
    
    context = {
        'title': 'Register',
        'form': form,
    }
    return render(request, 'accounts/register_editorial.html', context)

def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('home:index')
        
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)  # Session expires when browser closes
                
                messages.success(request, f'Welcome back, {username}!')
                logger.info(f"User logged in: {username}")
                
                next_url = request.GET.get('next', 'home:index')
                return redirect(next_url)
            else:
                logger.warning(f"Failed login attempt for username: {username}")
        else:
            logger.warning(f"Invalid login form submission from {request.META.get('REMOTE_ADDR')}")
    else:
        form = UserLoginForm()
    
    context = {
        'title': 'Login',
        'form': form,
    }
    return render(request, 'accounts/login_editorial.html', context)

@login_required
def logout_view(request):
    """Handle user logout."""
    username = request.user.username
    logout(request)
    messages.info(request, 'You have been logged out.')
    logger.info(f"User logged out: {username}")
    return redirect('home:index')

@login_required
def profile(request):
    """Display user profile."""
    context = {
        'title': 'My Profile',
        'user': request.user,
    }
    return render(request, 'accounts/profile_editorial.html', context)

@login_required
def profile_update(request):
    """Handle profile updates."""
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated!')
            logger.info(f"Profile updated for user: {request.user.username}")
            return redirect('accounts:profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    context = {
        'title': 'Update Profile',
        'form': form,
    }
    return render(request, 'accounts/profile_update_editorial.html', context)