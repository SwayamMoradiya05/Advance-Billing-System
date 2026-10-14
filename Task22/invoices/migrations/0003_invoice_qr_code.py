from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0002_alter_invoiceitem_gst_rate_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='qr_code',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Base64-encoded PNG verification QR code for this invoice.',
            ),
        ),
    ]
