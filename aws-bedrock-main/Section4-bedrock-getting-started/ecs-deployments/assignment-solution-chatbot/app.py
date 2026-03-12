import streamlit as st
import boto3
import json
import base64
import datetime

# Clients
client_bedrock = boto3.client('bedrock-runtime')
client_s3 = boto3.client('s3')
bucket_name = "nl-bedrock"

st.title("🎨 AI Image Generator with Bedrock")

if "responses" not in st.session_state:
    st.session_state.responses = []

with st.form(key="image_form"):
    prompt = st.text_input("Enter a prompt for image generation:", value="")
    submitted = st.form_submit_button("Generate")

    if submitted and prompt:
        try:
            # Bedrock Image Generation
            response = client_bedrock.invoke_model(
                contentType='application/json',
                accept='application/json',
                modelId='stability.stable-diffusion-xl-v1',
                body=json.dumps({
                    "text_prompts": [{"text": prompt}],
                    "cfg_scale": 10,
                    "steps": 50,
                    "seed": 0
                })
            )
            response_bedrock_byte = json.loads(response['body'].read())
            image_base64 = response_bedrock_byte['artifacts'][0]['base64']
            image_bytes = base64.b64decode(image_base64)

            # Upload to S3
            image_key = 'generated_images/img_' + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + '.png'
            client_s3.put_object(
                Bucket=bucket_name,
                Body=image_bytes,
                Key=image_key,
                ContentType='image/png'
            )

            # Generate Presigned URL
            presigned_url = client_s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': image_key},
                ExpiresIn=3600
            )

            st.session_state.responses.append((prompt, presigned_url))
            st.success("Image generated and uploaded successfully!")

        except Exception as e:
            st.error(f"Failed to generate image: {e}")

# Show past responses
st.markdown("### 📸 Generated Image Links")
for prompt, url in st.session_state.responses[::-1]:
    st.markdown(f"**Prompt:** {prompt}")
    st.markdown(f"[View Image]({url})", unsafe_allow_html=True)