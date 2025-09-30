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
                messages.success(request, "Nomination submitted successfully!")
                return redirect('nomination')
    else:
        form = NominationForm()

    return render(request, 'election/nomination_form.html', {
        'form': form,
        'session': current_session
    })


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
    if not session:
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
            return render(request, 'election/voting_complete.html')

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
        # Handle AJAX request for real-time vote count
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            candidate_id = request.POST.get('candidate')
            if candidate_id:
                # Get updated vote count for this candidate
                vote_count = Vote.objects.filter(
                    session=session,
                    position=position,
                    nominee_id=candidate_id
                ).count()
                
                return JsonResponse({
                    'success': True,
                    'candidate_id': candidate_id,
                    'vote_count': vote_count
                })

        # Handle form submission
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
                    return render(request, 'election/voting_complete.html')

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
                return redirect(f'/voting/?position={next_position.id}&email={voter.email}')
            else:
                return render(request, 'election/voting_complete.html')
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

    # Get candidates with vote counts
    candidates = Nomination.objects.filter(
        session=session, 
        desired_position=position, 
        approved=True
    ).annotate(
        vote_count=Count('votes', filter=Q(votes__session=session, votes__position=position))
    )

    return render(request, 'election/voting.html', {
        'form': form,
        'position': position,
        'candidates': candidates,
        'voter': voter,
        'session': session,
        'already_voted': already_voted,
        'is_first_vote': not voter,  # True if this is their first vote
    })


# --- API for real-time vote counts ---
def vote_counts_api(request, position_id):
    session = Session.objects.filter(status='Voting Open').first()
    if not session:
        return JsonResponse([], safe=False)

    position = Position.objects.get(id=position_id)
    vote_counts = get_vote_counts(session, position)

    data = [{'nomination_id': k, 'count': v} for k, v in vote_counts.items()]
    return JsonResponse(data, safe=False)