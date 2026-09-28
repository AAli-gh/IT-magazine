"""Editorial roles.

- نویسندگان (Authors): write their own articles, upload images, submit for review. Cannot publish.
- سردبیران (Editors): everything editorial, including publishing, featuring, comments, banners, pages.
"""

from django.contrib.auth.models import Group, Permission

AUTHORS = "نویسندگان"
EDITORS = "سردبیران"

AUTHOR_PERMS = [
    "magazine.add_article", "magazine.change_article", "magazine.view_article",
    "magazine.view_category", "magazine.view_tag", "magazine.add_tag",
    "magazine.add_mediafile", "magazine.view_mediafile", "magazine.change_mediafile",
    "magazine.add_interviewqa", "magazine.change_interviewqa", "magazine.delete_interviewqa",
    "magazine.view_interviewqa",
]

EDITOR_MODELS = {
    "magazine": ["article", "category", "tag", "mediafile", "interviewqa", "newssource"],
    "interactions": ["comment"],
    "core": ["banner", "page"],
    "newsletter": ["subscriber", "newsletterissue"],
}


def _perms(codes):
    result = []
    for code in codes:
        app_label, codename = code.split(".")
        perm = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
        if perm:
            result.append(perm)
    return result


def ensure_roles(**kwargs):
    authors, _ = Group.objects.get_or_create(name=AUTHORS)
    authors.permissions.set(_perms(AUTHOR_PERMS))

    editor_codes = ["magazine.publish_article", "core.view_sitesettings", "core.change_sitesettings"]
    for app_label, models in EDITOR_MODELS.items():
        for model in models:
            for action in ("add", "change", "delete", "view"):
                editor_codes.append(f"{app_label}.{action}_{model}")
    editors, _ = Group.objects.get_or_create(name=EDITORS)
    editors.permissions.set(_perms(editor_codes))


def make_author(user):
    user.is_author = True
    user.is_staff = True
    user.save(update_fields=["is_author", "is_staff"])
    user.groups.add(Group.objects.get(name=AUTHORS))


def make_editor(user):
    make_author(user)
    user.groups.add(Group.objects.get(name=EDITORS))
