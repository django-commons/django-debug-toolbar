"""Django settings for example project."""

from ..settings import *  # noqa: F403

ROOT_URLCONF = "example.async_.urls"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    }
}
