"""Staff-only endpoints used by the admin Markdown editor."""

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_image_file_extension
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

from .models import Article, MediaFile
from .rendering import render_markdown


@staff_member_required
@require_POST
def preview(request):
    html, _ = render_markdown(request.POST.get("text", ""))
    return HttpResponse(html)


@staff_member_required
@require_POST
def upload_image(request):
    if not request.user.has_perm("magazine.add_mediafile"):
        return JsonResponse({"error": "دسترسی ندارید"}, status=403)
    image = request.FILES.get("image")
    if not image:
        return JsonResponse({"error": "فایلی ارسال نشد"}, status=400)
    limit_mb = settings.MAX_IMAGE_UPLOAD_MB
    if image.size > limit_mb * 1024 * 1024:
        return JsonResponse({"error": f"حداکثر حجم {limit_mb} مگابایت است"}, status=400)
    try:
        validate_image_file_extension(image)
    except ValidationError:
        return JsonResponse({"error": "فرمت تصویر پشتیبانی نمی‌شود"}, status=400)
    article = Article.objects.filter(pk=request.POST.get("article") or 0).first()
    media = MediaFile(image=image, article=article, uploaded_by=request.user,
                      alt=image.name.rsplit(".", 1)[0][:200])
    try:
        media.full_clean(exclude=["article", "uploaded_by"])
    except ValidationError:
        return JsonResponse({"error": "فایل تصویر معتبر نیست"}, status=400)
    media.save()
    return JsonResponse({"url": media.image.url, "markdown": media.markdown})
