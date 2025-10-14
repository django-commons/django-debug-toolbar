from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render


async def async_db_view(request):
    names = []
    async for user in User.objects.all():
        names.append(user.username)
    return JsonResponse({"names": names})


def async_chat_index(request):
    return render(request, "chat/index.html")


def async_chat_room(request, room_name):
    return render(request, "chat/room.html", {"room_name": room_name})
