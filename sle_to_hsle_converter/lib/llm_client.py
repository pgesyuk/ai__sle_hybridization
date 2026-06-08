"""
llm_client.py — GitHub Copilot Chat API client for HSLE converter LLM fallback.

Token resolution order (first success wins):
  1. In-process cache (valid for ~28 min)
  2. ``gh auth token`` CLI
  3. GH_TOKEN / GITHUB_TOKEN / COPILOT_GITHUB_TOKEN environment variables
  4. Persistent token file  ~/.sle_hsle_token
  5. Interactive prompt (getpass) — with save option for future runs

If the Copilot exchange fails with 401/403, the stored token is cleared and
the user is re-prompted (once) so an expired token does not silently block
all LLM merges for the remainder of the run.
"""

import getpass
import json
import os
import stat
import sys
import time
import uuid
import subprocess
import urllib.request
import urllib.error

# --------------------------------------------------------------------------- #
#  Token storage
# --------------------------------------------------------------------------- #

_TOKEN_FILE   = os.path.expanduser('~/.sle_hsle_token')
_token_cache: dict = {}          # in-process cache for short-lived Copilot token
_oauth_cache: dict = {}          # in-process cache for the OAuth source token


def _load_stored_token() -> str:
    """Read the persisted OAuth token from the token file, or '' if absent/unreadable."""
    try:
        with open(_TOKEN_FILE, 'r') as f:
            return f.read().strip()
    except OSError:
        return ''


def _save_token(oauth_token: str) -> None:
    """Persist an OAuth token to disk with mode 0600 (owner-read-only)."""
    try:
        with open(_TOKEN_FILE, 'w') as f:
            f.write(oauth_token + '\n')
        os.chmod(_TOKEN_FILE, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # non-fatal — we still have the token in memory


def _clear_stored_token() -> None:
    """Remove the token file (called when exchange fails, token likely expired)."""
    try:
        os.unlink(_TOKEN_FILE)
    except OSError:
        pass
    _oauth_cache.clear()


# --------------------------------------------------------------------------- #
#  Interactive prompt
# --------------------------------------------------------------------------- #

def _prompt_for_token(reason: str = '') -> str:
    """
    Ask the user for a GitHub personal access token interactively.

    Prints a short explanation, then uses getpass to read the token without
    echoing it to the terminal.  If stdin is not a tty (pipe / batch mode),
    raises RuntimeError instead of blocking.

    Returns the entered token (stripped), or raises RuntimeError if the user
    presses Ctrl-C or leaves the input empty.
    """
    if not sys.stdin.isatty():
        raise RuntimeError(
            "No valid GitHub token found and stdin is not a terminal -- "
            "cannot prompt.  Set GH_TOKEN or GITHUB_TOKEN env var, or run "
            "the converter interactively."
        )

    print()
    print("=" * 60)
    print("  LLM Merge: GitHub token required")
    if reason:
        print(f"  Reason: {reason}")
    print()
    print("  A GitHub Personal Access Token (classic) is needed to call")
    print("  the GitHub Copilot Chat API for intelligent file merging.")
    print()
    print("  How to create one:")
    print("    1. https://github.com/settings/tokens")
    print("    2. Generate new token (classic)")
    print("    3. Scopes: 'repo' + ensure your account has Copilot access")
    print()
    print("  The token will be saved to:", _TOKEN_FILE)
    print("  (owner read-only, mode 0600)")
    print("=" * 60)

    try:
        token = getpass.getpass("  GitHub token (paste, then Enter): ").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        raise RuntimeError("Token entry cancelled by user")

    if not token:
        raise RuntimeError("Empty token entered -- LLM merge unavailable")
    return token


# --------------------------------------------------------------------------- #
#  Copilot token exchange
# --------------------------------------------------------------------------- #

def _exchange(oauth_token: str) -> dict:
    """
    Exchange an OAuth token for a short-lived Copilot API token.
    Returns the full response dict (contains 'token' and 'expires_at').
    Raises RuntimeError on HTTP error.
    """
    req = urllib.request.Request(
        'https://api.github.com/copilot_internal/v2/token',
        headers={
            'Authorization': f'token {oauth_token}',
            'Accept': 'application/json',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors='replace')
        raise RuntimeError(
            f"Copilot token exchange failed (HTTP {exc.code}): {body[:200]}"
        )
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error during token exchange: {exc.reason}")


# --------------------------------------------------------------------------- #
#  Public: get_copilot_token
# --------------------------------------------------------------------------- #

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
    """
    Return a valid short-lived Copilot API token, refreshing/prompting as needed.

    Full resolution order:
      1. In-process Copilot-token cache (still valid)
      2. gh auth token CLI
      3. GH_TOKEN / GITHUB_TOKEN / COPILOT_GITHUB_TOKEN environment variables
      4. Persistent token file  ~/.sle_hsle_token
      5. Interactive getpass prompt  (saves token to file on success)

    If the Copilot exchange fails (HTTP 401/403), the token is assumed expired:
    the file and cache are cleared and the user is prompted once more.
    """
    now = time.time()

    # 1. In-process Copilot token cache
    if _token_cache.get('expires_at', 0) - 60 > now:
        return _token_cache['token']

    # Collect OAuth token candidates
    oauth_token = ''

    # 2. gh CLI
    try:
        result = subprocess.run(
            ['gh', 'auth', 'token'], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            oauth_token = result.stdout.strip()
    except Exception:
        pass

    # 3. Environment variables
    if not oauth_token:
        for env_var in ('GH_TOKEN', 'GITHUB_TOKEN', 'COPILOT_GITHUB_TOKEN'):
            val = os.environ.get(env_var, '').strip()
            if val:
                oauth_token = val
                break

    # 4. Persistent token file
    if not oauth_token:
        oauth_token = _load_stored_token()
        if oauth_token:
            _oauth_cache['source'] = 'file'

    # 5. Interactive prompt (if stdin is a tty)
    prompted = False
    if not oauth_token:
        oauth_token = _prompt_for_token()
        prompted = True

    # Exchange for Copilot token (with one re-prompt on auth failure)
    for attempt in range(2):
        try:
            data = _exchange(oauth_token)
            # Success: cache Copilot token + persist OAuth token if it came from prompt
            _token_cache['token']      = data['token']
            _token_cache['expires_at'] = data.get('expires_at', now + 1700)
            if prompted or _oauth_cache.get('source') == 'prompt':
                _save_token(oauth_token)
                if attempt == 0 and prompted:
                    print("  [llm] Token saved to", _TOKEN_FILE)
            return _token_cache['token']
        except RuntimeError as exc:
            err = str(exc)
            if '401' in err or '403' in err or '404' in err:
                # Token expired or lacks Copilot access — clear and re-prompt once
                _clear_stored_token()
                _token_cache.clear()
                if attempt == 0:
                    reason = "Previous token expired or lacks Copilot access"
                    try:
                        oauth_token = _prompt_for_token(reason)
                        prompted = True
                        _oauth_cache['source'] = 'prompt'
                        continue
                    except RuntimeError as prompt_err:
                        raise RuntimeError(str(prompt_err)) from None
            raise


# --------------------------------------------------------------------------- #
#  Public: call_copilot + llm_merge_file
# --------------------------------------------------------------------------- #

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
    max_chars: int = 50_000,
    max_lines: int = 1_500,
) -> tuple[str, str]:
    """
    Use Copilot to apply an analogous SLE->HSLE change to the current file.

    donor_path: optional path to the same file in a donor HSLE model.
                If provided, its content is included in the prompt as an
                additional reference showing how a similar project handled this
                conversion.

    Returns (outcome, detail):
      llm_merged  -- successfully applied and written
      too_large   -- file exceeds size limits, skipped
      llm_empty   -- LLM returned empty response
      llm_error   -- API or auth error
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
            f"File too large for LLM ({len(current_content)} chars / {lines} lines) -- manual review",
        )

    # Optionally load donor content as an extra reference (capped to avoid bloat)
    donor_section = ''
    if donor_path and os.path.exists(donor_path):
        try:
            with open(donor_path, 'r', encoding='utf-8', errors='replace') as f:
                donor_raw = f.read(6000)
            donor_section = (
                f"\nDonor HSLE file (from a similar/previous project -- for reference only):\n"
                f"```\n{donor_raw}\n```\n"
            )
        except OSError:
            pass

    user_message = (
        f"Reference diff (ref_sle -> ref_hsle):\n"
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
        return ('llm_empty', 'LLM returned empty content -- file unchanged')

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

