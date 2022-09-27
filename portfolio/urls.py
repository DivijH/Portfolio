from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view()),
    path('gallery/', views.GalleryView.as_view()),
    path('blogs/', views.BlogView.as_view()),
    path('projects/', views.ProjectView.as_view()),
    path('contact/', views.ContactView.as_view()),
    path('projects/<str:slug>', views.SingleProjectView.as_view())
]
