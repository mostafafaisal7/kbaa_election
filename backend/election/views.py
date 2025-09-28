from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count

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
def voting_view(request):
    session = Session.objects.filter(status='Voting Open').first()
    if not session:
        return render(request, 'election/voting_closed.html')

    # Determine which position to show next
    positions = Position.objects.all()
    next_position_id = request.GET.get('position')
    if next_position_id:
        position = positions.get(id=next_position_id)
    else:
        position = positions.first()

    # Fetch existing voter if any
    voter = None
    email = request.POST.get('email') or request.GET.get('email')
    if email:
        voter = Voter.objects.filter(session=session, email=email).first()

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

            # Save vote
            candidate_id = form.cleaned_data['candidate']
            candidate = Nomination.objects.get(id=candidate_id)
            Vote.objects.create(
                session=session,
                voter=voter,
                position=position,
                nominee=candidate
            )

            # Next position
            next_index = list(positions).index(position) + 1
            if next_index < len(positions):
                next_position = positions[next_index]
                return redirect(f'/voting/?position={next_position.id}&email={voter.email}')
            else:
                return render(request, 'election/voting_complete.html')
    else:
        form = VoteForm(session=session, position=position)

    # Prepare vote counts with aggregation
    candidates = Nomination.objects.filter(session=session, desired_position=position, approved=True)
    vote_counts = get_vote_counts(session, position)

    return render(request, 'election/voting.html', {
        'form': form,
        'position': position,
        'candidates': candidates,
        'vote_counts': vote_counts,
        'voter': voter,  # Pass voter object to template for pre-filling
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
