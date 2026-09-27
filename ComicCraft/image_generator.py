from google import genai
from dotenv import load_dotenv
import os
import base64


# ==============================
# LOAD API KEY
# ==============================

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# ==============================
# GENERATE IMAGE
# ==============================

def generate_panel_image(prompt, filename):

    try:

        interaction = client.interactions.create(
            model="gemini-3.1-flash-image",
            input=prompt,
            response_format={
                "type": "image",
                "aspect_ratio": "16:9",
                "image_size": "1K"
            }
        )

        image_data = interaction.output_image.data

        image_bytes = base64.b64decode(image_data)

        output_path = os.path.join(
            "static",
            "images",
            filename
        )

        with open(output_path, "wb") as file:
            file.write(image_bytes)

        print(
            f"Image generated successfully: {output_path}"
        )

        return output_path


    except Exception as e:

        print(
            "IMAGE GENERATION ERROR:",
            repr(e)
        )

        return None