from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.http import HttpResponse
from django.conf import settings
import uuid
import os


@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        from api import models

        user_file = request.FILES.get('file')
        username = request.POST.get('username')
        password = request.POST.get('password')
        filename = request.POST.get('filename')
        server_filename = request.POST.get('server_filename')

        if not user_file or not username or not filename or not password:
            return HttpResponse('Missing file or metadata', status=400)

        try:
            user = authenticate(username=username, password=password)
            if user is not None:
                user_data = models.UserData.objects.get(user__username=username)

                if server_filename == '':
                    server_filename = str(uuid.uuid4())

                server_filepath = os.path.join(settings.MEDIA_ROOT, str(user_data.user_uuid), server_filename)

                with open(server_filepath, 'ab') as file:
                    for chunk in user_file.chunks():
                        file.write(chunk)

                return HttpResponse(server_filename, status=200)

        except Exception as e:
            return HttpResponse(f'Error saving file: {str(e)}', status=500)

    return HttpResponse('Invalid request method', status=405)


@csrf_exempt
def add_file(request):
    if request.method == 'POST':
        from api import models

        username = request.POST.get('username')
        password = request.POST.get('password')
        filename = request.POST.get('filename')
        server_filename = request.POST.get('server_filename')

        try:
            user = authenticate(username=username, password=password)
            if user is not None:
                user_data = models.UserData.objects.get(user__username=username)

                server_filepath = os.path.join(settings.MEDIA_ROOT, str(user_data.user_uuid), server_filename)
                url = settings.MEDIA_URL + str(user_data.user_uuid) + '/' + server_filename

                user_files = user_data.files
                user_files[filename] = {'server_filepath': server_filepath, 'url': url}
                user_data.save()

                return HttpResponse('File uploaded successfully', status=201)

        except Exception as e:
            return HttpResponse(f'Error saving file: {str(e)}', status=500)

    return HttpResponse('Invalid request method', status=405)
