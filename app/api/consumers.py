from channels.generic.websocket import WebsocketConsumer
from django.contrib.auth import authenticate
from asgiref.sync import async_to_sync
from django.conf import settings
from api import models
import base64
import json
import uuid
import os


class ApiConsumer(WebsocketConsumer):

    def connect(self):
        self.session_id = uuid.uuid4().hex
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name, self.channel_name
        )

    def _authenticate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if user is not None:

            self.user = user
            self.user_data = models.UserData.objects.filter(user=user).first()
            self.user_alerts = models.UserAlerts.objects.filter(user=user).first()

            self.files_dir = os.path.join(settings.MEDIA_ROOT, str(self.user_data.user_uuid))
            self.url = settings.MEDIA_URL + str(self.user_data.user_uuid) + '/'
            if not os.path.exists(self.files_dir):
                os.mkdir(self.files_dir)

            self.send(json.dumps({'status': 'Success'}))
        else:
            self.send(json.dumps({'status': 'Failed'}))
            self.close()

    def _sync_files(self):
        self.user_data.refresh_from_db()

        self.send(json.dumps({
            'status': 'Success',
            'action': 'sync_files',
            'files': self.user_data.files,
        }))

    def _upload_file(self, data):
        self.user_data.refresh_from_db()

        user_files = self.user_data.files
        filedata = base64.b64decode(data['filedata'])
        filename = str(uuid.uuid4())
        server_filepath = os.path.join(self.files_dir, filename)
        url = self.url + filename
        with open(server_filepath, 'wb') as file:
            file.write(filedata)
        user_files[data['filename']] = {'server_filepath': server_filepath, 'url': url}

        self.user_data.files = user_files
        self.user_data.save()
        self.user_data.refresh_from_db()

        self.send_message_to_group({'status': 'Success', 'action': 'download_file', 'files': self.user_data.files, 'filename': data['filename']})

    def _remove_files(self, data):
        self.user_data.refresh_from_db()

        user_files = self.user_data.files
        for filename in data['files_to_remove']:
            os.remove(user_files[filename]['server_filepath'])
            user_files.pop(filename)

        self.user_data.files = user_files
        self.user_data.save()
        self.user_data.refresh_from_db()

        self.send_message_to_group({'status': 'Success', 'action': 'remove_files', 'files_to_remove': data['files_to_remove']})

    def _sync_alerts(self, data):
        self.user_alerts.refresh_from_db()

        require_sync_alerts = False
        user_alerts = self.user_alerts.alerts
        for alert in data['alerts']:
            if alert not in user_alerts:
                user_alerts.append(alert)
                require_sync_alerts = True

        self.user_alerts.alerts = user_alerts
        self.user_alerts.save()
        self.user_alerts.refresh_from_db()

        self.send(json.dumps({
            'status': 'Success',
            'action': 'sync_alerts',
            'alerts': self.user_alerts.alerts,
        }))

        if require_sync_alerts:
            self.send_message_to_group({'status': 'Success', 'action': 'require_sync_alerts'})

    def _add_alerts(self, data):
        self.user_alerts.refresh_from_db()

        user_alerts = self.user_alerts.alerts
        user_alerts.extend(data['alerts'])

        self.user_alerts.alerts = user_alerts
        self.user_alerts.save()
        self.user_alerts.refresh_from_db()

        self.send_message_to_group({'status': 'Success', 'action': 'add_alerts', 'alerts': data['alerts']})

    def _remove_alerts(self, data):
        self.user_alerts.refresh_from_db()

        user_alerts = self.user_alerts.alerts
        for alert in data['alerts']:
            if alert in user_alerts:
                user_alerts.remove(alert)

        self.user_alerts.alerts = user_alerts
        self.user_alerts.save()
        self.user_alerts.refresh_from_db()

        self.send_message_to_group({'status': 'Success', 'action': 'remove_alerts', 'alerts': data['alerts']})

    def receive(self, text_data):
        data = json.loads(text_data)
        try:
            if data['action'] == 'authenticate':
                self._authenticate(data)

            if not hasattr(self, 'user'):
                self.close()

            if data['action'] == 'sync_files':
                self._sync_files()

            elif data['action'] == 'sync_alerts':
                self._sync_alerts(data)

            elif data['action'] == 'add_alerts':
                self._add_alerts(data)

            elif data['action'] == 'remove_alerts':
                self._remove_alerts(data)

            elif data['action'] == 'upload_file':
                self._upload_file(data)

            elif data['action'] == 'remove_files':
                self._remove_files(data)

        except Exception:
            self.send(json.dumps({
                'status': 'Failed'
            }))

    def chat_message(self, event):
        message = event["message"]
        if message.get('session_id') != self.session_id:
            self.send(text_data=json.dumps(message))

    def send_message_to_group(self, message):
        message['session_id'] = self.session_id
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name, {"type": "chat.message", "message": message}
        )
