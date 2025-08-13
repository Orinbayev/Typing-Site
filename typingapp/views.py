from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.http import require_POST

from .models import (
    Language,
    Text,
    Duration,
    Level,        # MUHIM: daraja
    Player,
    PracticeRun,  # faqat final_score saqlanadi
)
import random

SESSION_KEY = 'player_id'


def _get_player(request):
    pid = request.session.get(SESSION_KEY)
    if not pid:
        return None
    try:
        return Player.objects.get(id=pid)
    except Player.DoesNotExist:
        return None


def enter_name(request):
    """Ism kiritish (ro‘yxatdan o‘tish)."""
    player = _get_player(request)
    if player:
        return redirect('select_language')

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        if not name:
            return render(request, 'enter_name.html', {'error': "Ismni kiriting."})
        player, _ = Player.objects.get_or_create(name=name)
        request.session[SESSION_KEY] = player.id
        return redirect('select_language')

    return render(request, 'enter_name.html')


def logout_player(request):
    """Sessiyani tozalash."""
    request.session.pop(SESSION_KEY, None)
    return redirect('enter_name')


def select_language(request):
    """Til tanlash."""
    player = _get_player(request)
    if not player:
        return redirect('enter_name')
    languages = Language.objects.all()
    return render(request, 'select_language.html', {
        'languages': languages,
        'player': player
    })


def select_level(request, lang_id):
    """Tanlangan til bo‘yicha daraja tanlash."""
    player = _get_player(request)
    if not player:
        return redirect('enter_name')

    language = get_object_or_404(Language, id=lang_id)
    levels = Level.objects.all().order_by('name')
    return render(request, 'select_level.html', {
        'language': language,
        'levels': levels,
        'player': player
    })


def select_time(request, lang_id, level_id):
    """Tanlangan til + daraja bo‘yicha vaqt (sekund) tanlash."""
    player = _get_player(request)
    if not player:
        return redirect('enter_name')

    language = get_object_or_404(Language, id=lang_id)
    level = get_object_or_404(Level, id=level_id)
    durations = list(Duration.objects.order_by('seconds').values_list('seconds', flat=True))

    return render(request, 'select_time.html', {
        'language': language,
        'level': level,
        'durations': durations,
        'player': player
    })


def typing_practice(request, lang_id, level_id, duration):
    player = _get_player(request)
    if not player:
        return redirect('enter_name')

    language = get_object_or_404(Language, id=lang_id)
    level = get_object_or_404(Level, id=level_id)

    # faqat shu til + darajaga tegishli matnlar
    texts_qs = Text.objects.filter(language=language, level=level)
    texts = list(texts_qs)
    if not texts:
        # daraja bo‘yicha matn yo‘q – xabar ko‘rsatamiz
        return render(request, 'no_texts.html', {'language': language, 'level': level})

    chosen = random.choice(texts)
    return render(request, 'typing.html', {
        'player': player,
        'language': language,
        'level': level,
        'duration': int(duration),
        'text': chosen.content,
    })

@require_POST
def result_view(request):
    player = _get_player(request)
    if not player:
        return HttpResponseBadRequest('Player session not found')

    lang_id = request.POST.get('lang_id')
    level_id = request.POST.get('level_id')
    dur_seconds = request.POST.get('duration')

    language = Language.objects.filter(id=lang_id).first()
    level = Level.objects.filter(id=level_id).first()
    duration = Duration.objects.filter(seconds=dur_seconds).first()

    wpm = int(request.POST.get('wpm', 0))
    accuracy = int(request.POST.get('accuracy', 0))
    accuracy = max(0, min(100, accuracy))  # 0..100 oralig'ida

    # Frontend yuborgan bo‘lsa ham, serverda qayta hisoblab tekshiramiz
    final_score = request.POST.get('final_score')
    if final_score is None or str(final_score).strip() == "":
        final_score = round(wpm * (accuracy / 100))
    else:
        try:
            final_score = int(final_score)
        except ValueError:
            final_score = round(wpm * (accuracy / 100))

    PracticeRun.objects.create(
        player=player,
        language=language,
        level=level,
        duration=duration,
        final_score=final_score,   # faqat shu saqlanadi
    )

    return render(request, 'result_page.html', {
        'player': player,
        'language': language,
        'level': level,
        'duration': duration,
        'wpm': wpm,
        'accuracy': accuracy,
        'final_score': final_score,
    })