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
# change the path to your template directory
template_dir = os.path.join("..", "UIpages", "signup_UI_template_2")
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
    "name": "Sign-up UI Template 2",
    "html_export": html_export,
    "globals_css": globals_css,
    "style_css": style_css,
    "thumbnail_url": None,  # Add if available
    "metadata": {
        "category": "sign-up",
        "figma_url": "https://www.figma.com/design/GNPI5u6NpR4UXlBas7o7Iy/Login-pages-v1----Carey--Community-?node-id=0-1&p=f&t=QlLYGB52k0uNcdWq-0", # Placeholder, replace with actual Figma URL
        "description": "A sleek, dark-themed user registration page, offering detailed signup fields and social authentication options, designed to complement a modern web application's aesthetic. Same design with sign_UI_template_2",
    },
    "tags": ["sign-up form", "dark theme", "user registration", "futuristic aesthetic", "abstract gradients", "purple accents", "social signup", "account creation", "minimalist form", "onboarding flow", "sleek design", "web application signup", "expressive headline"]
}
    # Add more templates as needed
]

if __name__ == "__main__":
    result = db.templates.insert_many(templates)
    print(f"Inserted {len(result.inserted_ids)} templates.")
    for _id in result.inserted_ids:
        print(f"Inserted template with _id: {_id}") 