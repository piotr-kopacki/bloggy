from .models import Notification

def user_notifications(request):
    if request.user.is_authenticated:
        notifications = Notification.objects.filter(target=request.user)
        notifications.unread_count = sum([1 for n in notifications if not n.read])
        return {'notifications': notifications}
    return {}