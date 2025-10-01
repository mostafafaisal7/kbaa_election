from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Add this as the first pattern

    path('nomination/', views.nomination_view, name='nomination'),
    path('nomination/success/', views.nomination_success_view, name='nomination_success'),  # Add this line
    path('voting/', views.voting_view, name='voting'),
    path('results/', views.public_results_view, name='public_results'),  # NEW
    path('api/vote_counts/<int:position_id>/', views.vote_counts_api, name='vote_counts_api'),
]