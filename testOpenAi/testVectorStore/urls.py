from django.urls import path

from .views import DocumentUploadView, CreateNewEnterpriseAssistant, EvaluateTermsAndConditions

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
    path('createTermsAssistant/', CreateNewEnterpriseAssistant.as_view(), name='validate-terms'),
    path('validateTerms/', EvaluateTermsAndConditions.as_view(), name='validate-terms'),

]
