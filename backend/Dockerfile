FROM python:3.10-slim

WORKDIR /app

# نصب وابستگی‌های سیستم و ODBC Driver برای MSSQL
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    gnupg \
    unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && rm -rf /var/lib/apt/lists/*

# کپی کردن requirements و نصب وابستگی‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن فایل‌های بک‌اند
COPY *.py ./
COPY requirements.txt ./

# ایجاد دایرکتوری static و کپی فایل‌های فرانت‌اند
RUN mkdir -p static
COPY ../index.html static/
COPY ../portfolio.html static/
COPY ../admin.html static/
COPY ../styles.css static/
COPY ../portfolio.css static/

# لیارا از پورت 80 استفاده می‌کند
ENV PORT=80

# اجرای سرور
# استفاده از workers=1 برای جلوگیری از مشکلات SQLite
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-80} --workers 1

