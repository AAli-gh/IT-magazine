from django import forms
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Notification, Subscriber
from .services import send_confirmation


class SubscribeForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "ایمیل شما", "dir": "ltr"}))
    website = forms.CharField(required=False)  # honeypot


@require_POST
def subscribe(request):
    form = SubscribeForm(request.POST)
    context = {"form": form}
    if form.is_valid() and not form.cleaned_data["website"]:
        email = form.cleaned_data["email"].lower()
        subscriber, created = Subscriber.objects.get_or_create(
            email=email, defaults={"user": request.user if request.user.is_authenticated else None},
        )
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=["is_active"])
        if not subscriber.is_confirmed:
            send_confirmation(subscriber)
        context = {"done": True, "confirmed": subscriber.is_confirmed}
    template = "newsletter/partials/subscribe_form.html"
    if not request.headers.get("HX-Request"):
        return render(request, "newsletter/status.html", {"state": "sent" if context.get("done") else "invalid"})
    return render(request, template, context)


def confirm(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    if not subscriber.is_confirmed:
        subscriber.is_confirmed = True
        subscriber.is_active = True
        subscriber.confirmed_at = timezone.now()
        subscriber.save(update_fields=["is_confirmed", "is_active", "confirmed_at"])
    return render(request, "newsletter/status.html", {"state": "confirmed", "subscriber": subscriber})


def unsubscribe(request, token):
    subscriber = get_object_or_404(Subscriber, token=token)
    if request.method == "POST":
        subscriber.is_active = False
        subscriber.save(update_fields=["is_active"])
        return render(request, "newsletter/status.html", {"state": "unsubscribed"})
    return render(request, "newsletter/status.html", {"state": "confirm_unsubscribe", "subscriber": subscriber})


@login_required
def notifications(request):
    qs = request.user.notifications.all()
    page = Paginator(qs, 30).get_page(request.GET.get("page"))
    response = render(request, "newsletter/notifications.html", {"page_obj": page})
    qs.filter(is_read=False).update(is_read=True)
    return response


@login_required
def open_notification(request, pk):
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return redirect(notification.url)
