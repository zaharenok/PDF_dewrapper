# 🚀 Развертывание DocFix на Hostinger VPS

## Требования

- **VPS Plan**: KVM 1 или выше (минимум 2GB RAM)
- **OS**: Ubuntu 20.04/22.04 или Debian 11/12
- **Root доступ**: SSH доступ с правами root
- **Домен**: (опционально) для SSL сертификата

## Быстрая установка

### 1. Подключитесь к VPS через SSH

```bash
ssh root@your-server-ip
```

### 2. Скачайте и запустите скрипт установки

```bash
# Клонируйте репозиторий
git clone https://github.com/zaharenok/PDF_dewrapper.git /opt/docfix
cd /opt/docfix

# Сделайте скрипт исполняемым
chmod +x deploy.sh

# Запустите установку
sudo ./deploy.sh
```

Скрипт автоматически:
- ✅ Обновит систему
- ✅ Установит Docker и Docker Compose
- ✅ Установит необходимые зависимости (OpenCV, Python)
- ✅ Соберет и запустит приложение
- ✅ Проверит работоспособность

### 3. Настройте Nginx (опционально, для доступа через домен)

```bash
# Скопируйте конфиг Nginx
cp nginx-config.conf /etc/nginx/sites-available/docfix

# Отредактируйте домен в конфиге
nano /etc/nginx/sites-available/docfix
# Замените: your-domain.com на ваш реальный домен

# Создайте симлинк
ln -s /etc/nginx/sites-available/docfix /etc/nginx/sites-enabled/

# Проверьте конфигурацию
nginx -t

# Перезагрузите Nginx
systemctl reload nginx
```

### 4. Настройте SSL сертификат (Let's Encrypt)

```bash
# Установите Certbot (если еще не установлен)
apt-get install certbot python3-certbot-nginx

# Получите SSL сертификат
certbot --nginx -d your-domain.com -d www.your-domain.com

# Certbot автоматически настроит HTTPS редирект
```

### 5. Настройте Firewall

```bash
# Разрешите HTTP и HTTPS
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 22/tcp  # SSH (важно!)

# Включите firewall
ufw enable
```

## Проверка работы

### Локальная проверка (на сервере)

```bash
# Проверьте статус контейнеров
docker-compose ps

# Проверьте health endpoint
curl http://localhost:8000/health

# Посмотрите логи
docker-compose logs -f
```

### Проверка через браузер

1. **Без домена**: `http://your-server-ip:8000`
2. **С доменом (HTTP)**: `http://your-domain.com`
3. **С доменом (HTTPS)**: `https://your-domain.com`

Проверьте:
- Landing page: `/`
- Приложение: `/app`
- API docs: `/docs`
- Health: `/health`

## Управление приложением

### Основные команды

```bash
# Перейти в директорию проекта
cd /opt/docfix

# Посмотреть логи
docker-compose logs -f

# Перезапустить
docker-compose restart

# Остановить
docker-compose down

# Запустить
docker-compose up -d

# Пересобрать и запустить
docker-compose up -d --build
```

### Обновление приложения

```bash
cd /opt/docfix

# Получить последние изменения
git pull

# Пересобрать и запустить
docker-compose down
docker-compose build
docker-compose up -d

# Проверить статус
docker-compose ps
curl http://localhost:8000/health
```

## Мониторинг и обслуживание

### Просмотр логов

```bash
# Все логи
docker-compose logs

# Последние 100 строк
docker-compose logs --tail=100

# В реальном времени
docker-compose logs -f

# Только backend
docker-compose logs -f page-dewarp
```

### Очистка старых данных

```bash
# Очистить старые загрузки и результаты (старше 24 часов)
find /opt/docfix/uploads -type f -mtime +1 -delete
find /opt/docfix/results -type f -mtime +1 -delete
```

### Автоматическая очистка (cron)

```bash
# Добавьте в crontab
crontab -e

# Добавьте эту строку (очистка каждый день в 3:00)
0 3 * * * find /opt/docfix/uploads -type f -mtime +1 -delete && find /opt/docfix/results -type f -mtime +1 -delete
```

### Мониторинг ресурсов

```bash
# Использование ресурсов контейнерами
docker stats

# Использование диска
df -h

# Использование RAM
free -h
```

## Настройка автозапуска

Docker Compose настроен на автозапуск (`restart: unless-stopped`), но если нужно:

```bash
# Создайте systemd service
cat > /etc/systemd/system/docfix.service << 'EOF'
[Unit]
Description=DocFix Document Processing Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/docfix
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Включите и запустите
systemctl daemon-reload
systemctl enable docfix
systemctl start docfix

# Проверьте статус
systemctl status docfix
```

## Резервное копирование

### Ручное создание бэкапа

```bash
# Создайте директорию для бэкапов
mkdir -p /root/backups

# Создайте архив
tar -czf /root/backups/docfix-$(date +%Y%m%d-%H%M%S).tar.gz \
  /opt/docfix \
  --exclude=/opt/docfix/uploads \
  --exclude=/opt/docfix/results \
  --exclude=/opt/docfix/venv

# Бэкап базы данных (если используется)
# docker-compose exec -T postgres pg_dump -U user database > /root/backups/db-$(date +%Y%m%d).sql
```

### Автоматический бэкап (cron)

```bash
crontab -e

# Добавьте (бэкап каждую неделю в воскресенье в 2:00)
0 2 * * 0 tar -czf /root/backups/docfix-$(date +\%Y\%m\%d).tar.gz /opt/docfix --exclude=/opt/docfix/uploads --exclude=/opt/docfix/results --exclude=/opt/docfix/venv
```

## Troubleshooting

### Приложение не запускается

```bash
# Проверьте логи
docker-compose logs

# Проверьте порты
netstat -tulpn | grep 8000

# Проверьте Docker
systemctl status docker

# Перезапустите Docker
systemctl restart docker
docker-compose up -d
```

### Ошибки обработки изображений

```bash
# Проверьте наличие системных библиотек
docker-compose exec page-dewarp dpkg -l | grep libgl

# Проверьте Python зависимости
docker-compose exec page-dewarp pip list | grep opencv

# Пересоберите контейнер
docker-compose build --no-cache
docker-compose up -d
```

### Проблемы с SSL

```bash
# Обновите сертификат
certbot renew

# Проверьте конфиг Nginx
nginx -t

# Перезагрузите Nginx
systemctl reload nginx
```

### Нехватка памяти

```bash
# Проверьте использование
free -h

# Проверьте swap
swapon --show

# Создайте swap (если нет)
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

### Нехватка места на диске

```bash
# Проверьте использование
df -h

# Очистите Docker
docker system prune -a

# Очистите старые файлы
find /opt/docfix/uploads -type f -mtime +1 -delete
find /opt/docfix/results -type f -mtime +1 -delete
```

## Безопасность

### Рекомендации по безопасности

1. **Измените SSH порт**
```bash
nano /etc/ssh/sshd_config
# Измените Port 22 на другой (например, 2222)
systemctl restart sshd
ufw allow 2222/tcp
```

2. **Отключите root login по SSH**
```bash
nano /etc/ssh/sshd_config
# PermitRootLogin no
systemctl restart sshd
```

3. **Настройте fail2ban**
```bash
apt-get install fail2ban
systemctl enable fail2ban
systemctl start fail2ban
```

4. **Регулярно обновляйте систему**
```bash
apt-get update && apt-get upgrade -y
```

## Производительность

### Оптимизация для Hostinger VPS

**Для VPS с 2GB RAM:**
```yaml
# В docker-compose.yml добавьте limits
services:
  page-dewarp:
    deploy:
      resources:
        limits:
          memory: 1.5G
```

**Для VPS с 4GB+ RAM:**
Можно увеличить количество workers uvicorn:
```bash
# В Dockerfile или docker-compose.yml
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

## Контакты и поддержка

- **GitHub**: https://github.com/zaharenok/PDF_dewrapper
- **Issues**: https://github.com/zaharenok/PDF_dewrapper/issues

## Лицензия

MIT License - см. LICENSE файл в репозитории.
