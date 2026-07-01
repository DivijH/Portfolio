from . import models


def site(request):
    """Expose the singleton Profile (and derived socials) to every template."""
    try:
        profile = models.Profile.load()
    except Exception:
        # Database not migrated yet, etc. — fail soft so pages still render.
        profile = None
    return {'profile': profile}
