from django.db import migrations


def migrate_image_data(apps, schema_editor):
    """Copy legacy Cloudinary URLs into the new CloudinaryField.

    Assigning the existing URL string to a CloudinaryField does NOT trigger an
    upload (CloudinaryField.pre_save only uploads UploadedFile instances), so the
    asset is preserved in place without re-uploading it to Cloudinary.
    """
    Product = apps.get_model('products', 'Product')
    qs = (
        Product.objects
        .exclude(image_legacy__isnull=True)
        .exclude(image_legacy='')
    )
    for p in qs.iterator():
        raw = p.image_legacy or ''
        if 'res.cloudinary.com' in raw or raw.startswith('http'):
            try:
                p.image = raw
                p.save(update_fields=['image'])
            except Exception:
                # Leave blank if the value can't be stored (e.g. >255 chars).
                continue


def reverse_migrate_image_data(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for p in Product.objects.all().iterator():
        p.image = None
        p.save(update_fields=['image'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0009_alter_imageupload_image_and_image_legacy'),
    ]

    operations = [
        migrations.RunPython(migrate_image_data, reverse_migrate_image_data),
    ]
