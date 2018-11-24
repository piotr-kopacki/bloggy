from .models import Notification

def user_notifications(request):
    return {
        'notifications': Notification.objects.filter(target=request.user), 
        'notifications_unread': any([not n.read for n in Notification.objects.filter(target=request.user)])
    } if request.user.is_authenticated else {}