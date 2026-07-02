from django.urls import path

from . import views

app_name = 'portfolio'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('research/', views.ResearchView.as_view(), name='research'),
    path('publications/', views.PublicationsView.as_view(), name='publications'),
    path('publications/<slug:slug>/', views.SinglePublicationView.as_view(), name='publication'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('electionbench/', views.ElectionBenchView.as_view(), name='electionbench'),
    path('electionbench/ingest/', views.electionbench_ingest, name='electionbench_ingest'),
    path('electionbench/h2h/', views.electionbench_h2h, name='electionbench_h2h'),
    path('electionbench/game/<int:game_id>/', views.electionbench_game, name='electionbench_game'),
    path('electionbench/game/<int:game_id>/full/', views.electionbench_game_full, name='electionbench_game_full'),
]
