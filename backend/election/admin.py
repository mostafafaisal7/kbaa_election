# admin.py
from django.contrib import admin
from .models import Session, Position, Nomination, Voter, Vote, FormLabel

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'status', 'start_nomination', 'end_nomination', 'start_voting', 'end_voting')
    list_filter = ('status',)
    search_fields = ('name',)
    actions = ['open_nominations', 'close_nominations', 'open_voting', 'close_voting']

    def open_nominations(self, request, queryset):
        queryset.update(status="Nominations Open")
    open_nominations.short_description = "Open Nominations"

    def close_nominations(self, request, queryset):
        queryset.update(status="Closed")
    close_nominations.short_description = "Close Nominations"

    def open_voting(self, request, queryset):
        queryset.update(status="Voting Open")
    open_voting.short_description = "Open Voting"

    def close_voting(self, request, queryset):
        queryset.update(status="Closed")
    close_voting.short_description = "Close Voting"


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(Nomination)
class NominationAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'desired_position', 'approved', 'session')
    list_filter = ('approved', 'desired_position', 'session')
    actions = ['approve_nominations', 'reject_nominations']

    def approve_nominations(self, request, queryset):
        queryset.update(approved=True)
    approve_nominations.short_description = "Approve selected nominations"

    def reject_nominations(self, request, queryset):
        queryset.update(approved=False)
    reject_nominations.short_description = "Reject selected nominations"

@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'session', 'voted_at')
    list_filter = ('session',)


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('voter', 'candidate_name', 'position', 'session', 'created_at')
    list_filter = ('session','position')

    def candidate_name(self, obj):
        return obj.nominee.full_name if obj.nominee else "-"
    candidate_name.admin_order_field = 'nominee__full_name'
    candidate_name.short_description = 'Candidate'



@admin.register(FormLabel)
class FormLabelAdmin(admin.ModelAdmin):
    list_display = ('form_type', 'field_name', 'label_text')
    list_filter = ('form_type',)
