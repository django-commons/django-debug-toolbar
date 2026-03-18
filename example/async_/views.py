from django.contrib.auth.models import User
from django.http import JsonResponse


async def async_db_view(request):
    names = []
    async for user in User.objects.all():
        names.append(user.username)
    return JsonResponse({"names": names})
