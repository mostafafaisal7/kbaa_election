from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from .models import Session, Position, Voter, Nomination, Vote


@staff_member_required
def admin_dashboard(request):
    """Custom admin dashboard with statistics"""
    
    # Get current active session
    current_session = Session.objects.filter(
        status__in=['Nominations Open', 'Voting Open']
    ).first()
    
    if not current_session:
        current_session = Session.objects.last()
    
    # Statistics
    total_voters = Voter.objects.filter(session=current_session).count() if current_session else 0
    total_candidates = Nomination.objects.filter(
        session=current_session, 
        approved=True
    ).count() if current_session else 0
    total_positions = Position.objects.count()
    
    # Get limited data for dashboard
    candidates = Nomination.objects.filter(
        session=current_session
    ).annotate(
        vote_count=Count('votes')
    ).order_by('-vote_count')[:5]
    
    voters = Voter.objects.filter(session=current_session).order_by('-voted_at')[:6]
    
    context = {
        'total_voters': total_voters,
        'total_candidates': total_candidates,
        'total_positions': total_positions,
        'current_session': current_session,
        'candidates': candidates,
        'voters': voters,
    }
    
    return render(request, 'admin/dashboard.html', context)


@staff_member_required
def candidate_list(request):
    """List all candidates with vote counts"""
    
    current_session = Session.objects.filter(
        status__in=['Nominations Open', 'Voting Open']
    ).first()
    
    if not current_session:
        current_session = Session.objects.last()
    
    # Get candidates with vote counts
    candidates = Nomination.objects.filter(
        session=current_session
    ).annotate(
        vote_count=Count('votes')
    ).order_by('-vote_count')
    
    context = {
        'candidates': candidates,
        'current_session': current_session,
    }
    
    return render(request, 'admin/candidate_list.html', context)


@staff_member_required
def voter_list(request):
    """List all voters"""
    
    current_session = Session.objects.filter(
        status__in=['Nominations Open', 'Voting Open']
    ).first()
    
    if not current_session:
        current_session = Session.objects.last()
    
    voters = Voter.objects.filter(session=current_session).order_by('-voted_at')
    
    context = {
        'voters': voters,
        'current_session': current_session,
    }
    
    return render(request, 'admin/voter_list.html', context)


@staff_member_required
def votes_list(request):
    """List all votes"""
    
    current_session = Session.objects.filter(
        status__in=['Nominations Open', 'Voting Open']
    ).first()
    
    if not current_session:
        current_session = Session.objects.last()
    
    votes = Vote.objects.filter(session=current_session).select_related(
        'voter', 'nominee', 'position'
    ).order_by('-created_at')
    
    context = {
        'votes': votes,
        'current_session': current_session,
    }
    
    return render(request, 'admin/votes_list.html', context)


@staff_member_required
def results_view(request):
    """Show election results"""
    
    current_session = Session.objects.filter(
        status__in=['Voting Open', 'Closed']
    ).first()
    
    if not current_session:
        current_session = Session.objects.last()
    
    # Get results by position
    positions = Position.objects.all().order_by('order')
    results = []
    
    for position in positions:
        candidates = Nomination.objects.filter(
            session=current_session,
            desired_position=position,
            approved=True
        ).annotate(
            vote_count=Count('votes', filter=Q(votes__session=current_session, votes__position=position))
        ).order_by('-vote_count')
        
        if candidates.exists():
            results.append({
                'position': position,
                'candidates': candidates
            })
    
    context = {
        'results': results,
        'current_session': current_session,
    }
    
    return render(request, 'admin/results.html', context)


@staff_member_required
def voting_control(request):
    """Voting control page"""
    
    sessions = Session.objects.all().order_by('-created_at')
    
    context = {
        'sessions': sessions,
    }
    
    return render(request, 'admin/voting_control.html', context)