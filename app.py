from flask import Flask, request, jsonify, render_template, send_from_directory
from requests_oauthlib import OAuth1
import requests
import base64
import time
import openai
import logging
from io import BytesIO
from PIL import Image
from werkzeug.utils import secure_filename
import time
import os
app = Flask(__name__)

# API Credentials
openai.api_key = os.getenv("OPENAI_API_KEY")
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

UPLOAD_FOLDER = "/home/ubuntu/thesis"  # Change to a valid directory
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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
        prompt= prompt + "IKEA hacking is the practice of modifying, repurposing, or customizing IKEA products to create unique, personalized, or more functional furniture and decor. It often involves combining different pieces, adding new materials, or altering designs to fit specific needs or aesthetics. In this image uploaded image you will see three flat panels, imagine they are materials for building new stuff. now answer based on this. Limit response to 100 words."
        # Check if an image file was uploaded
        if 'image' not in request.files:
            return jsonify({"error": "No image uploaded"}), 400

        image_file = request.files['image']

        # Convert image to base64
        image = Image.open(image_file)
        buffered = BytesIO()
        image.save(buffered, format="PNG")  # Ensure it's in PNG format
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')

        logging.info("Image received and converted to base64.")
        timestamp = int(time.time())
        filename = secure_filename(f"{timestamp}_{image_file.filename}")
        image_path = os.path.join(UPLOAD_FOLDER, filename)

        # Save the image directly
        image.save(image_path)

        #logging.info(f"Image saved locally pyat: {image_path}")

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
    app.run(debug=True)

