FROM python:3.10-slim

WORKDIR /app

# نصب وابستگی‌های سیستم
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# کپی کردن requirements و نصب وابستگی‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن فایل‌های پروژه
COPY . .

# لیارا از پورت 80 استفاده می‌کند
ENV PORT=80

# اجرای سرور
# استفاده از workers=1 برای جلوگیری از مشکلات SQLite
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-80} --workers 1

