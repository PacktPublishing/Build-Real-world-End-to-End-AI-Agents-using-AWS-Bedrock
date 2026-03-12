# Deploy Cohere Chatbot to streamlit 

docker build -t mortgage-assistant .

# Optional
docker run -p 8501:8501 -v ~/.aws:/root/.aws mortgage-assistant

aws ecr get-login-password \
        --region us-east-1 | docker login \
        --username AWS \
        --password-stdin 127489365181.dkr.ecr.us-east-1.amazonaws.com

docker tag mortgage-assistant:latest 127489365181.dkr.ecr.us-east-1.amazonaws.com/genai-apps:mortgage-assistant

docker push 127489365181.dkr.ecr.us-east-1.amazonaws.com/genai-apps:mortgage-assistant
