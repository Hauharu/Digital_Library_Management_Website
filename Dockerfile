# Sử dụng Python image chính thức
FROM python:3.9-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Sao chép file requirements trước để tận dụng cache của Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Chạy Flask (cổng 5000 là mặc định)
EXPOSE 5000

# Lệnh chạy ứng dụng
CMD ["python", "app.py"]