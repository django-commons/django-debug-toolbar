import asyncio

import django
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render

TASKS_AVAILABLE = django.VERSION >= (6, 0)

if TASKS_AVAILABLE:
    from django.tasks import task

    @task
    def example_task(x=1, y=2):
        return x + y


def tasks_view(request):
    if TASKS_AVAILABLE:
        example_task.enqueue(1, y=2)
        example_task.enqueue(3, y=4)
    return render(request, "tasks.html", {"tasks_available": TASKS_AVAILABLE})


def increment(request):
    try:
        value = int(request.session.get("value", 0)) + 1
    except ValueError:
        value = 1
    request.session["value"] = value
    return JsonResponse({"value": value})


def jinja2_view(request):
    return render(request, "index.jinja", {"foo": "bar"}, using="jinja2")


async def async_home(request):
    return await sync_to_async(render)(request, "index.html")


async def async_db(request):
    user_count = await User.objects.acount()

    return await sync_to_async(render)(
        request, "async_db.html", {"user_count": user_count}
    )


async def async_db_concurrent(request):
    # Do database queries concurrently
    (user_count, _) = await asyncio.gather(
        User.objects.acount(), User.objects.filter(username="test").acount()
    )

    return await sync_to_async(render)(
        request, "async_db.html", {"user_count": user_count}
    )


def cache_view(request):
    cache.set("foo", "bar")
    cache.get("foo")
    cache.get("baz")
    return render(request, "cache.html")
