try:
    from django.tasks import task
except ImportError:
    # Define a fallback decorator
    def task(func=None, **kwargs):
        def decorator(f):
            return f

        return decorator if func is None else decorator(func)


@task
def send_welcome_message(message):
    return f"Sent message: {message}"


@task
def generate_report(report_id):
    return f"Report {report_id} generated"
