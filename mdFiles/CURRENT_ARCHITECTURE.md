# 🚨 CURRENT ARCHITECTURE STATUS

## ✅ Completed Components

### Infrastructure (Stage 1-2)
- ✅ Docker Compose (PostgreSQL, Redis, Bot, Worker)
- ✅ Configuration system (config.py)
- ✅ Dependencies (pyproject.toml)
- ✅ Environment variables (.env.example)

### Database (Stage 3)
- ✅ User model (MAX-specific fields)
- ✅ Payment model (with discount tracking)
- ✅ Referral model (coupon-based)
- ✅ Coupon model (discount codes)
- ✅ Server model
- ✅ CorporateServer model

### MAX API Integration (Stage 4)
- ✅ Official maxapi library integrated
- ✅ MAXBot wrapper
- ✅ MAXDispatcher with polling
- ✅ InlineKeyboardMarkup (callback, link, message, clipboard)
- ✅ Message types and utilities

### Payment Gateways (Stage 5)
- ✅ YooKassa gateway (SDK integrated)
- ✅ YooMoney gateway (SDK integrated)
- ✅ Discount coupon support
- ✅ Webhook handlers (ready)
- ✅ Payment model integration

### Bot Handlers (Stage 6 - 85%)
- ✅ Main Menu (/start, /menu)
- ✅ Subscription (/subscription) - payment flow incomplete
- ✅ Profile (/profile) - DB integration incomplete
- ✅ Referral (/referral) - DB integration incomplete
- ✅ Support (/support) - complete

### Services
- ✅ VPNService (placeholder for 3X-UI)
- ✅ NotificationService (complete)
- ✅ CouponService (complete)
- ✅ ServicesContainer (complete)

---

## ❌ Missing Components (Critical for Launch)

### 1. FSM (Finite State Machine)
**Status:** Not implemented  
**Priority:** 🔴 Critical  
**Purpose:** Store user state during payment flow

**What's needed:**
- FSM storage (Redis or Memory)
- State definitions for payment flow
- Save/restore SubscriptionData

**Files to create:**
- `app/bot/fsm/states.py`
- `app/bot/fsm/storage.py`

---

### 2. Database Helper Methods
**Status:** Partial (models exist, methods missing)  
**Priority:** 🔴 Critical  
**Purpose:** CRUD operations for users, payments, coupons

**What's needed:**

**User model:**
```python
get_or_create(session, max_user_id, username)
get_by_max_id(session, max_user_id)
update_subscription(session, user_id, **kwargs)
```

**Payment model:**
```python
get_user_payments(session, user_id)
get_by_payment_gateway_id(session, gateway_payment_id)
create_payment(session, **kwargs)
```

**Coupon model:**
```python
get_user_active_coupons(session, user_id)
use(session, code)
```

**Files to update:**
- `app/db/models/user.py`
- `app/db/models/payment.py`
- `app/db/models/coupon.py`
- `app/db/models/referral.py`

---

### 3. Alembic Migrations
**Status:** Not configured  
**Priority:** 🔴 Critical  
**Purpose:** Database schema management

**What's needed:**
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

**Files to create:**
- `alembic.ini`
- `alembic/env.py`
- `alembic/versions/*.py`

---

### 4. Payment Integration in Handlers
**Status:** Stub only  
**Priority:** 🔴 Critical  
**Purpose:** Actually process payments

**Current code (stub):**
```python
async def handle_payment_method_selection(...):
    text = "⚠️ Функция в разработке"
```

**Needed code:**
```python
async def handle_payment_method_selection(...):
    # Get subscription data from FSM
    data = await get_subscription_data(user_id)
    
    # Create payment
    gateway = GatewayFactory.get_gateway(method)
    payment_url = await gateway.create_payment(data)
    
    # Send payment link to user
    await bot.send_message(user_id, f"💳 Оплатите: {payment_url}")
```

**Files to update:**
- `app/bot/routers/subscription/subscription_handler.py`

---

### 5. Webhook Server
**Status:** Not configured  
**Priority:** 🔴 Critical  
**Purpose:** Receive payment notifications

**What's needed:**
- aiohttp web server in `__main__.py`
- Register webhook routes
- Run server alongside bot polling
- Configure public HTTPS URL

**Files to update:**
- `app/__main__.py`

---

### 6. User Creation on /start
**Status:** Not implemented  
**Priority:** 🔴 Critical  
**Purpose:** Track users in database

**Current code:**
```python
async def handle_start(...):
    user_id = update.message.from_user.id
    # No database interaction
```

**Needed code:**
```python
async def handle_start(...):
    user_id = update.message.from_user.id
    
    async with config.db.session() as session:
        user = await User.get_or_create(
            session=session,
            max_user_id=user_id,
            username=update.message.from_user.username,
        )
        await session.commit()
```

**Files to update:**
- `app/bot/routers/main_menu/handler.py`

---

### 7. Admin Tools
**Status:** Not started  
**Priority:** 🔵 Low (can be done after launch)  
**Purpose:** Manage bot from admin panel

**What's needed:**
- Server Manager
- User Editor
- Statistics
- Corporate Server Manager
- Discount Manager
- AI Support Manager

---

## 📦 External Dependencies

### Required from You:

1. **MAX Bot Credentials**
   - Bot token
   - Bot username
   - Bot domain (HTTPS)

2. **Database**
   - PostgreSQL connection details
   - Or use Docker Compose

3. **Payment Systems**
   - YooKassa: shop_id + secret token
   - YooMoney: wallet_id + notification secret

4. **Webhook Domain**
   - Public HTTPS URL for payment notifications
   - Or ngrok for testing

---

## 🔄 Data Flow (Current vs Needed)

### Current Flow (Incomplete):
```
/start → Show menu → Click subscription → Select plan → Select payment
                                                        ↓
                                               "Feature in development" ❌
```

### Needed Flow (Complete):
```
/start → Create user in DB → Show menu
    ↓
Click subscription → Select plan → Save to FSM
    ↓
Select payment → Apply coupon (if any) → Create payment
    ↓
Send payment URL → User pays → Webhook received
    ↓
Update payment status → Create subscription → Send key ✅
```

---

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────┐
│                  MAX API                        │
│           (Official maxapi library)             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│             MAXDispatcher                       │
│    (Routes updates to handlers)                 │
└─────────┬──────────────┬────────────┬───────────┘
          │              │            │
          ▼              ▼            ▼
┌──────────────┐ ┌────────────┐ ┌──────────┐
│   Handlers   │ │   FSM      │ │ Services │
│  (85% done)  │ │ (MISSING)  │ │  (Done)  │
└──────┬───────┘ └────────────┘ └────┬───────┘
       │                              │
       ▼                              ▼
┌──────────────┐            ┌──────────────────┐
│ Payment GWs  │            │   PostgreSQL     │
│  (Done)      │            │ (Models done,    │
│              │            │  methods MISSING)│
└──────────────┘            └──────────────────┘
       │                              ▲
       ▼                              │
┌──────────────┐            ┌──────────────────┐
│  Webhooks    │────────────▶│  Alembic Migs   │
│ (MISSING)    │            │   (MISSING)      │
└──────────────┘            └──────────────────┘
```

---

## 🎯 Next Steps

See `TODO_BEFORE_LAUNCH.md` for detailed action plan.

**Estimated time to complete:** ~3.5 hours

**Priority order:**
1. Database helper methods (30 min)
2. Alembic migrations (30 min)
3. FSM implementation (30 min)
4. Payment integration (1 hour)
5. Webhook server (30 min)
6. Testing (1 hour)

---

**Last updated:** 2026-04-13  
**Status:** 70% complete overall
