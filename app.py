from flask import Flask, request, jsonify, render_template
from requests_oauthlib import OAuth1
import requests
import base64
import time
import openai
import logging
from io import BytesIO

app = Flask(__name__)

# API Credentials
openai.api_key = 'sk-BdvdR2fxcXoEo8ysIwZsLBMOYTvgW8JMbe_0TvOGeQT3BlbkFJbql_039llyBDaW3LcVsrI0e3ipKELA1xQ0nxaiW5MA'
API_KEY = 'yNalRooq2QVIxSZNAI3i4vSJ'
API_SECRET = 'jFLaOBoa8LQgb3qqLgdcxb4JlJe1R665HALCHp3NXhXOQhm6'
API_KEY2 = 'Av64ZSAvZTRDvbB4IsK9Skc0'
API_SECRET2 = 'nykNuSKtJVEaQJj9wOovU2CR8dkRE9v2CoieBFzbri1fsIDk'
BASE_URL = 'https://cad.onshape.com'
document_id = '9e49cec3c578620a859fa54a'
workspace_id = '27b2af55d6f022c9c1b45612'
element_id = '77579d1b4ebccb2c5dbfda5f'

# Logging setup
logging.basicConfig(
    filename='flask_app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)


@app.route('/')
def home():
    """Interactive form for user input."""
    return render_template('index.html')  # Render a form to accept the user's prompt.


@app.route('/process-comment', methods=['POST'])
def process_comment():
    """Fetch image, generate text, and post comment in a single workflow."""
    try:
        # Fetch the prompt from the form or JSON
        prompt = request.form.get('prompt') or request.json.get('prompt', 'Describe the image.')

        # Step 1: Fetch Image
        params = {
            "viewMatrix": "isometric",
            "outputHeight": 500,
            "outputWidth": 500,
            "pixelSize": 0,
            "edges": "show",
            "showAllParts": "true",
            "includeSurfaces": "false",
            "useAntiAliasing": "false",
            "includeWires": "false",
        }
        url = f'{BASE_URL}/api/v10/partstudios/d/{document_id}/w/{workspace_id}/e/{element_id}/shadedviews?nocache={int(time.time())}'
        auth = OAuth1(API_KEY, API_SECRET)

        response = requests.get(url, auth=auth, params=params)

        if response.status_code != 200:
            logging.error(f"Error fetching image: {response.text}")
            return jsonify({"error": "Failed to fetch image."}), response.status_code

        data = response.json()
        image_data = data['images'][0]

        # Decode the base64 image data directly into memory
        image_bytes = base64.b64decode(image_data)
        base64_image = base64.b64encode(image_bytes).decode('utf-8')  # Re-encode for OpenAI input
        
        logging.info("Image fetched successfully.")

        # Step 2: Generate Text
        try:
    # Open the image file
   
        # Make the API request
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text", "text": prompt},
                            {
                                "type":"image_url",
                                "image_url":{
                                    "url":f'data:image/png;base64,{base64_image}'
                                }
                            }
                                
                        ],
                    }
                ],
                )

            ai_response = response.choices[0].message.content
            logging.info(f"Generated text: {ai_response}")
        except Exception as e:
            logging.error(f"Error during OpenAI API call: {str(e)}")
            return jsonify({"error": "Failed to generate text."}), 500

        # Step 3: Post Comment
        url_comment = f'{BASE_URL}/api/v10/comments'
        auth_comment = (API_KEY2, API_SECRET2)
        payload = {
            "documentId": document_id,
            "workspaceId": workspace_id,
            "elementId": element_id,
            "message": ai_response,
        }

        comment_response = requests.post(url_comment, json=payload, auth=auth_comment)

        if comment_response.status_code == 200:
            logging.info("Comment added successfully.")
            return jsonify({"message": "Comment added successfully.", "ai_response": ai_response})
        else:
            logging.error(f"Error adding comment: {comment_response.text}")
            return jsonify({"error": "Failed to add comment."}), comment_response.status_code

    except Exception as e:
        logging.error(f"Exception in /process-comment: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
