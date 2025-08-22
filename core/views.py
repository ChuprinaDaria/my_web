from django.shortcuts import render
from django.utils.translation import get_language
from django.utils import timezone
from django.template import TemplateDoesNotExist
from django.template.loader import get_template

from projects.models import Project
from services.models import Service

# 📰 Новини (опційно)
try:
    from news.models import ProcessedArticle, NewsCategory
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False
    print("⚠️ News models not available - news section will be hidden")


def home(request):
    # 🧠 Featured проєкти
    featured_projects = Project.objects.filter(
        is_active=True,
        is_featured=True
    ).order_by('-order', '-project_date')[:6]

    # 🎠 Featured сервіси (для каруселі)
    featured_services = Service.objects.filter(
        is_active=True,
        is_featured=True
    ).order_by('-priority', '-date_created')[:5]

    # 🧰 Базовий контекст
    context = {
        'featured_projects': featured_projects,
        'featured_services': featured_services,
    }

    # 📰 Якщо новини доступні
    if NEWS_AVAILABLE:
        lang = get_language() or 'uk'
        today = timezone.now().date()

        all_articles = ProcessedArticle.objects.filter(status='published')
        top_news = ProcessedArticle.objects.filter(
            status='published',
            priority__gte=3
        ).select_related('category').order_by('-priority', '-published_at')[:6]

        # Якщо мало — добираємо додаткові
        if top_news.count() < 4:
            extra_news = ProcessedArticle.objects.filter(
                status='published',
                priority__lt=3
            ).select_related('category').order_by('-published_at')[:6 - top_news.count()]
            top_news = list(top_news) + list(extra_news)

        # ID топ-новин, щоб виключити з дайджесту
        top_ids = [a.id for a in top_news]
        daily_digest = ProcessedArticle.objects.filter(
            status='published'
        ).exclude(id__in=top_ids).select_related('category').order_by('-published_at')[:10]

        today_articles = ProcessedArticle.objects.filter(
            status='published',
            published_at__date=today
        )

        context.update({
            'top_news': top_news,
            'daily_digest': daily_digest,
            'news_available': True,
            'news_stats': {
                'total_today': today_articles.count(),
                'total_all': all_articles.count(),
                'categories_count': NewsCategory.objects.filter(is_active=True).count()
                    if NewsCategory.objects.exists() else 0,
            },
        })
    else:
        context['news_available'] = False

    return render(request, 'core/home.html', context)


def about_view(request):
    """Рендеримо about з локаллю, з фолбеком на core/about.html."""
    lang = (get_language() or 'en')[:2]  # en/uk/pl
    candidates = [f"core/about_{lang}.html", "core/about.html"]
    for tpl in candidates:
        try:
            get_template(tpl)
            return render(request, tpl)
        except TemplateDoesNotExist:
            continue
    # Якщо зовсім нема шаблонів — простий текст як запасний варіант
    return render(request, "core/blank.html", {"message": "About page coming soon"})
