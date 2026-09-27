from dotenv import load_dotenv
import os
import json
import io

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from google import genai

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak
)
from reportlab.lib.units import mm


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")


# ==========================================
# GEMINI CLIENT
# ==========================================

client = genai.Client(api_key=API_KEY)


# ==========================================
# FASTAPI
# ==========================================

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator"
)

templates = Jinja2Templates(
    directory="templates"
)


# ==========================================
# REQUEST MODEL
# ==========================================

class ComicRequest(BaseModel):
    idea: str


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# ==========================================
# HISTORY
# ==========================================

@app.get("/history")
def history(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={}
    )


# ==========================================
# GENERATE COMIC
# ==========================================

@app.post("/generate")
def generate_comic(data: ComicRequest):

    try:

        idea = data.idea.strip()

        if not idea:

            return JSONResponse(
                status_code=400,
                content={
                    "message":
                    "Please enter a comic idea first."
                }
            )


        prompt = f"""
You are ComicCraft, an AI Comic Story Creator.

Create a complete comic storyline based on
the user's idea.

USER IDEA:
{idea}

Create the story with the following information:

1. TITLE
A creative title for the comic.

2. GENRE
The genre of the comic.

3. MAIN CHARACTERS
Create the important characters.

For every character provide:
- name
- personality
- role

4. SETTING
Describe where and when the story takes place.

5. CHAPTER 1
The beginning of the story.

Include:
- scene
- actions
- dialogue

6. CHAPTER 2
Continue directly from Chapter 1.

Include:
- scene
- actions
- dialogue

7. CHAPTER 3
Continue directly from Chapter 2.

Include:
- scene
- actions
- dialogue

8. ENDING
Give the story a clear ending.

IMPORTANT RULES:

- Keep the entire story connected.
- Characters must remain consistent.
- Use natural dialogue.
- Include interesting actions and scenes.
- Make the story suitable for a general audience.
- Make it detailed enough for a college project demonstration.
- Do not mention AI or Gemini inside the story.
- Do not explain how the story was created.
- Do not leave any section empty.

VERY IMPORTANT:

Return ONLY valid JSON.

Use EXACTLY this structure:

{{
    "title": "Comic title",
    "genre": "Comic genre",
    "characters": [
        {{
            "name": "Character name",
            "personality": "Character personality",
            "role": "Character role"
        }}
    ],
    "setting": "Story setting",
    "chapter1": {{
        "scene": "Scene description",
        "actions": "Actions happening in the scene",
        "dialogue": "Character dialogue"
    }},
    "chapter2": {{
        "scene": "Scene description",
        "actions": "Actions happening in the scene",
        "dialogue": "Character dialogue"
    }},
    "chapter3": {{
        "scene": "Scene description",
        "actions": "Actions happening in the scene",
        "dialogue": "Character dialogue"
    }},
    "ending": "Clear ending of the comic"
}}

Do not add Markdown.
Do not add ```json.
Do not add any text before or after the JSON.
"""


        response = client.models.generate_content(

            model="gemini-3.8-flash",

            contents=prompt,

            config={
                "response_mime_type":
                "application/json",

                "temperature": 0.9,

                "max_output_tokens": 3000
            }
        )


        response_text = response.text


        if not response_text:

            return JSONResponse(
                status_code=500,
                content={
                    "message":
                    "Gemini returned an empty response."
                }
            )


        try:

            comic = json.loads(
                response_text
            )

        except json.JSONDecodeError:

            print(
                "INVALID GEMINI JSON:",
                response_text
            )

            return JSONResponse(
                status_code=500,
                content={
                    "message":
                    "Gemini returned an invalid story format."
                }
            )


        return {

            "message":
            "Comic story generated successfully!",

            "comic":
            comic
        }


    except Exception as e:

        print(
            "GEMINI ERROR:",
            repr(e)
        )

        error_text = str(e)


        if "429" in error_text:

            message = (
                "Gemini rate limit reached. "
                "Please wait before trying again."
            )

        elif "503" in error_text:

            message = (
                "Gemini is temporarily busy right now. "
                "Please wait and try again later."
            )

        elif "404" in error_text:

            message = (
                "The selected Gemini model is "
                "unavailable for this API account."
            )

        elif (
            "API key" in error_text
            or "api_key" in error_text
            or "authentication"
            in error_text.lower()
        ):

            message = (
                "Gemini API key problem. "
                "Please check your .env file."
            )

        else:

            message = (
                "Comic generation failed. "
                "Please check the terminal."
            )


        return JSONResponse(

            status_code=500,

            content={

                "message":
                message,

                "error":
                error_text
            }
        )


# ==========================================
# DOWNLOAD PDF
# ==========================================

@app.post("/download-pdf")
def download_pdf(comic: dict):

    try:

        # --------------------------------------
        # PDF BUFFER
        # --------------------------------------

        buffer = io.BytesIO()


        # --------------------------------------
        # PDF DOCUMENT
        # --------------------------------------

        document = SimpleDocTemplate(

            buffer,

            pagesize=A4,

            rightMargin=18 * mm,

            leftMargin=18 * mm,

            topMargin=18 * mm,

            bottomMargin=18 * mm
        )


        # --------------------------------------
        # STYLES
        # --------------------------------------

        styles = getSampleStyleSheet()


        title_style = ParagraphStyle(

            "ComicTitle",

            parent=styles["Title"],

            fontSize=24,

            leading=30,

            alignment=TA_CENTER,

            textColor=colors.HexColor(
                "#6c5ce7"
            ),

            spaceAfter=12
        )


        genre_style = ParagraphStyle(

            "Genre",

            parent=styles["Normal"],

            fontSize=11,

            alignment=TA_CENTER,

            textColor=colors.HexColor(
                "#8e44ad"
            ),

            spaceAfter=20
        )


        heading_style = ParagraphStyle(

            "Heading",

            parent=styles["Heading2"],

            fontSize=17,

            leading=22,

            textColor=colors.HexColor(
                "#6c5ce7"
            ),

            spaceBefore=15,

            spaceAfter=8
        )


        subheading_style = ParagraphStyle(

            "SubHeading",

            parent=styles["Heading3"],

            fontSize=13,

            leading=18,

            textColor=colors.HexColor(
                "#8e44ad"
            ),

            spaceBefore=10,

            spaceAfter=5
        )


        body_style = ParagraphStyle(

            "Body",

            parent=styles["BodyText"],

            fontSize=10.5,

            leading=16,

            spaceAfter=8
        )


        # --------------------------------------
        # STORY CONTENT
        # --------------------------------------

        story = []


        title = comic.get(
            "title",
            "Untitled Comic"
        )


        genre = comic.get(
            "genre",
            "Comic"
        )


        setting = comic.get(
            "setting",
            "No setting provided."
        )


        ending = comic.get(
            "ending",
            "No ending provided."
        )


        # --------------------------------------
        # TITLE
        # --------------------------------------

        story.append(
            Paragraph(
                "COMICCRAFT",
                title_style
            )
        )


        story.append(
            Paragraph(
                escape_pdf_text(title),
                title_style
            )
        )


        story.append(
            Paragraph(
                escape_pdf_text(
                    "Genre: " + str(genre)
                ),
                genre_style
            )
        )


        story.append(
            Spacer(
                1,
                10
            )
        )


        # --------------------------------------
        # CHARACTERS
        # --------------------------------------

        story.append(
            Paragraph(
                "Main Characters",
                heading_style
            )
        )


        characters = comic.get(
            "characters",
            []
        )


        for character in characters:

            name = character.get(
                "name",
                "Unknown"
            )

            personality = character.get(
                "personality",
                ""
            )

            role = character.get(
                "role",
                ""
            )


            story.append(
                Paragraph(
                    escape_pdf_text(
                        str(name)
                    ),
                    subheading_style
                )
            )


            story.append(
                Paragraph(
                    "<b>Personality:</b> "
                    + escape_pdf_text(
                        str(personality)
                    ),
                    body_style
                )
            )


            story.append(
                Paragraph(
                    "<b>Role:</b> "
                    + escape_pdf_text(
                        str(role)
                    ),
                    body_style
                )
            )


        # --------------------------------------
        # SETTING
        # --------------------------------------

        story.append(
            Paragraph(
                "Setting",
                heading_style
            )
        )


        story.append(
            Paragraph(
                escape_pdf_text(
                    str(setting)
                ),
                body_style
            )
        )


        # --------------------------------------
        # CHAPTERS
        # --------------------------------------

        chapters = [

            (
                "Chapter 1",
                comic.get(
                    "chapter1",
                    {}
                )
            ),

            (
                "Chapter 2",
                comic.get(
                    "chapter2",
                    {}
                )
            ),

            (
                "Chapter 3",
                comic.get(
                    "chapter3",
                    {}
                )
            )

        ]


        for chapter_name, chapter in chapters:

            story.append(
                PageBreak()
            )


            story.append(
                Paragraph(
                    escape_pdf_text(
                        chapter_name
                    ),
                    heading_style
                )
            )


            scene = chapter.get(
                "scene",
                ""
            )


            actions = chapter.get(
                "actions",
                ""
            )


            dialogue = chapter.get(
                "dialogue",
                ""
            )


            story.append(
                Paragraph(
                    "Scene",
                    subheading_style
                )
            )


            story.append(
                Paragraph(
                    escape_pdf_text(
                        str(scene)
                    ),
                    body_style
                )
            )


            story.append(
                Paragraph(
                    "Actions",
                    subheading_style
                )
            )


            story.append(
                Paragraph(
                    escape_pdf_text(
                        str(actions)
                    ),
                    body_style
                )
            )


            story.append(
                Paragraph(
                    "Dialogue",
                    subheading_style
                )
            )


            story.append(
                Paragraph(
                    escape_pdf_text(
                        str(dialogue)
                    ),
                    body_style
                )
            )


        # --------------------------------------
        # ENDING
        # --------------------------------------

        story.append(
            PageBreak()
        )


        story.append(
            Paragraph(
                "Ending",
                heading_style
            )
        )


        story.append(
            Paragraph(
                escape_pdf_text(
                    str(ending)
                ),
                body_style
            )
        )


        # --------------------------------------
        # FOOTER
        # --------------------------------------

        story.append(
            Spacer(
                1,
                30
            )
        )


        story.append(
            Paragraph(
                "Created with ComicCraft",
                genre_style
            )
        )


        # --------------------------------------
        # BUILD PDF
        # --------------------------------------

        document.build(
            story
        )


        buffer.seek(0)


        # --------------------------------------
        # FILE NAME
        # --------------------------------------

        safe_title = "".join(

            c if c.isalnum()
            else "_"

            for c in str(title)

        )


        filename = (
            safe_title
            or "ComicCraft_Story"
        ) + ".pdf"


        # --------------------------------------
        # RETURN PDF
        # --------------------------------------

        return StreamingResponse(

            buffer,

            media_type="application/pdf",

            headers={
                "Content-Disposition":
                f'attachment; filename="{filename}"'
            }
        )


    except Exception as e:

        print(
            "PDF ERROR:",
            repr(e)
        )


        return JSONResponse(

            status_code=500,

            content={

                "message":
                "Unable to create PDF.",

                "error":
                str(e)
            }
        )


# ==========================================
# ESCAPE PDF TEXT
# ==========================================

def escape_pdf_text(text):

    text = str(text)

    return (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )