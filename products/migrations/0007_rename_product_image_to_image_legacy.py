from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_alter_category_options_category_index_order_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='image',
            new_name='image_legacy',
        ),
    ]
