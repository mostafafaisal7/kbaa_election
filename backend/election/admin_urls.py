from django.urls import path
from . import admin_views

urlpatterns = [
    path('dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('candidates/', admin_views.candidate_list, name='admin_candidates'),
    path('voters/', admin_views.voter_list, name='admin_voters'),
    path('votes/', admin_views.votes_list, name='admin_votes'),
    path('results/', admin_views.results_view, name='admin_results'),
    path('voting-control/', admin_views.voting_control, name='admin_voting_control'),
]