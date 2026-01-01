# راهنمای اتصال به MSSQL در لیارا

## تنظیمات متغیرهای محیطی

برای اتصال به دیتابیس MSSQL در لیارا، باید متغیرهای محیطی زیر را در پنل لیارا تنظیم کنید:

```
DB_USER=sa
DB_NAME=my_db
DB_HOST=bromo.liara.cloud
DB_PORT=31858
DB_PASS=yw8FVaUqlvliRFxmcp7VnDUG
```

## نحوه تنظیم در پنل لیارا

1. وارد پنل لیارا شوید: https://console.liara.ir
2. به اپلیکیشن خود بروید
3. به بخش **Environment Variables** یا **متغیرهای محیطی** بروید
4. متغیرهای بالا را اضافه کنید

## اولویت اتصال دیتابیس

برنامه به ترتیب زیر دیتابیس را انتخاب می‌کند:

1. **MSSQL**: اگر همه متغیرهای `DB_USER`, `DB_NAME`, `DB_HOST`, `DB_PORT`, `DB_PASS` تنظیم شده باشند
2. **DATABASE_URL**: اگر متغیر `DATABASE_URL` تنظیم شده باشد (برای PostgreSQL و سایر دیتابیس‌ها)
3. **SQLite**: در غیر این صورت از SQLite در `/tmp/resume.db` استفاده می‌شود

## نصب ODBC Driver

اگر از Docker استفاده می‌کنید، ODBC Driver 18 for SQL Server به صورت خودکار در Dockerfile نصب می‌شود.

اگر از Python Platform استفاده می‌کنید، ممکن است نیاز به نصب دستی داشته باشید.

## تست اتصال

بعد از تنظیم متغیرها و deploy مجدد:

1. بررسی لاگ‌ها: باید پیام `✅ Application started successfully with MSSQL database` را ببینید
2. تست API: `https://your-app.liara.run/docs`
3. تست Health: `https://your-app.liara.run/health`

