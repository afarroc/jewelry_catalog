from django.db import migrations
from cloudinary.models import CloudinaryField


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_rename_product_image_to_image_legacy'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image',
            field=CloudinaryField(
                'image',
                blank=True,
                null=True,
                help_text='Imagen del producto (se sube a Cloudinary desde el admin)',
            ),
        ),
    ]
