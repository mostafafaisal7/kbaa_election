from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Q

from .forms import NominationForm, VoteForm
from .models import Session, Position, Voter, Nomination, Vote





# --- Helper for vote counts ---
def get_vote_counts(session, position):
    votes = (
        Vote.objects.filter(session=session, position=position)
        .values('nominee_id')
        .annotate(count=Count('id'))
    )
    return {v['nominee_id']: v['count'] for v in votes}



def home(request):
    """Home page with main navigation"""
    current_session = Session.objects.filter(
        status__in=['Nominations Open', 'Voting Open', 'Results Published']
    ).first()
    
    context = {
        'current_session': current_session,
        'nomination_open': current_session and current_session.status == 'Nominations Open',
        'voting_open': current_session and current_session.status == 'Voting Open',
        'results_published': current_session and current_session.status == 'Results Published',
    }
    
    return render(request, 'election/home.html', context)

def nomination_view(request):
    # Get the current open nomination session
    current_session = Session.objects.filter(status='Nominations Open').first()

    if not current_session:
        return render(request, 'election/nomination_closed.html')

    if request.method == 'POST':
        form = NominationForm(request.POST, request.FILES)
        if form.is_valid():
            nomination = form.save(commit=False)
            nomination.session = current_session

            # Prevent duplicate submission per session
            if current_session.nomination_set.filter(email=nomination.email).exists():
                messages.error(request, "You have already submitted a nomination for this session.")
            else:
                nomination.save()
                # Redirect to thank you page instead of showing message
                return redirect('nomination_success')
    else:
        form = NominationForm()

    return render(request, 'election/nomination_form.html', {
        'form': form,
        'session': current_session
    })


def nomination_success_view(request):
    """Thank you page after successful nomination"""
    return render(request, 'election/nomination_success.html')



def get_next_available_position(session, positions, current_position):
    """Find the next position that has approved candidates"""
    current_index = list(positions).index(current_position)
    
    for position in positions[current_index + 1:]:
        if Nomination.objects.filter(
            session=session, 
            desired_position=position, 
            approved=True
        ).exists():
            return position
    
    return None


def voting_view(request):
    session = Session.objects.filter(status='Voting Open').first()
    
    # Check if results are published - redirect to results page
    if not session:
        published_session = Session.objects.filter(status='Results Published').first()
        if published_session:
            return redirect('public_results')
        return render(request, 'election/voting_closed.html')

    # Get all positions ordered
    positions = Position.objects.all().order_by('order')
    
    # Determine which position to show
    next_position_id = request.GET.get('position')
    email = request.POST.get('email') or request.GET.get('email')
    
    if next_position_id:
        position = positions.get(id=next_position_id)
    else:
        # Find first position with candidates
        position = None
        for pos in positions:
            if Nomination.objects.filter(
                session=session, 
                desired_position=pos, 
                approved=True
            ).exists():
                position = pos
                break
        
        if not position:
            # No positions available - redirect to fresh voting with completion message
            return redirect('/voting/?completed=true')

    # Fetch existing voter if any
    voter = None
    if email:
        voter = Voter.objects.filter(session=session, email=email).first()

    # Check if voter has already voted for this position
    already_voted = False
    if voter:
        already_voted = Vote.objects.filter(
            session=session,
            voter=voter,
            position=position
        ).exists()

    if request.method == 'POST':
        form = VoteForm(request.POST, session=session, position=position)
        if form.is_valid():
            # Create or update voter
            voter, created = Voter.objects.update_or_create(
                session=session,
                email=form.cleaned_data['email'],
                defaults={
                    'full_name': form.cleaned_data['full_name'],
                    'gender': form.cleaned_data['gender'],
                    'designation': form.cleaned_data['designation'],
                    'workplace_address': form.cleaned_data['workplace_address'],
                    'last_training_date': form.cleaned_data['last_training_date'],
                }
            )

            # Check if already voted for this position
            if Vote.objects.filter(session=session, voter=voter, position=position).exists():
                messages.warning(request, "You have already voted for this position.")
                # Find next available position
                next_position = get_next_available_position(session, positions, position)
                if next_position:
                    return redirect(f'/voting/?position={next_position.id}&email={voter.email}')
                else:
                    # All done - show completion alert
                    return redirect('/voting/?completed=true')

            # Save vote
            candidate_id = form.cleaned_data['candidate']
            candidate = Nomination.objects.get(id=candidate_id)
            Vote.objects.create(
                session=session,
                voter=voter,
                position=position,
                nominee=candidate
            )

            # Find next available position with candidates
            next_position = get_next_available_position(session, positions, position)
            
            if next_position:
                return redirect(f'/voting/?position={next_position.id}&email={voter.email}&voted=true')
            else:
                # All positions voted - show completion alert and fresh form
                return redirect('/voting/?completed=true')
    else:
        form = VoteForm(session=session, position=position)
        
        # Pre-fill voter data if exists
        if voter:
            form.fields['full_name'].initial = voter.full_name
            form.fields['email'].initial = voter.email
            form.fields['gender'].initial = voter.gender
            form.fields['designation'].initial = voter.designation
            form.fields['workplace_address'].initial = voter.workplace_address
            form.fields['last_training_date'].initial = voter.last_training_date

    # Get candidates without vote counts
    candidates = Nomination.objects.filter(
        session=session, 
        desired_position=position, 
        approved=True
    )

    # Check if showing success message
    show_success = request.GET.get('voted') == 'true'
    show_complete = request.GET.get('completed') == 'true'

    context = {
        'form': form,
        'position': position,
        'candidates': candidates,
        'voter': voter,
        'session': session,
        'already_voted': already_voted,
        'is_first_vote': not voter,
        'show_success': show_success,
        'show_complete': show_complete,
    }
    
    return render(request, 'election/voting.html', context)
# --- API for real-time vote counts ---
def vote_counts_api(request, position_id):
    session = Session.objects.filter(status='Voting Open').first()
    if not session:
        return JsonResponse([], safe=False)

    position = Position.objects.get(id=position_id)
    vote_counts = get_vote_counts(session, position)

    data = [{'nomination_id': k, 'count': v} for k, v in vote_counts.items()]
    return JsonResponse(data, safe=False)



# Add this to your existing views.py

def public_results_view(request):
    """Public results page for voters"""
    
    # Get session with published results
    session = Session.objects.filter(status='Results Published').first()
    
    if not session:
        # If no published results, check if voting is still open
        session = Session.objects.filter(status='Voting Open').first()
        if session:
            return render(request, 'election/results_not_published.html', {'session': session})
        else:
            return render(request, 'election/results_not_published.html')
    
    # Get results by position
    positions = Position.objects.all().order_by('order')
    results = []
    
    for position in positions:
        candidates = Nomination.objects.filter(
            session=session,
            desired_position=position,
            approved=True
        ).annotate(
            vote_count=Count('votes', filter=Q(votes__session=session, votes__position=position))
        ).order_by('-vote_count')
        
        if candidates.exists():
            results.append({
                'position': position,
                'candidates': candidates,
                'total_votes': sum(c.vote_count for c in candidates)
            })
    
    context = {
        'results': results,
        'session': session,
    }
    
    return render(request, 'election/public_results.html', context)