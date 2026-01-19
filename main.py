import eel
import json
import os
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
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
    "vocabulary_sentences": [
        "Sentence 1 using all vocabulary words.",
        "Sentence 2 using all vocabulary words."
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
2. vocabulary_sentences: Generate 1-3 sentences that use ALL of the vocabulary words. Shorter sentences are better.
3. article_content: {title_instruction} Provide a summary and 3-5 main points.
4. discussion_questions: Generate at least 10 thought-provoking discussion questions related to the text. Include both article-specific questions and broader discussion questions. Reference the following examples for style and format:

Example 1 (South Korea article):
- What are your thoughts on South Korea's soft power?
- Why do you think South Korean pop culture has become so popular globally?
- Do you know anyone who's obsessed with all things South Korean?
- Are you a fan of K-pop, Korean dramas or Korean films?
- Have you used any K-beauty products? Were you happy with them?
- What aspects of your country's culture are popular overseas?
- What are some things foreigners often get wrong about your country?
- What are you most proud of your country for?
- What countries have you always been interested in?
- If you could live anywhere in the world for a year, where would you choose?

Example 2 (Climate/wealth inequality article):
- What are your thoughts on Oxfam's findings?
- Are you surprised that the super rich have such a massive carbon footprint?
- Why do you think the super rich invest in the most polluting industries?
- Would you support increasing taxes on highly polluting luxury goods?
- What do you think could be done to take power away from the super rich and wealthy corporations?
- How aggressive has your country been in the fight against climate change?
- Are the effects of climate change already being felt in your country?
- What do you think will be worst impacts of climate change on your country?
- How hopeful are you when it comes to climate change?
- Do you know anyone who isn't concerned about climate change?

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


def format_article_html(article_text: str) -> str:
    """Format article text into HTML paragraphs."""
    paragraphs = []
    current_paragraph = []

    for line in article_text.split("\n"):
        line = line.strip()
        if line:
            current_paragraph.append(line)
        else:
            if current_paragraph:
                paragraphs.append(" ".join(current_paragraph))
                current_paragraph = []

    if current_paragraph:
        paragraphs.append(" ".join(current_paragraph))

    return "\n".join(f"<p>{p}</p>" for p in paragraphs)


def generate_html(content: dict, original_article: str) -> str:
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

    # Build vocabulary sentences HTML
    vocab_sentences_html = ""
    for sentence in content.get("vocabulary_sentences", []):
        vocab_sentences_html += f"<p>{sentence}</p>\n"

    # Build discussion questions HTML
    questions_html = ""
    for i, question in enumerate(content.get("discussion_questions", []), 1):
        questions_html += f"<li>{question}</li>\n"

    # Format original article into HTML paragraphs
    article_html = format_article_html(original_article)

    # Replace placeholders in template
    html = template.replace("{{TITLE}}", article.get("title", "English Learning Content"))
    html = html.replace("{{SUMMARY}}", article.get("summary", ""))
    html = html.replace("{{MAIN_POINTS}}", main_points_html)
    html = html.replace("{{VOCABULARY}}", vocab_html)
    html = html.replace("{{VOCABULARY_SENTENCES}}", vocab_sentences_html)
    html = html.replace("{{ARTICLE}}", article_html)
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


def upload_to_s3(html_content: str) -> dict:
    """Upload HTML content to S3 as index.html for static hosting."""
    bucket_name = os.environ.get("AWS_S3_BUCKET_NAME")
    if not bucket_name:
        return {"error": "AWS_S3_BUCKET_NAME is not configured"}

    region = os.environ.get("AWS_REGION", "ap-northeast-1")
    prefix = os.environ.get("AWS_S3_PREFIX", "").strip("/")
    s3_key = f"{prefix}/index.html" if prefix else "index.html"

    try:
        s3_client = boto3.client("s3", region_name=region)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=html_content.encode("utf-8"),
            ContentType="text/html; charset=utf-8",
        )

        s3_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com/"
        if prefix:
            s3_url += f"{prefix}/"

        return {"success": True, "s3_url": s3_url, "s3_key": s3_key}

    except NoCredentialsError:
        return {"error": "AWS credentials not found"}
    except ClientError as e:
        return {"error": f"S3 error: {e.response['Error']['Message']}"}
    except Exception as e:
        return {"error": f"S3 upload failed: {str(e)}"}


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

        # Generate HTML (pass original article text for Article section)
        html_content = generate_html(parsed_content, content)

        # Save to file
        filename, filepath = save_html(html_content)

        result = {
            "success": True,
            "title": parsed_content.get("article_content", {}).get("title", ""),
            "url": url,
            "filename": filename,
            "filepath": filepath
        }

        # Upload to S3 if configured
        if os.environ.get("AWS_S3_BUCKET_NAME"):
            s3_result = upload_to_s3(html_content)
            if s3_result.get("success"):
                result["s3_url"] = s3_result["s3_url"]
            else:
                result["s3_warning"] = s3_result.get("error")

        return result

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
