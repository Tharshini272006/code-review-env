"""
dashboard.py
Gradio UI Dashboard for CodeReviewEnv — Self Improvement Layer
Shows live reward curve climbing as the agent trains.

Wires together:
  bug_generator.py        → generates dynamic LLM challenges
  difficulty_escalator.py → escalates difficulty based on rewards
  inference.py            → LLM agent that fixes bugs
  client.py               → talks to the FastAPI env server

Run:
  python dashboard.py
Then open http://localhost:7861
"""

import os
import time
import threading
import json
import urllib.request
from typing import List, Optional

import gradio as gr
import plotly.graph_objects as go
from openai import OpenAI

# ── Import our modules ────────────────────────────────────────────────────────
from bug_generator import generate_bug_challenge
from difficulty_escalator import DifficultyEscalator

# ── LLM + Server config (mirrors inference.py) ───────────────────────────────
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL   = os.getenv("SERVER_URL", "http://localhost:7860")

client_llm = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

SYSTEM_PROMPT = """You are an expert Python engineer. You will be given a buggy Python function.
Return ONLY the complete corrected function. No explanation, no markdown, no extra text."""

# ── Shared Training State ─────────────────────────────────────────────────────
class TrainingState:
    def __init__(self):
        self.lock                       = threading.Lock()
        self.running                    = False
        self.stopped                    = False
        self.episode                    = 0
        self.reward_history: List[dict] = []   # [{episode, reward, difficulty}]
        self.current_difficulty         = "easy"
        self.current_challenge: dict    = {}
        self.last_decision: dict        = {}
        self.log_lines: List[str]       = []
        self.win_streak                 = 0
        self.avg_easy                   = 0.0
        self.avg_medium                 = 0.0
        self.avg_hard                   = 0.0

    def log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        line = f"[{timestamp}] {msg}"
        with self.lock:
            self.log_lines.append(line)
            if len(self.log_lines) > 300:
                self.log_lines = self.log_lines[-300:]
        print(line, flush=True)

    def get_log(self) -> str:
        with self.lock:
            return "\n".join(self.log_lines[-60:])


STATE = TrainingState()

# ── HTTP helpers (standalone, mirrors client.py) ──────────────────────────────
def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        f"{SERVER_URL}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _get(path: str) -> dict:
    req = urllib.request.Request(f"{SERVER_URL}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def server_healthy() -> bool:
    try:
        _get("/health")
        return True
    except Exception:
        return False

# ── LLM Agent (mirrors inference.py / call_llm) ───────────────────────────────
def call_llm(buggy_code: str, task_description: str,
             feedback: str = "", hint: Optional[str] = None) -> str:
    user_msg = f"""Task: {task_description}

Buggy code:
{buggy_code}

Previous feedback: {feedback or 'None'}
Hint: {hint or 'None'}

Return ONLY the corrected Python function."""
    try:
        response = client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=512,
            temperature=0.2,
        )
        code = response.choices[0].message.content.strip()
        if code.startswith("`"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1]) if lines[-1].strip().startswith("`") else "\n".join(lines[1:])
        return code
    except Exception as e:
        STATE.log(f"⚠️  LLM error: {e}")
        return buggy_code

# ── One episode against the env server ───────────────────────────────────────
def run_episode(task_id: str, challenge: dict) -> float:
    """Run one episode on the FastAPI env. Returns final reward."""
    buggy_code       = challenge["buggy_code"]
    task_description = challenge.get("description", "Fix the bug in this Python function.")
    hint             = challenge.get("hint")
    feedback         = ""
    rewards: List[float] = []

    try:
        obs_data = _post("/reset", {"task_id": task_id})
        done     = obs_data.get("done", False)
        feedback = obs_data.get("feedback", "")

        while not done:
            fixed_code = call_llm(buggy_code, task_description, feedback, hint)
            try:
                step_data = _post("/step", {"code": fixed_code, "explanation": "LLM fix"})
                reward    = step_data["reward"]
                done      = step_data["done"]
                obs       = step_data["observation"]
                feedback  = obs.get("feedback", "")
                hint      = obs.get("hint", hint)
                rewards.append(reward)
            except Exception as e:
                STATE.log(f"⚠️  Step error: {e}")
                rewards.append(0.0)
                break

        return rewards[-1] if rewards else 0.0

    except Exception as e:
        STATE.log(f"⚠️  Episode error: {e}")
        return 0.0

# ── Simulated reward (when server is offline) ─────────────────────────────────
def simulate_reward(episode: int, difficulty: str) -> float:
    import random
    base_by_diff = {"easy": 0.5, "medium": 0.35, "hard": 0.2}
    base = min(base_by_diff.get(difficulty, 0.4) + episode * 0.035, 0.98)
    return max(0.0, min(1.0, base + random.uniform(-0.12, 0.12)))

# ── Background training loop ──────────────────────────────────────────────────
def training_loop(num_episodes: int, use_server: bool):
    STATE.log("🚀 Training started!")
    escalator  = DifficultyEscalator()
    server_ok  = use_server and server_healthy()

    if use_server and not server_ok:
        STATE.log("⚠️  Env server unreachable — switching to simulated rewards.")

    for ep in range(1, num_episodes + 1):
        if STATE.stopped:
            STATE.log("🛑 Training stopped by user.")
            break

        with STATE.lock:
            STATE.episode = ep

        difficulty = escalator.state.current_difficulty

        STATE.log(f"━━━ Episode {ep}/{num_episodes} | {difficulty.upper()} ━━━")

        # 1. Generate challenge via bug_generator
        challenge = escalator.get_next_challenge()
        fn_name   = challenge.get("function_name", "unknown")
        bug_type  = challenge.get("bug_type", "?")
        STATE.log(f"🐛 {fn_name}()  bug_type={bug_type}")

        with STATE.lock:
            STATE.current_challenge  = challenge
            STATE.current_difficulty = difficulty

        # 2. Get reward
        if server_ok:
            reward = run_episode(difficulty, challenge)
        else:
            reward = simulate_reward(ep, difficulty)
            STATE.log(f"🎲 Simulated reward: {reward:.3f}")

        # 3. Feed to escalator → get decision
        decision = escalator.record_reward(reward)
        summary  = escalator.state.summary()

        with STATE.lock:
            STATE.reward_history     = list(summary["reward_history"])
            STATE.last_decision      = dict(decision)
            STATE.win_streak         = summary["win_streak"]
            STATE.avg_easy           = summary["avg_easy"]
            STATE.avg_medium         = summary["avg_medium"]
            STATE.avg_hard           = summary["avg_hard"]
            STATE.current_difficulty = summary["current_difficulty"]

        emoji = "✅" if reward >= 0.85 else ("💡" if reward < 0.3 else "📊")
        STATE.log(f"{emoji} Reward: {reward:.3f}  →  {decision['message']}")
        STATE.log(
            f"📈 Avg  Easy={summary['avg_easy']:.3f}  "
            f"Med={summary['avg_medium']:.3f}  "
            f"Hard={summary['avg_hard']:.3f}"
        )

        # Auto-save every 5 episodes
        if ep % 5 == 0:
            escalator.save_progress("progress.json")
            STATE.log(f"💾 Checkpoint saved (ep {ep})")

        time.sleep(0.4)   # breathe so UI can poll

    escalator.save_progress("progress.json")
    STATE.log("🏁 Training complete!  progress.json saved.")
    with STATE.lock:
        STATE.running = False

# ── Plotly chart builder ──────────────────────────────────────────────────────
DIFF_COLOR = {"easy": "#4ade80", "medium": "#facc15", "hard": "#f87171"}

DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(17,17,27,1)",
    font=dict(color="#cdd6f4", size=13),
    xaxis=dict(title="Episode", gridcolor="#313244", color="#cdd6f4"),
    yaxis=dict(title="Reward", range=[0, 1.05], gridcolor="#313244", color="#cdd6f4"),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#45475a"),
    margin=dict(l=50, r=20, t=50, b=50),
)

def build_chart() -> go.Figure:
    with STATE.lock:
        history = list(STATE.reward_history)

    fig = go.Figure()

    if not history:
        fig.update_layout(title="Reward Curve — waiting for training…", **DARK)
        return fig

    # Scatter per difficulty
    for diff in ["easy", "medium", "hard"]:
        xs = [e["episode"] for e in history if e["difficulty"] == diff]
        ys = [e["reward"]  for e in history if e["difficulty"] == diff]
        if xs:
            fig.add_trace(go.Scatter(
                x=xs, y=ys, mode="markers",
                name=diff.capitalize(),
                marker=dict(color=DIFF_COLOR[diff], size=11, symbol="circle",
                            line=dict(color="#1e1e2e", width=1)),
            ))

    # Smooth trend line
    rewards  = [e["reward"]  for e in history]
    episodes = [e["episode"] for e in history]
    if len(rewards) >= 3:
        w        = max(3, len(rewards) // 6)
        smoothed = [
            sum(rewards[max(0, i-w+1):i+1]) / (i - max(0, i-w+1) + 1)
            for i in range(len(rewards))
        ]
        fig.add_trace(go.Scatter(
            x=episodes, y=smoothed, mode="lines",
            name="Trend",
            line=dict(color="#89b4fa", width=2.5, dash="dot"),
        ))

    # Difficulty change markers
    prev_diff = None
    for e in history:
        if e["difficulty"] != prev_diff and prev_diff is not None:
            fig.add_vline(
                x=e["episode"], line_dash="dash",
                line_color=DIFF_COLOR.get(e["difficulty"], "#cdd6f4"),
                opacity=0.5,
                annotation_text=f"→{e['difficulty']}",
                annotation_font_color=DIFF_COLOR.get(e["difficulty"], "#cdd6f4"),
            )
        prev_diff = e["difficulty"]

    fig.update_layout(title="📈 Live Reward Curve", **DARK)
    return fig

# ── UI callbacks ──────────────────────────────────────────────────────────────
def on_start(num_episodes, use_server):
    if STATE.running:
        return "⚠️ Already running!"
    with STATE.lock:
        STATE.running = True
        STATE.stopped = False
        STATE.episode = 0
        STATE.reward_history.clear()
        STATE.log_lines.clear()
        STATE.current_challenge = {}
        STATE.last_decision = {}
    threading.Thread(
        target=training_loop,
        args=(int(num_episodes), bool(use_server)),
        daemon=True
    ).start()
    return "✅ Training started!"

def on_stop():
    with STATE.lock:
        STATE.stopped = True
        STATE.running = False
    return "🛑 Stop signal sent."

def refresh():
    with STATE.lock:
        ep         = STATE.episode
        running    = STATE.running
        difficulty = STATE.current_difficulty
        win_streak = STATE.win_streak
        avg_e      = STATE.avg_easy
        avg_m      = STATE.avg_medium
        avg_h      = STATE.avg_hard
        challenge  = dict(STATE.current_challenge)
        decision   = dict(STATE.last_decision)

    # Status card
    status = "🟢 Running" if running else ("✅ Done" if ep > 0 else "⏸ Idle")
    diff_label = {"easy": "🟢 Easy", "medium": "🟡 Medium", "hard": "🔴 Hard"}.get(difficulty, difficulty)
    streak_fire = "🔥" * min(win_streak, 5)

    stats_md = f"""### {status}
| | |
|---|---|
| Episode | **{ep}** |
| Difficulty | **{diff_label}** |
| Win Streak | **{win_streak}** {streak_fire} |
| Avg (Easy) | **{avg_e:.3f}** |
| Avg (Medium) | **{avg_m:.3f}** |
| Avg (Hard) | **{avg_h:.3f}** |
"""

    # Current challenge card
    fn_name  = challenge.get("function_name", "—")
    bug_type = challenge.get("bug_type", "—")
    hint     = challenge.get("hint", "—")
    buggy    = challenge.get("buggy_code", "# waiting…")
    dec_msg  = decision.get("message", "—")

    challenge_md = f"""**Function:** `{fn_name}`  
**Bug Type:** `{bug_type}`  
**Hint:** _{hint}_  
**Decision:** {dec_msg}

```python
{buggy}
```"""

    return stats_md, challenge_md, build_chart(), STATE.get_log()

# ── Gradio layout ─────────────────────────────────────────────────────────────
css = """
body { background: #1e1e2e !important; }
.gradio-container { max-width: 1350px !important; margin: auto; }
#title { text-align: center; padding: 0.5rem 0 1rem; }
.log-box textarea {
    font-family: 'Fira Code', monospace !important;
    font-size: 12px !important;
    background: #11111b !important;
    color: #a6e3a1 !important;
}
"""

with gr.Blocks(
    title="🐛 CodeReviewEnv Dashboard",
    theme=gr.themes.Base(primary_hue="blue", neutral_hue="slate"),
    css=css,
) as demo:

    gr.Markdown(
        "# 🐛 CodeReviewEnv — Self-Play Training Dashboard\n"
        "Live reward curve as the agent fixes bugs and auto-escalates difficulty · "
        "Meta × PyTorch × HuggingFace OpenEnv Hackathon 🚀",
        elem_id="title",
    )

    # ── Controls ──────────────────────────────────────────────────────────────
    with gr.Row():
        num_eps    = gr.Slider(5, 100, value=20, step=5, label="Episodes")
        use_server = gr.Checkbox(value=True,  label="Use Env Server (uncheck = simulate)")
        btn_start  = gr.Button("▶ Start Training", variant="primary")
        btn_stop   = gr.Button("⏹ Stop",           variant="stop")
        btn_manual = gr.Button("🔄 Refresh Now",    variant="secondary")

    status_box = gr.Textbox(label="", interactive=False, max_lines=1)

    btn_start.click(on_start, inputs=[num_eps, use_server], outputs=status_box)
    btn_stop.click(on_stop, outputs=status_box)

    # ── Stats + Chart ─────────────────────────────────────────────────────────
    with gr.Row():
        with gr.Column(scale=1, min_width=280):
            stats_md     = gr.Markdown("### ⏸ Idle\nPress **▶ Start Training** to begin.")
            challenge_md = gr.Markdown("_No challenge yet._")
        with gr.Column(scale=3):
            chart = gr.Plot(label="Reward Curve")

    # ── Log ───────────────────────────────────────────────────────────────────
    log_box = gr.Textbox(
        label="📋 Training Log",
        lines=18,
        interactive=False,
        elem_classes=["log-box"],
    )

    # ── Wire refresh ──────────────────────────────────────────────────────────
    outputs = [stats_md, challenge_md, chart, log_box]
    btn_manual.click(refresh, outputs=outputs)

    # Auto-refresh every 3 s
    gr.Timer(3).tick(refresh, outputs=outputs)


if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        show_error=True,
    )