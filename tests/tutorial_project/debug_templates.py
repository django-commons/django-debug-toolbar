import django
from django.conf import settings
from django.template import engines

print("Django version:", django.get_version())
print("\nTEMPLATES setting:")
print(settings.TEMPLATES)

print("\nAvailable template engines:")
for engine in engines.all():
    print(f"  - {engine.name} ({engine.__class__.__name__})")
