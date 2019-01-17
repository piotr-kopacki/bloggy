from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Entry, Notification, PrivateMessage, Tag, User
from .permissions import (DeletedReadOnly, DisallowVoteChanges,
                          IsOwnerOrReadOnly, IsTarget,
                          PrivateMessageGetOnlyRelatedMessages,
                          PrivateMessagePostAndGetOnly)
from .serializers import (EntrySerializer, NotificationSerializer,
                          PrivateMessageSerializer, TagSerializer)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"])
    def blacklist(self, request, pk=None):
        tag = self.get_object()
        if tag.blacklisters.filter(username=self.request.user.username):
            tag.blacklisters.remove(self.request.user)
        else:
            # If user is observing a tag and blacklists it
            # then delete user from observers
            if tag.observers.filter(username=self.request.user.username):
                tag.observers.remove(self.request.user)
            tag.blacklisters.add(self.request.user)
        serializer = self.serializer_class(tag, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def observe(self, request, pk=None):
        tag = self.get_object()
        if tag.observers.filter(username=self.request.user.username):
            tag.observers.remove(self.request.user)
        else:
            # If user blacklisted a tag and starts observing it
            # then delete user from blacklisters
            if tag.blacklisters.filter(username=self.request.user.username):
                tag.blacklisters.remove(self.request.user)
            tag.observers.add(self.request.user)
        serializer = self.serializer_class(tag, context={"request": request})
        return Response(serializer.data)

    def get_queryset(self):
        return Tag.objects.all()


class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsTarget, IsAuthenticated]

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        user_notifications = Notification.objects.filter(target=self.request.user)
        user_notifications.update(read=True)
        page = self.paginate_queryset(user_notifications)
        if page:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(user_notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        notification = self.get_object()
        if request.user == notification.target:
            notification.read = True
            notification.save()
            serializer = self.get_serializer(notification)
            return Response(serializer.data)
        

    @action(detail=False, methods=["get"])
    def unread(self, request):
        unread_notifications = Notification.objects.filter(
            target=self.request.user
        ).filter(read=False)
        page = self.paginate_queryset(unread_notifications)
        if page:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(unread_notifications, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        return Notification.objects.filter(target=self.request.user)


class PrivateMessageViewSet(viewsets.ModelViewSet):
    serializer_class = PrivateMessageSerializer
    permission_classes = (
        IsAuthenticated,
        PrivateMessageGetOnlyRelatedMessages,
        PrivateMessagePostAndGetOnly,
    )

    @action(detail=False, methods=["get"])
    def unread(self, request):
        unread_pms = PrivateMessage.objects.filter(target=self.request.user).filter(read=False)
        author = request.GET.get('from', None)
        if author:
            try:
                author = User.objects.get(username=author)
            except ObjectDoesNotExist:
                return Response({"status": "user with such nickname doesn't exist"})
            unread_pms = unread_pms.filter(author=author)
        serializer = self.get_serializer(unread_pms, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        user_pms = PrivateMessage.objects.filter(target=self.request.user).filter(read=False)
        n = user_pms.update(read=True, read_date=timezone.now())
        return Response({"status": f"succesfully read {n} messages"})

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        private_message = self.get_object()
        if not private_message.read and private_message.target == self.request.user:
            private_message.read = True
            private_message.read_date = timezone.now()
        private_message.save()
        serializer = self.get_serializer(private_message)
        return Response(serializer.data)

    def perform_create(self, serializer):
        try:
            target = serializer.validated_data["target"]
            target = User.objects.get(username=target)
        except User.DoesNotExist:
            raise ValidationError("User with that username doesn't exist!")
        if target == self.request.user:
            raise ValidationError("You cannot message yourself!")
        serializer.save(author=self.request.user, target=target)

    def get_queryset(self):
        return PrivateMessage.objects.filter(
            Q(author=self.request.user) | Q(target=self.request.user)
        ).order_by('-created_date')


class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    permission_classes = [
        IsOwnerOrReadOnly,
        IsAuthenticated,
        DisallowVoteChanges,
        DeletedReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def list(self, request):
        queryset = self.get_queryset()
        for entry in queryset:
            if entry.deleted:
                entry.content = "deleted"
                entry.content_formatted = "<em>deleted<em>"
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)
        serializer = self.serializer_class(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        entry = get_object_or_404(Entry, pk=pk)
        if entry.deleted:
            entry.content = "deleted"
            entry.content_formatted = "<em>deleted</em>"
        context = {"request": request}
        serializer = self.serializer_class(entry, many=False, context=context)
        return Response(serializer.data)


class VoteViewSet(viewsets.ViewSet):
    """
    View to vote for an entry

    Required data:
        pk - primary key of an entry
        votetype - 'upvote' or 'downvote'
    """

    permission_classes = [IsAuthenticated]

    def create(self, request):
        context = {"request": self.request}
        pk = request.data.get("pk")
        votetype = request.data.get("votetype")
        if not pk:
            return Response(
                {"detail": "Provide pk"}, status=status.HTTP_400_BAD_REQUEST
            )
        if not votetype or votetype not in ["upvote", "downvote"]:
            return Response(
                {"detail": "Provide votetype"}, status=status.HTTP_400_BAD_REQUEST
            )
        entry = get_object_or_404(Entry, pk=pk)
        if votetype == "upvote":
            if request.user in entry.downvotes.all():
                entry.downvotes.remove(request.user)
            if request.user in entry.upvotes.all():
                entry.upvotes.remove(request.user)
            else:
                entry.upvotes.add(request.user)
            return Response(EntrySerializer(entry, context=context).data)
        else:
            if request.user in entry.upvotes.all():
                entry.upvotes.remove(request.user)
            if request.user in entry.downvotes.all():
                entry.downvotes.remove(request.user)
            else:
                entry.downvotes.add(request.user)
            return Response(EntrySerializer(entry, context=context).data)

    def get_serializer_context(self):
        return {"request": self.request}
