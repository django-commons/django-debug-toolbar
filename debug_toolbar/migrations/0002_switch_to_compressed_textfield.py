import json
import zlib
import base64
from django.db import migrations, models

def convert_json_to_text(apps, schema_editor):
    """Convert existing JSON data to text format with compression."""
    HistoryEntry = apps.get_model('debug_toolbar', 'HistoryEntry')
    for entry in HistoryEntry.objects.all():
        if entry.data and not isinstance(entry.data, str):
            # Convert dict to JSON string and compress
            json_str = json.dumps(entry.data)
            compressed = zlib.compress(json_str.encode('utf-8'), level=6)
            entry.data = base64.b64encode(compressed).decode('ascii')
            entry.save()

class Migration(migrations.Migration):
    dependencies = [
        ('debug_toolbar', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historyentry',
            name='data',
            field=models.TextField(default=''),
        ),
        migrations.RunPython(convert_json_to_text, migrations.RunPython.noop),
    ]
