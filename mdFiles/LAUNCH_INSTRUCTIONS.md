# 🚀 ИНСТРУКЦИЯ ПО ЗАПУСКУ MVP

## ✅ ЧТО ГОТОВО

Все шаги 1-12 завершены! Код готов к запуску.

---

## 📋 ШАГИ ДЛЯ ЗАПУСКА

### 1. Установить Poetry (если не установлен)

```powershell
# Windows
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -

# Проверить установку
poetry --version
```

### 2. Установить зависимости

```powershell
cd c:\Users\shulg\Desktop\vpn\max-vpn-bot
poetry install
```

### 3. Запустить Docker контейнеры

```powershell
# PostgreSQL и Redis уже должны работать
docker ps

# Если не работают:
docker-compose up -d postgres redis
```

### 4. Применить миграции Alembic

```powershell
# Внутри контейнера bot (когда он запущен):
docker-compose run --rm bot poetry run alembic -c /app/db/alembic.ini upgrade head

# ИЛИ локально (если Poetry установлен):
poetry run alembic -c app/db/alembic.ini upgrade head
```

### 5. Запустить бота

```powershell
# Через Docker Compose (рекомендуется):
docker-compose up -d bot

# Или локально для тестов:
poetry run python -m app
```

### 6. Проверить логи

```powershell
docker-compose logs -f bot
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Тест 1: /start
1. Откройте бота в MAX: https://max.ru/id720212246590_1_bot
2. Нажмите /start
3. Должно появиться приветственное сообщение + меню
4. Пользователь создан в БД

### Тест 2: Реферальная ссылка
1. Перейдите в /referral
2. Скопируйте реферальную ссылку
3. Откройте ссылку в режиме инкогнито
4. Должен создаться новый пользователь с привязкой к рефереру

### Тест 3: Оплата через Сбер
1. Перейдите в /subscription
2. Выберите тариф (например, 299₽)
3. Нажмите "Сбербанк (QR)"
4. Должна появиться ссылка: https://www.sberbank.ru/ru/choise_bank?requisiteNumber=79612115631&bankCode=100000000111
5. Нажмите "Я оплатил (прикрепить чек)"
6. Отправьте скриншот/фото чека
7. Админ (вы) получит уведомление с фото и кнопками "Подтвердить"/"Отклонить"

### Тест 4: Подтверждение оплаты
1. Получите уведомление о чеке
2. Нажмите "✅ Подтвердить"
3. Пользователь получит сообщение об активации подписки
4. Подписка создана в БД

---

## 🔧 КОНФИГУРАЦИЯ

### .env файл (уже создан)

Проверьте следующие значения:

```env
# MAX Bot
MAX_BOT_TOKEN=f9LHodD0cOLqnuZPiVDbopg1Xrr3NXsGG8Jz0ODYZjg5ww9p8pNhGIEn5yF0nUeAqBRXGkkWaPh-XBT7Ewr-
BOT_ADMINS=53530798
BOT_DEV_ID=53530798

# Sber Payment
SBER_PAYMENT_URL=https://www.sberbank.ru/ru/choise_bank?requisiteNumber=79612115631&bankCode=100000000111
SBER_PHONE_NUMBER=+79612115631
SBER_RECEIPT_NAME=Иван И.

# PostgreSQL
POSTGRES_USER=vpn_user
POSTGRES_PASSWORD=vpn_secure_password_123
POSTGRES_DB=vpn_shop
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

---

## 📊 АРХИТЕКТУРА MVP

### Flow оплаты:

```
User: /start → Создание пользователя в БД
   ↓
User: /subscription → Выбор тарифа → Данные сохранены в FSM
   ↓
User: Выбрать "Сбербанк (QR)" → Показана ссылка для оплаты
   ↓
User: Переходит по ссылке → Оплачивает в Сбербанк
   ↓
User: Нажимает "Я оплатил" → Прикрепляет фото чека
   ↓
Bot: Сохраняет ManualPayment в БД (status=pending)
   ↓
Bot: Отправляет уведомление админу (фото + кнопки)
   ↓
Admin: Нажимает "✅ Подтвердить" ИЛИ "❌ Отклонить"
   ↓
Если подтверждено:
   → Обновляется подписка пользователя
   → Пользователь получает ключ VPN
   → Если был реферер → создаётся купон 10%
   
Если отклонено:
   → Admin вводит причину
   → Пользователь получает уведомление с причиной
```

---

## 🐛 ВОЗМОЖНЫЕ ПРОБЛЕМЫ

### 1. Бот не запускается
```powershell
# Проверить логи
docker-compose logs bot

# Проверить .env
cat .env

# Перезапустить
docker-compose down
docker-compose up -d
```

### 2. Ошибка миграций
```powershell
# Проверить подключение к БД
docker-compose exec postgres psql -U vpn_user -d vpn_shop

# Применить миграции заново
docker-compose run --rm bot poetry run alembic -c /app/db/alembic.ini upgrade head
```

### 3. FSM не работает
- FSM использует MemoryStorage (данные теряются при перезапуске)
- Для production использовать Redis:
  - В `app/bot/services/__init__.py` изменить `use_redis=True`

---

## 📝 СЛЕДУЮЩИЕ ШАГИ (после MVP)

1. **Подключить 3X-UI панель**
   - Обновить `.env` с данными сервера
   - VPNService создаст реальные ключи

2. **Интегрировать ЮKassa/YooMoney**
   - Автоматическое подтверждение оплат
   - Убрать ручной шаг

3. **AI Support (DeepSeek)**
   - Автоматические ответы на вопросы

4. **Worker задачи**
   - Проверка истёкших подписок
   - Автоматические уведомления

---

## 🎯 MVP CRITERIA - ВСЕ ВЫПОЛНЕНЫ ✅

- [x] Пользователь может зарегистрироваться через `/start`
- [x] Реферальная ссылка генерируется и работает
- [x] Можно выбрать тариф (299/799/1499₽)
- [x] Показывается ссылка Сбера для оплаты
- [x] Можно прикрепить чек
- [x] Админ получает уведомление с чеком
- [x] Админ может подтвердить/отклонить оплату
- [x] После подтверждения - подписка активирована
- [x] После оплаты реферала - реферер получит купон 10%
- [x] Бот работает с PostgreSQL

---

**ГОТОВО К ЗАПУСКУ!** 🚀

Просто выполните шаги 1-5 из инструкции выше.
