from django.shortcuts import render, get_object_or_404
from .models import Project
from services.models import ServiceCategory
from django.utils.translation import get_language
from django.http import JsonResponse
from django.http import HttpResponse

def projects_list(request):
    

    lang = get_language()

    categories = ServiceCategory.objects.prefetch_related('projects').all()

    localized_categories = []
    for category in categories:
        projects = category.projects.filter(is_active=True)

        localized_projects = []
        for project in projects:
            localized_projects.append({
                "slug": project.slug,
                "featured_image": project.featured_image,
                "title": getattr(project, f"title_{lang}", project.title_en),
                "short_description": getattr(project, f"short_description_{lang}", project.short_description_en),
            })

        localized_categories.append({
            "title": getattr(category, f"title_{lang}", category.title_en),
            "description": getattr(category, f"description_{lang}", category.description_en),
            "projects": localized_projects
        })

    context = {
        "categories": localized_categories,
        "overview_title": {
            "en": "Projects we’re proud of",
            "uk": "Проєкти, якими ми пишаємося",
            "pl": "Projekty, z których jesteśmy dumni"
        }.get(lang, ""),
        "overview_description": {
            "en": "We bring real value to clients by automating what matters most.",
            "uk": "Ми приносимо реальну цінність автоматизуючи те, що важливо.",
            "pl": "Przynosimy realną wartość, automatyzując to, co najważniejsze."
        }.get(lang, ""),
        "seo_title": {
            "en": "Our Projects | Lazysoft",
            "uk": "Наші проєкти | Lazysoft",
            "pl": "Nasze projekty | Lazysoft"
        }.get(lang, "Our Projects | Lazysoft"),
        "seo_description": {
            "en": "Explore our automation and AI projects.",
            "uk": "Ознайомтеся з нашими проєктами автоматизації та ШІ.",
            "pl": "Zobacz nasze projekty automatyzacji i AI."
        }.get(lang, ""),
        "lang": lang,
    }
    print("Категорії з проєктами:", localized_categories)
    
    return render(request, "projects/projects.html", context)




def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug, is_active=True)
    current_lang = get_language()

    title = getattr(project, f"title_{current_lang}", project.title_en)
    seo_title = getattr(project, f"seo_title_{current_lang}", project.seo_title_en)
    seo_description = getattr(project, f"seo_description_{current_lang}", project.seo_description_en)

    context = {
        "project": project,
        "title": title,
        "seo_title": seo_title,
        "seo_description": seo_description,
    }
    return render(request, "projects/project_detail.html", context)


def projects_api(request):
    data = list(Project.objects.filter(is_active=True).values("title_en", "slug", "project_date"))
    return JsonResponse({"projects": data})



def project_contact_submit(request, slug):
    return HttpResponse("Contact form submission is not implemented yet.")
