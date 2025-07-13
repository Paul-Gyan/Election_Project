from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from datetime import datetime
from django.db.models import Sum
import io
from django.http import FileResponse, HttpResponse
from reportlab.pdfgen import canvas
from openpyxl import Workbook
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAdminUser
from .models import Candidate, PollingCenter, VoteSubmission
from .serializers import CandidateSerializer, PollingCenterSerializer, VoteSubmissionSerializer

# Create your views here.

class CandidateList(generics.ListCreateAPIView):
    queryset = Candidate.objects.all()
    serializer_class = CandidateSerializer
    permission_classes = [AllowAny]

class PollingCenterList(generics.ListCreateAPIView):
    queryset = PollingCenter.objects.all()
    serializer_class = PollingCenterSerializer
    permission_classes = [AllowAny]

class VoteSubmissionList(generics.ListCreateAPIView):
    queryset = VoteSubmission.objects.all()
    serializer_class = VoteSubmissionSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(submitted_by=self.request.user)

# views.py
from django.contrib.auth.views import LogoutView

class LogoutGetView(LogoutView):
    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class ResultView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        total_votes = VoteSubmission.objects.aggregate(total_votes=Sum('votes'))['total_votes'] or 0
        candidates = Candidate.objects.all()
        results = []

        for candidate in candidates:
            candidate_votes_qs = VoteSubmission.objects.filter(candidate=candidate)
            candidate_votes = candidate_votes_qs.aggregate(total_votes=Sum('votes'))['total_votes'] or 0
            percentage = (candidate_votes / total_votes * 100) if total_votes else 0

            results.append({
                'candidate': candidate.name,
                'votes': candidate_votes,
                'percentage': f"{percentage:.2f}%",
                'regions': list(candidate_votes_qs.values_list('polling_center__region', flat=True).distinct()),
                'constituencies': list(candidate_votes_qs.values_list('polling_center__constituency', flat=True).distinct()),
            })

        return Response(results)



# views.py
@login_required
def results_dashboard(request):
    from datetime import datetime
    from django.db.models import Sum

    region = request.GET.get('region')
    votes_qs = VoteSubmission.objects.all()

    if region:
        votes_qs = votes_qs.filter(polling_center__region=region)

    total_votes = votes_qs.aggregate(Sum('votes'))['votes__sum'] or 0
    candidates = Candidate.objects.all()
    results = []

    for candidate in candidates:
        candidate_votes_qs = votes_qs.filter(candidate=candidate)
        candidate_votes = candidate_votes_qs.aggregate(Sum('votes'))['votes__sum'] or 0
        percent = (candidate_votes / total_votes * 100) if total_votes else 0

        results.append({
            'candidate': candidate.name,
            'votes': candidate_votes,
            'percentage': round(percent, 2),
        })

    results.sort(key=lambda x: x['votes'], reverse=True)
    top_two = results[:2]
    all_regions = PollingCenter.objects.values_list('region', flat=True).distinct()

    return render(request, 'results_dashboard.html', {
        'results': results,
        'top_two': top_two,
        'regions': all_regions,
        'selected_region': region,
    })


from django.db.models import F

@login_required
def vote_form(request):
    if request.method == 'POST':
        candidate_id = request.POST.get('candidate')
        center_id = request.POST.get('polling_center')
        votes = request.POST.get('votes')

        VoteSubmission.objects.create(
            candidate_id=candidate_id,
            polling_center_id=center_id,
            votes=votes,
            submitted_by=request.user
        )
        messages.success(request, 'Vote submitted successfully!')
        return redirect('vote-form')

    centers = list(PollingCenter.objects.values('id', 'region', 'constituency'))
    regions = sorted({c['region'] for c in centers})

    return render(request, 'vote_form.html', {
    'candidates': Candidate.objects.all(),
    'polling_centers': list(PollingCenter.objects.values('id', 'region', 'constituency')),
    'regions': sorted({c['region'] for c in PollingCenter.objects.values('region')}),
})


def export_results_pdf(request):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer)
    y = 800
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, y, "Election Results Summary")
    y -= 40

    candidates = Candidate.objects.all()
    total_votes = VoteSubmission.objects.aggregate(Sum('votes'))['votes__sum'] or 0

    for candidate in candidates:
        votes = VoteSubmission.objects.filter(candidate=candidate).aggregate(Sum('votes'))['votes__sum'] or 0
        percent = (votes / total_votes * 100) if total_votes else 0
        line = f"{candidate.name}: {votes} votes ({percent:.2f}%)"
        p.drawString(100, y, line)
        y -= 25

    p.showPage()
    p.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename='election_results.pdf')

def export_results_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Election Results"

    ws.append(["Region", "Constituency", "Candidate", "Votes", "Percentage"])

    total_votes = VoteSubmission.objects.aggregate(Sum('votes'))['votes__sum'] or 0

    # Group by region, constituency, and candidate
    grouped_votes = VoteSubmission.objects.select_related('polling_center', 'candidate') \
        .values('polling_center__region', 'polling_center__constituency', 'candidate__name') \
        .annotate(total_votes=Sum('votes'))

    for item in grouped_votes:
        region = item['polling_center__region']
        constituency = item['polling_center__constituency']
        candidate = item['candidate__name']
        votes = item['total_votes']
        percent = (votes / total_votes * 100) if total_votes else 0

        ws.append([region, constituency, candidate, votes, f"{percent:.2f}%"])

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="election_results.xlsx"'
    wb.save(response)
    return response


def vote_form(request):
    if request.method == 'POST':
        region = request.POST.get('region')
        constituency = request.POST.get('constituency')
        polling_center_id = request.POST.get('polling_center')
        polling_center = PollingCenter.objects.get(id=polling_center_id)

        candidates = Candidate.objects.all()
        for candidate in candidates:
            vote_key = f'votes_{candidate.id}'
            vote_val = request.POST.get(vote_key)

            if vote_val and vote_val.strip():
                votes = int(vote_val)
                VoteSubmission.objects.create(
                    candidate=candidate,
                    polling_center=polling_center,
                    region=region,
                    constituency=constituency,
                    votes=votes
                )

        messages.success(request, "Votes successfully submitted.")
        return redirect('vote-form')

    # GET context:
    context = {
        'regions': PollingCenter.objects.values_list('region', flat=True).distinct(),
        'candidates': Candidate.objects.all(),
        'polling_centers': list(PollingCenter.objects.values()),  # JSON serializable
    }
    return render(request, 'vote_form.html', context)

def results_dashboard(request):
    region = request.GET.get("region")
    constituency = request.GET.get("constituency")

    filters = {}
    if region:
        filters["polling_center__region"] = region
    if constituency:
        filters["polling_center__constituency"] = constituency

    filtered_qs = VoteSubmission.objects.filter(**filters)

    total_votes = filtered_qs.aggregate(total_votes=Sum('votes'))['total_votes'] or 0
    candidates = Candidate.objects.all()
    aggregated_results = []

    for candidate in candidates:
        candidate_votes_qs = filtered_qs.filter(candidate=candidate)
        votes = candidate_votes_qs.aggregate(total=Sum('votes'))['total'] or 0
        percentage = (votes / total_votes * 100) if total_votes else 0

        aggregated_results.append({
            'candidate': candidate.name,
            'total_votes': votes,
            'percentage': f"{percentage:.2f}",
        })

    context = {
        'aggregated_results': aggregated_results,
        'all_regions': VoteSubmission.objects.values_list('polling_center__region', flat=True).distinct(),
        'all_constituencies': VoteSubmission.objects.values_list('polling_center__constituency', flat=True).distinct(),
        'selected_region': region,
        'selected_constituency': constituency,
    }
    return render(request, 'results_dashboard.html', context)