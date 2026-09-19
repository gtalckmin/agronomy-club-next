from django.contrib import admin
from django.db.models import Count
import unfold
from agronomy_club.models import ChapterMembership, User, Quiz, Chapter, Resource, ResourceTypeTag, Event  # noqa


class UserChapterMembershipInline(unfold.admin.TabularInline):
    model = ChapterMembership
    fk_name = "user_id"
    fields = ("chapter_id", "chapter_role", "position")
    autocomplete_fields = ("chapter_id",)
    extra = 0
    verbose_name = "Chapter membership"
    verbose_name_plural = "Chapter memberships"


class ChapterMemberInline(unfold.admin.TabularInline):
    model = ChapterMembership
    fk_name = "chapter_id"
    fields = ("user_id", "chapter_role", "position")
    autocomplete_fields = ("user_id",)
    extra = 0
    verbose_name = "Member"
    verbose_name_plural = "Members and committee"


# Register your models here.
@admin.register(Chapter)
class ChaptersAdmin(unfold.admin.ModelAdmin):
    list_display = ('id', 'name', 'abbrev', 'location', 'email')
    search_fields = ('id', 'name', 'abbrev', 'location')
    inlines = (ChapterMemberInline,)


@admin.register(Quiz)
class QuizAdmin(unfold.admin.ModelAdmin):
    list_display = ('id', 'name', 'public', 'chapter', 'upload_date')
    search_fields = ('id', 'name', 'chapter__name')


@admin.register(ResourceTypeTag)
class ResourceTypeTagAdmin(unfold.admin.ModelAdmin):
    list_display = ('id', 'name', 'lucide_name')
    search_fields = ('name', 'lucide_name')

    # Make resource type tag immutable in admin dashboard
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Resource)
class ResourceAdmin(unfold.admin.ModelAdmin):
    list_display = ('id', 'name', 'public', 'link', 'chapter', 'upload_date')
    search_fields = ('id', 'name', 'link')
    list_filter = ('type_tags', 'chapter')


@admin.register(Event)
class EventAdmin(unfold.admin.ModelAdmin):
    list_display = ('id', 'title', 'location', 'date', 'chapter')
    search_fields = ('id', 'title', 'location', 'chapter__name')
    list_filter = ('chapter',)


@admin.register(User)
class UsersAdmin(unfold.admin.ModelAdmin):
    list_display = ('full_name', 'email', 'global_role', 'grad_yr', 'discipline', 'chapter_count')
    search_fields = ('id', 'full_name', 'email', 'firebase_uid', 'discipline')
    list_filter = ('grad_yr', 'global_role')
    readonly_fields = ('firebase_uid',)
    inlines = (UserChapterMembershipInline,)
    fieldsets = (
        ("Member details", {"fields": (("full_name", "email"), "photo")}),
        ("Academic profile", {"fields": (("discipline", "grad_yr"),)}),
        ("Club access", {"fields": ("global_role",)}),
        (
            "Firebase identity",
            {
                "fields": ("firebase_uid",),
                "classes": ("collapse",),
                "description": "This value is set automatically when the member signs in.",
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            chapter_count=Count("user_memberships", distinct=True)
        )

    @admin.display(description="Chapters", ordering="chapter_count")
    def chapter_count(self, user):
        return user.chapter_count


@admin.register(ChapterMembership)
class ChapterMembershipsAdmin(unfold.admin.ModelAdmin):
    list_display = ('id', 'member', 'chapter', 'chapter_role', 'position')
    search_fields = ('id', 'user_id__full_name', 'user_id__email', 'chapter_id__name')
    list_filter = ('chapter_id', 'chapter_role', 'position')

    @admin.display(description="Member", ordering="user_id__full_name")
    def member(self, membership):
        return membership.user_id.full_name

    @admin.display(description="Chapter", ordering="chapter_id__name")
    def chapter(self, membership):
        return membership.chapter_id.name
