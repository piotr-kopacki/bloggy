from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Entry
from .permissions import IsOwnerOrReadOnly, DisallowVoteChanges
from .serializers import EntrySerializer
from rest_framework.permissions import IsAuthenticated

class EntryViewSet(viewsets.ModelViewSet):
    queryset = Entry.objects.all()
    serializer_class = EntrySerializer
    permission_classes = [IsOwnerOrReadOnly, IsAuthenticated, DisallowVoteChanges]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class VoteViewSet(viewsets.ViewSet):
    """
    View to vote for an entry

    Required data:
        pk - primary key of an entry
        votetype - 'upvote' or 'downvote'
    """
    permission_classes = [IsAuthenticated]

    def create(self, request):
        pk = request.data.get('pk')
        votetype = request.data.get('votetype')
        if not pk:
            return Response({"detail": "Provide pk"}, status=status.HTTP_400_BAD_REQUEST)
        if not votetype:
            return Response({"detail": "Provide votetype"}, status=status.HTTP_400_BAD_REQUEST)
        entry = get_object_or_404(Entry, pk=pk)
        if votetype == 'upvote':
            if request.user in entry.downvotes.all():
                entry.downvotes.remove(request.user)
            if request.user in entry.upvotes.all():
                entry.upvotes.remove(request.user)
            else:
                entry.upvotes.add(request.user)
            return Response(EntrySerializer(entry).data)
        else:
            if request.user in entry.upvotes.all():
                entry.upvotes.remove(request.user)
            if request.user in entry.downvotes.all():
                entry.downvotes.remove(request.user)
            else:
                entry.downvotes.add(request.user)
            return Response(EntrySerializer(entry).data)
