# Scripts y herramientas

Esta carpeta contiene scripts locales que no pertenecen al paquete Django, agrupados por finalidad.

## Estructura

```
scripts/
├── admin/
│   ├── create_social_media.py
│   ├── create_superuser.py
│   └── dev_setup.sh
├── dev/
│   ├── assign_images.py
│   ├── assign_simulated_images.py
│   ├── iniciar_servidor_lan.bat
│   ├── test/
│   │   ├── test_env.py
│   │   ├── test_s3.py
│   │   └── test_s3_connection.py
│   └── simulate/
│       ├── seed_grid_test.py
│       ├── simulate_algo.py
│       ├── simulate_grid.py
│       ├── simulate_index.py
│       ├── simulate_large_dataset.py
│       ├── simulate_optimization.py
│       ├── simulate_reel_60.py
│       ├── simulate_report.py
│       └── simulate_zero_gaps.py
```

## Migración desde la raíz

Los scripts quitados de la raíz para evitar ruido en deploy y revisiones:

| Ruta anterior | Ruta actual |
|---------------|-------------|
| `create_superuser.py` | `scripts/admin/create_superuser.py` |
| `create_social_media.py` | `scripts/admin/create_social_media.py` |
| `dev_setup.sh` | `scripts/admin/dev_setup.sh` |
| `iniciar_servidor_lan.bat` | `scripts/dev/iniciar_servidor_lan.bat` |
| `assign_images.py` | `scripts/dev/assign_images.py` |
| `assign_simulated_images.py` | `scripts/dev/assign_simulated_images.py` |
| `seed_grid_test.py` | `scripts/dev/simulate/seed_grid_test.py` |
| `simulate_*.py` | `scripts/dev/simulate/` |

## Usos comunes

```bash
# Setup completo local
bash scripts/admin/dev_setup.sh

# Crear superusuario
python scripts/admin/create_superuser.py

# Diagnóstico S3
python scripts/dev/test/test_s3.py
```

## Notas

- `build.sh` se mantiene en la raíz porque Render/Uservica lo invoca desde ahí.
- `tests/` sigue en la raíz porque es parte de `pytest`/Django test runner.
- Si actualizás pasos en docs, usá estas rutas canónicas.
