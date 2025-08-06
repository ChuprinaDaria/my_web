from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from .models import Service, ServiceCategory, ServiceOverview, FAQ, ServiceFeature
from projects.models import Project

def services_list(request):
    lang = get_language()

    overview = ServiceOverview.objects.first()
    categories = ServiceCategory.objects.prefetch_related("services").all()
    all_projects = list(Project.objects.filter(is_active=True))

    localized_categories = []
    for category in categories:
        services = []
        for service in category.services.filter(is_active=True):
            services.append({
                "slug": service.slug,
                "icon": service.icon,
                "title": getattr(service, f"title_{lang}", service.title_en),
                "short_description": getattr(service, f"short_description_{lang}", service.short_description_en),
            })

        projects = [p for p in all_projects if p.category_id == category.id]
        localized_projects = []
        for project in projects:
            localized_projects.append({
                "slug": project.slug,
                "title": getattr(project, f"title_{lang}", project.title_en),
                "short_description": getattr(project, f"short_description_{lang}", project.short_description_en),
                "featured_image": project.featured_image.url if project.featured_image else None,
            })

        localized_categories.append({
            "slug": category.slug,
            "title": getattr(category, f"title_{lang}", category.title_en),
            "description": getattr(category, f"description_{lang}", category.description_en),
            "services": services,
            "projects": localized_projects,
        })

    # ... features, faqs ...

    context = {
        "overview_title": getattr(overview, f"title_{lang}", overview.title_en) if overview else "",
        "overview_description": getattr(overview, f"description_{lang}", overview.description_en) if overview else "",
        "seo_title": overview.seo_title if overview else "",
        "seo_description": overview.seo_description if overview else "",
        "og_image": overview.og_image.url if overview and overview.og_image else None,
        "categories": localized_categories,
        "features": [
            {
                "icon": f.icon,
                "title": getattr(f, f"title_{lang}", f.title_en)
            }
            for f in ServiceFeature.objects.filter(is_active=True).order_by("order")
        ],
        "faqs": [
            {
                "question": getattr(f, f"question_{lang}", f.question_en),
                "answer": getattr(f, f"answer_{lang}", f.answer_en),
            }
            for f in FAQ.objects.filter(is_active=True).order_by("order")
        ],
        "lang": lang,
    }

    return render(request, "services/services_list.html", context)


def service_detail(request, slug):
    lang = get_language()
    service = get_object_or_404(Service, slug=slug, is_active=True)

    context = {
        "service": {
            "slug": service.slug,
            "icon": service.icon,
            "title": getattr(service, f"title_{lang}", service.title_en),
            "short_description": getattr(service, f"short_description_{lang}", service.short_description_en),
            "description": getattr(service, f"description_{lang}", service.description_en),
            "seo_title": getattr(service, f"seo_title_{lang}", service.seo_title_en),
            "seo_description": getattr(service, f"seo_description_{lang}", service.seo_description_en),
        },
        "lang": lang,
        "request": request,  # для соцмереж і canonical
    }
    return render(request, "services/service_detail.html", context)


def faq_page(request):
    lang = get_language()

    faqs = FAQ.objects.filter(is_active=True).order_by("order")

    localized_faqs = [
        {
            "question": getattr(f, f"question_{lang}", f.question_en),
            "answer": getattr(f, f"answer_{lang}", f.answer_en),
        }
        for f in faqs
    ]

    context = {
        "faqs": localized_faqs,
        "lang": lang,
        "request": request,  # для canonical і OG
    }

    return render(request, "services/faq.html", context)

