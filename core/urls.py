from django.urls import path
from .views import CandidateList, PollingCenterList, VoteSubmissionList, ResultView
from .views import vote_form
from .views import results_dashboard
from .views import export_results_pdf, export_results_excel

urlpatterns = [
    path('candidates/', CandidateList.as_view()),
    path('polling-centers/', PollingCenterList.as_view()),
    path('vote-submission/', VoteSubmissionList.as_view()),
    path('results/', ResultView.as_view()),
    path('submit-vote/', vote_form, name='vote-form'),
    path('results-dashboard/', results_dashboard, name='results-dashboard'),
     path('export/pdf/', export_results_pdf, name='export-pdf'),
    path('export/excel/', export_results_excel, name='export-excel'),
]
