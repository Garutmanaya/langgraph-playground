from __future__ import annotations

import base64
import sys
from pathlib import Path
from typing import NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from PIL import Image, ImageDraw, ImageFont


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_IMAGE_PATH = BASE_DIR / "sample_dashboard.png"


class AgentState(TypedDict):
    input: str
    image_path: NotRequired[str]
    image_base64: NotRequired[str]
    image_mime_type: NotRequired[str]
    visual_observations: NotRequired[str]
    final_answer: NotRequired[str]


def create_sample_dashboard(path: Path = SAMPLE_IMAGE_PATH) -> Path:
    """Create a simple synthetic monitoring dashboard image."""
    img = Image.new("RGB", (1000, 620), "white")
    draw = ImageDraw.Draw(img)

    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
        label_font = ImageFont.truetype("DejaVuSans.ttf", 18)
        small_font = ImageFont.truetype("DejaVuSans.ttf", 14)
    except Exception:
        title_font = label_font = small_font = None

    draw.text((40, 30), "EPP SLA Monitoring Dashboard - Release R13", fill="black", font=title_font)

    # Panel outlines
    draw.rectangle((40, 90, 470, 300), outline="black", width=2)
    draw.rectangle((530, 90, 960, 300), outline="black", width=2)
    draw.rectangle((40, 350, 960, 570), outline="black", width=2)

    draw.text((60, 105), "CHECK-DOMAIN p95 response_time", fill="black", font=label_font)
    draw.text((550, 105), "Failure reasons", fill="black", font=label_font)
    draw.text((60, 365), "Volume and timeout trend", fill="black", font=label_font)

    # Line chart panel 1
    points = [(80, 250), (140, 235), (200, 230), (260, 210), (320, 160), (380, 135), (440, 130)]
    draw.line(points, fill="black", width=4)
    for x, y in points:
        draw.ellipse((x - 4, y - 4, x + 4, y + 4), fill="black")
    draw.line((80, 260, 440, 260), fill="gray", width=1)
    draw.text((75, 265), "Before R13", fill="gray", font=small_font)
    draw.text((335, 265), "After R13", fill="gray", font=small_font)
    draw.text((350, 145), "p95 ~240 ms", fill="black", font=small_font)

    # Bar chart panel 2
    bars = [
        ("CONNECTION_TIMEOUT", 150),
        ("AUTH_FAILED", 70),
        ("INVALID_TLD", 45),
        ("QUOTA_EXCEEDED", 35),
    ]
    y = 150
    for label, width in bars:
        draw.text((550, y), label, fill="black", font=small_font)
        draw.rectangle((730, y, 730 + width, y + 22), fill="lightgray", outline="black")
        draw.text((740 + width, y + 2), str(width), fill="black", font=small_font)
        y += 35

    # Trend chart panel 3
    volume_points = [(80, 520), (200, 500), (320, 470), (440, 430), (560, 390), (680, 385), (900, 380)]
    timeout_points = [(80, 540), (200, 535), (320, 525), (440, 480), (560, 430), (680, 410), (900, 405)]
    draw.line(volume_points, fill="black", width=3)
    draw.line(timeout_points, fill="gray", width=3)
    draw.text((80, 530), "Volume", fill="black", font=small_font)
    draw.text((80, 550), "Timeouts", fill="gray", font=small_font)
    draw.text((740, 400), "Timeouts elevated after release", fill="black", font=small_font)

    img.save(path)
    return path


def encode_image(path: str | Path) -> tuple[str, str]:
    image_path = Path(path)
    suffix = image_path.suffix.lower()
    mime_type = "image/png" if suffix == ".png" else "image/jpeg"

    encoded = base64.b64encode(image_path.read_bytes()).decode("utf-8")
    return encoded, mime_type


def prepare_image_node(state: AgentState) -> AgentState:
    image_path = Path(state.get("image_path") or create_sample_dashboard())

    if not image_path.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    encoded, mime_type = encode_image(image_path)

    return {
        "image_path": str(image_path),
        "image_base64": encoded,
        "image_mime_type": mime_type,
    }


def vision_analysis_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    data_url = f"data:{state['image_mime_type']};base64,{state['image_base64']}"

    message = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        "Analyze this monitoring dashboard image. "
                        "Extract visible signals, anomalies, metrics, and likely operational meaning. "
                        f"User question: {state['input']}"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": data_url},
                },
            ],
        }
    ]

    response = llm.invoke(message)
    return {"visual_observations": response.content}


def final_answer_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
User question:
{state["input"]}

Visual observations:
{state["visual_observations"]}

Write a concise final answer with:
1. what the image shows
2. likely incident interpretation
3. recommended next action
"""

    response = llm.invoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("prepare_image", prepare_image_node)
    graph_builder.add_node("vision_analysis", vision_analysis_node)
    graph_builder.add_node("final_answer", final_answer_node)

    graph_builder.add_edge(START, "prepare_image")
    graph_builder.add_edge("prepare_image", "vision_analysis")
    graph_builder.add_edge("vision_analysis", "final_answer")
    graph_builder.add_edge("final_answer", END)

    return graph_builder.compile()


def run(question: str, image_path: str | None = None) -> AgentState:
    graph = build_graph()
    state: AgentState = {"input": question}
    if image_path:
        state["image_path"] = image_path
    return graph.invoke(state)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What does this monitoring dashboard show?"
    result = run(question)
    print("Image:", result["image_path"])
    print()
    print(result["final_answer"])
