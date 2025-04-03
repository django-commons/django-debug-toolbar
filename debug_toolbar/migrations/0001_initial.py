from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    operations = [
        migrations.CreateModel(
            name="HistoryEntry",
            fields=[
                (
                    "request_id",
                    models.UUIDField(primary_key=True, serialize=False),
                ),
                ("data", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Debug Toolbar Entry",
                "verbose_name_plural": "Debug Toolbar Entries",
                "ordering": ["-created_at"],
            },
        ),
    ]
