# Guía de Estilos CSS - Miluxious accesorios

## Sistema de Grid Responsive

### Clases de Grid Disponibles

#### Columnas (1-12)
```html
<!-- Desktop: 4 columnas, Tablet: 6 columnas, Móvil: 12 columnas -->
<div class="col-12 col-md-6 col-lg-4">
  Contenido
</div>
```

#### Breakpoints
- **Sin prefijo**: Desktop (> 992px)
- **`-md-`**: Tablets (768px - 992px)
- **`-sm-`**: Móviles grandes (576px - 768px)
- **`-xs-`**: Móviles pequeños (< 576px)

### Ejemplos de Grid

```html
<!-- Layout de 3 columnas en desktop, 2 en tablet, 1 en móvil -->
<div class="row">
  <div class="col-12 col-md-6 col-lg-4">Columna 1</div>
  <div class="col-12 col-md-6 col-lg-4">Columna 2</div>
  <div class="col-12 col-md-6 col-lg-4">Columna 3</div>
</div>

<!-- Sidebar layout -->
<div class="row">
  <div class="col-12 col-lg-8">Contenido principal</div>
  <div class="col-12 col-lg-4">Sidebar</div>
</div>
```

## Utilidades Flexbox

### Clases de Alineación
```html
<!-- Flexbox utilities -->
<div class="d-flex justify-content-center align-items-center">
  <div>Contenido centrado</div>
</div>

<!-- Flex direction -->
<div class="d-flex flex-column"> <!-- flex-direction: column -->
<div class="d-flex flex-row">    <!-- flex-direction: row -->
```

### Espaciado
```html
<!-- Margins -->
<div class="mt-md">Margin top medium</div>
<div class="mb-lg">Margin bottom large</div>

<!-- Padding -->
<div class="p-sm">Padding small</div>
<div class="px-md">Padding horizontal medium</div>
```

## Componentes Responsive

### Botones
```html
<!-- Botones con diferentes tamaños -->
<button class="btn primary-btn">Botón normal</button>
<button class="btn primary-btn btn-sm">Botón pequeño</button>
<button class="btn primary-btn btn-lg">Botón grande</button>

<!-- Botones outline -->
<button class="btn outline-btn">Botón outline</button>
```

### Cards
```html
<!-- Card básica -->
<div class="card">
  <div class="card-header">
    <h3>Título</h3>
  </div>
  <div class="card-body">
    Contenido
  </div>
  <div class="card-footer">
    Footer
  </div>
</div>
```

### Product Cards
```html
<!-- Product card responsive -->
<div class="product-card">
  <div class="product-image-container">
    <img src="..." alt="Producto" class="product-image">
  </div>
  <div class="product-info">
    <h3 class="product-title">Nombre del producto</h3>
    <p class="product-meta">Categoría - Material</p>
    <p class="product-price">S/. 99.99</p>
    <div class="product-actions">
      <a href="#" class="btn primary-btn">Ver detalles</a>
    </div>
  </div>
</div>
```

## Animaciones y Estados

### Clases de Animación
```html
<!-- Animaciones de entrada -->
<div class="fade-in">Aparece con fade</div>
<div class="slide-in-left">Entra desde la izquierda</div>
<div class="slide-in-right">Entra desde la derecha</div>

<!-- Estados hover -->
<div class="hover-grow">Crece al hacer hover</div>
<div class="hover-shadow">Sombra al hacer hover</div>
<div class="hover-lift">Se eleva al hacer hover</div>
```

### Estados de Carga
```html
<!-- Loading state -->
<button class="btn primary-btn loading" disabled>
  Procesando...
</button>
```

## Responsive Images

### Imágenes Responsive
```html
<!-- Imagen responsive básica -->
<img src="image.jpg" alt="Descripción" class="img-responsive">

<!-- Contenedor de imagen de producto -->
<div class="product-image-container">
  <img src="product.jpg" alt="Producto" class="product-image">
</div>
```

## Formularios

### Formulario Básico
```html
<form class="auth-form">
  <div class="form-group">
    <label for="email" class="form-label">Email</label>
    <input type="email" id="email" class="form-control" required>
  </div>

  <div class="form-group">
    <label for="password" class="form-label">Contraseña</label>
    <input type="password" id="password" class="form-control" required>
  </div>

  <button type="submit" class="btn primary-btn btn-block">Enviar</button>
</form>
```

## Breakpoints de Referencia

| Breakpoint | Ancho | Dispositivo |
|------------|-------|-------------|
| `xl` | > 1200px | Desktop grande |
| `lg` | 992px - 1200px | Desktop |
| `md` | 768px - 992px | Tablet |
| `sm` | 576px - 768px | Móvil grande |
| `xs` | < 576px | Móvil pequeño |

## Mejores Prácticas

### 1. Mobile-First
```css
/* Mobile first approach */
.component {
  /* Estilos base para móvil */
}

@media (min-width: 768px) {
  .component {
    /* Estilos para tablet y desktop */
  }
}
```

### 2. Touch Targets
```css
/* Mínimo 44px para touch targets */
.btn {
  min-height: 44px;
  padding: 12px 24px;
}
```

### 3. Performance
```css
/* Usa transform en lugar de cambiar width/height */
.element:hover {
  transform: scale(1.05);
}
```

### 4. Accesibilidad
```css
/* Focus visible */
.btn:focus-visible {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

/* Skip links */
.skip-link {
  position: absolute;
  top: -40px;
  left: 6px;
}

.skip-link:focus {
  top: 6px;
}
```

## Variables CSS

El proyecto usa variables CSS para mantener consistencia:

```css
:root {
  --primary-color: #6a4c93;
  --secondary-color: #8a5a44;
  --accent-color: #f8c537;
  --spacing-md: 1rem;
  --border-radius: 4px;
  --transition-fast: 0.2s;
}
```

## Soporte de Navegadores

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ iOS Safari 14+
- ✅ Chrome Android 90+