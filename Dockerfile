FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (better Docker caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Streamlit runs on port 8501
EXPOSE 8501

# Run Streamlit
CMD ["streamlit", "run", "streamlit_gui.py", "--server.address", "0.0.0.0", "--server.port", "8501"]
