# Create your models here.
from django.db import models

class Company(models.Model):
    id_company = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_assistant = models.CharField(max_length=30)
    id_vector_store = models.CharField(max_length=30)
