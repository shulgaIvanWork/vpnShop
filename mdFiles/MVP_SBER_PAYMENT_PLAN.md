# 🚀 MVP PLAN - Ручное подтверждение оплаты (Сбер QR)

**Дата создания:** 2026-04-14  
**Цель:** Быстрый запуск с реферальной системой и ручной оплатой через Сбер  
**Время реализации:** ~3-4 часа

---

## 📋 АРХИТЕКТУРНЫЕ ИЗМЕНЕНИЯ

### Новые компоненты:

```
app/
├── bot/
│   ├── fsm/
│   │   ├── __init__.py          # НОВОЕ: FSM инициализация
│   │   ├── states.py            # НОВОЕ: Состояния FSM
│   │   └── storage.py           # НОВОЕ: Хранилище (Redis/Memory)
│   │
│   ├── routers/
│   │   ├── subscription/
│   │   │   ├── sber_payment.py  # НОВОЕ: Оплата через Сбер
│   │   │   └── receipt_handler.py # НОВОЕ: Обработка чеков
│   │   │
│   │   └── admin_tools/
│   │       └── payment_approval.py # НОВОЕ: Подтверждение оплат
│   │
│   └── services/
│       └── sber_payment.py      # НОВОЕ: Сервис оплаты Сбер
│
└── db/
    ├── models/
    │   └── manual_payment.py    # НОВОЕ: Таблица ручных оплат
    │
    └── migration/
        └── versions/
            └── [new_migration].py # НОВОЕ: Миграция для manual_payments
```

### Изменённые компоненты:

```
app/
├── __main__.py                  # ИЗМЕНЕНИЕ: Добавить FSM, обновить handlers
├── bot/
│   ├── routers/
│   │   ├── main_menu/
│   │   │   └── handler.py       # ИЗМЕНЕНИЕ: Создать пользователя в БД
│   │   ├── subscription/
│   │   │   └── subscription_handler.py # ИЗМЕНЕНИЕ: Интегрировать Сбер оплату
│   │   └── referral/
│   │       └── handler.py       # ИЗМЕНЕНИЕ: Подключить к БД
│   │
│   └── services/
│       ├── referral.py          # ИЗМЕНЕНИЕ: Реальная генерация купонов
│       └── coupon.py            # ИЗМЕНЕНИЕ: CRUD операции
│   │
│   └── models/
│       └── subscription_data.py # ИЗМЕНЕНИЕ: Добавить поле payment_method
│
└── db/
    └── models/
        ├── user.py              # ИЗМЕНЕНИЕ: Добавить helper методы
        ├── payment.py           # ИЗМЕНЕНИЕ: Добавить helper методы
        ├── coupon.py            # ИЗМЕНЕНИЕ: Добавить helper методы
        └── referral.py          # ИЗМЕНЕНИЕ: Добавить helper методы
```

---

## 🎯 ПЛАН РАЗРАБОТКИ (по шагам)

### **ШАГ 1: Database Helper Methods** (30 мин)

**Файлы для изменения:**
- `app/db/models/user.py`
- `app/db/models/payment.py`
- `app/db/models/coupon.py`
- `app/db/models/referral.py`

**Что добавить:**

**User модель:**
```python
@classmethod
async def get_or_create(cls, session, max_user_id: int, username: str = None) -> User

@classmethod
async def get_by_max_id(cls, session, max_user_id: int) -> User | None

async def update_subscription(self, session, **kwargs)
```

**Payment модель:**
```python
@classmethod
async def get_user_payments(cls, session, user_id: int) -> list[Payment]

@classmethod
async def create_payment(cls, session, **kwargs) -> Payment
```

**Coupon модель:**
```python
@classmethod
async def get_user_active_coupons(cls, session, user_id: int) -> list[Coupon]

@classmethod
async def use_coupon(cls, session, code: str) -> bool
```

**Referral модель:**
```python
@classmethod
async def create_referral(cls, session, referrer_id: int, referred_id: int)

@classmethod
async def get_referrer_stats(cls, session, user_id: int) -> dict
```

---

### **ШАГ 2: Alembic Migrations** (30 мин)

**Файлы:**
- `app/db/alembic.ini` (создать/настроить)
- `app/db/migration/env.py` (настроить)
- `app/db/migration/versions/` (создать миграции)

**Команды:**
```bash
cd c:\Users\shulg\Desktop\vpn\max-vpn-bot
docker-compose up -d postgres  # Запустить PostgreSQL

# Внутри контейнера bot или локально:
alembic revision --autogenerate -m "Add manual payments and helpers"
alembic upgrade head
```

**Что будет создано:**
- Таблица `manual_payments` (для отслеживания чеков)
- Все остальные таблицы (users, payments, coupons, referrals, servers)

---

### **ШАГ 3: FSM Implementation** (30 мин)

**Файлы:**
- `app/bot/fsm/__init__.py` (создать)
- `app/bot/fsm/states.py` (создать)
- `app/bot/fsm/storage.py` (создать)

**States:**
```python
class PaymentStates(StatesGroup):
    waiting_for_plan = State()        # Выбор тарифа
    waiting_for_payment_method = State()  # Выбор способа оплаты
    waiting_for_receipt = State()     # Ожидание чека
    waiting_for_coupon = State()      # Ввод купона
```

**Storage:** Redis (или Memory для тестов)

**Data to store:**
```python
{
    "user_id": 123,
    "plan_duration": 30,
    "plan_price": 299,
    "coupon_code": "ABC123",
    "discount_percent": 10,
    "final_price": 269,
    "payment_method": "sber_qr"
}
```

---

### **ШАГ 4: Manual Payment Model** (15 мин)

**Файл:** `app/db/models/manual_payment.py` (создать)

**Структура:**
```python
class ManualPayment(Base):
    __tablename__ = "manual_payments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    plan_duration = Column(Integer)  # 30, 90, 180 дней
    original_price = Column(Integer)  # 299, 799, 1499
    discount_applied = Column(Integer)  # 0-50%
    final_price = Column(Integer)
    
    receipt_photo_id = Column(String)  # MAX message ID с фото
    receipt_text = Column(Text)  # Комментарий клиента
    
    status = Column(String)  # pending/approved/rejected
    admin_id = Column(Integer)  # Кто подтвердил
    admin_comment = Column(Text)
    
    created_at = Column(DateTime)
    approved_at = Column(DateTime)
```

---

### **ШАГ 5: Sber Payment Service** (30 мин)

**Файл:** `app/bot/services/sber_payment.py` (создать)

**Функционал:**
```python
class SberPaymentService:
    def get_qr_code() -> str:
        """Вернуть QR код (статичный)"""
    
    def get_payment_details() -> dict:
        """Реквизиты для перевода"""
    
    async def create_manual_payment(
        session, user_id, plan_duration, price, receipt_data
    ) -> ManualPayment:
        """Создать запись о ручной оплате"""
    
    async def approve_payment(
        session, payment_id, admin_id
    ) -> User:
        """Подтвердить оплату и выдать ключ"""
    
    async def reject_payment(
        session, payment_id, admin_id, reason
    ):
        """Отклонить оплату"""
```

---

### **ШАГ 6: Subscription Handler Update** (45 мин)

**Файл:** `app/bot/routers/subscription/subscription_handler.py` (изменить)

**Новый flow:**

```
1. handle_plan_selection()
   ↓ Сохранить в FSM: duration, price
   
2. handle_payment_method_selection()
   ↓ Выбрать "sber_qr"
   ↓ Показать QR + реквизиты
   ↓ Попросить прикрепить чек
   
3. handle_receipt_upload()
   ↓ Получить фото/текст
   ↓ Сохранить в БД (ManualPayment)
   ↓ Отправить уведомление админу
   
4. [WAITING FOR ADMIN]
   
5. After admin approval:
   ↓ Создать клиента в 3X-UI
   ↓ Обновить подписку пользователя
   ↓ Отправить ключ клиенту
```

---

### **ШАГ 7: Receipt Handler** (30 мин)

**Файл:** `app/bot/routers/subscription/receipt_handler.py` (создать)

**Функционал:**
```python
async def handle_receipt_photo(update: Update):
    """Обработать полученный чек"""
    - Получить фото из сообщения
    - Получить данные из FSM (какой тариф)
    - Создать ManualPayment в БД (status=pending)
    - Отправить уведомление админу
    
async def handle_receipt_text(update: Update):
    """Обработать комментарий к оплате"""
    - Сохранить текст
    - Прикрепить к ManualPayment
```

---

### **ШАГ 8: Admin Payment Approval** (30 мин)

**Файл:** `app/bot/routers/admin_tools/payment_approval.py` (создать)

**Функционал:**
```python
@admin_command("pending_payments")
async def show_pending_payments(update: Update):
    """Показать все ожидающие оплаты"""
    - Получить из БД все pending payments
    - Показать чек + инфо о клиенте
    - Кнопки: "Подтвердить" / "Отклонить"

@callback_query_handler("approve_payment_")
async def approve_payment(update: Update):
    """Подтвердить оплату"""
    - Обновить ManualPayment (status=approved)
    - Создать/обновить подписку пользователя
    - Сгенерировать ключ (VPN Service)
    - Отправить ключ клиенту
    - Уведомить клиента

@callback_query_handler("reject_payment_")
async def reject_payment(update: Update):
    """Отклонить оплату"""
    - Обновить ManualPayment (status=rejected)
    - Спросить причину
    - Уведомить клиента
```

---

### **ШАГ 9: Referral System Integration** (30 мин)

**Файлы:**
- `app/bot/routers/referral/handler.py` (изменить)
- `app/bot/services/referral.py` (изменить)

**Функционал:**
```python
async def handle_referral(update: Update):
    """Показать реферальную ссылку"""
    - Получить user_id
    - Сгенерировать ссылку: https://max.ru/bot?start=ref_{user_id}
    - Показать статистику
    - Показать доступные купоны

async def process_referral_on_start(update: Update, referrer_id: int):
    """Обработать регистрацию по реферальной ссылке"""
    - Создать referral запись
    - Увеличить счётчик рефералов
    - (Купон создаётся после первой оплаты реферала)
```

---

### **ШАГ 10: User Creation on /start** (15 мин)

**Файл:** `app/bot/routers/main_menu/handler.py` (изменить)

**Изменения:**
```python
async def handle_start(update: Update):
    # Проверить есть ли referrer_id в start parameter
    referrer_id = extract_referrer_from_start_command(update)
    
    # Создать или получить пользователя
    async with config.db.session() as session:
        user = await User.get_or_create(
            session=session,
            max_user_id=update.message.from_user.id,
            username=update.message.from_user.username,
        )
        
        # Если есть реферер - создать запись
        if referrer_id:
            await Referral.create_referral(
                session, referrer_id, user.id
            )
        
        await session.commit()
    
    # Показать меню
```

---

### **ШАГ 11: Config & Environment** (15 мин)

**Файл:** `.env` (обновить)

**Добавить:**
```env
# Sber Payment
SBER_QR_CODE=base64_encoded_qr_or_url
SBER_RECEIPT_NUMBER=+79001234567  # Номер для перевода
SBER_RECEIPT_NAME=Иван И.  # Имя получателя

# Bot
MAX_BOT_TOKEN=f9LHodD0cOLqnuZPiVDbopg1Xrr3NXsGG8Jz0ODYZjg5ww9p8pNhGIEn5yF0nUeAqBRXGkkWaPh-XBT7Ewr-
MAX_BOT_USERNAME=@id720212246590_1_bot
MAX_BOT_DOMAIN=https://max.ru/id720212246590_1_bot

# Admin
BOT_ADMINS=YOUR_MAX_USER_ID  # Твой ID
BOT_DEV_ID=YOUR_MAX_USER_ID
```

---

### **ШАГ 12: Testing & Launch** (30 мин)

**Тесты:**
1. `/start` - создание пользователя ✅
2. `/referral` - генерация ссылки ✅
3. `/subscription` - выбор тарифа ✅
4. Оплата Сбер - показ QR ✅
5. Загрузка чека ✅
6. Admin подтверждение ✅
7. Выдача ключа ✅
8. Реферал оплачивает → купон рефереру ✅

---

## 📊 TIMELINE

| Шаг | Задача | Время | Статус |
|-----|--------|-------|--------|
| 1 | Database helpers | 30 мин | ⏳ Pending |
| 2 | Alembic migrations | 30 мин | ⏳ Pending |
| 3 | FSM implementation | 30 мин | ⏳ Pending |
| 4 | ManualPayment model | 15 мин | ⏳ Pending |
| 5 | Sber payment service | 30 мин | ⏳ Pending |
| 6 | Subscription handler | 45 мин | ⏳ Pending |
| 7 | Receipt handler | 30 мин | ⏳ Pending |
| 8 | Admin approval | 30 мин | ⏳ Pending |
| 9 | Referral integration | 30 мин | ⏳ Pending |
| 10 | User creation /start | 15 мин | ⏳ Pending |
| 11 | Config & .env | 15 мин | ⏳ Pending |
| 12 | Testing | 30 мин | ⏳ Pending |

**ИТОГО:** ~5 часов (можно сократить до 3-4 если параллельно делать)

---

## 🎯 MVP CRITERIA (Критерии готовности)

- [ ] Пользователь может зарегистрироваться через `/start`
- [ ] Реферальная ссылка генерируется и работает
- [ ] Можно выбрать тариф (299/799/1499₽)
- [ ] Показывается QR Сбера для оплаты
- [ ] Можно прикрепить чек
- [ ] Админ получает уведомление с чеком
- [ ] Админ может подтвердить/отклонить оплату
- [ ] После подтверждения - ключ выдаётся автоматически
- [ ] После оплаты реферала - реферер получает купон 10%
- [ ] Бот работает стабильно с PostgreSQL

---

## 🔜 FUTURE IMPROVEMENTS (После MVP)

1. **Автоматизация оплаты:**
   - Интеграция ЮKassa/YooMoney
   - Автоматическое подтверждение
   - Убрать ручной шаг

2. **AI Support (Этап 7):**
   - DeepSeek интеграция
   - Автоматические ответы

3. **Admin Tools (Этап 6 - остаток):**
   - Статистика
   - Управление серверами
   - Редактор пользователей

4. **Worker tasks (Этап 11):**
   - Проверка истёкших подписок
   - Автоматические уведомления

---

## ❓ ВОПРОСЫ ПЕРЕД НАЧАЛОМ:

1. **PostgreSQL:**
   - Запускаем через Docker Compose? (`docker-compose up -d postgres`)
   - Или у тебя есть локальный сервер?

2. **QR код Сбера:**
   - У тебя есть статичный QR код (картинка)?
   - Какой номер телефона/карты для перевода?
   - Какое имя указать получателя?

3. **Твой MAX User ID:**
   - Какой твой user ID в MAX? (нужен для админ-панели)
   - Можно узнать отправив сообщение боту и посмотрев логи

4. **3X-UI Panel:**
   - Есть ли уже рабочая панель 3X-UI?
   - IP, username, password?
   - Или пока сделать заглушку для выдачи ключей?

5. **Подтверждение:**
   - Начинаем с Шага 1 (Database helpers)?
   - Или сначала нужно что-то настроить?

---

**ГОТОВ НАЧАТЬ!** Скажи по вопросам выше - и погнали! 🚀
