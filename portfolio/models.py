from django.db import models

# Create your models here.

class Experience(models.Model):
    company_name = models.CharField(max_length=50)
    job_title = models.CharField(max_length=50)
    start_date = models.CharField(max_length=10)
    end_date = models.CharField(max_length=10, null=True, blank=True)
    job_description = models.CharField(max_length=500)

    def __str__(self):
        return self.company_name + '(' + self.start_date + ')'

class Blog(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField(max_length=500)
    link = models.URLField(max_length=300)
    tags = models.CharField(max_length=50, default='')

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'Blogs'

class Tag(models.Model):
    tag_name = models.CharField(max_length=50, default='')

    def __str__(self):
        return self.tag_name

class Link(models.Model):
    link_name = models.CharField(max_length=50)
    link_desc = models.CharField(max_length=100)
    link_url = models.URLField(max_length=500)

    def __str__(self):
        return self.link_name

class Project(models.Model):
    title = models.CharField(max_length=100)
    summary = models.TextField(max_length=500)
    slug = models.SlugField(max_length=100, null=True)
    content = models.TextField(max_length=2000, null=True)
    tags = models.ManyToManyField(Tag)
    links = models.ManyToManyField(Link)

    def __str__(self):
        return self.title

class ImageLink(models.Model):
    link_name = models.CharField(max_length=50)
    google_drive_code = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.link_name