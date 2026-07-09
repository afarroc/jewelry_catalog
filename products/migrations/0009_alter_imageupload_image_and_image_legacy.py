from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0008_product_cloudinary_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='imageupload',
            name='image',
            field=models.ImageField(
                help_text='Upload an image file (JPG, PNG, GIF). Max 5MB.',
                upload_to='jewelry_catalog/uploads/%Y/%m/%d/',
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='image_legacy',
            field=models.TextField(blank=True, null=True),
        ),
    ]
