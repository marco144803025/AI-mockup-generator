import httpx
from sqlmodel import Session, select
from models import Template
from db import engine, init_db

API_URL = "http://localhost:8000/api/templates"

sample_templates = [
    {
        "name": "Modern Dashboard",
        "figma_url": "https://figma.com/file/modern-dashboard",
        "html_export": "<html><!-- dashboard html --></html>",
        "globals_css": "/* global dashboard css */",
        "style_css": "/* dashboard style css */",
        "tags": ["dashboard", "modern", "light", "analytics"],
        "metadata": {"category": "dashboard", "style": "modern"},
        "thumbnail_url": None
    },
    {
        "name": "E-commerce Storefront",
        "figma_url": "https://figma.com/file/ecommerce-storefront",
        "html_export": "<html><!-- ecommerce html --></html>",
        "globals_css": "/* global ecommerce css */",
        "style_css": "/* ecommerce style css */",
        "tags": ["ecommerce", "store", "minimal", "light"],
        "metadata": {"category": "ecommerce", "style": "minimal"},
        "thumbnail_url": None
    },
    {
        "name": "Dark Portfolio",
        "figma_url": "https://figma.com/file/dark-portfolio",
        "html_export": "<html><!-- portfolio html --></html>",
        "globals_css": "/* global portfolio css */",
        "style_css": "/* portfolio style css */",
        "tags": ["portfolio", "dark", "personal", "creative"],
        "metadata": {"category": "portfolio", "style": "dark"},
        "thumbnail_url": None
    }
]

def post_samples():
    with httpx.Client() as client:
        for tpl in sample_templates:
            resp = client.post(API_URL, json=tpl)
            print(f"POST {tpl['name']}: {resp.status_code} {resp.json()}")

def list_templates():
    with httpx.Client() as client:
        resp = client.get(API_URL)
        print("\nAll templates:")
        for tpl in resp.json():
            print(tpl)

def update_first_template_tag():
    # Direct DB manipulation example
    with Session(engine) as session:
        template = session.exec(select(Template)).first()
        if template:
            template.tags = template.tags or []
            template.tags.append("featured")
            session.add(template)
            session.commit()
            print(f"Updated template {template.id} with new tag 'featured'")
        else:
            print("No templates found to update.")

def main():
    init_db()
    post_samples()
    list_templates()
    update_first_template_tag()
    list_templates()

if __name__ == "__main__":
    main() 