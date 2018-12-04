from .models import Notification

def user_notifications(request):
    """
    If user's authenticated add all notifications to the context
    Also notifications.unread_count returns the number of unread notifications
    """
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(target=request.user)
        notifications.unread_count = sum([1 for n in notifications if not n.read])
        return {'notifications': notifications}
    return {}