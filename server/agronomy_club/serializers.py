from rest_framework import serializers
from .models import Quiz, Resource, ResourceTypeTag, Event, User, Chapter, ChapterMembership


class QuizDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ["quiz_data"]


class ResourceTypeTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceTypeTag
        fields = [
            'id',
            'name',
            'lucide_name'
            ]


class ResourceSerializer(serializers.ModelSerializer):
    # type tag serializer for read request (show name and color)
    type_tags = ResourceTypeTagSerializer(many=True, read_only=True)

    chapter_name = serializers.CharField(source="chapter.name")
    chapter_colour = serializers.CharField(source="chapter.colour")

    class Meta:
        model = Resource
        fields = [
            'id',
            'chapter_name',
            'name',
            'link',
            'upload_date',
            'type_tags',
            'chapter_colour',
            ]


class AlumniSerializer(serializers.ModelSerializer):
    chapters = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'grad_yr',
            'discipline',
            'photo',
            'chapters',
        ]

    def get_chapters(self, obj: User):
        chapter_data = []
        for membership in obj.user_memberships.all():
            chapter_data.append({
                'abbrev': membership.chapter_id.abbrev,
                'colour': membership.chapter_id.colour
            })

        return chapter_data


class MemberProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'grad_yr',
            'discipline',
            'email',
            'global_role',
        ]
        read_only_fields = ['id', 'email', 'global_role']


class MemberProfileWriteSerializer(serializers.ModelSerializer):
    """Validate a complete profile without exposing identity or role fields."""

    class Meta:
        model = User
        fields = [
            'full_name',
            'grad_yr',
            'discipline',
        ]
        extra_kwargs = {
            'full_name': {'required': True, 'allow_blank': False},
            'grad_yr': {'required': True, 'allow_null': False},
            'discipline': {'required': True, 'allow_blank': False},
        }

    def validate(self, attrs):
        """Permit an imported incomplete profile only until it is completed."""
        instance = self.instance
        values = {
            field: attrs.get(field, getattr(instance, field, None))
            for field in self.Meta.fields
        }
        errors = {}

        if not isinstance(values['full_name'], str) or not values['full_name'].strip():
            errors['full_name'] = 'A full name is required.'
        if values['grad_yr'] is None:
            errors['grad_yr'] = 'A graduation year is required.'
        if not isinstance(values['discipline'], str) or not values['discipline'].strip():
            errors['discipline'] = 'A discipline is required.'

        if errors:
            raise serializers.ValidationError(errors)

        return attrs


class EventListSerializer(serializers.ModelSerializer):
    chapterName = serializers.CharField(source="chapter.name")
    chapterColour = serializers.CharField(source="chapter.colour")

    class Meta:
        model = Event
        fields = [
            "id",
            "title",
            "description",
            "location",
            "date",
            "thumbnail",
            "link",
            "chapterName",
            "chapterColour"
        ]


class ListedChapterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chapter
        fields = [
            'id',
            'name',
            'abbrev',
            'logo',
            'location',
            'desc',
            'colour',
        ]


class CommitteeSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user_id.full_name")
    photo = serializers.SerializerMethodField()

    class Meta:
        model = ChapterMembership
        fields = [
            "id",
            "full_name",
            "position",
            "photo"
        ]

    def get_photo(self, obj):
        path = obj.user_id.photo

        if not path:
            return None

        request = self.context.get('request')

        if request is not None:
            return f"{request.build_absolute_uri(path).split('/api')[0]}/media/{path}"

        return path


class ChapterSerializer(serializers.ModelSerializer):
    # resources serializer for read request
    # (show all resources owned by chapter)
    resources = ResourceSerializer(many=True, read_only=True)
    committee = serializers.SerializerMethodField()

    class Meta:
        model = Chapter
        fields = [
            "id",
            "name",
            "abbrev",
            "logo",
            "location",
            "desc",
            "email",
            "colour",
            "resources",
            "committee",
        ]

    def get_committee(self, obj):
        query_param = self.context['request'].query_params.get('committee')
        if query_param == 'exec':
            executives = obj.chapter_memberships.filter(position__in=["pres", "vpres", "sec", "treas"])
            return CommitteeSerializer(executives, many=True, context=self.context).data
        if query_param == 'all':
            committee = obj.chapter_memberships.filter(position__in=["pres", "vpres", "sec", "treas", "mark", "ocm"])
            return CommitteeSerializer(committee, many=True, context=self.context).data

        raise serializers.ValidationError("The provided URL param for committee is invalid.")


class QuizSerializer(serializers.ModelSerializer):
    chapterName = serializers.CharField(source="chapter.name")
    chapterColour = serializers.CharField(source="chapter.colour")

    class Meta:
        model = Quiz
        fields = [
            "id",
            "name",
            "chapterName",
            "upload_date",
            "chapterColour",
        ]
