# typingapp/admin.py
from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils import timezone

from .models import (
    Center,
    Language,
    Duration,
    Level,
    Text,
    Player,
    PracticeRun,
    # Premium musobaqa modullari:
    Contest,
    ContestEntry,
    ContestRun,
)

# ----- Admin titles -----
admin.site.site_header = "Typing Tutor Admin"
admin.site.site_title = "Typing Tutor Admin"
admin.site.index_title = "Boshqaruv paneli"


# =========================
# Text form: Level majburiy
# =========================
class TextForm(forms.ModelForm):
    class Meta:
        model = Text
        fields = ("title", "level", "content", "language")

    def clean_level(self):
        lvl = self.cleaned_data.get("level")
        if not lvl:
            raise forms.ValidationError("Daraja (Level) tanlang.")
        return lvl


# ==============
# Inline-lar
# ==============
class TextInline(admin.TabularInline):
    model = Text
    form = TextForm
    extra = 1
    fields = ("title", "level", "content")
    show_change_link = True


class PracticeRunInline(admin.TabularInline):
    model = PracticeRun
    extra = 0
    can_delete = False
    readonly_fields = ("center", "language", "level", "duration", "wpm", "accuracy", "final_score", "created_at")
    ordering = ("-created_at",)
    fields = ("center", "language", "level", "duration", "wpm", "accuracy", "final_score", "created_at")


# ==================
# Center admin
# ==================
@admin.register(Center)
class CenterAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "runs_count")
    search_fields = ("name",)
    ordering = ("name",)

    @admin.display(description="Natijalar soni")
    def runs_count(self, obj):
        return obj.runs.count()


# ==================
# Language admin
# ==================
@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "texts_count")
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [TextInline]

    @admin.display(description="Matnlar soni")
    def texts_count(self, obj):
        return obj.texts.count()


# ==================
# Duration admin
# ==================
@admin.register(Duration)
class DurationAdmin(admin.ModelAdmin):
    list_display = ("id", "seconds")
    list_editable = ("seconds",)
    ordering = ("seconds",)


# =============
# Level admin
# =============
@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


# ============
# Text admin
# ============
@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    form = TextForm
    list_display = ("id", "title", "language", "level", "preview")
    list_filter = ("language", "level")
    search_fields = ("title", "content")
    ordering = ("language__name", "level__name", "title")

    @admin.display(description="Matn preview")
    def preview(self, obj):
        s = (obj.content or "").strip().replace("\n", " ")
        return (s[:60] + "…") if len(s) > 60 else s


# ===============
# Player admin
# ===============
@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    # Username’ni ko‘rsatamiz; “name” ixtiyoriy maydon – reklama uchun xolos
    list_display = ("id", "username", "created_at", "runs_count", "best_score_badge")
    search_fields = ("user__username", "name")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    inlines = [PracticeRunInline]
    list_per_page = 25

    @admin.display(description="Username", ordering="user__username")
    def username(self, obj):
        return obj.user.username

    @admin.display(description="Mashqlar soni")
    def runs_count(self, obj):
        return obj.runs.count()

    @admin.display(description="Eng yaxshi ball")
    def best_score_badge(self, obj):
        best = obj.runs.order_by("-final_score").first()
        if not best:
            return "-"
        # Decimal bo'lsa ham solishtirish normal ishlaydi:
        color = "#198754" if best.final_score >= 60 else "#0d6efd" if best.final_score >= 40 else "#6c757d"
        return format_html(
            '<span style="padding:.2rem .5rem;border-radius:.5rem;background:{};color:#fff;">{} ball</span>',
            color, best.final_score
        )


# ====================
# PracticeRun admin
# ====================
@admin.register(PracticeRun)
class PracticeRunAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "player_username",
        "center",
        "language",
        "level",
        "get_seconds",
        "wpm",
        "accuracy",
        "final_score",
        "created_at",
    )
    list_filter = ("center", "language", "level", "duration")
    search_fields = ("player__user__username", "center__name")
    date_hierarchy = "created_at"
    readonly_fields = ("player", "center", "language", "level", "duration", "wpm", "accuracy", "final_score", "created_at")
    ordering = ("-final_score", "-created_at")
    list_per_page = 25

    @admin.display(description="Foydalanuvchi", ordering="player__user__username")
    def player_username(self, obj):
        return obj.player.user.username

    @admin.display(description="Sekund")
    def get_seconds(self, obj):
        return obj.duration.seconds if obj.duration else "-"


# ============================
# PREMIUM: Contest (manual to'lov)
# ============================
@admin.register(Contest)
class ContestAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "entry_fee", "start_at", "end_at", "language", "level", "duration", "created_at")
    list_filter  = ("status", "language", "level", "duration", "center")
    search_fields = ("title", "description")
    date_hierarchy = "start_at"
    ordering = ("-created_at",)


@admin.register(ContestEntry)
class ContestEntryAdmin(admin.ModelAdmin):
    list_display = ("id", "contest", "user", "status", "created_at", "reviewed_at", "telegram", "phone")
    list_filter  = ("status", "contest")
    search_fields = ("user__username", "telegram", "phone")
    readonly_fields = ("created_at", "reviewed_at", "reviewed_by")
    fields = ("contest", "user", "telegram", "phone", "receipt", "status", "review_message", "reviewed_by", "reviewed_at", "created_at")
    ordering = ("-created_at",)
    actions = ["approve_entries", "reject_entries"]

    @admin.action(description="Tasdiqlash (APPROVED)")
    def approve_entries(self, request, queryset):
        updated = 0
        for e in queryset:
            e.status = ContestEntry.APPROVED
            e.reviewed_by = request.user
            e.reviewed_at = timezone.now()
            if not e.review_message:
                e.review_message = "To'lov tasdiqlandi."
            e.save()
            updated += 1
        self.message_user(request, f"{updated} ta ariza tasdiqlandi.")

    @admin.action(description="Rad etish (REJECTED) — default sabab bilan")
    def reject_entries(self, request, queryset):
        updated = 0
        for e in queryset:
            e.status = ContestEntry.REJECTED
            e.reviewed_by = request.user
            e.reviewed_at = timezone.now()
            if not e.review_message:
                e.review_message = "Chek noto'g'ri yoki o'qilmaydi. Iltimos, qayta yuklang."
            e.save()
            updated += 1
        self.message_user(request, f"{updated} ta ariza rad etildi.")


@admin.register(ContestRun)
class ContestRunAdmin(admin.ModelAdmin):
    list_display = ("id", "contest", "user", "final_score", "wpm", "accuracy", "suspicious", "created_at")
    list_filter  = ("contest", "suspicious")
    search_fields = ("user__username",)
    date_hierarchy = "created_at"
    ordering = ("-final_score", "-created_at")
