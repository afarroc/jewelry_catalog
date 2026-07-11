(function () {
  'use strict';

  // Selectores compatibles con editor standalone e inline
  const imageInput = document.getElementById('ieImageInput') || document.querySelector('input[name="image"]');
  const imageToCrop = document.getElementById('ieImageToCrop');
  const canvasContainer = document.getElementById('ieCanvasContainer');
  const placeholder = document.getElementById('iePlaceholder');
  const ratioGrid = document.getElementById('ieRatioGrid');
  const previewStrip = document.getElementById('iePreviewStrip');
  const cropDataInput = document.getElementById('id_crop_data');
  const form = document.getElementById('ieForm') || document.getElementById('productForm');

  let cropper = null;
  let currentAspect = 1;
  let currentRatioKey = 'card';
  let currentW = 800;
  let currentH = 800;

  function initCropper(img) {
    console.log('[ImageEditor] initCropper', img.naturalWidth, 'x', img.naturalHeight);
    if (cropper) {
      cropper.destroy();
      cropper = null;
    }
    try {
      cropper = new Cropper(img, {
        aspectRatio: currentAspect,
        viewMode: 1,
        autoCropArea: 0.8,
        responsive: true,
        checkCrossOrigin: false,
        touchDragZoom: true,
        zoomOnWheel: true,
        zoomOnTouch: true,
        ready: function () {
          console.log('[ImageEditor] Cropper ready');
          updatePreview();
        },
        crop: function () {
          updatePreview();
        }
      });
    } catch (e) {
      console.error('[ImageEditor] Error inicializando Cropper:', e);
      if (previewStrip) {
        previewStrip.innerHTML = '<p style="color:#b00020">Error al inicializar el editor de imagen.</p>';
      }
    }
  }

  function updatePreview() {
    console.log('[ImageEditor] updatePreview, cropper=', !!cropper);
    if (!cropper) return;
    try {
      const canvas = cropper.getCroppedCanvas({
        width: currentW,
        height: currentH,
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high'
      });
      if (!canvas) {
        console.warn('[ImageEditor] getCroppedCanvas devolvió null');
        return;
      }

      const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
      previewStrip.innerHTML = [
        '<div class="ie-preview-item">',
        '  <div class="ie-preview-label">' + currentRatioKey + ' (' + currentW + '×' + currentH + ')</div>',
        '  <img src="' + dataUrl + '" alt="Preview ' + currentRatioKey + '">',
        '</div>'
      ].join('\n');

      const cropData = cropper.getData(true);
      cropDataInput.value = JSON.stringify({
        ratio: currentRatioKey,
        x: Math.round(cropData.x),
        y: Math.round(cropData.y),
        width: Math.round(cropData.width),
        height: Math.round(cropData.height),
        scale: 1
      });
    } catch (e) {
      console.error('[ImageEditor] Error actualizando preview:', e);
    }
  }

  function loadImage(file) {
    console.log('[ImageEditor] loadImage', file.name, file.type, file.size);
    if (!file) return;
    const url = URL.createObjectURL(file);
    imageToCrop.src = url;
    imageToCrop.style.display = 'block';
    if (placeholder) {
      placeholder.style.display = 'none';
    }

    // Asignar onload ANTES de cambiar src para evitar race condition con cache
    imageToCrop.onload = function () {
      console.log('[ImageEditor] imagen cargada (onload)');
      initCropper(imageToCrop);
    };

    // Fallback por si onload no se dispara (imagen cacheada)
    if (imageToCrop.complete && imageToCrop.naturalWidth > 0) {
      console.log('[ImageEditor] imagen ya cargada (fallback)');
      initCropper(imageToCrop);
    }
  }

  function handleRatioClick(e) {
    const btn = e.target.closest('.ie-ratio-btn, .ie-inline-ratio');
    if (!btn) return;
    document.querySelectorAll('.ie-ratio-btn, .ie-inline-ratio').forEach(function (b) {
      b.classList.remove('active');
    });
    btn.classList.add('active');
    currentRatioKey = btn.dataset.ratio;
    currentAspect = parseFloat(btn.dataset.aspect) || 1;
    currentW = parseInt(btn.dataset.w, 10) || 800;
    currentH = parseInt(btn.dataset.h, 10) || 800;
    if (cropper) {
      cropper.setAspectRatio(currentAspect);
      updatePreview();
    } else {
      console.warn('[ImageEditor] Croper no inicializado al cambiar ratio');
    }
  }

  if (imageInput) {
    imageInput.addEventListener('change', function (e) {
      const file = e.target.files[0];
      if (!file) return;
      loadImage(file);
    });

    // Soporte drag & drop
    if (canvasContainer) {
      canvasContainer.addEventListener('dragover', function (e) {
        e.preventDefault();
        canvasContainer.style.borderColor = 'var(--ink)';
      });
      canvasContainer.addEventListener('dragleave', function (e) {
        e.preventDefault();
        canvasContainer.style.borderColor = 'var(--line)';
      });
      canvasContainer.addEventListener('drop', function (e) {
        e.preventDefault();
        canvasContainer.style.borderColor = 'var(--line)';
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
          loadImage(file);
          // Sincronizar input file
          const dt = new DataTransfer();
          dt.items.add(file);
          imageInput.files = dt.files;
        }
      });
    }
  }

  // Mapeo bento_size -> ratio recomendado
  const BENTO_RATIO_MAP = {
    'standard': 'card',
    'wide': 'wide',
    'wide-image': 'wide',
    'tall': 'tall',
    'tall-image': 'tall',
    'featured': 'card',
    'hero': 'hero',
  };

  function setRatioByKey(ratioKey) {
    const mapping = {
      'card': { aspect: 1, w: 800, h: 800 },
      'banner': { aspect: 3, w: 1200, h: 400 },
      'hero': { aspect: 3.2, w: 1920, h: 600 },
      '1x1': { aspect: 1, w: 800, h: 800 },
      '1x2': { aspect: 0.5, w: 800, h: 1600 },
      'wide': { aspect: 2, w: 1200, h: 600 },
      'tall': { aspect: 0.5, w: 600, h: 1200 },
      'classic': { aspect: 1.33, w: 800, h: 600 },
    };
    const m = mapping[ratioKey] || mapping['card'];
    currentRatioKey = ratioKey;
    currentAspect = m.aspect;
    currentW = m.w;
    currentH = m.h;

    // Actualizar botones activos
    document.querySelectorAll('.ie-ratio-btn, .ie-inline-ratio').forEach(function (b) {
      b.classList.toggle('active', b.dataset.ratio === ratioKey);
    });

    if (cropper) {
      cropper.setAspectRatio(currentAspect);
      updatePreview();
    }
  }

  function handleBentoChange(e) {
    const select = e.target;
    const bento = select.value;
    const ratioKey = BENTO_RATIO_MAP[bento] || 'card';
    setRatioByKey(ratioKey);
  }

  // Event delegation robusto: escucha en el document y filtra por ratioGrid
  document.addEventListener('click', function (e) {
    if (!ratioGrid || !ratioGrid.contains(e.target)) return;
    handleRatioClick(e);
  });

  // Sincronizar bento_size -> ratio
  const bentoSelect = document.getElementById('id_bento_size');
  if (bentoSelect) {
    bentoSelect.addEventListener('change', handleBentoChange);
    // Al cargar, si ya tiene valor, sincronizar
    if (bentoSelect.value) {
      handleBentoChange({ target: bentoSelect });
    }
  }

  if (form) {
    form.addEventListener('submit', function (e) {
      if (!cropper) {
        e.preventDefault();
        alert('Selecciona una imagen para recortar antes de guardar.');
      }
    });
  }
})();
