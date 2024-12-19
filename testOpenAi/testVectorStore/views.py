# Create your views here.
import os
import tempfile

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from openai import OpenAI
from rest_framework.permissions import IsAuthenticated
import requests
from urllib.parse import urlsplit, unquote


class DocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Check if a file was uploaded
        data = request.data
        try:
            if data and "files" in data and "vector_store_id" in data and "assistant_id" in data:
                file_paths = []
                files = data["files"]
                assistant_id = data["assistant_id"]
                vector_store_id = data["vector_store_id"]
                print(type(files))
                if type(files) == list:
                    for file in files:
                        file_to_upload = requests.get(url=file)
                        if file_to_upload.status_code == 200:
                            file_name_original = ""
                            if 'Content-Disposition' in file_to_upload.headers:
                                content_disposition = file_to_upload.headers['Content-Disposition']
                                file_name_original = content_disposition
                                file_name_original = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{file_name_original}"
                            else:
                                filename = os.path.basename(urlsplit(file).path)
                                file_name_original = unquote(filename)
                                file_name_original = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{file_name_original}"
                            with open(file_name_original, 'wb+') as destination:
                                destination.write(file_to_upload.content)
                            file_paths.append(file_name_original)

                elif type(files) == str:
                    file_to_upload = requests.get(url=files)
                    if file_to_upload.status_code == 200:
                        file_name_original = ""
                        if 'Content-Disposition' in file_to_upload.headers:
                            content_disposition = file_to_upload.headers['Content-Disposition']
                            file_name_original = content_disposition
                            file_name_original = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{file_name_original}"
                        else:
                            filename = os.path.basename(urlsplit(files).path)
                            file_name_original = unquote(filename)
                            file_name_original = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{file_name_original}"
                        with open(file_name_original, 'wb+') as destination:
                            destination.write(file_to_upload.content)
                        file_paths.append(file_name_original)
                            # Define a unique file name based on the current timestamp

                client = OpenAI()
                if not vector_store_id:
                    if "case_name" in data:
                        vector_store = client.beta.vector_stores.create(name=data["case_name"]+"Vector_store")
                        vector_store_id = vector_store.id
                    else:
                        return Response({"message": "case_name parameter not found"}, status=status.HTTP_400_BAD_REQUEST)

                file_streams = [open(path, "rb") for path in file_paths]

                file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id, files=file_streams
                )

                assistant = client.beta.assistants.update(
                assistant_id=assistant_id,
                tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
                )
                print(assistant)
                for fileStream in file_streams:
                    fileStream.close()
                for file in file_paths:
                    os.remove(file)
                return Response({"message": "File/s uploaded successfully!", "vector_store_id": vector_store_id, "assistant_id":assistant_id}, status=status.HTTP_201_CREATED)

            else:
                return Response({"message": "Not enough parameters found"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"message": "Unexpected error: "+str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):

        return Response({"message": "Request excecuted correctly"}, status=status.HTTP_201_CREATED)
    

