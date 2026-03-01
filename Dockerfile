# Use the official lightweight Python 3.11 image
FROM python:3.11-slim
# Set the working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
build-essential \
&& rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install pip dependencies
# Note: Adding extra dependencies missing from the base requirements.txt
RUN pip install --no-cache-dir -r requirements.txt deep-translator nltk fpdf certifi

# Pre-download the NLTK VADER lexicon during the image build
RUN python -c "import nltk; nltk.download('vader_lexicon')"

# Copy the rest of the application code
COPY . .

# Ensure the startup script is executable
RUN chmod +x start.sh

# Expose the Streamlit ports
EXPOSE 8501 8502

# Command to run the application
CMD ["./start.sh"]
