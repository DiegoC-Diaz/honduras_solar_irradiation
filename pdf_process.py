import os
from pathlib import Path
from pypdf import PdfReader, PdfWriter

FILES = [
    "data/ICAEH/ICEH-2022.pdf",
    "data/ICAEH/ICAEH-2023.pdf",
    "data/ICAEH/ICAEH-2024.pdf",
]

PAGE_START = 63
PAGE_END = 70

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def extract_pages(input_pdf: str):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    # Convert to zero-based indexing
    for page_num in range(PAGE_START - 1, PAGE_END):
        writer.add_page(reader.pages[page_num])

    output_name = OUTPUT_DIR / f"{Path(input_pdf).stem}-extract.pdf"

    with open(output_name, "wb") as f:
        writer.write(f)

    print(f"✓ Saved {output_name}")

    return output_name


def main():
    extracted_files = []

    for pdf in FILES:
        extracted = extract_pages(pdf)
        extracted_files.append(extracted)

    print("\nFinished!")
    print("Extracted PDFs:")
    for pdf in extracted_files:
        print(f" - {pdf}")


if __name__ == "__main__":
    main()