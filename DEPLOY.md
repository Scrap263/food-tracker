# 🚀 Деплой на Linux сервер (Ubuntu/Debian)

Эта инструкция поможет тебе развернуть проект на твоем VPS-сервере. Мы будем использовать **Gunicorn** для запуска Python-приложения и **Nginx** для раздачи статики (картинок, стилей) и проксирования запросов, а также **Systemd** для автоматического запуска.

---

### 1. Подготовка сервера

Зайди на сервер через SSH:
```bash
ssh root@твой_ip_адрес
# или с логином юзера
ssh username@твой_ip_адрес
```

Обнови пакеты и установи Python, pip, nginx и git:
```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx git -y
```

### 2. Установка приложения

Клонируй репозиторий в папку `/var/www` (или в домашнюю папку, например `~/food-tracker`):

```bash
cd /var/www
# Если папки нет, создай: sudo mkdir -p /var/www && sudo chown $USER:$USER /var/www
git clone https://github.com/Scrap263/food-tracker.git
cd food-tracker
```

Создай виртуальное окружение и установи зависимости:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn # Убедись, что gunicorn установлен
```

Проверь, работает ли приложение (нажми `Ctrl+C`, чтобы выйти после проверки):
```bash
gunicorn --bind 0.0.0.0:8000 app:app
# Если ошибок нет - идем дальше.
```

### 3. Настройка Systemd (автозапуск)

Создай файл службы, чтобы приложение работало в фоне и перезапускалось при сбоях.

```bash
sudo nano /etc/systemd/system/food-tracker.service
```

Вставь этот конфиг (замени `/var/www/food-tracker` на свой путь, если он отличается, и `root` на своего пользователя `User=` если не под рутом):

```ini
[Unit]
Description=Gunicorn instance to serve food-tracker
After=network.target

[Service]
User=root
Group=www-data
WorkingDirectory=/var/www/food-tracker
Environment="PATH=/var/www/food-tracker/venv/bin"
ExecStart=/var/www/food-tracker/venv/bin/gunicorn --workers 3 --bind unix:food-tracker.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
```

Сохрани (`Ctrl+O`, `Enter`) и выйди (`Ctrl+X`).

Запусти и включи службу:
```bash
sudo systemctl start food-tracker
sudo systemctl enable food-tracker
sudo systemctl status food-tracker # Должно быть active (running)
```

### 4. Настройка Nginx (Веб-сервер)

Создай конфиг для Nginx:

```bash
sudo nano /etc/nginx/sites-available/food-tracker
```

Вставь следующий код (замени `ТВОЙ_IP_СЕРВЕРА` на реальный IP, например `45.132.89.123`):

```nginx
server {
    listen 80;
    server_name ТВОЙ_IP_СЕРВЕРА;

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/food-tracker/food-tracker.sock;
    }

    location /static {
        alias /var/www/food-tracker/static;
        expires 30d;
    }
}
```

Сохрани и выйди.

Активируй сайт:
```bash
sudo ln -s /etc/nginx/sites-available/food-tracker /etc/nginx/sites-enabled
```

Проверь конфиг на ошибки:
```bash
sudo nginx -t
```
Если всё `successful`, перезагрузи Nginx:
```bash
sudo systemctl restart nginx
```

### 🎉 Готово!

Теперь открой в браузере: `http://ТВОЙ_IP_СЕРВЕРА`
Приложение должно работать!
