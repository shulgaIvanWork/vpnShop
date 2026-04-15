# 📊 Прогресс разработки MVP - Sber QR Payment

**Дата:** 2026-04-14  
**Цель:** Быстрый запуск с реферальной системой и ручной оплатой через Сбер QR

---

## ✅ ВЫПОЛНЕНО (Шаги 1-6)

### Шаг 1: Database Helper Methods ✅
**Файлы изменены:**
- `app/db/models/user.py` - добавлены `get_or_create()`, `update_subscription()`
- `app/db/models/payment.py` - добавлен `get_pending_payments()`
- `app/db/models/coupon.py` - добавлен `get_total_user_discount()`
- `app/db/models/manual_payment.py` - **НОВЫЙ** модель для ручных оплат
- `app/db/models/__init__.py` - зарегистрирована ManualPayment

### Шаг 2: Alembic Migrations ✅
**Готово:**
- Alembic уже настроен в `app/db/migration/env.py`
- `alembic.ini` существует
- **Осталось запустить** когда Docker будет доступен:
  ```bash
  docker-compose up -d postgres
  alembic revision --autogenerate -m "Add manual payments table"
  alembic upgrade head
  ```

### Шаг 3: FSM Implementation ✅
**Файлы созданы:**
- `app/bot/fsm/__init__.py` - инициализация модуля
- `app/bot/fsm/states.py` - состояния PaymentStates (Enum)
- `app/bot/fsm/storage.py` - MemoryFSMStorage + RedisFSMStorage

**Состояния:**
- IDLE
- CHOOSING_PLAN
- CHOOSING_PAYMENT_METHOD
- WAITING_FOR_COUPON
- WAITING_FOR_RECEIPT
- PAYMENT_PENDING
- PAYMENT_COMPLETED

### Шаг 4: ManualPayment Model + Sber Config ✅
**Файлы созданы/изменены:**
- `app/db/models/manual_payment.py` - модель (create, approve, reject)
- `app/config.py` - добавлен SberPaymentConfig
- `.env` - добавлены SBER_QR_IMAGE_PATH, SBER_PHONE_NUMBER, SBER_RECEIPT_NAME

### Шаг 5: Sber Payment Service ✅
**Файлы созданы:**
- `app/bot/services/sber_payment.py`

**Методы:**
- `get_payment_details()` - реквизиты для перевода
- `get_payment_instructions(amount)` - инструкция для клиента
- `create_manual_payment()` - создать запись в БД
- `approve_payment()` - подтвердить оплату (админ)
- `reject_payment()` - отклонить оплату (админ)

### Шаг 6: Subscription Handler Integration ✅
**Файлы изменены:**
- `app/bot/routers/subscription/subscription_handler.py`
  - `handle_plan_selection()` - сохраняет данные в FSM
  - `handle_payment_method_selection()` - показывает Sber QR
  - `_show_sber_payment()` - новый helper для показа QR
- `app/__main__.py` - добавлен callback `payment_sber_qr`
- `app/bot/services/__init__.py` - добавлены FSM и SberPaymentService
- `app/bot/models/services_container.py` - добавлены поля fsm, sber_payment

**Новый Flow:**
```
1. User выбирает тариф → сохраняется в FSM
2. User выбирает "Сбербанк (QR)" → показывается QR + инструкция
3. User нажимает "Я оплатил" → (будет в Шаге 7)
4. Admin получает уведомление → (будет в Шаге 8)
5. Admin подтверждает → выдача ключа
```

---

## 🔄 В ПРОЦЕССЕ

### Шаг 7: Receipt Handler (приём чеков) ⏳ NEXT
**Что нужно сделать:**
- Создать `app/bot/routers/subscription/receipt_handler.py`
- Обработать фото/текст от пользователя
- Сохранить в ManualPayment
- Отправить уведомление админу

### Шаг 8: Admin Payment Approval ⏳
**Что нужно сделать:**
- Создать `app/bot/routers/admin_tools/payment_approval.py`
- Команда `/pending_payments` - показать все ожидающие
- Кнопки "Подтвердить" / "Отклонить"
- После подтверждения → создать VPN ключ

### Шаг 9: Referral System Integration ⏳
**Что нужно сделать:**
- Обновить `app/bot/routers/referral/handler.py`
- Подключить к БД (get_or_create user)
- Генерация реферальных ссылок
- Показ статистики + купонов

### Шаг 10: User Creation on /start ⏳
**Что нужно сделать:**
- Обновить `app/bot/routers/main_menu/handler.py`
- Создать пользователя в БД при /start
- Обработать referrer_id из start parameter

### Шаг 11: Config & .env ⏳ (почти готово)
**Готово:**
- `.env` создан с Sber config
- `config.py` обновлён

**Осталось:**
- Указать реальный номер телефона Сбера
- Проверить путь к QR изображению

### Шаг 12: Testing & Launch ⏳
**Что нужно:**
- Запустить Docker (postgres, redis)
- Применить миграции Alembic
- Протестировать весь flow
- Исправить баги

---

## 📋 СЛЕДУЮЩИЕ ШАГИ (сегодня)

### Приоритет 1: Receipt Handler (30 мин)
Создать обработчик для приёма чеков от пользователей.

### Приоритет 2: Admin Approval (30 мин)
Создать админ-панель для подтверждения оплат.

### Приоритет 3: Referral + /start (30 мин)
Завершить реферальную систему.

### Приоритет 4: Test (30 мин)
Запустить и протестировать.

---

## 🎯 MVP Flow (готов на 60%)

```
✅ /start → (нужно создать пользователя)
✅ /subscription → выбрать тариф → FSM сохранён
✅ Выбрать Сбербанк QR → показан QR + инструкция
⏳ Прикрепить чек → (Шаг 7)
⏳ Admin уведомление → (Шаг 8)
⏳ Admin подтверждение → (Шаг 8)
⏳ Выдача ключа → (Шаг 8)
⏳ Реферальный купон → (Шаг 9)
```

---

## 🐛 ЗАМЕЧЕННЫЕ ПРОБЛЕМЫ

1. **Docker не запущен** - нужно запустить PostgreSQL для миграций
2. **QR изображение** - лежит в `app/images/qr.webp`, нужно проверить что путь правильный
3. **Номер телефона Сбера** - в `.env` стоит заглушка `+79001234567`, заменить на реальный
4. **3X-UI панель** - не подключена, пока создаём заглушку для ключей

---

## 📝 ЗАМЕТКИ

- FSM использует MemoryStorage (пока Redis не запущен)
- Payment flow полностью ручной (админ подтверждает)
- ЮKassa/YooMoney отключены (будут добавлены позже)
- Все тексты на русском языке

---

**Время затрачено:** ~2 часа  
**Осталось:** ~2 часа до рабочего MVP
