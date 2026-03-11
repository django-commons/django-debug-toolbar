import json

from django.db import migrations

import debug_toolbar.fields


def convert_to_binary(apps, schema_editor):
    """Convert existing text data to binary format."""
    HistoryEntry = apps.get_model("debug_toolbar", "HistoryEntry")
    for entry in HistoryEntry.objects.all():
        if entry.data:
            try:
                # Try to parse as JSON if it's a string
                if isinstance(entry.data, str):
                    data_dict = json.loads(entry.data)
                else:
                    data_dict = entry.data
                # Re-save with new field (will trigger compression)
                entry.data = data_dict
                entry.save()
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON, skip
                pass


class Migration(migrations.Migration):
    dependencies = [
        ("debug_toolbar", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="historyentry",
            name="data",
            field=debug_toolbar.fields.CompressedJSONField(default=dict),
        ),
        migrations.RunPython(convert_to_binary, migrations.RunPython.noop),
    ]
