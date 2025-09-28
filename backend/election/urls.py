from django.urls import path
from . import views

urlpatterns = [
    path('nomination/', views.nomination_view, name='nomination'),
    path('voting/', views.voting_view, name='voting'),
    path('api/vote_counts/<int:position_id>/', views.vote_counts_api, name='vote_counts_api'),


]
