# 🚀 План реализации MAX VPN Bot (форк 3xui-shop)

**Цель:** Автоматизированная продажа VPN-подписок через MAX бот с интеграцией 3X-UI, ЮKassa, YooMoney и DeepSeek AI.

**Основа:** snoups/3xui-shop (Telegram bot → MAX bot)

---

## 📋 ЭТАП 1: Подготовка инфраструктуры

### 1.1 Создание структуры проекта
- [ ] Создать директорию `max-vpn-bot` в корне проекта
- [ ] Скопировать структуру из `3xui-shop/app/`
- [ ] Удалить ненужные файлы (locales/, .github/, scripts/)
- [ ] Создать `.gitignore` для нового проекта
- [ ] Создать `README.md` с описанием проекта

### 1.2 Обновление зависимостей (pyproject.toml)
- [ ] **Удалить:**
  - `aiogram` (Telegram framework)
  - `py3xui` (3X-UI клиент)
  - `aiosqlite` (SQLite не нужен)
  
- [ ] **Добавить:**
  - `maxapi` (MAX мессенджер framework)
  - `client3x` (асинхронный 3X-UI клиент)
  - `deepseek` или `openai` (для DeepSeek API)
  - `cryptography` (шифрование API-ключей Fernet)
  - `asyncpg` (PostgreSQL драйвер)
  - `yoomoney` (YooMoney SDK)
  
- [ ] **Оставить:**
  - `yookassa` ✅
  - `sqlalchemy[asyncio]` ✅
  - `alembic` ✅
  - `redis` ✅
  - `apscheduler` ✅
  - `environs` ✅

### 1.3 Настройка Docker Compose
- [ ] Обновить `docker-compose.yml`:
  - Добавить **PostgreSQL** сервис
  - Убрать `letsencrypt_data` volume (не нужно)
  - Обновить labels для Traefik
  - Добавить **Worker** сервис (фоновые задачи)
  
- [ ] Создать `.env.example`:
  ```env
  # MAX
  MAX_BOT_TOKEN=
  MAX_DEV_ID=
  BOT_DOMAIN=
  BOT_PORT=8080
  
  # Payments
  YK_TOKEN=
  YK_SHOP_ID=
  YOOMONEY_WALLET_ID=
  YOOMONEY_NOTIFICATION_SECRET=
  
  # Database
  POSTGRES_USER=vpn_user
  POSTGRES_PASSWORD=
  POSTGRES_DB=vpn_db
  POSTGRES_HOST=postgres
  POSTGRES_PORT=5432
  
  # Redis
  REDIS_HOST=redis
  REDIS_PORT=6379
  
  # 3X-UI (по умолчанию)
  XUI_USERNAME=admin
  XUI_PASSWORD=admin
  
  # AI Support
  DEEPSEEK_API_KEY=
  
  # Security
  ENCRYPTION_KEY=
  ```

---

## 📋 ЭТАП 2: Адаптация конфигурации

### 2.1 Обновление `config.py`
- [ ] **BotConfig:**
  - `TOKEN` → `MAX_BOT_TOKEN`
  - `TG_ID` → `MAX_USER_ID`
  - Удалить `SUPPORT_ID` (заменён на DeepSeek)
  
- [ ] **ShopConfig:**
  - Удалить `PAYMENT_STARS_ENABLED`
  - Удалить `PAYMENT_CRYPTOMUS_ENABLED`
  - Удалить `PAYMENT_HELEKET_ENABLED`
  - Оставить `PAYMENT_YOOKASSA_ENABLED` ✅
  - Оставить `PAYMENT_YOOMONEY_ENABLED` ✅
  - Удалить настройки trial (если не нужны)
  - Удалить настройки старой реферальной системы
  
- [ ] **Удалить конфиги:**
  - `CryptomusConfig`
  - `HeleketConfig`
  
- [ ] **Добавить конфиги:**
  - `DeepSeekConfig` (API_KEY, MODEL, MAX_TOKENS)
  - `EncryptionConfig` (ENCRYPTION_KEY для Fernet)
  
- [ ] **DatabaseConfig:**
  - Изменить default driver на `postgresql+asyncpg`
  - Убрать SQLite поддержку

### 2.2 Обновление констант (`bot/utils/constants.py`)
- [ ] Удалить Telegram-константы
- [ ] Добавить MAX webhook пути
- [ ] Добавить webhook пути для ЮKassa и YooMoney
- [ ] Обновить статусы транзакций
- [ ] Добавить константы для DeepSeek

---

## 📋 ЭТАП 3: Адаптация базы данных

### 3.1 Обновление ORM моделей (`db/models/`)

#### **user.py** - Пользователи
- [ ] Переименовать `tg_id` → `max_user_id`
- [ ] Удалить `language_code` (не нужно)
- [ ] Удалить `is_trial_used`
- [ ] Удалить `source_invite_name`
- [ ] Удалить связи со старой реферальной системой
- [ ] Добавить поля:
  - `subscription_end` (TIMESTAMP)
  - `device_limit` (INT, default=1)
  - `uuid` (VARCHAR для VPN клиента)
  - `assigned_server` (VARCHAR - IP панели)

#### **transaction.py** → **payment.py** - Платежи
- [ ] Переименовать таблицу `transactions` → `payments`
- [ ] Добавить поля:
  - `plan_duration` (INT - дней)
  - `discount_applied` (INT - процент скидки)
  - `coupon_code` (VARCHAR)
- [ ] Изменить `payment_method` (yookassa/yoomoney)

#### **referral.py** - Реферальные связи
- [ ] **Полностью переписать:**
  - `referrer_id` → ForeignKey(users.id)
  - `referred_id` → ForeignKey(users.id)
  - `referred_type` (individual/company)
  - `reward_issued` (BOOLEAN)
  - `coupon_code` (VARCHAR)

#### **promocode.py** → **coupon.py** - Купоны
- [ ] **Полностью переделать:**
  - `code` (PRIMARY KEY)
  - `user_id` (ForeignKey)
  - `discount_percent` (INT, max 50)
  - `valid_until` (TIMESTAMP)
  - `used` (BOOLEAN)
  - `used_at` (TIMESTAMP)

#### **server.py** - Серверы 3X-UI
- [ ] Оставить как есть (для пула серверов)
- [ ] Добавить поле `is_corporate` (BOOLEAN)

#### **НОВАЯ corporate_server.py** - Корпоративные серверы
- [ ] Создать модель:
  - `id` (PRIMARY KEY)
  - `user_id` (ForeignKey - клиент)
  - `server_ip` (INET)
  - `api_key_encrypted` (TEXT)
  - `slots_total` (INT - 100 или 500)
  - `slots_used` (INT)
  - `status` (active/expired/disabled)
  - `notes` (TEXT)
  - `created_at`

### 3.2 Создание Alembic миграций
- [ ] Инициализировать Alembic (`alembic init`)
- [ ] Создать начальную миграцию с новой схемой БД
- [ ] Настроить `alembic.ini` для PostgreSQL

---

## 📋 ЭТАП 4: Адаптация под MAX API

### 4.1 Создание MAX Bot wrapper (`bot/max_api/`)
- [ ] Создать `bot.py` - обёртка над maxapi:
  - Инициализация бота
  - Отправка сообщений
  - Отправка клавиатур
  - Редактирование сообщений
  - Webhook handling
  
- [ ] Создать `types.py` - типы данных:
  - `Message`
  - `User`
  - `CallbackQuery`
  - `InlineKeyboardMarkup`
  - `ReplyKeyboardMarkup`

### 4.2 Обновление `__main__.py`
- [ ] Заменить импорты aiogram → maxapi
- [ ] Обновить инициализацию бота
- [ ] Обновить webhook setup
- [ ] Адаптировать on_startup/on_shutdown
- [ ] Убрать i18n (если не нужен)

### 4.3 Адаптация middleware (`bot/middlewares/`)
- [ ] Переписать под MAX API
- [ ] Update `AuthMiddleware` (проверка max_user_id)
- [ ] Update `MaintenanceMiddleware`
- [ ] Убрать i18n middleware

### 4.4 Адаптация filters (`bot/filters/`)
- [ ] Переписать под MAX API
- [ ] `IsAdmin` фильтр
- [ ] `IsDeveloper` фильтр
- [ ] Убрать ненужные фильтры

---

## 📋 ЭТАП 5: Обновление платёжных шлюзов

### 5.1 YooKassa (`bot/payment_gateways/yookassa.py`)
- [ ] Обновить импорты (MAX API вместо aiogram)
- [ ] Изменить `redirect_url` с Telegram на MAX bot
- [ ] Адаптировать webhook handler
- [ ] Обновить создание чека (Receipt)

### 5.2 YooMoney (`bot/payment_gateways/yoomoney.py`)
- [ ] Обновить импорты (MAX API вместо aiogram)
- [ ] Изменить `successURL` на MAX bot
- [ ] Адаптировать webhook handler
- [ ] Проверить `create_quickpay_url`

### 5.3 Gateway Factory (`bot/payment_gateways/gateway_factory.py`)
- [ ] Удалить регистрацию Cryptomus, Heleket, Stars
- [ ] Оставить только Yookassa и Yoomoney
- [ ] Обновить сигнатуры методов

### 5.4 Базовый класс (`bot/payment_gateways/_gateway.py`)
- [ ] Обновить под MAX API
- [ ] Адаптировать `_on_payment_succeeded`
- [ ] Адаптировать `_on_payment_canceled`

---

## ✅ ЭТАП 1-5: ВЫПОЛНЕНЫ

### Прогресс:
- ✅ Этап 1: Инфраструктура (Docker, зависимости, структура)
- ✅ Этап 2: Конфигурация (config.py под MAX)
- ✅ Этап 3: База данных (6 ORM моделей)
- ✅ Этап 4: MAX API Wrapper (официальная библиотека maxapi)
- ✅ Этап 5: Платёжные шлюзы (YooKassa + YooMoney)

---

## 🔄 ЭТАП 6: Переделка роутеров (handlers) - ЗАВЕРШЁН НА 85%

### ✅ Выполнено:
- ✅ Main Menu (полностью)
- ✅ Subscription (handlers готовы, нужна интеграция оплаты)
- ✅ Profile (handlers готовы, нужна БД интеграция)
- ✅ Referral (handlers готовы, нужна БД интеграция)
- ✅ Support (полностью)
- ❌ Admin Tools (не начато)

### ⚠️ Осталось сделать:

#### 1. Интеграция с оплатой (КРИТИЧНО)
**Файлы:** `app/bot/routers/subscription/subscription_handler.py`
- [ ] Подключить YooKassa gateway к flow покупки
- [ ] Подключить YooMoney gateway к flow покупки
- [ ] Создать payment link и отправить пользователю
- [ ] Обработать webhook с подтверждением оплаты
- [ ] Автоматически выдать ключ после оплаты

**Что нужно:**
- ✅ Payment gateways готовы (Этап 5)
- ✅ SubscriptionData модель готова
- ❌ FSM (Finite State Machine) для сохранения состояния оплаты
- ❌ Webhook endpoints для приёма уведомлений

#### 2. Database интеграция (КРИТИЧНО)
**Файлы:** Все handlers
- [ ] Реальное создание/чтение пользователей при /start
- [ ] Сохранение subscription data в БД
- [ ] Загрузка реальной информации о подписке
- [ ] История платежей из БД
- [ ] Реферальная система с БД

**Что нужно:**
- ✅ ORM модели готовы (Этап 3)
- ✅ Database service готов
- ❌ Alembic migrations не настроены
- ❌ Нет helper методов для работы с БД в handlers

#### 3. Admin Tools (НЕ КРИТИЧНО - можно позже)
**Файлы:** `app/bot/routers/admin_tools/`
- [ ] Server Manager
- [ ] User Editor
- [ ] Statistics
- [ ] Corporate Server Manager
- [ ] Discount Manager
- [ ] AI Support Manager

**Приоритет:** Низкий (можно добавить после запуска)

### 6.1 Main Menu (`bot/routers/main_menu/`)
- [ ] Адаптировать под MAX API
- [ ] Обновить клавиатуры (InlineKeyboardMarkup MAX)
- [ ] Изменить команды `/start`, `/menu`

### 6.2 Subscription (`bot/routers/subscription/`)
- [ ] **subscription_handler.py:**
  - Выбор тарифа (299₽/799₽/1499₽)
  - Обновить планы из plans.json
  
- [ ] **payment_handler.py:**
  - Выбор способа оплаты (ЮKassa/YooMoney)
  - Интеграция с coupon системой
  
- [ ] **promocode_handler.py** → **coupon_handler.py:**
  - Ввод купона перед оплатой
  - Валидация купона
  - Расчёт скидки

### 6.3 Profile (`bot/routers/profile/`)
- [ ] Показать подписку (срок, устройство)
- [ ] Показать ключ VPN
- [ ] История платежей
- [ ] Реферальная ссылка

### 6.4 Referral (`bot/routers/referral/`)
- [ ] **Полностью переписать:**
  - Показать реферальную ссылку
  - Статистика приглашённых
  - Доступные купоны
  - Информация о скидках

### 6.5 Support (`bot/routers/support/`)
- [ ] **Полностью переделать в AI Support:**
  - Обработка вопросов через DeepSeek
  - Кнопка "Эскалировать"
  - Интеграция с владельцем

### 6.6 Admin Tools (`bot/routers/admin_tools/`)
- [ ] **Обновить модули:**
  - Server Manager (оставить)
  - User Editor (обновить под новую модель)
  - Statistics (обновить)
  - Notifications (оставить)
  
- [ ] **Добавить новые:**
  - Corporate Server Manager
    - `/add_corp_server` (интерактивный)
    - `/list_corp_servers`
    - `/remove_corp_server`
  - Discount Manager
    - `/grant_corp_discount`
  - AI Support Manager
    - Просмотр эскалаций
    - Ответы пользователям

---

## 📋 ЭТАП 7: AI Support (DeepSeek)

### 7.1 Сервис DeepSeek (`bot/services/deepseek.py`)
- [ ] Создать класс `DeepSeekService`:
  - Инициализация клиента (OpenAI-compatible API)
  - Метод `ask_question(question: str) → str`
  - Системный промпт:
    ```
    Ты – поддержка VPN-сервиса. Если вопрос касается оплаты, 
    подключения, настроек – отвечай по инструкции.
    Если вопрос не связан с темой, содержит угрозы, или ты не уверен – 
    ответь только: "НЕ УВЕРЕН"
    ```
  - Парсинг ответа на "НЕ УВЕРЕН"
  - Оценка уверенности (если доступно)

### 7.2 Эскалация к владельцу
- [ ] Создать `EscalationService`:
  - Отправка уведомления владельцу (MAX_DEV_ID)
  - Кнопка "Ответить" для владельца
  - Пересылка ответа пользователю с пометкой
  - История эскалаций

### 7.3 Интеграция в Support Router
- [ ] При получении вопроса:
  1. Отправить в DeepSeek
  2. Если "НЕ УВЕРЕН" → эскалация
  3. Если пользователь нажал "Эскалировать" → владельцу
  4. Логирование всех обращений

---

## 📋 ЭТАП 8: Система купонов

### 8.1 Coupon Service (`bot/services/coupon.py`)
- [ ] Создать `CouponService`:
  - `generate_coupon(user_id, discount_percent, valid_days)` → код
  - `validate_coupon(code, user_id)` → bool
  - `apply_coupon(code, user_id)` → discount_percent
  - `get_user_coupons(user_id)` → список купонов
  - Генерация кодов: `secrets.token_urlsafe(8)`

### 8.2 Интеграция с платежами
- [ ] Обновить `SubscriptionData` модель:
  - Добавить `coupon_code`
  - Добавить `original_price`
  - Добавить `final_price` (со скидкой)
  
- [ ] Обновить создание платежа:
  - Проверка купона
  - Расчёт скидки
  - Сохранение в payments.discount_applied

### 8.3 Реферальная система
- [ ] Обновить `ReferralService`:
  - При регистрации по ссылке → создать referral (status=pending)
  - После первой оплаты реферала → создать купон 10%
  - Уведомление рефереру с кодом купона
  - Проверка на максимум 50% (5 купонов)

---

## 📋 ЭТАП 9: Корпоративные серверы

### 9.1 Corporate Server Service (`bot/services/corporate_server.py`)
- [ ] Создать `CorporateServerService`:
  - `add_server(ip, api_key, slots, user_id)`
  - Шифрование API-ключа (Fernet)
  - Проверка подключения к 3X-UI
  - `get_server(user_id)`
  - `list_servers()` (для админа)
  - `check_expiry()`

### 9.2 Admin Commands
- [ ] `/add_corp_server` (интерактивный):
  1. Запрос IP панели
  2. Запрос API-ключа
  3. Запрос количества слотов (100/500)
  4. Запрос user_id клиента
  5. Проверка подключения
  6. Сохранение в БД
  
- [ ] `/list_corp_servers` - список всех корп. серверов
- [ ] `/remove_corp_server` - удаление сервера
- [ ] `/grant_corp_discount <user_id>` - начисление скидки

### 9.3 User Commands
- [ ] `/my_corp_server` - информация о сервере
- [ ] Кнопка "Связаться с владельцем" при выборе корп. тарифа

---

## 📋 ЭТАП 10: VPN Service адаптация

### 10.1 Обновление `bot/services/vpn.py`
- [ ] Заменить `py3xui` → `client3x`
- [ ] Обновить все методы:
  - `is_client_exists`
  - `create_client` (limitIp=1, expiryTime)
  - `update_client`
  - `get_client_data`
  - `get_key` (формирование ссылки подписки)
  
- [ ] Асинхронный режим client3x

### 10.2 Server Pool Service
- [ ] Оставить как есть
- [ ] Обновить под client3x API
- [ ] Добавить поддержку корпоративных серверов

---

## 📋 ЭТАП 11: Worker (фоновые задачи)

### 11.1 Создание `worker.py`
- [ ] Отдельный процесс для фоновых задач
- [ ] APScheduler для cron задач

### 11.2 Задачи
- [ ] **Subscription Expiry Check** (ежедневно):
  - Проверка истёкших подписок
  - Блокировка клиентов в 3X-UI (`remove_client`)
  - Уведомление пользователей
  
- [ ] **Corporate Server Check** (ежедневно):
  - Проверка корпоративных подписок
  - Уведомление владельца и клиента
  
- [ ] **Referral Reward Check** (при оплате):
  - Создание купонов для рефереров
  
- [ ] **Notifications** (за N дней до окончания):
  - За 3 дня
  - За 1 день
  - В день окончания

---

## 📋 ЭТАП 12: Тарифные планы

### 12.1 Обновление `plans.json`
```json
{
  "personal": [
    {"duration": 30, "price": 299},
    {"duration": 90, "price": 799},
    {"duration": 180, "price": 1499}
  ],
  "corporate": [
    {"slots": 100, "price": 9899},
    {"slots": 500, "price": 19499}
  ]
}
```

### 12.2 Plan Service
- [ ] Обновить `bot/services/plan.py`
- [ ] Загрузка из plans.json
- [ ] Методы получения цен
- [ ] Поддержка скидок

---

## 📋 ЭТАП 13: Локализация (опционально)

- [ ] Удалить Babel/i18n (если не нужен мультиязык)
- [ ] Все тексты в константах или config
- [ ] Или оставить для будущего расширения

---

## 📋 ЭТАП 14: Тестирование

### 14.1 Unit Tests
- [ ] Тесты Coupon Service
- [ ] Тесты Referral Service
- [ ] Тесты DeepSeek Service
- [ ] Тесты Corporate Server Service
- [ ] Тесты Payment Gateways (mock)

### 14.2 Integration Tests
- [ ] Покупка подписки (песочница ЮKassa)
- [ ] Применение купона
- [ ] Реферальная система
- [ ] AI Support
- [ ] Корпоративные серверы

### 14.3 E2E Tests
- [ ] Полный цикл покупки
- [ ] Эскалация к владельцу
- [ ] Worker задачи (истечение подписки)

---

## 📋 ЭТАП 15: Деплой

### 15.1 Docker
- [ ] Обновить `Dockerfile`
- [ ] Обновить `docker-compose.yml`
- [ ] Создать `.dockerignore`

### 15.2 Production Setup
- [ ] Настройка PostgreSQL
- [ ] Настройка Redis
- [ ] Настройка Traefik (SSL)
- [ ] Настройка webhook'ов (ЮKassa, YooMoney, MAX)
- [ ] Запуск миграций Alembic
- [ ] Запуск Bot + Worker

### 15.3 Monitoring
- [ ] Логирование (структурированное)
- [ ] Health checks
- [ ] Error tracking (Sentry опционально)

---

## 📊 Приоритизация

### 🔴 **КРИТИЧНЫЙ ПУТЬ (MVP):**
1. Этап 1-3: Инфраструктура + БД
2. Этап 4: MAX API адаптация
3. Этап 5: Платёжки (Yookassa + Yoomoney)
4. Этап 6: Основные роутеры (menu, subscription, profile)
5. Этап 10: VPN Service
6. Этап 12: Тарифы
7. Этап 15: Деплой

### 🟡 **ВТОРОЙ ПРИОРИТЕТ:**
8. Этап 7: AI Support (DeepSeek)
9. Этап 8: Купоны + рефералы
10. Этап 11: Worker задачи

### 🟢 **ТРЕТИЙ ПРИОРИТЕТ:**
11. Этап 9: Корпоративные серверы
12. Этап 14: Тесты
13. Этап 13: Локализация

---

## ⏱️ Оценка времени

| Этап | Сложность | Время |
|------|-----------|-------|
| 1-3: Инфраструктура + БД | ⭐⭐⭐ | 2-3 часа |
| 4: MAX API | ⭐⭐⭐⭐⭐ | 4-6 часов |
| 5: Платёжки | ⭐⭐⭐ | 2-3 часа |
| 6: Роутеры | ⭐⭐⭐⭐ | 4-5 часов |
| 7: AI Support | ⭐⭐⭐⭐ | 3-4 часа |
| 8: Купоны | ⭐⭐⭐ | 2-3 часа |
| 9: Корп. серверы | ⭐⭐⭐⭐ | 3-4 часа |
| 10: VPN Service | ⭐⭐⭐ | 2-3 часа |
| 11: Worker | ⭐⭐⭐ | 2-3 часа |
| 12-15: Тесты + Деплой | ⭐⭐⭐⭐ | 4-5 часов |

**ИТОГО:** ~28-39 часов разработки

---

## 🎯 Критерии готовности MVP

- [ ] Пользователь может купить подписку (299/799/1499₽)
- [ ] Оплата через ЮKassa или YooMoney
- [ ] Автоматическое создание клиента в 3X-UI
- [ ] Получение VPN ключа
- [ ] Админ-панель для управления серверами
- [ ] Базовая реферальная система (купон 10%)
- [ ] Worker блокирует истёкшие подписки
- [ ] Деплой через Docker Compose

---

## 📝 Примечания

1. **maxapi** - проверить документацию перед началом (может быть не на PyPi)
2. **client3x** - убедиться в поддержке async режима
3. **DeepSeek** - использовать OpenAI-compatible endpoint
4. **Fernet** - ENCRYPTION_KEY генерировать через `cryptography.fernet.Fernet.generate_key()`
5. **PostgreSQL** - использовать asyncpg драйвер
6. **Webhook URL'ы:**
   - MAX: `/webhook`
   - YooKassa: `/yookassa`
   - YooMoney: `/yoomoney`

---

**Дата создания:** 2026-04-13  
**Версия:** 1.0  
**Статус:** Готов к реализации ✅
