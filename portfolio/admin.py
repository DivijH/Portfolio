from django.contrib import admin

from . import models

# Register your models here.


admin.site.register(models.Experience)
admin.site.register(models.Blog)
admin.site.register(models.Project)
admin.site.register(models.Tag)
admin.site.register(models.Link)
admin.site.register(models.ImageLink)