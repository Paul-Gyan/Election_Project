from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Candidate(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class PollingCenter(models.Model):
    region = models.CharField(max_length=100)
    constituency = models.CharField(max_length=100)


    def __str__(self):
        return f"{self.region} - {self.constituency}"
    
class VoteSubmission(models.Model):
    candidate = models.ForeignKey('Candidate', on_delete=models.CASCADE)
    polling_center = models.ForeignKey('PollingCenter', on_delete=models.CASCADE)
    votes = models.PositiveIntegerField()
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.candidate} - {self.polling_center} ({self.votes} votes)'
    

