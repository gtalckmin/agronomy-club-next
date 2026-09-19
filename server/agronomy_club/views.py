from django.db import IntegrityError
from django.http import FileResponse, HttpResponse
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import FirebaseTokenAuthentication
from .serializers import AlumniSerializer, ChapterSerializer, EventListSerializer, ListedChapterSerializer, MemberProfileSerializer, QuizDataSerializer, QuizSerializer, ResourceSerializer, ResourceTypeTagSerializer  # noqa: E501
from .models import Resource, ResourceTypeTag, User, Event, Quiz, Chapter
from rest_framework.pagination import PageNumberPagination


# Create your views here.
@api_view(["GET"])
def ping(request):
    return HttpResponse("Pong!", status=200)


class MemberProfileAPIView(APIView):
    authentication_classes = [FirebaseTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @staticmethod
    def _profile_for_request(request):
        try:
            return User.objects.get(firebase_uid=request.auth.uid)
        except User.DoesNotExist:
            return None

    def get(self, request):
        profile = self._profile_for_request(request)
        if profile is None:
            return Response(
                {"detail": "Member profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(MemberProfileSerializer(profile).data)

    def post(self, request):
        if self._profile_for_request(request) is not None:
            return Response(
                {"detail": "Member profile already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        if User.objects.filter(email=request.auth.email).exists():
            return Response(
                {"detail": "A member profile with this email already exists."},
                status=status.HTTP_409_CONFLICT,
            )

        serializer = MemberProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            profile = User.objects.create(
                **serializer.validated_data,
                email=request.auth.email,
                firebase_uid=request.auth.uid,
            )
        except IntegrityError:
            return Response(
                {"detail": "Member profile could not be created."},
                status=status.HTTP_409_CONFLICT,
            )

        return Response(
            MemberProfileSerializer(profile).data,
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request):
        profile = self._profile_for_request(request)
        if profile is None:
            return Response(
                {"detail": "Member profile not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MemberProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class EventsPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 30


class ChaptersPagination(PageNumberPagination):
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 30


class QuizDataAPIView(generics.RetrieveAPIView):
    serializer_class = QuizDataSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Quiz.objects.filter(public=True)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        fileHandle = instance.quiz_data.open()

        response = FileResponse(fileHandle, as_attachment=True, filename=f"{instance.name}.json")
        return response


class ResourceTypeTagListAPIView(generics.ListAPIView):
    queryset = ResourceTypeTag.objects.all()
    serializer_class = ResourceTypeTagSerializer


class ResourceListAPIView(generics.ListAPIView):
    serializer_class = ResourceSerializer

    def get_queryset(self):
        queryset = Resource.objects.filter(public=True).order_by("-upload_date")
        tags = self.request.GET.get("tags")
        if tags:
            tag_ids = [t for t in tags.split(",") if t.strip().isdigit()]
            if tag_ids:
                queryset = queryset.filter(type_tags__id__in=tag_ids).distinct()

        return queryset


class IndividualChapterAPIView(generics.RetrieveAPIView):
    serializer_class = ChapterSerializer
    lookup_field = "id"

    def get_queryset(self):
        return Chapter.objects.all()


class AlumniListAPIView(generics.ListAPIView):
    serializer_class = AlumniSerializer

    def get_queryset(self):
        return User.objects.filter(global_role="alumni").prefetch_related("user_memberships__chapter_id").order_by("-grad_yr")


class EventListAPIView(generics.ListAPIView):
    """
    GET /api/events/
    Returns a list of events.
    """
    serializer_class = EventListSerializer
    pagination_class = EventsPagination

    def get_queryset(self):
        return Event.objects.all().order_by("-date")


class QuizListAPIView(generics.ListAPIView):
    """
    GET /api/quizzes/
    Returns a list of quizzes
    """
    serializer_class = QuizSerializer

    def get_queryset(self):
        return Quiz.objects.filter(public=True).order_by("-upload_date")


class ChapterListAPIView(generics.ListAPIView):
    serializer_class = ListedChapterSerializer
    pagination_class = ChaptersPagination

    def get_queryset(self):
        return Chapter.objects.order_by("abbrev")
