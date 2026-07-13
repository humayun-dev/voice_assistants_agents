"""
Supabase integration. Anything that touches the database goes through here —
agent nodes never talk to Supabase directly, they call get_catalog_text().

Uses the secret key, which bypasses Row Level Security. That's safe here
because this code only ever runs inside our own trusted FastAPI backend,
never in a browser.
"""
from supabase import create_client, Client
from app.config import settings

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SECRET_KEY)


def get_catalog() -> list[dict]:
    try:
        response = supabase.table("products").select("*").execute()
        return response.data
    except Exception as e:
        print(f"[Supabase] Failed to fetch catalog: {e}")
        return []


def get_catalog_text() -> str:
    catalog = get_catalog()
    if not catalog:
        return "No products are currently available."
    return "\n".join(
        f"- {item['name']}: Rs {item['price']} ({item['stock']} in stock)"
        + (f" — {item['description']}" if item.get("description") else "")
        for item in catalog
    )
