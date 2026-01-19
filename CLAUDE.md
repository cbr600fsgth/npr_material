# Strict Constraints

## No Emojis

Never use emojis in any output, code comments, or generated content.

## Git Commit

Create a clear, descriptive commit message in Japanese.

## uv

- Use uv for Python project and package management
- Use modern commands: `uv add`, `uv remove`, `uv sync`
- Do not use `pip` or `uv pip` commands

## Project Structure

```
npr_material/
├── main.py              # Main application (Eel + Gemini API)
├── templates/           # HTML templates for generated content
│   └── learning_template.html
├── web/                 # Eel frontend
│   ├── index.html
│   ├── script.js
│   └── style.css
├── output/              # Generated HTML files
├── pyproject.toml       # Project configuration
└── .env                 # Environment variables (not in git)
```

## Running the Application

```bash
uv run python main.py
```

Then open http://localhost:8000/index.html

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `GOOGLE_CLOUD_PROJECT`: Google Cloud project ID for Vertex AI
- `AWS_S3_BUCKET_NAME`: S3 bucket for hosting (optional)
- `AWS_REGION`: AWS region (default: ap-northeast-1)
- `AWS_S3_PREFIX`: S3 key prefix (optional)
