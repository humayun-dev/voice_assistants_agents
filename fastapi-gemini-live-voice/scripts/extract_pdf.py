"""
One-time utility script — run this manually whenever you have a new PDF
to add as reference material for the assistant.

Usage:
    python scripts/extract_pdf.py path/to/document.pdf app/config/output.txt

This does NOT run as part of the live server — it's a prep step you run
once per document, before updating prompts.py to load the resulting .txt
file. Keeping this separate from the request path avoids adding PDF
parsing overhead to every conversation.
"""

import sys
from pypdf import PdfReader


def extract_pdf_text(pdf_path: str, output_path: str) -> None:
    reader = PdfReader(pdf_path)

    all_text = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        all_text.append(text)

    combined = "\n".join(all_text)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(combined)

    print(f"Extracted {len(reader.pages)} pages -> {output_path}")
    print("NOTE: raw PDF extraction is often messy (broken lines, headers "
          "repeated on every page, stray page numbers). Review the output "
          "and clean it up by hand before using it as a reference document "
          "-- a tidy, well-structured .txt gives the model much better "
          "answers than a raw dump.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/extract_pdf.py <input.pdf> <output.txt>")
        sys.exit(1)

    extract_pdf_text(sys.argv[1], sys.argv[2])
