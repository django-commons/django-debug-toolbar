import json
import zlib
from django.db import migrations, models
import debug_toolbar.fields

def convert_to_binary(apps, schema_editor):
    """Convert existing text data to binary format."""
    HistoryEntry = apps.get_model('debug_toolbar', 'HistoryEntry')
    for entry in HistoryEntry.objects.all():
        if entry.data and isinstance(entry.data, str):
            try:
                # Try to parse as JSON (old format)
                data_dict = json.loads(entry.data)
                # Re-save with new field (will trigger compression)
                entry.data = data_dict
                entry.save()
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON, skip
                pass

class Migration(migrations.Migration):
    dependencies = [
        ('debug_toolbar', '0002_switch_to_compressed_textfield'),
    ]

    operations = [
        migrations.AlterField(
            model_name='historyentry',
            name='data',
            field=debug_toolbar.fields.CompressedJSONField(default=dict),
        ),
        migrations.RunPython(convert_to_binary, migrations.RunPython.noop),
    ]
