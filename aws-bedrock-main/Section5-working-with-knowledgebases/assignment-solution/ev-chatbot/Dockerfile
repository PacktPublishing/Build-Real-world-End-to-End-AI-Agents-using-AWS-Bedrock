# Use an official Python runtime as a parent image.
FROM python:3.9-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file into the container.
COPY requirements.txt .

# Upgrade pip and install dependencies.
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the rest of the app code into the container.
COPY . .

# Expose the port that Streamlit uses.
EXPOSE 8501

# Command to run the Streamlit app.
CMD ["streamlit", "run", "app.py", "--server.enableCORS", "false", "--server.port", "8501"]