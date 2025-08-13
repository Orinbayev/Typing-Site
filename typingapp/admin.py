from django.contrib import admin
from django import forms
from .models import Language, Text, Duration, Level, Player, PracticeRun

admin.site.site_header = "Typing Tutor Admin"
admin.site.site_title = "Typing Tutor Admin"
admin.site.index_title = "Boshqaruv paneli"

# ---- Text form: Level majburiy
class TextForm(forms.ModelForm):
    class Meta:
        model = Text
        fields = ("title", "level", "content", "language")  # language inline’da avtomatik bo‘ladi

    def clean_level(self):
        lvl = self.cleaned_data.get("level")
        if not lvl:
            raise forms.ValidationError("Daraja (Level) tanlang.")
        return lvl

class TextInline(admin.TabularInline):
    model = Text
    form = TextForm
    extra = 1
    fields = ("title", "level", "content")
    show_change_link = True

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "texts_count")
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [TextInline]

    @admin.display(description="Matnlar soni")
    def texts_count(self, obj):
        return obj.texts.count()

@admin.register(Duration)
class DurationAdmin(admin.ModelAdmin):
    list_display = ("id", "seconds")
    list_editable = ("seconds",)
    ordering = ("seconds",)

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)

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

class PracticeRunInline(admin.TabularInline):
    model = PracticeRun
    extra = 0
    readonly_fields = ("language", "level", "duration", "final_score", "created_at")
    can_delete = False
    ordering = ("-created_at",)

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at", "runs", "best_score_badge")
    search_fields = ("name",)
    date_hierarchy = "created_at"
    inlines = [PracticeRunInline]

    @admin.display(description="Mashqlar soni")
    def runs(self, obj):
        return obj.practicerun_set.count()

    @admin.display(description="Eng yaxshi ball")
    def best_score_badge(self, obj):
        best = obj.practicerun_set.order_by("-final_score").first()
        if not best:
            return "-"
        color = "#198754" if best.final_score >= 60 else "#0d6efd" if best.final_score >= 40 else "#6c757d"
        from django.utils.html import format_html
        return format_html(
            '<span style="padding:.2rem .5rem;border-radius:.5rem;background:{};color:#fff;">{} ball</span>',
            color, best.final_score
        )

@admin.register(PracticeRun)
class PracticeRunAdmin(admin.ModelAdmin):
    list_display = ("id", "player", "language", "level", "get_seconds", "final_score", "created_at")
    list_filter = ("language", "level", "duration")
    search_fields = ("player__name",)
    date_hierarchy = "created_at"
    readonly_fields = ("player", "language", "level", "duration", "final_score", "created_at")
    ordering = ("-created_at",)
    list_per_page = 25

    @admin.display(description="Sekund")
    def get_seconds(self, obj):
        return obj.duration.seconds if obj.duration else "-"
