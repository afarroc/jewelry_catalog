// Main JavaScript for Jewelry Ecommerce

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components with enhanced functionality
    initBannerCarousel();
    initSmoothScroll();
    initProductHoverEffects();
    initProductCardActions();
});

// Banner Carousel Functionality
function initBannerCarousel() {
    const banners = document.querySelectorAll('.banner-container');
    if (banners.length <= 1) return;

    let currentBanner = 0;
    const totalBanners = banners.length;

    // Create navigation dots
    const bannersSection = document.querySelector('.banners-section');
    if (bannersSection) {
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'carousel-dots';
        dotsContainer.style.cssText = `
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            gap: 10px;
            z-index: 10;
        `;

        for (let i = 0; i < totalBanners; i++) {
            const dot = document.createElement('button');
            dot.className = `carousel-dot ${i === 0 ? 'active' : ''}`;
            dot.style.cssText = `
                width: 12px;
                height: 12px;
                border-radius: 50%;
                border: none;
                background-color: rgba(255, 255, 255, 0.5);
                cursor: pointer;
                transition: all 0.3s ease;
            `;
            dot.addEventListener('click', () => goToBanner(i));
            dotsContainer.appendChild(dot);
        }

        bannersSection.appendChild(dotsContainer);
    }

    // Show first banner
    showBanner(currentBanner);

    // Auto-play carousel
    setInterval(() => {
        currentBanner = (currentBanner + 1) % totalBanners;
        showBanner(currentBanner);
    }, 5000);

    function showBanner(index) {
        banners.forEach((banner, i) => {
            banner.style.display = i === index ? 'flex' : 'none';
        });

        // Update dots
        const dots = document.querySelectorAll('.carousel-dot');
        dots.forEach((dot, i) => {
            dot.classList.toggle('active', i === index);
            dot.style.backgroundColor = i === index ? '#D4AF37' : 'rgba(255, 255, 255, 0.5)';
        });
    }

    function goToBanner(index) {
        currentBanner = index;
        showBanner(currentBanner);
    }
}


// Smooth Scroll for Anchor Links
function initSmoothScroll() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');

    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Product Hover Effects
function initProductHoverEffects() {
    const productCards = document.querySelectorAll('.product-card');

    productCards.forEach(card => {
        const image = card.querySelector('.product-image');

        if (image) {
            card.addEventListener('mouseenter', function() {
                image.style.transform = 'scale(1.05)';
            });

            card.addEventListener('mouseleave', function() {
                image.style.transform = 'scale(1)';
            });
        }
    });
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add loading states for buttons
function addLoadingState(button) {
    const originalText = button.textContent;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Cargando...';

    return function removeLoading() {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

// Lazy load images
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Initialize lazy loading
initLazyLoading();

// Enhanced add to cart functionality
function addToCart(productId, quantity = 1) {
    console.log('Adding product to cart:', productId, 'Quantity:', quantity);

    // Show loading state
    showNotification('Agregando producto al carrito...', 'info');

    // Get CSRF token - try multiple selectors
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
    }
    if (!csrfToken) {
        // Try to get from meta tag
        csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    }

    if (!csrfToken) {
        console.error('CSRF token not found');
        showNotification('Error: CSRF token not found. Please refresh the page.', 'error');
        return;
    }

    // Prepare form data
    const formData = new FormData();
    formData.append('quantity', quantity);
    formData.append('csrfmiddlewaretoken', csrfToken);

    // Make AJAX request
    fetch(`/cart/add/${productId}/ajax/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showNotification(data.message || 'Producto agregado al carrito!', 'success');
            updateCartCounter(data.cart_total);
        } else {
            showNotification(data.error || 'Error al agregar producto', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        // Fallback: try to submit the form normally
        console.warn('AJAX failed, falling back to form submission');
        form.submit();
    });
}

// Update cart counter in header
function updateCartCounter(total) {
    const cartCounter = document.querySelector('.cart-counter');
    if (cartCounter) {
        cartCounter.textContent = total;
        cartCounter.style.display = total > 0 ? 'inline' : 'none';
    }
}

// Handle add to cart via AJAX
async function handleAddToCartAjax(form, productId, quantity) {
    try {
        // Get CSRF token - try multiple selectors
        let csrfToken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;
        if (!csrfToken) {
            csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        }
        if (!csrfToken) {
            csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
        }
        if (!csrfToken) {
            // Try to get from meta tag
            csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        }

        if (!csrfToken) {
            console.error('CSRF token not found');
            showNotification('Error: CSRF token not found. Please refresh the page.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('quantity', quantity);
        formData.append('csrfmiddlewaretoken', csrfToken);

        const response = await fetch(`/cart/add/${productId}/ajax/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            showNotification(data.message || 'Producto agregado al carrito!', 'success');
            updateCartCounter(data.cart_total || 0);
        } else {
            showNotification(data.error || 'Error al agregar producto', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        // Fallback: try to submit the form normally
        console.warn('AJAX failed, falling back to form submission');
        form.submit();
    }
}

// Show notification
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas ${getNotificationIcon(type)}"></i>
        <span>${message}</span>
    `;

    // Set colors based on type
    let backgroundColor = '#007bff'; // primary
    if (type === 'success') backgroundColor = '#28a745';
    if (type === 'error') backgroundColor = '#dc3545';
    if (type === 'warning') backgroundColor = '#ffc107';

    notification.style.cssText = `
        position: fixed;
        top: auto;
        left: auto;
        bottom: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        background-color: ${backgroundColor};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        max-width: 400px;
        height: auto;
        min-height: auto;
        max-height: 90vh;
        overflow-y: auto;
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

// Get notification icon based on type
function getNotificationIcon(type) {
    switch (type) {
        case 'success': return 'fa-check-circle';
        case 'error': return 'fa-exclamation-triangle';
        case 'warning': return 'fa-exclamation-circle';
        default: return 'fa-info-circle';
    }
}

// Add notification animations
const notificationStyles = document.createElement('style');
notificationStyles.textContent = `
    @keyframes slideIn {
        from { transform: translateY(100%); opacity: 0; }
        to { transform: translateY(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateY(0); opacity: 1; }
        to { transform: translateY(100%); opacity: 0; }
    }
`;
document.head.appendChild(notificationStyles);

// Product Card Actions
function initProductCardActions() {
    // Quick view buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.quick-view-btn')) {
            e.preventDefault();
            const button = e.target.closest('.quick-view-btn');
            const url = button.getAttribute('data-url');
            if (url) {
                window.open(url, '_blank');
            }
        }
    });

    // Handle add to cart form submission with AJAX
    document.addEventListener('submit', function(e) {
        if (e.target.classList.contains('add-to-cart-form')) {
            e.preventDefault();

            const form = e.target;
            const submitBtn = form.querySelector('button[type="submit"]');
            const productId = submitBtn?.getAttribute('data-product-id');

            if (!productId) {
                console.error('No product ID found');
                return;
            }

            // Get form data
            const formData = new FormData(form);
            const quantity = formData.get('quantity') || 1;

            // Add loading state
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Agregando...';

                // Re-enable button after timeout
                setTimeout(() => {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalText;
                }, 5000);
            }

            // Try AJAX first, fallback to form submission
            handleAddToCartAjax(form, productId, quantity)
                .catch(error => {
                    console.warn('AJAX failed, falling back to form submission:', error);
                    form.submit(); // Fallback to normal form submission
                });
        }
    });

    // Handle add to cart buttons (for product cards)
    document.addEventListener('click', function(e) {
        if (e.target.closest('.add-to-cart-btn') && !e.target.closest('.add-to-cart-form')) {
            e.preventDefault();
            const button = e.target.closest('.add-to-cart-btn');
            const productId = button.getAttribute('data-product-id');
            if (productId) {
                addToCart(productId);
            }
        }
    });
}

// Product Detail Page Functionality
function initProductDetailPage() {
    initImageGallery();
    initDescriptionTabs();
    initImageModal();
    initProductActions();
}

// Quantity Selector - handles both product detail and cart pages
function initQuantitySelector() {
    console.log('Initializing quantity selectors...');

    // Handle product detail page quantity selector
    const productMinusBtn = document.getElementById('qty-minus');
    const productPlusBtn = document.getElementById('qty-plus');
    const productQuantityInput = document.getElementById('quantity');

    if (productMinusBtn && productPlusBtn && productQuantityInput) {
        console.log('Found product detail quantity selector');
        initSingleQuantitySelector(productMinusBtn, productPlusBtn, productQuantityInput);
    }

    // Handle cart page quantity selectors (Bootstrap version)
    const cartInputGroups = document.querySelectorAll('.input-group');
    console.log('Found', cartInputGroups.length, 'cart input groups');

    cartInputGroups.forEach((inputGroup, index) => {
        const minusBtn = inputGroup.querySelector('.qty-btn.minus');
        const plusBtn = inputGroup.querySelector('.qty-btn.plus');
        const quantityInput = inputGroup.querySelector('input[name="quantity"]');

        if (minusBtn && plusBtn && quantityInput) {
            console.log('Initializing cart quantity selector', index + 1);
            initSingleQuantitySelector(minusBtn, plusBtn, quantityInput);
        } else {
            console.warn('Cart input group', index + 1, 'missing elements:', {
                minusBtn: !!minusBtn,
                plusBtn: !!plusBtn,
                quantityInput: !!quantityInput
            });
        }
    });
}

// Initialize a single quantity selector
function initSingleQuantitySelector(minusBtn, plusBtn, quantityInput) {
    // Check if already initialized to prevent duplicate event listeners
    if (quantityInput.hasAttribute('data-quantity-initialized')) {
        console.log('Quantity selector already initialized, skipping');
        return;
    }
    console.log('Initializing quantity selector for input:', quantityInput.id || quantityInput.name);
    quantityInput.setAttribute('data-quantity-initialized', 'true');

    const maxStock = parseInt(quantityInput.getAttribute('max')) || 1;
    const minStock = parseInt(quantityInput.getAttribute('min')) || 1;

    function updateQuantityButtons() {
        const currentValue = parseInt(quantityInput.value) || 1;
        minusBtn.disabled = currentValue <= minStock;
        plusBtn.disabled = currentValue >= maxStock;
    }

    minusBtn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Minus button clicked, current value:', quantityInput.value);
        const currentValue = parseInt(quantityInput.value) || 1;
        if (currentValue > minStock) {
            quantityInput.value = currentValue - 1;
            console.log('New value:', quantityInput.value);
            updateQuantityButtons();
            // For cart page, submit form automatically
            if (quantityInput.form && quantityInput.form.classList.contains('quantity-form')) {
                console.log('Submitting cart form');
                quantityInput.form.submit();
            }
        } else {
            console.log('Cannot decrease: at minimum stock');
        }
    });

    plusBtn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Plus button clicked, current value:', quantityInput.value);
        const currentValue = parseInt(quantityInput.value) || 1;
        if (currentValue < maxStock) {
            quantityInput.value = currentValue + 1;
            console.log('New value:', quantityInput.value);
            updateQuantityButtons();
            // For cart page, submit form automatically
            if (quantityInput.form && quantityInput.form.classList.contains('quantity-form')) {
                console.log('Submitting cart form');
                quantityInput.form.submit();
            }
        } else {
            console.log('Cannot increase: at maximum stock');
        }
    });

    // Handle manual input and validate
    quantityInput.addEventListener('input', () => {
        let value = parseInt(quantityInput.value);
        if (isNaN(value) || value < minStock) {
            value = minStock;
        } else if (value > maxStock) {
            value = maxStock;
        }
        quantityInput.value = value;
        updateQuantityButtons();
    });

    quantityInput.addEventListener('blur', () => {
        if (!quantityInput.value || quantityInput.value === '') {
            quantityInput.value = 1;
        }
        updateQuantityButtons();
    });

    // Initialize button states
    updateQuantityButtons();
}

// Image Gallery
function initImageGallery() {
    const thumbnails = document.querySelectorAll('.thumbnail-item');
    const mainImage = document.getElementById('main-product-image');

    if (!thumbnails.length || !mainImage) return;

    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', () => {
            // Remove active class from all thumbnails
            thumbnails.forEach(t => t.classList.remove('active'));
            // Add active class to clicked thumbnail
            thumbnail.classList.add('active');

            // Update main image
            const imageSrc = thumbnail.getAttribute('data-image');
            if (imageSrc) {
                mainImage.src = imageSrc;
            }
        });
    });
}

// Description Tabs
function initDescriptionTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    if (!tabButtons.length) return;

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Remove active class from all buttons and panes
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabPanes.forEach(pane => pane.classList.remove('active'));

            // Add active class to clicked button and corresponding pane
            button.classList.add('active');
            const targetPane = document.getElementById(targetTab);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        });
    });
}

// Image Modal
function initImageModal() {
    // Modal functionality is handled by global functions
}

function openImageModal(imageSrc) {
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-image');

    if (modal && modalImg && imageSrc) {
        modalImg.src = imageSrc;
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        document.body.style.overflow = 'hidden';
    }
}

function closeImageModal() {
    const modal = document.getElementById('image-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('image-modal');
    if (modal && e.target === modal) {
        closeImageModal();
    }
});

// Close modal with ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeImageModal();
        closeQuickView();
    }
});

// FAQ Accordion
function toggleFaq(button) {
    const faqItem = button.parentElement;
    const isActive = faqItem.classList.contains('active');

    // Close all FAQ items
    document.querySelectorAll('.faq-item').forEach(item => {
        item.classList.remove('active');
    });

    // Open clicked item if it wasn't active
    if (!isActive) {
        faqItem.classList.add('active');
    }
}

// Enhanced Image Modal Navigation
let currentImageIndex = 0;
let galleryImages = [];

function navigateImage(direction) {
    if (galleryImages.length === 0) return;

    currentImageIndex = (currentImageIndex + direction + galleryImages.length) % galleryImages.length;
    const modalImg = document.getElementById('modal-image');
    if (modalImg && galleryImages[currentImageIndex]) {
        modalImg.src = galleryImages[currentImageIndex];
    }
}

// Update openImageModal to handle gallery
function openImageModal(imageSrc) {
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-image');

    if (modal && modalImg && imageSrc) {
        // Get all thumbnail images for gallery navigation
        galleryImages = Array.from(document.querySelectorAll('.thumbnail-item img')).map(img => img.src);
        currentImageIndex = galleryImages.indexOf(imageSrc);

        if (currentImageIndex === -1) {
            galleryImages = [imageSrc];
            currentImageIndex = 0;
        }

        modalImg.src = imageSrc;
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';
        document.body.style.overflow = 'hidden';
    }
}

// Quick View Modal
function openQuickView(productCard) {
    const modal = document.getElementById('quick-view-modal');
    const modalImg = document.getElementById('quick-view-image');
    const modalTitle = document.getElementById('quick-view-title');
    const modalPrice = document.getElementById('quick-view-price');
    const modalLink = document.getElementById('quick-view-link');

    if (modal && productCard) {
        const img = productCard.querySelector('.product-image');
        const title = productCard.querySelector('.product-title');
        const price = productCard.querySelector('.product-price');
        const link = productCard.querySelector('.product-link');

        if (img) modalImg.src = img.src;
        if (title) modalTitle.textContent = title.textContent;
        if (price) modalPrice.textContent = price.textContent;
        if (link) modalLink.href = link.href;

        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
}

function closeQuickView() {
    const modal = document.getElementById('quick-view-modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

function addToCartFromQuickView() {
    // This would typically get the product ID from the modal and add to cart
    showNotification('Product added to cart!', 'success');
    closeQuickView();
}

// Social Sharing Functions
function shareOnFacebook() {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(document.title);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}&quote=${title}`, '_blank');
}

function shareOnTwitter() {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(`Check out this amazing product: ${document.title}`);
    window.open(`https://twitter.com/intent/tweet?url=${url}&text=${text}`, '_blank');
}

function shareOnPinterest() {
    const url = encodeURIComponent(window.location.href);
    const description = encodeURIComponent(document.title);
    const image = encodeURIComponent(document.querySelector('.main-image')?.src || '');
    window.open(`https://pinterest.com/pin/create/button/?url=${url}&description=${description}&media=${image}`, '_blank');
}

function shareOnWhatsApp() {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent(`Check out this product: ${document.title} ${url}`);
    window.open(`https://wa.me/?text=${text}`, '_blank');
}

function shareByEmail() {
    const subject = encodeURIComponent(`Check out this product: ${document.title}`);
    const body = encodeURIComponent(`I thought you might be interested in this product:\n\n${document.title}\n${window.location.href}`);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
}

// Enhanced Product Actions
function initEnhancedProductActions() {
    // Quick view from product cards
    document.addEventListener('click', (e) => {
        if (e.target.closest('.quick-view-btn')) {
            e.preventDefault();
            const button = e.target.closest('.quick-view-btn');
            const productCard = button.closest('.product-card');
            if (productCard) {
                openQuickView(productCard);
            }
        }
    });

    // Close quick view when clicking outside
    document.addEventListener('click', (e) => {
        const modal = document.getElementById('quick-view-modal');
        if (modal && e.target === modal) {
            closeQuickView();
        }
    });

    // Keyboard navigation for image modal
    document.addEventListener('keydown', (e) => {
        const modal = document.getElementById('image-modal');
        if (modal && modal.style.display === 'flex') {
            if (e.key === 'ArrowLeft') {
                navigateImage(-1);
            } else if (e.key === 'ArrowRight') {
                navigateImage(1);
            }
        }
    });
}

// Initialize enhanced functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize quantity selector on all pages that have it
    initQuantitySelector();

    // Check if we're on a product detail page
    if (document.querySelector('.product-detail-container')) {
        initProductDetailPage();
        initEnhancedProductActions();
    }

    // Check if we're on cart page
    if (document.querySelector('.cart-table') || document.querySelector('.cart-detail-container')) {
        initCartPage();
    }
});

// Product Actions
function initProductActions() {
    // Quick add to cart from image overlay
    document.addEventListener('click', (e) => {
        if (e.target.closest('.quick-add-btn')) {
            e.preventDefault();
            const button = e.target.closest('.quick-add-btn');
            const productId = button.getAttribute('data-product-id');
            if (productId) {
                addToCart(productId);
            }
        }
    });

    // Wishlist functionality
    document.addEventListener('click', (e) => {
        if (e.target.closest('.wishlist-btn')) {
            e.preventDefault();
            const button = e.target.closest('.wishlist-btn');
            const productId = button.getAttribute('data-product-id');
            if (productId) {
                toggleWishlist(productId, button);
            }
        }
    });

    // Notify me functionality
    document.addEventListener('click', (e) => {
        if (e.target.closest('.notify-btn')) {
            e.preventDefault();
            const button = e.target.closest('.notify-btn');
            const productId = button.getAttribute('data-product-id');
            if (productId) {
                notifyWhenAvailable(productId, button);
            }
        }
    });
}

// Wishlist functionality
function toggleWishlist(productId, button) {
    // This would typically make an AJAX request
    const icon = button.querySelector('i');
    const text = button.querySelector('span');

    if (icon.classList.contains('fas')) {
        // Remove from wishlist
        icon.classList.remove('fas');
        icon.classList.add('far');
        text.textContent = 'Add to Wishlist';
        showNotification('Removed from wishlist', 'info');
    } else {
        // Add to wishlist
        icon.classList.remove('far');
        icon.classList.add('fas');
        text.textContent = 'Remove from Wishlist';
        showNotification('Added to wishlist', 'success');
    }

    console.log('Toggle wishlist for product:', productId);
}

// Notify when available
function notifyWhenAvailable(productId, button) {
    // This would typically make an AJAX request
    const removeLoading = addLoadingState(button);
    button.disabled = true;

    setTimeout(() => {
        removeLoading();
        button.innerHTML = '<i class="fas fa-check"></i> We\'ll notify you!';
        button.classList.add('notified');
        showNotification('We\'ll notify you when this product is back in stock!', 'success');
    }, 1000);

    console.log('Notify when available for product:', productId);
}

// Share product
function shareProduct() {
    if (navigator.share) {
        navigator.share({
            title: document.title,
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            showNotification('Product link copied to clipboard!', 'success');
        });
    }
}

// Print product
function printProduct() {
    window.print();
}

// Report product
function reportProduct() {
    const reason = prompt('Please provide a reason for reporting this product:');
    if (reason) {
        // This would typically make an AJAX request
        showNotification('Thank you for your report. We\'ll review it shortly.', 'info');
        console.log('Report product:', reason);
    }
}

// Cart Page Functionality
function initCartPage() {
    // Initialize cart-specific functionality
    console.log('Initializing cart page functionality');

    // Add any cart-specific event listeners here
    // For example, handling remove buttons, update forms, etc.
}

// Additional initialization for product detail page
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a product detail page
    if (document.querySelector('.product-detail-container')) {
        initProductDetailPage();
    }
});














// Test function for quantity selectors
window.testQuantitySelectors = function() {
    console.log('=== Testing Quantity Selectors ===');

    // Test product detail selector
    const productInput = document.getElementById('quantity');
    if (productInput) {
        console.log('Product detail input found, value:', productInput.value);
        console.log('Step attribute:', productInput.getAttribute('step'));
        console.log('Min attribute:', productInput.getAttribute('min'));
        console.log('Max attribute:', productInput.getAttribute('max'));
    } else {
        console.log('Product detail input not found');
    }

    // Test cart selectors
    const cartSelectors = document.querySelectorAll('.quantity-selector');
    console.log('Found', cartSelectors.length, 'cart selectors');

    cartSelectors.forEach((selector, index) => {
        const input = selector.querySelector('input[name="quantity"]');
        if (input) {
            console.log(`Cart selector ${index + 1}: value=${input.value}, step=${input.getAttribute('step')}`);
        }
    });

    console.log('=== End Test ===');
};

// Export functions for global use
window.JewelryEcommerce = {
    addToCart,
    showNotification,
    addLoadingState,
    openImageModal,
    closeImageModal,
    shareProduct,
    printProduct,
    reportProduct,
    testQuantitySelectors
};