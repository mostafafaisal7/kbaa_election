from django.db import models
from django.core.validators import FileExtensionValidator


# -----------------------------
# 1. Session / Election Cycle
# -----------------------------
class Session(models.Model):
    name = models.CharField(max_length=100, unique=True)
    start_nomination = models.DateTimeField()
    end_nomination = models.DateTimeField()
    start_voting = models.DateTimeField()
    end_voting = models.DateTimeField()

    # Admin manual control
    nomination_open = models.BooleanField(default=False)
    voting_open = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ("Nominations Open", "Nominations Open"),
        ("Voting Open", "Voting Open"),
        ("Results Published", "Results Published"),  # NEW STATUS
        ("Closed", "Closed"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Nominations Open")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
# -----------------------------
# 2. Position
# -----------------------------
class Position(models.Model):
    name = models.CharField(max_length=100, unique=True)
    order = models.PositiveIntegerField(default=0, help_text="Controls order in multi-step voting")

    def __str__(self):
        return self.name


# -----------------------------
# 3. Nomination (Candidate) - UPDATED
# -----------------------------
class Nomination(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)  # NEW FIELD
    gender = models.CharField(max_length=10, choices=[("Male", "Male"), ("Female", "Female")])
    designation = models.CharField(max_length=100)
    workplace_address = models.CharField(max_length=255)
    last_training_date = models.DateField(blank=True, null=True)  # NEW FIELD
    interested = models.BooleanField(default=True)
    desired_position = models.ForeignKey(Position, on_delete=models.SET_NULL, null=True)
    approved = models.BooleanField(default=False)
    photo = models.ImageField(
        upload_to="candidate_photos/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png"])],
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("session", "email")

    def __str__(self):
        return f"{self.full_name} ({self.desired_position})"


# -----------------------------
# 4. Voter
# -----------------------------
class Voter(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    gender = models.CharField(max_length=10, choices=[("Male", "Male"), ("Female", "Female")])
    designation = models.CharField(max_length=100)
    workplace_address = models.CharField(max_length=255)
    last_training_date = models.DateField(blank=True, null=True)
    voted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("session", "email")

    def __str__(self):
        return f"{self.full_name} ({self.email})"


# -----------------------------
# 5. Vote
# -----------------------------
class Vote(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE)
    position = models.ForeignKey(Position, on_delete=models.CASCADE)
    nominee = models.ForeignKey(Nomination, on_delete=models.CASCADE, related_name="votes")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("voter", "position")  # prevent multiple votes for same position

    def __str__(self):
        return f"{self.voter.full_name} -> {self.nominee.full_name} ({self.position.name})"


# -----------------------------
# 6. Form Labels
# -----------------------------
class FormLabel(models.Model):
    FORM_CHOICES = [
        ("nominee", "Nominee Form"),
        ("voter", "Voter Form"),
    ]
    form_type = models.CharField(max_length=10, choices=FORM_CHOICES)
    field_name = models.CharField(max_length=50)
    label_text = models.CharField(max_length=200)

    class Meta:
        unique_together = ("form_type", "field_name")

    def __str__(self):
        return f"{self.get_form_type_display()} - {self.field_name} → {self.label_text}"