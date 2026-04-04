---
title: Code Review Env
emoji: 🐛
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# CodeReviewEnv 🐛→✅

RL environment where an AI agent identifies and fixes Python bugs.

Built for the Meta x PyTorch x HuggingFace OpenEnv Hackathon (Scaler).

## Tasks

| ID | Name | Difficulty | Max Attempts |
|----|------|-----------|-------------|
| easy | syntax_fix | ⭐ Easy | 1 |
| medium | logic_fix | ⭐⭐ Medium | 3 |
| hard | refactor_and_fix | ⭐⭐⭐ Hard | 5 |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /health | Health check |
| GET | /tasks | List all 3 tasks |
| POST | /reset | Start new episode |
| POST | /step | Submit fix |
| GET | /state | Current episode state |
| POST | /grader | Grade code |
| GET | /docs | Swagger UI |

## Inference Output Format
```
[START] task=easy env=code_review_env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=def average... reward=1.00 done=true error=null
[END] success=true steps=1 score=1.000 rewards=1.00
```