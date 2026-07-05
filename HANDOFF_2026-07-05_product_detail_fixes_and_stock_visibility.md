# HANDOFF — Sesión: fix product detail editorial + stock visibility en bento/cards

## Datos básicos
- **Proyecto:** `jewelry_catalog`
- **Sesión:** 2026-07-05
- **Alcance:** Reimplementar estilos faltantes de detalle de producto sin Bootstrap, estabilizar CSS, y corregir visibilidad/CTA de stock en tarjetas bento y product card clásica.

## Checklist
- [x] Plantilla `product_detail_editorial.html` sincronizada con estilos no-Bootstrap.
- [x] CSS balanceado y verificado.
- [x] Footer intacto y sin regresiones.
- [x] Stock visibility corregida en bento y product cards.
- [x] Handoff documentado.
- [x] Cambios commit localmente.

## Cambios

### Templates
- `products/templates/products/product_detail_editorial.html`
  - Secciones nuevas agregadas desde `_product_detail.html`:
    - Badges: New Arrival, Limited Stock, Available.
    - Overlay de galería: zoom y quick-add.
    - Thumbnails.
    - Propiedades con íconos: tipo, material, stock, ID.
    - Indicador de stock visual (high/low/out).
    - Wishlist (autenticados) / login (anónimos).
    - Acciones: Share, Print, Report, Edit, Delete.
    - Breadcrumb navigation.
    - Tabs: Description / Specifications / Reviews.
    - Productos relacionados por categoría (excluye actual, máx. 4).
    - Recently Viewed (placeholder).
    - Shipping info cards (4 items).
    - FAQ accordion (4 items).
    - Social share buttons (Facebook, Twitter, Pinterest, WhatsApp, Email).
    - Modales: image modal y quick view modal.
  - Fix template-level:
    - Aviso "Currently unavailable" junto al precio cuando `stock == 0`.
    - Overlay/quick-add visible incluso cuando no hay imagen.
    - Íconos en filas Stock e ID.

- `templates/_bento_standard.html`, `_bento_wide.html`, `_bento_tall.html`, `_bento_featured.html`, `_bento_hero.html`, `_bento_wide_image.html`, `_bento_item.html`, `_product_card_classic.html`
  - Fix stock visibility:
    - Formulario `add-to-cart` solo se renderiza cuando `product.stock > 0`.
    - Badges: `Disponible`/`Agotado` siempre visibles; `stock-badge--qty` solo cuando hay stock.
  - Eliminado CTA doble/duplicado en estados agotados.

### Styles
- `static/css/styles.css`
  - Bloque nuevo al final del archivo bajo comentario `Product Detail — Editorial additions`.
  - Estilos alineados al sistema editorial existente (variables CSS, tipografía Cormorant/Inter, cards con `border-radius: 16-18px`, bordes `var(--line)`, botones pill-shaped uppercase).
  - Selectores prefijados por contexto de detalle para no afectar footer ni otras páginas.
  - Corrección de cierre de llaves original desbalanceado (stray `}` previo a `@media (max-width: 480px)`).
  - Estilos agregados/revisados para:
    - `.price-display`, `.current-price`, `.out-of-stock-notice`
    - `.product-image-overlay` y `.product-gallery-placeholder` (overlay funcional sin imagen)
    - thumbnails, badges, stock indicator, tabs, specs, reviews
    - related/recently viewed, shipping, FAQ, social share
    - modales (image/quick view) y responsivos de esas secciones
  - Balance final verificado: `702/702` llaves.
  - Sin referencias a Bootstrap.

## Validaciones
- HTML tags balanceadas en `product_detail_editorial.html`.
- CSS balanceado; footer intacto (`.site-footer`, `.footer-inner`, `.footer-grid`, `.footer-bottom`).
- Templates bento/card: stock visibility consistente con `product.stock`.
- No se introdujeron clases Bootstrap en templates ni estilos nuevos.

## Próximo paso recomendado
- Verificar visualmente el detalle de producto y tarjetas bento en desktop/tablet/mobile.
- Si se requiere, agregar lógica JS para `recently viewed` en session/localStorage.
- Considerar traducción/consistencia de textos (`Currently unavailable` vs `Agotado`).
