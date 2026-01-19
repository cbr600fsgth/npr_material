# NPR Material - English Learning Content Generator

English learning content generator powered by Google Gemini AI.

Paste English articles and generate structured learning materials including vocabulary, summaries, and discussion questions.

## Features

- Vocabulary extraction with pronunciation and definitions
- Article summary and key points
- Discussion questions for conversation practice
- HTML output with Oxford Learner's Dictionary links
- Optional S3 upload for web hosting

## Requirements

- Python 3.12+
- Google Cloud project with Vertex AI enabled
- AWS credentials (optional, for S3 hosting)

## Setup

1. Install dependencies:

```bash
uv sync
```

2. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your Google Cloud project ID
```

3. Authenticate with Google Cloud:

```bash
gcloud auth application-default login
```

## Usage

```bash
uv run python main.py
```

Open http://localhost:8000/index.html in your browser.

1. Enter a title (optional)
2. Paste the English article content
3. Click "Generate" to create learning materials
4. Output HTML is saved to the `output/` directory

## Dependencies

- eel: Desktop web app framework
- google-genai: Google Gemini API client
- boto3: AWS SDK (for S3 upload)
- python-dotenv: Environment variable management
