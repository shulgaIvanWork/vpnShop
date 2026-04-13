# 🚨 НЕДОСТАЮЩИЕ КОМПОНЕНТЫ ДЛЯ ЗАПУСКА

## Статус: Этап 6 - 85% завершён

---

## 🔴 КРИТИЧНО (нужно для запуска)

### 1. FSM (Finite State Machine)

**Зачем нужно:**
- Сохранять состояние пользователя во время оплаты
- Запоминать выбранный тариф до завершения оплаты
- Хранить данные о применённом купоне

**Текущая проблема:**
```python
# Сейчас данные теряются между callback handlers
subscription_data = SubscriptionData.create(...)  # Создаётся, но не сохраняется
```

**Что нужно сделать:**
- [ ] Создать FSM storage (Redis или Memory)
- [ ] Определить states для payment flow
- [ ] Сохранять SubscriptionData в FSM
- [ ] Восстанавливать данные при возврате из платёжной системы

**Файлы:**
- `app/bot/fsm/states.py` (создать)
- `app/bot/fsm/storage.py` (создать)

---

### 2. Database Helper Methods

**Зачем нужно:**
- Создать/обновить пользователя при `/start`
- Проверить существование подписки
- Загрузить историю платежей
- Получить реферальную статистику

**Текущая проблема:**
```python
# В handlers нет методов для работы с БД
user = await User.get(session, max_user_id=user_id)  # Метод get() не реализован
```

**Что нужно добавить в модели:**

**User модель:**
```python
@classmethod
async def get_or_create(cls, session, max_user_id: int, username: str = None) -> User:
    """Get existing user or create new one."""
    ...

@classmethod  
async def get_by_max_id(cls, session, max_user_id: int) -> User | None:
    """Get user by MAX user ID."""
    ...
```

**Payment модель:**
```python
@classmethod
async def get_user_payments(cls, session, user_id: int) -> list[Payment]:
    """Get all payments for user."""
    ...

@classmethod
async def get_by_payment_gateway_id(cls, session, gateway_payment_id: str) -> Payment | None:
    """Get payment by gateway ID (yookassa/yoomoney payment ID)."""
    ...
```

**Файлы для обновления:**
- `app/db/models/user.py` (добавить методы)
- `app/db/models/payment.py` (добавить методы)
- `app/db/models/coupon.py` (добавить методы)
- `app/db/models/referral.py` (добавить методы)

---

### 3. Webhook Server для оплат

**Зачем нужно:**
- Принимать уведомления от YooKassa/YooMoney
- Автоматически активировать подписку после оплаты
- Отправлять ключ пользователю

**Текущая проблема:**
```python
# Payment gateways регистрируют webhook handlers,
# но нет aiohttp server для их обработки
```

**Что нужно сделать:**
- [ ] Настроить aiohttp server в `__main__.py`
- [ ] Зарегистрировать webhook routes
- [ ] Запустить server вместе с ботом
- [ ] Настроить webhook URLs в YooKassa/YooMoney

**Файлы:**
- `app/__main__.py` (обновить - добавить web server)
- `app/bot/payment_gateways/yookassa.py` (webhook уже есть ✅)
- `app/bot/payment_gateways/yoomoney.py` (webhook уже есть ✅)

---

### 4. Alembic Migrations

**Зачем нужно:**
- Создать таблицы в PostgreSQL
- Управлять схемой БД
- Мигрировать при изменениях

**Текущая проблема:**
```bash
# Нет миграций - таблицы не созданы
alembic revision --autogenerate  # Не настроено
```

**Что нужно сделать:**
- [ ] Инициализировать Alembic
- [ ] Создать первую миграцию
- [ ] Настроить alembic.ini
- [ ] Запустить миграции

**Команды:**
```bash
cd max-vpn-bot
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## 🟡 ВАЖНО (нужно скоро)

### 5. Интеграция оплаты в Subscription Handler

**Файл:** `app/bot/routers/subscription/subscription_handler.py`

**Что изменить:**
```python
async def handle_payment_method_selection(...):
    # СЕЙЧАС: Заглушка
    text = "⚠️ Функция в разработке"
    
    # НУЖНО: Создать реальную оплату
    subscription_data = await get_subscription_data_from_fsm(user_id)
    payment_url = await gateway.create_payment(subscription_data)
    await bot.send_message(user_id, f"Оплатите: {payment_url}")
```

---

### 6. Создание пользователей при /start

**Файл:** `app/bot/routers/main_menu/handler.py`

**Что изменить:**
```python
async def handle_start(...):
    # СЕЙЧАС: Не создаёт пользователя
    user_id = update.message.from_user.id
    
    # НУЖНО: Создать или получить пользователя
    async with config.db.session() as session:
        user = await User.get_or_create(
            session=session,
            max_user_id=user_id,
            username=update.message.from_user.username,
        )
        await session.commit()
```

---

## 🔵 ОПЦИОНАЛЬНО (можно позже)

### 7. Admin Tools

**Приоритет:** Низкий (после запуска)

**Что нужно:**
- [ ] Server Manager
- [ ] User Editor  
- [ ] Statistics
- [ ] Corporate Server Manager
- [ ] Discount Manager

---

## 📋 ЧТО НУЖНО ОТ ВАС:

### 🔧 Конфигурация (.env файл)

Создайте файл `.env` в `max-vpn-bot/`:

```env
# MAX Bot
MAX_BOT_TOKEN=your_max_bot_token_here
MAX_BOT_DOMAIN=https://your-bot-domain.com

# Database
POSTGRES_USER=vpn_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=vpn_shop
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# YooKassa
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_TOKEN=your_secret_key

# YooMoney
YOOMONEY_WALLET_ID=your_wallet_id
YOOMONEY_NOTIFICATION_SECRET=your_secret

# DeepSeek (для AI поддержки - позже)
DEEPSEEK_API_KEY=your_api_key

# Bot admins
BOT_ADMINS=123456789  # Your MAX user ID
BOT_DEV_ID=123456789
```

### 🗄️ База данных

Вариант 1: **Docker Compose** (рекомендую)
```bash
docker-compose up -d postgres
```

Вариант 2: **Локальная PostgreSQL**
- Установите PostgreSQL
- Создайте базу данных
- Обновите .env

### 🌐 Webhook Domain

Для приёма платежей нужен публичный HTTPS URL:

**Вариант 1:** Ngrok (для тестов)
```bash
ngrok http 8080
# Получите https://abc123.ngrok.io
```

**Вариант 2:** Свой сервер с SSL
- VPS с доменом
- Let's Encrypt SSL сертификат

---

## 🎯 ПЛАН ЗАВЕРШЕНИЯ:

### Шаг 1: Database (30 минут)
1. Добавить helper методы в модели
2. Настроить Alembic
3. Создать миграции

### Шаг 2: FSM (30 минут)
1. Создать FSM storage
2. Определить states
3. Интегрировать в handlers

### Шаг 3: Payment Integration (1 час)
1. Подключить payment gateways к subscription handler
2. Создать payment flow
3. Обработать webhooks

### Шаг 4: Webhook Server (30 минут)
1. Настроить aiohttp server
2. Зарегистрировать routes
3. Протестировать webhooks

### Шаг 5: Testing (1 час)
1. Протестировать /start
2. Протестировать покупку
3. Протестировать webhooks

**Итого:** ~3.5 часов работы

---

## ❓ ВОПРОСЫ К ВАМ:

1. **База данных:**
   - Есть ли уже PostgreSQL сервер?
   - Или запустить через Docker?

2. **MAX Bot Token:**
   - Получили ли токен бота от MAX?
   - Есть ли bot username?

3. **Платёжные системы:**
   - Настроены ли аккаунты YooKassa/YooMoney?
   - Есть ли shop_id и tokens?

4. **Webhook Domain:**
   - Есть ли публичный HTTPS URL для бота?
   - Или использовать ngrok для тестов?

5. **Приоритеты:**
   - Сначала завершить Этап 6 полностью?
   - Или перейти к AI Support (Этап 7)?

---

**Готов продолжить как только получу ответы!** 🚀
