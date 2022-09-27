from django.shortcuts import render
from django.views import View

from . import models

# Create your views here.

class IndexView(View):
    def get(self, request):
        experiences = models.Experience.objects.all().order_by('-id')
        return render(request, 'portfolio/index.html', {'experiences' : experiences})

class BlogView(View):
    def get(self, request):
        blogs = models.Blog.objects.all().order_by('-id')
        return render(request, 'portfolio/blogs.html', {'blogs':blogs})

class ProjectView(View):
    def get(self, request):
        if len(request.GET)!=0:
            search_name = request.GET['tag']
            projects = models.Project.objects.all().filter(tags__tag_name = search_name).order_by('-id')
        else:
            search_name = ''
            projects = models.Project.objects.all().order_by('-id')
        tags = models.Tag.objects.all()
        return render(request, 'portfolio/projects.html', {'search':search_name, 'projects':projects, 'tags':tags})
    
class SingleProjectView(View):
    def get(self, request, slug):
        project = models.Project.objects.filter(slug=slug)
        return render(request, f'portfolio/project.html', {'project':project[0]})

class ContactView(View):
    def get(self, request):
        return render(request, 'portfolio/contact.html')

class GalleryView(View):
    def get(self, request):
        images = models.ImageLink.objects.all().order_by('-id')
        return render(request, 'portfolio/gallery.html', {
            'images' : images
        })