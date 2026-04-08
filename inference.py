# -*- coding: utf-8 -*-
import os
import json
import urllib.request
from typing import List, Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",  "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL   = os.getenv("SERVER_URL",  "http://localhost:7860")

