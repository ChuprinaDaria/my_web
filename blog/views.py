from django.shortcuts import render, get_object_or_404, redirect
from django.utils.translation import get_language
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.core.paginator import Paginator

from .models import BlogPost, BlogPostRating
from services.models import ServiceCategory


def blog_list(request):
    lang = get_language() or "uk"
    posts_qs = BlogPost.objects.filter(is_published=True).order_by("-published_at", "-created_at")

    paginator = Paginator(posts_qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    posts = []
    for post in page_obj:
        avg, count = post.get_average_rating()
        posts.append(
            {
                "object": post,
                "slug": post.slug,
                "title": post.get_title(lang),
                "short": post.get_short(lang),
                "main_image": post.main_image,
                "average_rating": avg,
                "ratings_count": count,
            }
        )

    return render(
        request,
        "blog/blog_list.html",
        {
            "posts": posts,
            "page_obj": page_obj,
            "CURRENT_LANG": lang,
            "breadcrumbs": [
                {
                    "name": "Blog" if lang == "en" else ("Блог" if lang == "uk" else "Blog"),
                    "url": request.path,
                }
            ],
        },
    )


def blog_detail(request, slug):
    lang = get_language() or "uk"
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)

    title = post.get_title(lang)
    short = post.get_short(lang)
    content = post.get_content(lang)
    gallery = post.get_gallery_images()
    avg, count = post.get_average_rating()

    related_services = []
    for s in post.related_services.all():
        related_services.append(
            {
                "slug": s.slug,
                "title": s.get_title(lang),
                "short": s.get_short(lang),
                "main_image": s.main_image,
                "icon": s.icon,
            }
        )

    og_title = post.get_seo_title(lang)
    og_description = post.get_seo_description(lang)
    og_image_url = None
    if post.og_image:
        og_image_url = request.build_absolute_uri(post.og_image.url)
    elif post.main_image:
        og_image_url = request.build_absolute_uri(post.main_image.url)

    return render(
        request,
        "blog/blog_detail.html",
        {
            "post": post,
            "title": title,
            "short": short,
            "content": content,
            "main_image": post.main_image,
            "gallery": gallery,
            "related_services": related_services,
            "average_rating": avg,
            "ratings_count": count,
            "CURRENT_LANG": lang,
            "og_title": og_title,
            "og_description": og_description,
            "og_image": og_image_url,
            "og_url": request.build_absolute_uri(),
            "breadcrumbs": [
                {
                    "name": "Blog" if lang == "en" else ("Блог" if lang == "uk" else "Blog"),
                    "url": f"/{lang}/blog/" if lang != "en" else "/blog/",
                },
                {
                    "name": title,
                    "url": request.path,
                },
            ],
        },
    )


@require_POST
def rate_post(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    try:
        score = int(request.POST.get("score", 0))
    except ValueError:
        score = 0

    if 1 <= score <= 5:
        ip = request.META.get("REMOTE_ADDR")
        ua = request.META.get("HTTP_USER_AGENT", "")[:500]
        BlogPostRating.objects.create(post=post, score=score, ip_address=ip, user_agent=ua)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        avg, count = post.get_average_rating()
        return JsonResponse({"average": avg, "count": count})

    return redirect("blog:blog_detail", slug=post.slug)

