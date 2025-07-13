from rest_framework import serializers
from .models import Candidate, PollingCenter, VoteSubmission

class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Candidate
        fields = ['id', 'name']  

class PollingCenterSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollingCenter
        fields = ['id', 'name', 'constituency', 'region']  #  include new field

class VoteSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoteSubmission
        fields = ['id', 'votes', 'candidate', 'polling_center', 'submitted_by', 'timestamp']
        read_only_fields = ['submitted_by', 'timestamp']  # these should be set automatically
