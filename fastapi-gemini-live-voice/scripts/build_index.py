"""
Run this once (and again whenever leave_rules.txt changes) to build the
searchable vector index. This requires network access to Gemini's API
and your real GEMINI_API_KEY in .env -- it is NOT run automatically by
the server, so the running app never pays embedding cost per request
for the document itself (only for each user query at search time).

Usage:
    python scripts/build_index.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.vector_store import build_index


if __name__ == "__main__":
    asyncio.run(build_index())
