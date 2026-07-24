# 🩺 Medical Report AI Assistant

An AI-powered assistant that extracts information from medical reports,
summarizes findings, highlights abnormal values, and generates easy to
understand health insights.

## How it works
1. **Upload Medical Report** — JPG, PNG, or PDF
2. **Extract Report Text** — OCR (Tesseract) for images / scanned PDFs,
   native text extraction for digital PDFs
3. **Analyze Health Metrics** — parses common lab values (Hemoglobin,
   Cholesterol, Vitamin D, Blood Sugar, etc.) and flags them against
   reference ranges
4. **Generate AI Summary** — LangChain + OpenAI turn the results into a
   plain-language summary
5. **Download Report** — a formatted PDF with patient info, results table,
   and summary

## Tech stack
Python · Tesseract OCR · LangChain · OpenAI API · Streamlit · Pandas

## Setup

### 1. System dependencies (required for OCR)
Tesseract and Poppler must be installed on your machine — `pytesseract`
and `pdf2image` are just Python wrappers around them.

**macOS**
```bash
brew install tesseract poppler
```

**Ubuntu/Debian**
```bash
sudo apt-get install tesseract-ocr poppler-utils
```

**Windows**
- Install [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and
  add it to your PATH.
- Install [Poppler](https://github.com/oschwartz10612/poppler-windows/releases)
  and add its `bin` folder to your PATH.

### 2. Python environment
```bash
cd medical_report_ai_assistant
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Add your OpenAI API key
Copy `.env.example` to `.env` and paste in your real key:
```bash
cp .env.example .env    # Windows: copy .env.example .env
```
Then edit `.env` so it looks like:
```
OPENAI_API_KEY=sk-your-real-key-here
```
The app reads this automatically — no key entry in the UI, and `.env` is
never uploaded or shared anywhere.

### 4. Run the app
```bash
streamlit run app.py
```
Upload a report and click **Analyze Report**.

## Project structure
```
medical_report_ai_assistant/
├── app.py                    # Streamlit UI, orchestrates the 5-step pipeline
├── utils/
│   ├── extractor.py          # Step 2: OCR / PDF text extraction
│   ├── analyzer.py           # Step 3: lab value parsing + abnormality flags
│   ├── summarizer.py         # Step 4: LangChain + OpenAI summary generation
│   ├── report_builder.py     # Step 5: PDF report generation
│   └── reference_ranges.py   # Reference ranges for supported lab tests
├── .streamlit/config.toml    # Theme
├── .env.example              # Copy to .env and add your OpenAI key
├── requirements.txt
└── README.md
```

## Notes & limitations
- Lab value extraction uses pattern matching over the OCR'd text — very
  noisy scans or unusual report layouts may not parse perfectly. The raw
  extracted text is always shown in an expander so you can verify it.
- The `REFERENCE_RANGES` dictionary in `utils/reference_ranges.py` covers
  ~15 common tests. Add more entries there to support additional tests.
- This is a demo/educational tool, **not** a certified medical device. AI
  summaries and range checks are for informational purposes only.
