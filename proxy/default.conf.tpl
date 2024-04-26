upstream django_app{
    server ${APP_HOST}:${APP_PORT};
}
server {
    listen 80;
    listen [::]:80;

    location /static {
        alias /vol/static;
    }

    location / {
        include                 /etc/nginx/gunicorn_params;
        proxy_pass              http://django_app;
        client_max_body_size    200M;
    }
}
