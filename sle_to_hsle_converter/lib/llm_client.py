"""
llm_client.py — GitHub Copilot Chat API client for HSLE converter LLM fallback.

Token flow: gh auth token → OAuth token → Copilot internal token (cached).
Reused from the diff agent pattern; isolated here so each agent stays self-contained.
"""

import json
import os
import time
import uuid
import subprocess
import urllib.request
import urllib.error
from typing import Optional

_token_cache: dict = {}

_SYSTEM_PROMPT = """\
You are a senior emulation engineer performing an SLE-to-HSLE model conversion.
You will receive:
  1. A unified diff showing how a reference SLE file was changed to its HSLE version.
  2. The current content of a new SLE file that needs analogous changes applied.
  3. A short description of what the change represents.

Rules:
- Apply the SAME KIND of change to the new SLE file as shown in the diff.
- Do NOT blindly copy the reference HSLE content — the new SLE file may differ.
- Preserve all content that is NOT related to the diff's change.
- Return ONLY the final file content. No markdown fences, no explanations, no prose.
- If you are not confident, return the original new SLE content unchanged."""


def get_copilot_token() -> str:
    """Return a valid short-lived Copilot API token, refreshing when needed."""
    now = time.time()
    if _token_cache.get('expires_at', 0) - 60 > now:
        return _token_cache['token']

    result = subprocess.run(['gh', 'auth', 'token'], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"gh auth token failed: {result.stderr.strip()}")
    oauth_token = result.stdout.strip()
    if not oauth_token:
        raise RuntimeError("gh auth token returned empty — run: gh auth login")

    req = urllib.request.Request(
        'https://api.github.com/copilot_internal/v2/token',
        headers={
            'Authorization': f'token {oauth_token}',
            'Accept': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Copilot token exchange failed ({exc.code}): {exc.read().decode(errors='replace')}")

    _token_cache['token']      = data['token']
    _token_cache['expires_at'] = data.get('expires_at', now + 1700)
    return _token_cache['token']


def call_copilot(user_message: str, *, max_tokens: int = 4096) -> str:
    """
    Send a single chat completion request to GitHub Copilot.
    Returns the assistant's response content string.
    Raises RuntimeError on API errors.
    """
    token = get_copilot_token()

    payload = json.dumps({
        'model':       'gpt-4o',
        'messages':    [
            {'role': 'system', 'content': _SYSTEM_PROMPT},
            {'role': 'user',   'content': user_message},
        ],
        'max_tokens':  max_tokens,
        'temperature': 0,
    }).encode('utf-8')

    req = urllib.request.Request(
        'https://api.githubcopilot.com/chat/completions',
        data=payload,
        method='POST',
        headers={
            'Authorization':           f'Bearer {token}',
            'Content-Type':            'application/json',
            'Accept':                  'application/json',
            'Editor-Version':          'vscode/1.90.0',
            'Editor-Plugin-Version':   'copilot-chat/0.22.0',
            'Copilot-Integration-Id':  'vscode-chat',
            'X-Request-Id':            str(uuid.uuid4()),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Copilot API error ({exc.code}): {exc.read().decode(errors='replace')}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Copilot API unreachable: {exc.reason}")

    return data['choices'][0]['message']['content']


def llm_merge_file(
    *,
    current_path: str,
    base_path: str,
    theirs_path: str,
    diff_text: str,
    description: str,
    donor_path: str | None = None,
    max_chars: int = 10_000,
    max_lines: int = 300,
) -> tuple[str, str]:
    """
    Use Copilot to apply an analogous SLE→HSLE change to the current file.

    donor_path: optional path to the same file in a donor HSLE model.
                If provided, its content is included in the prompt as an
                additional reference showing how a similar project handled this
                conversion — useful context for the LLM.

    Returns (outcome, detail):
      llm_merged  — successfully applied and written
      too_large   — file exceeds size limits, skipped
      llm_empty   — LLM returned empty response
      llm_error   — API or parse error
    """
    try:
        with open(current_path, 'r', encoding='utf-8', errors='replace') as f:
            current_content = f.read()
    except OSError as exc:
        return ('llm_error', f"Cannot read current file: {exc}")

    lines = current_content.count('\n')
    if len(current_content) > max_chars or lines > max_lines:
        return (
            'too_large',
            f"File too large for LLM ({len(current_content)} chars / {lines} lines) — manual review",
        )

    # Optionally load donor content as an extra reference (capped to avoid bloat)
    donor_section = ''
    if donor_path and os.path.exists(donor_path):
        try:
            with open(donor_path, 'r', encoding='utf-8', errors='replace') as f:
                donor_raw = f.read(6000)  # cap donor at 6000 chars in prompt
            donor_section = (
                f"\nDonor HSLE file (from a similar/previous project — for reference only):\n"
                f"```\n{donor_raw}\n```\n"
            )
        except OSError:
            pass  # donor unreadable — silently skip

    user_message = (
        f"Reference diff (ref_sle → ref_hsle):\n"
        f"```diff\n{diff_text}\n```\n"
        f"{donor_section}\n"
        f"New SLE file to transform (apply analogous changes):\n"
        f"```\n{current_content}\n```\n\n"
        f"Change description: {description}"
    )

    try:
        result = call_copilot(user_message)
    except RuntimeError as exc:
        return ('llm_error', str(exc))

    # Strip accidental code fences from response
    result = result.strip()
    if result.startswith('```'):
        lines_list = result.split('\n')
        end = len(lines_list) - 1 if lines_list[-1].strip() == '```' else len(lines_list)
        result = '\n'.join(lines_list[1:end])

    if not result.strip():
        return ('llm_empty', 'LLM returned empty content — file unchanged')

    # Preserve original line endings
    try:
        with open(current_path, 'rb') as f:
            orig = f.read(4096)
        use_crlf = b'\r\n' in orig
    except OSError:
        use_crlf = False

    data = (
        result.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
        if use_crlf
        else result.encode('utf-8')
    )
    with open(current_path, 'wb') as f:
        f.write(data)

    return ('llm_merged', '')
