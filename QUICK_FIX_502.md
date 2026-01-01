# راهنمای سریع رفع خطای 502

## مشکل: 502 Bad Gateway

## راه حل سریع:

### 1. بررسی لاگ‌ها در پنل لیارا

1. وارد پنل لیارا شوید: https://console.liara.ir
2. به اپلیکیشن `artprinte3` بروید
3. روی **"مشاهده لاگ‌ها"** یا **"View Logs"** کلیک کنید
4. خطاها را بررسی کنید

### 2. بررسی تنظیمات Start Command

در پنل لیارا:
1. به بخش **"Settings"** یا **"Configuration"** بروید
2. **Start Command** باید این باشد:
   ```
   uvicorn main:app --host 0.0.0.0 --port 80 --workers 1
   ```

### 3. دیپلوی مجدد

**روش 1: از طریق Git**
```bash
git add backend/
git commit -m "Fix 502: add health check and improve startup"
git push origin main
```

**روش 2: از طریق پنل**
- فایل‌های جدید را آپلود کنید
- Deploy کنید

## تغییرات اعمال شده:

✅ Health check endpoint (`/health`) اضافه شد
✅ Root endpoint بهبود یافت
✅ Start command در liara.json بهبود یافت
✅ Procfile اضافه شد
✅ Error handling بهتر شد

## تست بعد از دیپلوی:

1. Health Check: `https://artprinte3.liara.run/health`
2. Root: `https://artprinte3.liara.run/`
3. Docs: `https://artprinte3.liara.run/docs`

---

**مهم: بعد از دیپلوی، حتماً لاگ‌ها را بررسی کنید!**

