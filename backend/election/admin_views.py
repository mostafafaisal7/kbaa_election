from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from .models import Session, Position, Voter, Nomination, Vote
from django.contrib import messages



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


@staff_member_required
def publish_results(request, session_id):
    """Publish election results and close voting"""
    if request.method == 'POST':
        session = Session.objects.get(id=session_id)
        session.status = 'Results Published'
        session.voting_open = False
        session.save()
        
        messages.success(request, f'Results published for {session.name}. Voting is now closed.')
    
    return redirect('admin_voting_control')


@staff_member_required
def edit_session(request, session_id):
    """Edit session - simplified form"""
    session = Session.objects.get(id=session_id)
    
    if request.method == 'POST':
        # Update session fields
        session.name = request.POST.get('name')
        session.status = request.POST.get('status')
        session.start_voting = request.POST.get('start_voting')
        session.end_voting = request.POST.get('end_voting')
        session.save()
        
        messages.success(request, f'Session "{session.name}" updated successfully!')
        return redirect('admin_voting_control')
    
    context = {
        'session': session,
    }
    
    return render(request, 'admin/edit_session.html', context)


@staff_member_required
def candidate_detail(request, candidate_id):
    """View and edit candidate details"""
    candidate = Nomination.objects.get(id=candidate_id)
    
    if request.method == 'POST':
        # Update candidate fields
        candidate.full_name = request.POST.get('full_name')
        candidate.email = request.POST.get('email')
        candidate.gender = request.POST.get('gender')
        candidate.designation = request.POST.get('designation')
        candidate.workplace_address = request.POST.get('workplace_address')
        candidate.approved = request.POST.get('approved') == 'on'
        
        # Handle photo upload
        if request.FILES.get('photo'):
            candidate.photo = request.FILES['photo']
        
        candidate.save()
        
        messages.success(request, f'Candidate "{candidate.full_name}" updated successfully!')
        return redirect('admin_candidates')
    
    # Get vote count
    vote_count = Vote.objects.filter(nominee=candidate).count()
    
    context = {
        'candidate': candidate,
        'vote_count': vote_count,
    }
    
    return render(request, 'admin/candidate_detail.html', context)


@staff_member_required
def voter_detail(request, voter_id):
    """View and edit voter details"""
    voter = Voter.objects.get(id=voter_id)
    
    if request.method == 'POST':
        # Update voter fields
        voter.full_name = request.POST.get('full_name')
        voter.email = request.POST.get('email')
        voter.gender = request.POST.get('gender')
        voter.designation = request.POST.get('designation')
        voter.workplace_address = request.POST.get('workplace_address')
        
        # Handle optional fields
        last_training_date = request.POST.get('last_training_date')
        if last_training_date:
            voter.last_training_date = last_training_date
        
        voter.save()
        
        messages.success(request, f'Voter "{voter.full_name}" updated successfully!')
        return redirect('admin_voters')
    
    # Get vote count for this voter
    votes_cast = Vote.objects.filter(voter=voter).count()
    
    context = {
        'voter': voter,
        'votes_cast': votes_cast,
    }
    
    return render(request, 'admin/voter_detail.html', context)