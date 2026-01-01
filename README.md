# رزومه آنلاین تعاملی - Interactive Resume

پروژه رزومه آنلاین تعاملی با FastAPI و HTML/CSS که شامل فرم درخواست پروژه، صفحه مدیریت ادمین و نمایش تعداد کاربران آنلاین به صورت زنده است.

## ویژگی‌های پروژه

### فرانت‌اند
- ✅ رزومه آنلاین با طراحی مدرن
- ✅ فرم درخواست پروژه با فیلدهای کامل
- ✅ نمایش تعداد کاربران آنلاین به صورت زنده (WebSocket)
- ✅ صفحه ادمین برای مدیریت درخواست‌ها

### بک‌اند
- ✅ FastAPI با مستندات Swagger/OpenAPI
- ✅ فرم درخواست پروژه با اعتبارسنجی
- ✅ احراز هویت JWT برای صفحه ادمین
- ✅ مدیریت درخواست‌ها (مشاهده، حذف، تغییر وضعیت)
- ✅ WebSocket برای نمایش تعداد کاربران آنلاین
- ✅ دیتابیس SQLite

## نصب و راه‌اندازی

### پیش‌نیازها
- Python 3.8 یا بالاتر
- pip

### نصب بک‌اند

1. وارد پوشه بک‌اند شوید:
```bash
cd backend
```

2. نصب وابستگی‌ها:
```bash
pip install -r requirements.txt
```

3. اجرای سرور:
```bash
python main.py
```

یا با uvicorn:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

سرور روی `http://localhost:8000` اجرا می‌شود.

### مستندات API

پس از اجرای سرور، می‌توانید به مستندات Swagger دسترسی داشته باشید:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### راه‌اندازی فرانت‌اند

فایل‌های HTML را می‌توانید با یک سرور ساده HTTP باز کنید. برای مثال:

```bash
# با Python
python -m http.server 8080

# یا با Node.js (http-server)
npx http-server -p 8080
```

**نکته مهم:** برای استفاده از WebSocket و API، باید URL بک‌اند را در فایل‌های HTML تنظیم کنید. در حال حاضر روی `http://localhost:8000` تنظیم شده است.

## استفاده از پروژه

### ورود به صفحه ادمین

1. به صفحه `admin.html` بروید
2. اطلاعات ورود پیش‌فرض:
   - Username: `admin`
   - Password: `admin123`

**⚠️ هشدار امنیتی:** در محیط production حتماً رمز عبور را تغییر دهید!

### ارسال درخواست پروژه

1. به صفحه اصلی (`index.html`) بروید
2. فرم "Request a Project" را پر کنید
3. درخواست خود را ارسال کنید

### مشاهده تعداد کاربران آنلاین

تعداد کاربران آنلاین به صورت خودکار در بالای صفحه اصلی نمایش داده می‌شود و با WebSocket به‌روزرسانی می‌شود.

## ساختار پروژه

```
.
├── backend/
│   ├── main.py              # فایل اصلی FastAPI
│   ├── database.py          # تنظیمات دیتابیس
│   ├── models.py            # مدل‌های دیتابیس
│   ├── requirements.txt     # وابستگی‌های Python
│   └── resume.db            # فایل دیتابیس SQLite (پس از اولین اجرا ایجاد می‌شود)
├── index.html               # صفحه اصلی رزومه
├── portfolio.html           # صفحه پورتفولیو
├── admin.html               # صفحه ادمین
├── styles.css               # استایل‌های CSS
├── portfolio.css            # استایل‌های پورتفولیو
└── README.md                # این فایل
```

## API Endpoints

### احراز هویت
- `POST /api/auth/login` - ورود به سیستم

### درخواست‌های پروژه
- `POST /api/project-requests` - ایجاد درخواست جدید
- `GET /api/project-requests` - دریافت همه درخواست‌ها (نیاز به احراز هویت)
- `GET /api/project-requests/{id}` - دریافت یک درخواست (نیاز به احراز هویت)
- `PATCH /api/project-requests/{id}` - به‌روزرسانی وضعیت درخواست (نیاز به احراز هویت)
- `DELETE /api/project-requests/{id}` - حذف درخواست (نیاز به احراز هویت)

### WebSocket
- `WS /ws/online-users` - اتصال WebSocket برای نمایش تعداد کاربران آنلاین

## دیپلوی

### دیپلوی روی لیارا (Liara)

1. حساب کاربری در [لیارا](https://liara.ir) ایجاد کنید
2. یک اپلیکیشن جدید ایجاد کنید
3. فایل‌های بک‌اند را آپلود کنید
4. متغیرهای محیطی را تنظیم کنید (در صورت نیاز)
5. اپلیکیشن را دیپلوی کنید

### دیپلوی روی VPS

1. سرور خود را آماده کنید (Python, pip)
2. فایل‌های پروژه را آپلود کنید
3. وابستگی‌ها را نصب کنید:
```bash
pip install -r requirements.txt
```
4. سرور را با systemd یا supervisor اجرا کنید

مثال systemd service:
```ini
[Unit]
Description=Resume Backend API
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/backend
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### تنظیم CORS

در فایل `backend/main.py`، تنظیمات CORS را برای دامنه فرانت‌اند خود تغییر دهید:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # دامنه فرانت‌اند
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### تغییر URL API در فرانت‌اند

در فایل‌های HTML (`index.html` و `admin.html`)، متغیر `API_BASE_URL` را به آدرس سرور خود تغییر دهید:

```javascript
const API_BASE_URL = 'https://your-backend-domain.com';
```

## امنیت

- ✅ احراز هویت JWT
- ✅ هش کردن رمز عبور (SHA256)
- ⚠️ در محیط production حتماً:
  - رمز عبور ادمین را تغییر دهید
  - از HTTPS استفاده کنید
  - SECRET_KEY را به صورت امن تنظیم کنید
  - CORS را محدود کنید
  - از دیتابیس امن‌تر (PostgreSQL) استفاده کنید

## توسعه

### افزودن فیلد جدید به فرم

1. در `backend/models.py` فیلد جدید را به مدل `ProjectRequest` اضافه کنید
2. در `backend/main.py` فیلد را به `ProjectRequestCreate` و `ProjectRequestResponse` اضافه کنید
3. در `index.html` فیلد را به فرم اضافه کنید

## پشتیبانی

برای سوالات و مشکلات، می‌توانید از طریق ایمیل تماس بگیرید: e3gaming47@gmail.com

## لایسنس

این پروژه برای استفاده آموزشی و شخصی است.

