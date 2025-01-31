from django.urls import path

from .views import DocumentUploadView, TermsAndPrivacityReadingView

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('validateTerms/', TermsAndPrivacityReadingView.as_view(), name='validate-terms'),

]
