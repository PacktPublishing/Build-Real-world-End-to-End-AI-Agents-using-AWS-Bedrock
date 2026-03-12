# Deploy Cohere Chatbot to streamlit 

docker build -t genai-cohere-chatbot .

# Optional
docker run -p 8501:8501 -v ~/.aws:/root/.aws genai-cohere-chatbot

aws ecr get-login-password \
        --region us-east-1 | docker login \
        --username AWS \
        --password-stdin 127489365181.dkr.ecr.us-east-1.amazonaws.com

docker tag genai-cohere-chatbot:latest 127489365181.dkr.ecr.us-east-1.amazonaws.com/genai-apps:genai-cohere-chatbot

docker push 127489365181.dkr.ecr.us-east-1.amazonaws.com/genai-apps:genai-cohere-chatbot
