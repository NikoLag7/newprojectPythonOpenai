

# Create your views here.
import os
#from dotenv import load_dotenv
from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from openai import OpenAI
#from decouple import config


#load_dotenv()

class DocumentUploadView(APIView):
    def post(self, request, *args, **kwargs):
        # Check if a file was uploaded
        file = request.FILES.get('file')
        if not file:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Define the directory where files will be saved
        upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # Define a unique file name based on the current timestamp
        file_name = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{file.name}"
        file_path = os.path.join(upload_dir, file_name)

        # Save the file to the file system
        with open(file_path, 'wb+') as destination:
            for chunk in file.chunks():
                destination.write(chunk)

        OPENAI_API_KEY = config('OPENAI_API_KEY', default='clave-defecto')

        client = OpenAI()
        
        print(OPENAI_API_KEY)
        assistant = client.beta.assistants.create(
        name="Software developer expert",
        instructions="You are expert in develop tecnology.",
        model="gpt-4o-mini",
        tools=[{"type": "file_search"}],
        )



        vector_store = client.beta.vector_stores.create(name="FFF")

        file_paths = [file_path]
        file_streams = [open(path, "rb") for path in file_paths]




        file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
        )

        print(file_batch.status)
        print(file_batch.file_counts)


        assistant = client.beta.assistants.update(
        assistant_id=assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )

        print(assistant)    

        return Response({"message": "File uploaded successfully!", "file_path": file_path}, status=status.HTTP_201_CREATED)
    

