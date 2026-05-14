from .models import ActivityLog


def log_activity(user, action, details):

    ActivityLog.objects.create(
        user=user,
        action=action,
        details=details
    )