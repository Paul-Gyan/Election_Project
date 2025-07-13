from django.contrib import admin
from .models import Candidate, PollingCenter, VoteSubmission

# Register your models here.

@admin.register(PollingCenter)
class PollingCenterAdmin(admin.ModelAdmin):
    list_display = ('constituency', 'region')
    list_filter = ('region', 'constituency')  # ✅ add dropdown filters
    search_fields = ( 'constituency', 'region')

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(VoteSubmission)
class VoteSubmissionAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'polling_center', 'votes')
    list_filter = ('polling_center__region', 'polling_center__constituency')
    search_fields = ('candidate__name', 'polling_center__name', 'submitted_by__username')