# Create your views here.
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from openai import OpenAI
from rest_framework.permissions import IsAuthenticated
import requests
from urllib.parse import urlsplit, unquote
from .company import *


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
                extensiones_imagen = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
                if type(files) == list:
                    for file in files:
                        # Verifica si alguna extensión de imagen está al final de la URL
                        if not any(file.lower().endswith(ext) for ext in extensiones_imagen):
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
                    if not any(files.lower().endswith(ext) for ext in extensiones_imagen):
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
                if len(file_paths) > 0:
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
                    return Response({"message": "Not valid files found"}, status=status.HTTP_204_NO_CONTENT)


            else:
                return Response({"message": "Not enough parameters found"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({"message": "Unexpected error: "+str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):

        return Response({"message": "Request excecuted correctly"}, status=status.HTTP_200_OK)
    

class CreateNewEnterpriseAssistant(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Check if a file was uploaded
        data = request.data
        try:
            if data and "URL" in data and "company_name" in data:
                file_paths = []
                terms = None
                privacity = None
                if "privacity" in data and "terms" in data:
                    terms = data["terms"]
                    privacity = data["privacity"]
                URL_pages = data["URL"]
                company_obj = None
                extensiones_imagen = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
                company_name = data["company_name"]
                company = CompanyClass()
                client = OpenAI()

                my_assistant = client.beta.assistants.create(
                    instructions="""Te desempeñas en un ambito legal. Eres un asistente de recolección y comparación de textos, con el fin de encontrar disparidades entre ambos textos.""",
                    name="Y-CORRECTOR AI-" + company_name,
                    tools=[{"type": "file_search"}],
                    model="gpt-4o-mini",
                )
                assistant_id = my_assistant.id
                print("ASISTENTE CREADO")

                urls_internas, terms, privacity = extract_internal_links(URL_pages)
                list_respuestas_page = []
                contentTXT = "Contenido de todas las paginas\n\n"
                for url in urls_internas:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
                    url_response_content = requests.get(url, headers=headers)
                    if url_response_content.status_code == 200:
                        soup = BeautifulSoup(url_response_content.text, "html.parser")
                        paragraphs = soup.find_all("p")
                        content = " ".join([p.get_text() for p in paragraphs])
                        contentTXT = contentTXT + "URL: {0} \n Content: {1} \n\n".format(url, content)

                filename_content = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{company_name}_pageContents.txt"
                with open(filename_content, "w", encoding="utf-8") as file:
                    file.write(contentTXT)
                    file_paths.append(file)

                clasificacion_enterprise = enviar_mensaje_asistente(assistant_id, "Segun las normas colombianas define cual es el objeto social de la empresa segun el contenido de sus paginas descrito en el siguiente texto: " + contentTXT)
                print(clasificacion_enterprise)

                if type(terms) != "text" and not terms.name.rsplit(".")[-1] in extensiones_imagen:
                    file_name_original = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{terms.name}"
                    file_terms = request.FILES.get('terms')
                    with open(file_name_original, 'wb+') as destination:
                        for chunk in file_terms.chunks():  # Escribir el archivo en partes
                          destination.write(chunk)
                    file_paths.append(file_name_original)
                elif terms is not None:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
                    url_response_content = requests.get(terms, headers=headers)
                    if url_response_content.status_code == 200:
                        soup = BeautifulSoup(url_response_content.text, "html.parser")
                        paragraphs = soup.find_all("p")
                        content = "Terminos y condiciones \n\n ".join([p.get_text() for p in paragraphs])
                        filename_content = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{company_name}_Terms.txt"
                        with open(filename_content, "w", encoding="utf-8") as file:
                            file.write(content)
                            file_paths.append(file)

                if type(privacity) != "text" and not privacity.name.rsplit(".")[-1] in extensiones_imagen:
                    file_name_original = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{privacity.name}"
                    file_privacity = request.FILES.get('privacity')
                    with open(file_name_original, 'wb+') as destination:
                        for chunk in file_privacity.chunks():  # Escribir el archivo en partes
                            destination.write(chunk)
                    file_paths.append(file_name_original)
                elif privacity is not None:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
                    url_response_content = requests.get(terms, headers=headers)
                    if url_response_content.status_code == 200:
                        soup = BeautifulSoup(url_response_content.text, "html.parser")
                        paragraphs = soup.find_all("p")
                        content = "Politica de privacidad \n\n ".join([p.get_text() for p in paragraphs])
                        filename_content = f"{timezone.now().strftime('%Y%m%d%H%M%S')}_{company_name}_Privacity.txt"
                        with open(filename_content, "w", encoding="utf-8") as file:
                            file.write(content)
                            file_paths.append(file)

                print("URLS PROCESADAS")

                vector_store = client.beta.vector_stores.create(
                    name="Y-CORRECTOR AI-" + company_name + "  Vector_store")
                vector_store_id = vector_store.id

                file_streams = [open(path, "rb") for path in file_paths]
                file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store_id, files=file_streams)
                assistant = client.beta.assistants.update(
                    assistant_id=assistant_id,
                    tool_resources={"file_search": {"vector_store_ids": [vector_store_id]}},
                )
                print("VECTOR STORE CREADO")
                for fileStream in file_streams:
                    fileStream.close()
                for file in file_paths:
                    os.remove(file)

                company_obj = company.create_company(id_assistant=assistant_id, id_vector_store=vector_store_id,
                                                     company_name=company_name)
                print("OBJETO ALMACENADO")

                return Response({"message": "New company created", "company_id": company_obj.id_company},
                                    status=status.HTTP_201_CREATED)

            return Response({"message": "Not enough parameters"}, status=status.HTTP_400_BAD_REQUEST)


        except Exception as exc:
            return Response({"message": "Unexpected error: "+str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):

        return Response({"message": "Request excecuted correctly"}, status=status.HTTP_200_OK)


class EvaluateTermsAndConditions(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Check if a file was uploaded
        data = request.data
        try:
            if data and "id_company" in data:
                company = CompanyClass()
                client = OpenAI()
                id_company = data["company_id"]
                company_obj = company.get_company(id_company)

                if company_obj:

                    print("ENVIANDO RESPUESTA")
                    terminos_prompt = "Compara los archivos de terminos y condiciones contra el archivo de contenidos de las paginas y lista las incongruencias y vacios legales que tengan"
                    terminos_respuesta = enviar_mensaje_asistente(company_obj.id_assistant,terminos_prompt, client)
                    privacity_prompt = "Compara los archivos de politica de privacidad contra el archivo de contenidos de las paginas y lista las incongruencias y vacios legales que tengan"
                    privacity_respuesta = enviar_mensaje_asistente(company_obj.id_assistant,privacity_prompt, client)
                    return Response({"respuesta_privacidad": privacity_respuesta,"terminos_respuesta": terminos_respuesta, "id_company": company_obj.id_company, "id_assistant": company_obj.id_company}, status=status.HTTP_200_OK)
            return Response({"message": "Not enough parameters"}, status=status.HTTP_400_BAD_REQUEST)


        except Exception as exc:
            return Response({"message": "Unexpected error: " + str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, *args, **kwargs):

        return Response({"message": "Request excecuted correctly"}, status=status.HTTP_200_OK)


def extract_internal_links(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

        response = requests.get(url,headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"

        internal_links = set()
        terms = None
        privacity = None
        for link in soup.find_all("a", href=True):
            absolute_link = urljoin(base_url, link["href"])
            if absolute_link.startswith(base_url) and "terminos" not in absolute_link and "privaci" not in absolute_link:
                internal_links.add(absolute_link)
            if "terminos" not in absolute_link:
                terms = absolute_link

            if "privaci" in absolute_link:
                privacity = absolute_link

        return list(internal_links), terms, privacity
    except requests.RequestException as e:
        return {"error": str(e)},None, None

def enviar_mensaje_asistente(assistant_id, mensaje, client):
    """
    Envía un mensaje a un asistente de OpenAI por su ID y retorna la respuesta.

    Parámetros:
    - assistant_id (str): ID del asistente en OpenAI.
    - mensaje (str): Mensaje a enviar.

    Retorna:
    - str: Respuesta del asistente.
    """
    try:
        # Crear un nuevo hilo de conversación si es necesario
        thread = client.beta.threads.create()

        # Enviar mensaje al asistente
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=mensaje
        )

        # Ejecutar el asistente en el hilo
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Esperar la respuesta del asistente
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed" or run_status.status == "failed":
                break

        # Obtener la respuesta del asistente
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        respuesta = messages.data[0].content[0].text.value

        return respuesta

    except Exception as e:
        return f"Error: {str(e)}"


