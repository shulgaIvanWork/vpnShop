# MAX VPN Shop Bot

Автоматизированная продажа VPN-подписок через MAX мессенджер с интеграцией 3X-UI панели.

## 🚀 Возможности

- **Продажа подписок**: 299₽/мес, 799₽/3 мес, 1499₽/6 мес
- **Платёжные системы**: ЮKassa + YooMoney
- **Мульти-серверность**: Несколько панелей 3X-UI
- **Реферальная система**: Купоны на скидку 10% (до 50%)
- **AI поддержка**: DeepSeek с эскалацией к владельцу
- **Корпоративные тарифы**: 9899₽/100 слотов, 19499₽/500 слотов
- **Автоматизация**: Блокировка истёкших подписок, уведомления

## 📋 Требования

- Docker & Docker Compose
- MAX Bot Token (получить в @BotFather аналог в MAX)
- 3X-UI панель
- ЮKassa аккаунт
- YooMoney кошелёк
- DeepSeek API ключ (опционально)

## 🛠️ Установка

### 1. Клонирование репозитория

```bash
git clone https://github.com/shulgaIvanWork/vpnShop.git
cd vpnShop
```

### 2. Настройка окружения

```bash
cp .env.example .env
```

Заполните `.env` файл:

```env
# MAX Bot
MAX_BOT_TOKEN=ваш_токен
MAX_DEV_ID=ваш_id
BOT_DOMAIN=your-domain.com

# Payments
YK_TOKEN=ваш_токен_юкасса
YK_SHOP_ID=id_магазина
YOOMONEY_WALLET_ID=id_кошелька
YOOMONEY_NOTIFICATION_SECRET=секрет

# Database
POSTGRES_PASSWORD=надёжный_пароль

# AI Support
DEEPSEEK_API_KEY=ваш_api_key

# Security
ENCRYPTION_KEY=сгенерированный_ключ
```

### 3. Генерация ключа шифрования

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 4. Запуск

```bash
docker-compose build
docker-compose up -d
```

### 5. Настройка webhook

**MAX Bot:**
```
URL: https://your-domain.com/webhook
```

**ЮKassa:**
```
URL: https://your-domain.com/yookassa
События: payment.succeeded, payment.canceled
```

**YooMoney:**
```
URL: https://your-domain.com/yoomoney
```

## 📁 Структура проекта

```
max-vpn-bot/
├── app/
│   ├── __main__.py              # Точка входа
│   ├── config.py                # Конфигурация
│   ├── worker.py                # Фоновые задачи
│   │
│   ├── bot/
│   │   ├── max_api/             # MAX API wrapper
│   │   ├── routers/             # Обработчики команд
│   │   ├── services/            # Бизнес-логика
│   │   ├── payment_gateways/    # Платёжные системы
│   │   ├── models/              # Pydantic модели
│   │   ├── middlewares/         # Middleware
│   │   ├── filters/             # Фильтры
│   │   └── utils/               # Утилиты
│   │
│   └── db/
│       ├── models/              # SQLAlchemy ORM модели
│       └── migration/           # Alembic миграции
│
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── plans.json                   # Тарифные планы
└── .env.example
```

## 💳 Тарифы

### Личные подписки

| Срок | Цена | Устройства |
|------|------|------------|
| 1 месяц | 299₽ | 1 |
| 3 месяца | 799₽ | 1 |
| 6 месяцев | 1499₽ | 1 |

### Корпоративные тарифы

| Слоты | Цена |
|-------|------|
| 100 | 9899₽ |
| 500 | 19499₽ |

## 🎫 Реферальная система

- Каждый пользователь получает реферальную ссылку
- За каждого приглашённого → купон на скидку 10%
- Купон действует 1 год
- Можно накопить до 50% скидки (5 купонов)

## 🤖 AI Поддержка

- Автоматические ответы через DeepSeek
- Эскалация к владельцу при сложных вопросах
- Владелец отвечает через бота

## 👨‍💼 Админ-команды

- `/servers` - Управление серверами
- `/users` - Редактор пользователей
- `/stats` - Статистика
- `/notify` - Рассылка уведомлений
- `/add_corp_server` - Добавить корпоративный сервер
- `/grant_corp_discount` - Начислить скидку компании

## 🔒 Безопасность

- Все секреты в `.env`
- Webhook'и проверяются по подписи
- API-ключи 3X-UI шифруются (Fernet)
- PostgreSQL с парольной аутентификацией

## 📊 Мониторинг

Логи доступны через:

```bash
docker-compose logs -f bot
docker-compose logs -f worker
```

## 🔄 Обновление

```bash
git pull
docker-compose build
docker-compose up -d
```

## 🐛 Решение проблем

### Бот не запускается

```bash
# Проверьте логи
docker-compose logs bot

# Проверьте .env
cat .env

# Перезапустите
docker-compose down
docker-compose up -d
```

### Миграции БД

```bash
docker-compose exec bot poetry run alembic upgrade head
```

## 📝 Лицензия

MIT

## 👥 Контакты

- GitHub: [shulgaIvanWork](https://github.com/shulgaIvanWork)
- Support: через бота (AI + эскалация)
