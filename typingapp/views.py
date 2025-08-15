# typingapp/views.py
from decimal import Decimal, ROUND_HALF_UP
import random

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import F, OuterRef, Subquery
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    
    Center,
    Language,
    Level,
    Duration,
    Text,
    Player,
    PracticeRun,
    Contest,
    ContestEntry,
    ContestRun,
)

# --- Session keys ---
SESSION_PLAYER_KEY = "player_id"
SESSION_CENTER_KEY = "center_id"


# =========================
# Helpers
# =========================
def _get_player(request):
    """Session orqali Player obyektini qaytaradi (yo‘q bo‘lsa None)."""
    pid = request.session.get(SESSION_PLAYER_KEY)
    if not pid:
        return None
    try:
        return Player.objects.get(id=pid)
    except Player.DoesNotExist:
        return None


def _ensure_player_for_user(user):
    """User mavjud bo‘lsa, unga bog‘langan Player bo‘lmasa yaratib beradi."""
    if not user:
        return None
    player, _ = Player.objects.get_or_create(
        user=user,
        defaults={"name": user.get_full_name() or user.username},
    )
    return player


def _quantize_2(x):
    """Ikki kasrga yaxlitlash (HALF_UP)."""
    return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# =========================
# Auth
# =========================
def register_view(request):
    if request.method == "POST":
        first = (request.POST.get("first_name") or "").strip()
        patronymic = (request.POST.get("patronymic") or "").strip()
        last = (request.POST.get("last_name") or "").strip()
        username = (request.POST.get("username") or "").strip()
        p1 = request.POST.get("password1") or ""
        p2 = request.POST.get("password2") or ""

        data = {"first_name": first, "patronymic": patronymic, "last_name": last, "username": username}

        # basic validation
        if not all([first, last, username, p1, p2]):
            return render(request, "auth/register.html", {"error": "Maydonlar to‘liq emas.", "data": data})
        if p1 != p2:
            return render(request, "auth/register.html", {"error": "Parollar mos kelmadi.", "data": data})
        if len(p1) < 6:
            return render(request, "auth/register.html", {"error": "Parol uzunligi kamida 6 bo‘lsin.", "data": data})

        from django.contrib.auth.models import User

        if User.objects.filter(username=username).exists():
            return render(request, "auth/register.html", {"error": "Ushbu username band.", "data": data})

        # create user
        user = User.objects.create_user(username=username, password=p1, first_name=first, last_name=last)

        # create/bind player (display name = full name)
        full_name = " ".join([x for x in [first, patronymic, last] if x]).strip()
        player, _ = Player.objects.get_or_create(user=user, defaults={"name": full_name or username})
        if player.name != (full_name or username):
            player.name = full_name or username
            player.save(update_fields=["name"])

        login(request, user)
        request.session[SESSION_PLAYER_KEY] = player.id
        messages.success(request, "Ro‘yxatdan o‘tish muvaffaqiyatli. Xush kelibsiz!")
        return redirect("typingapp:center_list")

    return render(request, "auth/register.html")


def login_view(request):
    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""
        user = authenticate(request, username=username, password=password)
        if not user:
            return render(
                request,
                "auth/login.html",
                {"error": "Login yoki parol xato.", "data": {"username": username}},
            )
        login(request, user)
        player = _ensure_player_for_user(user)
        request.session[SESSION_PLAYER_KEY] = player.id

        # Remember me
        if request.POST.get("remember"):
            request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            request.session.set_expiry(0)

        messages.success(request, "Xush kelibsiz!")
        return redirect("typingapp:center_list")
    return render(request, "auth/login.html")


def logout_view(request):
    request.session.pop(SESSION_PLAYER_KEY, None)
    request.session.pop(SESSION_CENTER_KEY, None)
    logout(request)
    return redirect("typingapp:login")


# =========================
# Centers
# =========================
@login_required
def center_list(request):
    centers = Center.objects.all().order_by("name")
    return render(request, "centers/list.html", {"centers": centers})


@login_required
def center_pick(request, center_id):
    center = get_object_or_404(Center, id=center_id)
    request.session[SESSION_CENTER_KEY] = center.id
    # namespace bilan
    try:
        return redirect("typingapp:select_language")
    except NoReverseMatch:
        return redirect("/languages/")


# =========================
# Typing flow
# =========================
@login_required
def select_language(request):
    player = _get_player(request) or _ensure_player_for_user(request.user)
    if not player:
        return redirect("typingapp:login")

    languages = Language.objects.all().order_by("name")
    return render(request, "select_language.html", {"languages": languages, "player": player})


@login_required
def select_level(request, lang_id):
    player = _get_player(request) or _ensure_player_for_user(request.user)
    if not player:
        return redirect("typingapp:login")

    language = get_object_or_404(Language, id=lang_id)
    levels = Level.objects.all().order_by("name")
    return render(request, "select_level.html", {"language": language, "levels": levels, "player": player})


@login_required
def select_time(request, lang_id, level_id):
    player = _get_player(request) or _ensure_player_for_user(request.user)
    if not player:
        return redirect("typingapp:login")

    language = get_object_or_404(Language, id=lang_id)
    level = get_object_or_404(Level, id=level_id)
    durations = list(Duration.objects.order_by("seconds").values_list("seconds", flat=True))

    return render(
        request,
        "select_time.html",
        {"language": language, "level": level, "durations": durations, "player": player},
    )


@login_required
def typing_practice(request, lang_id, level_id, duration):
    player = _get_player(request) or _ensure_player_for_user(request.user)
    if not player:
        return redirect("typingapp:login")

    language = get_object_or_404(Language, id=lang_id)
    level = get_object_or_404(Level, id=level_id)

    texts = list(Text.objects.filter(language=language, level=level))
    if not texts:
        return render(request, "no_text.html", {"language": language, "level": level})

    chosen = random.choice(texts)
    return render(
        request,
        "typing.html",
        {"player": player, "language": language, "level": level, "duration": int(duration), "text": chosen.content},
    )


# =========================
# Result (practice)
# =========================
@require_POST
@login_required
def result_view(request):
    player = _get_player(request) or _ensure_player_for_user(request.user)
    if not player:
        return HttpResponseBadRequest("Player session not found")

    # Parametrlar
    lang_id = request.POST.get("lang_id")
    level_id = request.POST.get("level_id")
    dur_seconds = request.POST.get("duration")

    language = Language.objects.filter(id=lang_id).first()
    level = Level.objects.filter(id=level_id).first()
    duration = Duration.objects.filter(seconds=dur_seconds).first()

    def D(s, default="0"):
        try:
            return Decimal(str(s))
        except Exception:
            return Decimal(default)

    wpm = D(request.POST.get("wpm", "0"))
    acc = D(request.POST.get("accuracy", "0"))

    # 0..100 orasida
    if acc < 0:
        acc = Decimal("0")
    if acc > 100:
        acc = Decimal("100")

    wpm_d = _quantize_2(wpm)
    acc_d = _quantize_2(acc)

    # final_score
    final_param = request.POST.get("final_score", "")
    try:
        final_d = _quantize_2(Decimal(str(final_param)))
    except Exception:
        final_d = _quantize_2(wpm_d * acc_d / Decimal("100"))

    # Sessiondan markaz
    center = None
    cid = request.session.get(SESSION_CENTER_KEY)
    if cid:
        center = Center.objects.filter(id=cid).first()

    PracticeRun.objects.create(
        player=player,
        center=center,
        language=language,
        level=level,
        duration=duration,
        wpm=wpm_d,
        accuracy=acc_d,
        final_score=final_d,
    )

    return render(
        request,
        "result_page.html",
        {
            "player": player,
            "language": language,
            "level": level,
            "duration": duration,
            "wpm": wpm_d,
            "accuracy": acc_d,
            "final_score": final_d,
        },
    )


# =========================
# Global leaderboard (+ filter)
# =========================
def leaderboard(request):
    """Global reyting + ixtiyoriy ?center=ID filtri."""
    center_id = request.GET.get("center")
    qs = PracticeRun.objects.select_related("player__user", "center", "language", "level", "duration")

    if center_id and center_id.isdigit():
        qs = qs.filter(center_id=center_id)

    runs = qs.annotate(username=F("player__user__username")).order_by("-final_score", "-created_at")[:200]

    centers = Center.objects.all().order_by("name")
    return render(
        request,
        "leaderboard.html",
        {"runs": runs, "centers": centers, "current_center": center_id or ""},
    )


def leaderboard_center(request, center_id):
    """Markaz bo‘yicha reyting (alohida URL)."""
    center = get_object_or_404(Center, id=center_id)
    qs = (
        PracticeRun.objects.select_related("player__user", "center", "language", "level", "duration")
        .filter(center=center)
    )
    runs = qs.annotate(username=F("player__user__username")).order_by("-final_score", "-created_at")[:200]

    centers = Center.objects.all().order_by("name")
    return render(
        request,
        "leaderboard.html",
        {"runs": runs, "centers": centers, "current_center": str(center.id)},
    )


# =========================
# PREMIUM CONTEST
# =========================
@login_required
def contests_list(request):
    now = timezone.now()
    contests = Contest.objects.all().order_by("-created_at")
    return render(request, "contest/contests.html", {"contests": contests, "now": now})


def _contest_user_entry(user, contest):
    if not user.is_authenticated:
        return None
    return ContestEntry.objects.filter(user=user, contest=contest).first()


@login_required
def contest_detail(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    entry = _contest_user_entry(request.user, contest)
    now = timezone.now()

    # templatega flag sifatida uzatamiz
    is_open_for_upload = contest.status in {Contest.OPEN, Contest.RUNNING} and now < contest.end_at
    is_running = contest.status in {Contest.RUNNING} and contest.start_at <= now <= contest.end_at

    return render(
        request,
        "contest/contest_detail.html",
        {"contest": contest, "entry": entry, "now": now, "is_open_for_upload": is_open_for_upload, "is_running": is_running},
    )


@login_required
def contest_join(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    if not contest.is_open_for_upload():
        messages.error(request, "Bu musobaqada hozir ro'yxatdan o'tib bo'lmaydi.")
        return redirect("typingapp:contest_detail", contest_id=contest.id)

    entry = _contest_user_entry(request.user, contest)
    if entry and entry.status in (ContestEntry.SUBMITTED, ContestEntry.APPROVED):
        messages.info(request, "Arizangiz mavjud.")
        return redirect("typingapp:contest_detail", contest_id=contest.id)

    if request.method == "POST":
        telegram = (request.POST.get("telegram") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        receipt = request.FILES.get("receipt")
        if not receipt:
            return render(
                request,
                "contest/contest_join.html",
                {"contest": contest, "error": "Chek faylini yuklang."},
            )

        ContestEntry.objects.create(
            user=request.user,
            contest=contest,
            telegram=telegram,
            phone=phone,
            receipt=receipt,
            status=ContestEntry.SUBMITTED,
        )
        messages.success(request, "Chek yuborildi. Tekshirilishini kuting.")
        return redirect("typingapp:contest_detail", contest_id=contest.id)

    return render(request, "contest/contest_join.html", {"contest": contest})


@login_required
def contest_start(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)
    entry = _contest_user_entry(request.user, contest)
    now = timezone.now()

    if not entry or entry.status != ContestEntry.APPROVED:
        messages.error(request, "Typingga ruxsat yo'q. Avval to'lovingiz tasdiqlansin.")
        return redirect("typingapp:contest_detail", contest_id=contest.id)

    if not (contest.status in {Contest.RUNNING} and contest.start_at <= now <= contest.end_at):
        messages.error(request, "Musobaqa vaqti emas.")
        return redirect("typingapp:contest_detail", contest_id=contest.id)

    # Attempts limit (0 = cheksiz)
    if contest.attempts_per_user and ContestRun.objects.filter(
        contest=contest, user=request.user
    ).count() >= contest.attempts_per_user:
        messages.error(request, "Urinishlar limiti tugagan.")
        return redirect("typingapp:contest_detail", contest_id=contest.id)

    texts = list(Text.objects.filter(language=contest.language, level=contest.level))
    if not texts:
        return render(request, "no_text.html", {"language": contest.language, "level": contest.level})

    chosen = random.choice(texts)
    duration = contest.duration.seconds

    return render(
        request,
        "contest/contest_typing.html",
        {"contest": contest, "duration": duration, "text": chosen.content},
    )


@login_required
def contest_result(request, contest_id):
    if request.method != "POST":
        return redirect("typingapp:contest_detail", contest_id=contest_id)

    contest = get_object_or_404(Contest, id=contest_id)
    entry = _contest_user_entry(request.user, contest)
    now = timezone.now()

    if not entry or entry.status != ContestEntry.APPROVED or not (
        contest.status in {Contest.RUNNING} and contest.start_at <= now <= contest.end_at
    ):
        messages.error(request, "Yaroqsiz holat.")
        return redirect("typingapp:contest_detail", contest_id=contest.id)

    def D(x):
        try:
            return Decimal(str(x))
        except Exception:
            return Decimal("0")

    wpm = D(request.POST.get("wpm", "0"))
    acc = D(request.POST.get("accuracy", "0"))

    if acc < 0:
        acc = Decimal("0")
    if acc > 100:
        acc = Decimal("100")

    final = _quantize_2(wpm * acc / Decimal("100"))

    suspicious = (wpm > Decimal("200")) or (acc < Decimal("40"))

    center = None
    cid = request.session.get(SESSION_CENTER_KEY)
    if cid:
        center = Center.objects.filter(id=cid).first()

    ContestRun.objects.create(
        contest=contest,
        user=request.user,
        center=center,
        wpm=_quantize_2(wpm),
        accuracy=_quantize_2(acc),
        final_score=final,
        suspicious=suspicious,
    )

    return render(
        request,
        "contest/contest_result_page.html",
        {"contest": contest, "wpm": _quantize_2(wpm), "accuracy": _quantize_2(acc), "final_score": final},
    )


@login_required
def contest_leaderboard(request, contest_id):
    contest = get_object_or_404(Contest, id=contest_id)

    # ixtiyoriy filter: ?center=ID
    center_id = request.GET.get("center")
    base_qs = ContestRun.objects.filter(contest=contest)

    if center_id and center_id.isdigit():
        # Tanlangan markaz bo‘yicha ko‘rsatish
        qs = base_qs.filter(center_id=center_id)

        # HAR FOYDALANUVCHI UCHUN shu markazdagi OXIRGI urinish ID’si
        last_id_sq = (ContestRun.objects
                      .filter(contest=contest, user=OuterRef("user"), center_id=center_id)
                      .order_by("-created_at")
                      .values("id")[:1])
    else:
        # Barcha markazlar bo‘yicha
        qs = base_qs

        # HAR FOYDALANUVCHI UCHUN OXIRGI urinish ID’si (umumiy)
        last_id_sq = (ContestRun.objects
                      .filter(contest=contest, user=OuterRef("user"))
                      .order_by("-created_at")
                      .values("id")[:1])

    # Faqat o‘sha oxirgi urinishlarni qoldiramiz
    qs = qs.annotate(last_id=Subquery(last_id_sq)).filter(id=F("last_id"))

    # Nikni annotate qilib olamiz va ko‘rish uchun FK’larni tayyorlaymiz
    runs = (qs.annotate(username=F("user__username"))
              .select_related("center")
              # Oxirgi urinishlar orasida ball bo‘yicha tartib (xohlasangiz created_at bo‘yicha ham qo‘yishingiz mumkin)
              .order_by("-final_score", "-created_at"))

    # Filtr tugmalari uchun markazlar
    centers = (base_qs
               .filter(center__isnull=False)
               .values("center_id", "center__name")
               .distinct()
               .order_by("center__name"))

    return render(request, "contest/contest_leaderboard.html", {
        "contest": contest,
        "runs": runs,
        "centers": centers,
        "current_center": center_id or "",
    })