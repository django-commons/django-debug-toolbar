import asyncio

import django
from asgiref.sync import sync_to_async
from django.contrib.auth.models import User
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render


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
    if django.VERSION >= (6, 0):
        from .async_.tasks import generate_report, send_welcome_message

        # Queue some tasks
        send_welcome_message.enqueue(message="hi there")
        generate_report.enqueue(report_id=456)

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
