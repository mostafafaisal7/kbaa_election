from django.urls import path
from . import admin_views

urlpatterns = [
    path('dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('candidates/', admin_views.candidate_list, name='admin_candidates'),
    path('voters/', admin_views.voter_list, name='admin_voters'),
    path('votes/', admin_views.votes_list, name='admin_votes'),
    path('results/', admin_views.results_view, name='admin_results'),
    path('voting-control/', admin_views.voting_control, name='admin_voting_control'),
    path('publish-results/<int:session_id>/', admin_views.publish_results, name='admin_publish_results'),
    path('edit-session/<int:session_id>/', admin_views.edit_session, name='admin_edit_session'),
    path('candidate/<int:candidate_id>/', admin_views.candidate_detail, name='admin_candidate_detail'),
]