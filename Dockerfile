FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
COPY startup.sh .
RUN chmod +x startup.sh
CMD ["./startup.sh"]
