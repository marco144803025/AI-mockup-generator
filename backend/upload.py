import os
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "ui_templates")

client = MongoClient(MONGODB_URI)
db = client[MONGO_DB_NAME]

# --- Read files for the first template ---
template_dir = os.path.join("..", "UIpages", "landing_UI_template_2")
with open(os.path.join(template_dir, "index.html"), encoding="utf-8") as f:
    html_export = f.read()
with open(os.path.join(template_dir, "globals.css"), encoding="utf-8") as f:
    globals_css = f.read()
with open(os.path.join(template_dir, "style.css"), encoding="utf-8") as f:
    style_css = f.read()

# --- TEMPLATE: Add your UI templates here ---
# category: profile, login, signup, settings, dashboard, FAQ, about us, search result
# style: modern, dark, light, professional, minimal, elgent, luxurious, classic, futuristic
# layout:grid,asymmetric,symmetric,boxed,full width, sidebar, topbar, footer
# UX: user-friendly, engaging, informative, conversion-based
#industry: business/corporate, technology/saas, creative/agency, Education,Healthcare etc
templates = [
        {
        "name": "About Me UI Template 1",
        "html_export": html_export,
        "globals_css": globals_css,
        "style_css": style_css,
        "thumbnail_url": None,  # Add if available
        "metadata": {"category": "About me",
        "figma_url":"https://www.figma.com/design/EOSjmqgxyiGGQ13O4ER167/10-Framer-websites-%E2%80%94-Landing-Page-UI-%E2%80%94-Web-to-Figma--Community-?node-id=2-9955&t=jjTc9OP86s629vVy-0",
        "description": "A vibrant and structured personal portfolio page designed for creative professionals, showcasing capabilities, work history, contact information, and a photo gallery within distinct, colorful content blocks.",},
        "tags": ["portfolio", "about me", "personal", "creative", "designer", "modern", "playful", "colorful", "asymmetrical", "card-based", "image-heavy", "work history", "skills showcase", "gallery", "half-width", "engaging", "unique layout", "illustration-heavy"],
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    },
    # Add more templates as needed
]

if __name__ == "__main__":
    result = db.templates.insert_many(templates)
    print(f"Inserted {len(result.inserted_ids)} templates.")
    for _id in result.inserted_ids:
        print(f"Inserted template with _id: {_id}") 