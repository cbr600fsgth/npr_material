import eel
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
import vertexai
from vertexai.generative_models import GenerativeModel

# Load environment variables from .env file
load_dotenv()


# Initialize paths
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATE_DIR = BASE_DIR / "templates"

# Ensure output directory exists
OUTPUT_DIR.mkdir(exist_ok=True)


def init_vertex_ai():
    """Initialize Vertex AI with project settings."""
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")
    vertexai.init(project=project_id, location="us-central1")


def create_prompt(title: str, content: str) -> str:
    """Create the prompt for Gemini to analyze the English text."""
    if title:
        title_instruction = f'Use this exact title: "{title}"'
    else:
        title_instruction = "Generate an appropriate title based on the article content."

    return f"""Analyze the following English text and generate learning content in JSON format.

The JSON should have this exact structure:
{{
    "vocabulary": [
        {{
            "word": "example",
            "part_of_speech": "noun",
            "definition": "a thing characteristic of its kind",
            "example_sentence": "This is an example of good writing."
        }}
    ],
    "article_content": {{
        "title": "Article Title",
        "summary": "A brief summary of the article content.",
        "main_points": ["point 1", "point 2", "point 3"]
    }},
    "discussion_questions": [
        "Question 1?",
        "Question 2?",
        "Question 3?"
    ]
}}

Requirements:
1. vocabulary: Select 6-10 important words for English learners. Consider words from NAWL (New Academic Word List), TSL (TOEIC Service List), and BSL (Business Service List). Include definition and example sentence for each.
2. article_content: {title_instruction} Provide a summary and 3-5 main points.
3. discussion_questions: Generate at least 10 thought-provoking discussion questions related to the text.

Return ONLY valid JSON, no additional text or explanation.

English Text:
{content}
"""


def parse_json_response(response_text: str) -> dict:
    """Parse JSON from Gemini response, handling markdown code blocks."""
    text = response_text.strip()

    # Remove markdown code blocks if present
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    return json.loads(text.strip())


def generate_html(content: dict) -> str:
    """Generate HTML content from the parsed JSON using template."""
    template_path = TEMPLATE_DIR / "learning_template.html"

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # Build vocabulary HTML
    vocab_html = ""
    for item in content.get("vocabulary", []):
        vocab_html += f"""
        <div class="vocab-item">
            <div class="word">{item.get('word', '')}</div>
            <div class="pos">{item.get('part_of_speech', '')}</div>
            <div class="definition">{item.get('definition', '')}</div>
            <div class="example">{item.get('example_sentence', '')}</div>
        </div>
        """

    # Build article content HTML
    article = content.get("article_content", {})
    main_points_html = ""
    for point in article.get("main_points", []):
        main_points_html += f"<li>{point}</li>\n"

    # Build discussion questions HTML
    questions_html = ""
    for i, question in enumerate(content.get("discussion_questions", []), 1):
        questions_html += f"<li>{question}</li>\n"

    # Replace placeholders in template
    html = template.replace("{{TITLE}}", article.get("title", "English Learning Content"))
    html = html.replace("{{SUMMARY}}", article.get("summary", ""))
    html = html.replace("{{MAIN_POINTS}}", main_points_html)
    html = html.replace("{{VOCABULARY}}", vocab_html)
    html = html.replace("{{DISCUSSION_QUESTIONS}}", questions_html)

    return html


def save_html(html_content: str) -> tuple[str, str]:
    """Save HTML content to a file with timestamp-based name."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"learning_content_{timestamp}.html"
    filepath = OUTPUT_DIR / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    return filename, str(filepath)


# Initialize Eel
eel.init(str(BASE_DIR / "web"))


@eel.expose
def generate_content(title: str, url: str, content: str) -> dict:
    """Generate learning content from English text."""
    try:
        # Initialize Vertex AI
        init_vertex_ai()

        # Create model and generate content
        model = GenerativeModel("gemini-2.5-flash")
        prompt = create_prompt(title, content)

        response = model.generate_content(prompt)
        response_text = response.text

        # Parse JSON response
        parsed_content = parse_json_response(response_text)

        # Generate HTML
        html_content = generate_html(parsed_content)

        # Save to file
        filename, filepath = save_html(html_content)

        return {
            "success": True,
            "title": parsed_content.get("article_content", {}).get("title", ""),
            "url": url,
            "filename": filename,
            "filepath": filepath
        }

    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse API response as JSON: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Start the Eel application."""
    print("Starting English Learning Content Generator...")
    print("Open the following URL in your browser:")
    print("  http://localhost:8000/index.html")
    eel.start("index.html", size=(900, 800), mode=None, host="localhost", port=8000)


if __name__ == "__main__":
    main()
