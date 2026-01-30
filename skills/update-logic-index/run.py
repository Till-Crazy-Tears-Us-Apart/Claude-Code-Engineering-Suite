#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@FileName    : run.py
@Description : Logic Indexer - Generates semantic summaries for Python code using AST and Gemini API.
               Features:
               - Incremental updates via MD5 hashing
               - AST-based parsing (Classes + Functions)
               - Concurrent API calls (ThreadPoolExecutor)
               - Zero-dependency (Standard Library only)
@Author      : Logic Indexer Skill
@Version     : 1.2.0
"""

import ast
import hashlib
import json
import os
import sys
import time
import random
import concurrent.futures
import urllib.request
import urllib.error
import ssl
import fnmatch
from pathlib import Path
from datetime import datetime

# --- Configuration ---
VERSION = "1.2.0"
CACHE_FILE = os.path.join(".claude", "logic_index.json")
CONFIG_FILE = os.path.join(".claude", "logic_index_config")
OUTPUT_MD = os.path.join(".claude", "logic_tree.md")
DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
DEFAULT_MAX_WORKERS = 5
DEFAULT_RETRY_LIMIT = 3
DEFAULT_TIMEOUT = 60
MAX_CTX_CHARS = 200000

class ImportVisitor(ast.NodeVisitor):
    """AST visitor to collect internal imports."""
    def __init__(self, root_dir, current_file_path):
        self.root_dir = root_dir
        self.current_dir = os.path.dirname(current_file_path)
        self.internal_imports = []

    def visit_Import(self, node):
        for alias in node.names:
            self._add_import(alias.name)

    def visit_ImportFrom(self, node):
        # Base module name (e.g. 'pkg' in 'from pkg import ...')
        module = node.module or ""

        for alias in node.names:
            # Construct potential sub-module path
            if module:
                full_name = f"{module}.{alias.name}"
            else:
                full_name = alias.name

            # Try to resolve specific submodule first (e.g. pkg.module_a)
            if self._add_import(full_name, node.level):
                continue

            # If specific submodule not found, try base module (e.g. pkg containing ClassA)
            # Only if module is not empty (avoid trying to import empty string)
            if module:
                self._add_import(module, node.level)

    def _add_import(self, module_name, level=0):
        # Resolve to potential file path
        if module_name:
            parts = module_name.split('.')
        else:
            parts = []

        if level > 0:
            # Relative import
            base = self.current_dir
            for _ in range(level - 1):
                base = os.path.dirname(base)
            potential_path = os.path.join(base, *parts)
        else:
            # Absolute import (check if starts with internal package)
            potential_path = os.path.join(self.root_dir, *parts)

        # Check .py or /__init__.py
        py_file = potential_path + ".py"
        init_file = os.path.join(potential_path, "__init__.py")

        found = False
        if os.path.exists(py_file):
            self.internal_imports.append(os.path.relpath(py_file, self.root_dir).replace(os.sep, '/'))
            found = True
        elif os.path.exists(init_file):
            self.internal_imports.append(os.path.relpath(init_file, self.root_dir).replace(os.sep, '/'))
            found = True

        return found

class FatalError(Exception):
    """Custom exception to trigger circuit breaker and halt execution."""
    pass

class LogicIndexer:
    def __init__(self, root_dir):
        self.root_dir = os.path.abspath(root_dir)
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.model = os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self.base_url = os.environ.get("GEMINI_BASE_URL", "") # Optional override
        self.circuit_open = False # Flag to stop all processing on fatal error

        # Configure Concurrency
        try:
            self.max_workers = int(os.environ.get("GEMINI_MAX_WORKERS", DEFAULT_MAX_WORKERS))
        except ValueError:
            self.max_workers = DEFAULT_MAX_WORKERS

        # Configure Resilience
        try:
            self.retry_limit = int(os.environ.get("GEMINI_RETRY_LIMIT", DEFAULT_RETRY_LIMIT))
            self.timeout = int(os.environ.get("GEMINI_TIMEOUT", DEFAULT_TIMEOUT))
        except ValueError:
            self.retry_limit = DEFAULT_RETRY_LIMIT
            self.timeout = DEFAULT_TIMEOUT

        self.exclusions = []
        self._load_config()
        self.cache = self._load_cache()
        self.dirty_nodes = [] # Nodes that need LLM summary

        # Configure SSL Context (Fix for Windows missing certs)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _load_config(self):
        """Loads exclusion patterns from config file."""
        config_path = os.path.join(self.root_dir, CONFIG_FILE)

        if not os.path.exists(config_path):
            try:
                template_path = os.path.join(os.path.dirname(__file__), "default_logic_config.template")
                if os.path.exists(template_path):
                    os.makedirs(os.path.dirname(config_path), exist_ok=True)
                    with open(template_path, "r", encoding="utf-8") as src:
                        content = src.read()
                    with open(config_path, "w", encoding="utf-8") as dst:
                        dst.write(content)
                    print(f"Initialized logic config at {CONFIG_FILE}")
            except Exception as e:
                print(f"Warning: Failed to create default config: {e}")

        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if line.startswith("!"):
                        self.exclusions.append(line[1:])
        else:
            # Hardcoded fallback
            self.exclusions = [".git/", "__pycache__/", "venv/", "node_modules/", ".claude/", "dist/", "build/"]

    def _is_excluded(self, path):
        """Checks if path matches any exclusion pattern."""
        rel_path = os.path.relpath(path, self.root_dir).replace(os.sep, "/")
        if rel_path == ".":
            return False

        basename = os.path.basename(rel_path)
        is_dir = os.path.isdir(path)

        for pattern in self.exclusions:
            must_be_dir = pattern.endswith("/")
            clean_pattern = pattern.rstrip("/")

            if must_be_dir and not is_dir:
                continue

            # Match against basename or relative path
            if fnmatch.fnmatch(basename, clean_pattern) or fnmatch.fnmatch(rel_path, clean_pattern):
                return True
        return False

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Schema Version Check
                    cache_version = data.get("_meta", {}).get("version", "1.1.0")
                    if cache_version != VERSION:
                        print(f"检测到缓存版本升级 ({cache_version} -> {VERSION})。正在重置缓存...")
                        return {}
                    return data
            except Exception:
                pass
        return {}

    def _save_cache(self):
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        # Add timestamp and version for expiry/migration check
        self.cache["_meta"] = {
            "last_updated": datetime.now().isoformat(),
            "model": self.model,
            "version": VERSION
        }
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)

    def _calculate_hash(self, source_code, extra_data=""):
        """Calculates MD5 hash of normalized source code and optional dependency data."""
        # Normalize: strip whitespace to ignore formatting changes
        normalized = "".join(source_code.split()) + extra_data
        return hashlib.md5(normalized.encode('utf-8')).hexdigest()

    def _determine_thinking_level(self, source_code):
        """Determines the appropriate thinking_level based on code complexity."""
        lines = source_code.splitlines()
        line_count = len(lines)

        # Heuristics for complex logic
        complex_indicators = ["yield", "__metaclass__", "getattr", "setattr", "eval", "exec", "ast.", "compile("]
        is_complex = any(indicator in source_code for indicator in complex_indicators)

        if line_count > 100 or is_complex:
            return "low"
        return "minimal"

    def _call_gemini(self, prompt, thinking_level="minimal"):
        """Calls Gemini API using standard library with retry logic."""
        if not self.api_key:
            return "Error: GEMINI_API_KEY not set."

        if self.circuit_open:
            return "Error: Circuit breaker open."

        # Construct URL
        if self.base_url:
            url = f"{self.base_url.rstrip('/')}/models/{self.model}:generateContent?key={self.api_key}"
        else:
            url = DEFAULT_API_URL.format(model=self.model, api_key=self.api_key)

        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1000,
                "responseMimeType": "application/json",
                "responseJsonSchema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "summary": {"type": "string"}
                        },
                        "required": ["name", "summary"]
                    }
                }
            }
        }

        # Handle Thinking Level separately as it's model-dependent
        if thinking_level != "minimal":
             data["generationConfig"]["thinkingConfig"] = {
                "thinkingLevel": thinking_level
            }

        retries = 0
        while retries <= self.retry_limit:
            try:
                req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
                with urllib.request.urlopen(req, context=self.ssl_context, timeout=self.timeout) as response:
                    raw_data = response.read().decode('utf-8')
                    result = json.loads(raw_data)
                    try:
                        text_content = result['candidates'][0]['content']['parts'][0]['text'].strip()

                        # Robust JSON Extraction
                        try:
                            # 1. Try direct parse (fast path)
                            json.loads(text_content)
                            return text_content
                        except json.JSONDecodeError:
                            # 2. Try to extract from markdown blocks
                            if "```json" in text_content:
                                text_content = text_content.split("```json")[1].split("```")[0].strip()
                            elif "```" in text_content:
                                text_content = text_content.split("```")[1].split("```")[0].strip()
                            return text_content
                    except (KeyError, IndexError):
                        print(f"API Debug - Response Structure: {json.dumps(result)[:500]}")
                        return "Error: Unexpected API response format."
            except urllib.error.HTTPError as e:
                # Fatal errors: Auth or Rate Limit
                if e.code in (401, 403, 429):
                    self.circuit_open = True
                    raise FatalError(f"Fatal API Error {e.code}: {e.reason}")

                # Retriable errors: Server or Timeout
                if e.code in (500, 502, 503, 504) and retries < self.retry_limit:
                    retries += 1
                    wait = (2 ** retries) + (random.random() * 0.3)
                    time.sleep(wait)
                    continue
                return f"Error: HTTP {e.code} - {e.reason}"
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                if retries < self.retry_limit:
                    retries += 1
                    wait = (2 ** retries) + (random.random() * 0.3)
                    time.sleep(wait)
                    continue
                return f"Error: Network error ({str(e)})"
            except Exception as e:
                return f"Error: {str(e)}"
        return "Error: Maximum retries exceeded."

    def parse_file(self, file_path):
        """Parses a single Python file."""
        rel_path = os.path.relpath(file_path, self.root_dir).replace(os.sep, '/')

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            print(f"Skipping {rel_path}: {e}")
            return None

        # Resolve imports
        visitor = ImportVisitor(self.root_dir, file_path)
        visitor.visit(tree)
        imports = list(set(visitor.internal_imports))

        # Calculate dependency-aware hash
        dep_summaries = []
        for imp_path in imports:
            cached_imp = self.cache.get(imp_path)
            if cached_imp:
                for sym in cached_imp.get("symbols", []):
                    if sym.get("summary"):
                        dep_summaries.append(f"{sym['name']}:{sym['summary']}")

        extra_data = "|".join(sorted(dep_summaries))
        file_hash = self._calculate_hash(source, extra_data)

        file_node = {
            "path": rel_path,
            "hash": file_hash,
            "imports": imports,
            "symbols": []
        }

        # Check if file or dependencies changed
        cached_file = self.cache.get(rel_path)
        file_changed = not cached_file or cached_file.get("hash") != file_hash

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                self._process_node(node, source, file_node, file_changed, cached_file)

                # Recursively handle methods inside classes
                if isinstance(node, ast.ClassDef):
                    for subnode in node.body:
                        if isinstance(subnode, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            # Prefix method name with class name for clarity
                            original_name = subnode.name
                            subnode.name = f"{node.name}.{original_name}"
                            self._process_node(subnode, source, file_node, file_changed, cached_file)
                            subnode.name = original_name # Restore

        return file_node

    def _process_node(self, node, source, file_node, file_changed, cached_file):
        """Helper to process a single AST node."""
        symbol_name = node.name
        # Determine type based on original class (even if name modified)
        symbol_type = "class" if isinstance(node, ast.ClassDef) else "function"

        # Get source segment
        try:
            segment = ast.get_source_segment(source, node)
        except Exception:
            segment = None

        if not segment: return

        # Extract arguments for display (e.g., "(self, a, b=1)")
        args_str = ""
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                # Use ast.unparse for Python 3.9+
                if sys.version_info >= (3, 9):
                    args_str = f"({ast.unparse(node.args)})"
                else:
                    args_str = "(...)"
            except Exception:
                pass

        symbol_hash = self._calculate_hash(segment)

        # Try to reuse cache
        summary = None
        if not file_changed and cached_file:
            for s in cached_file.get("symbols", []):
                if s["name"] == symbol_name and s.get("hash") == symbol_hash:
                    summary = s.get("summary")
                    break

        if not summary and cached_file:
             for s in cached_file.get("symbols", []):
                if s["name"] == symbol_name and s.get("hash") == symbol_hash:
                    summary = s.get("summary")
                    break

        # --- New Logic: Docstring Extraction and Small Function Filtering ---
        if not summary:
            # 1. Try Docstring
            doc = ast.get_docstring(node)
            if doc:
                # Extract first 3 non-empty lines
                lines = [line.strip() for line in doc.splitlines() if line.strip()]
                if lines:
                    summary = "[Doc] " + " ".join(lines[:3])

            # 2. Check line count (if no docstring)
            elif len(segment.splitlines()) < 3:
                summary = "Small utility function."

        symbol_data = {
            "name": symbol_name,
            "args": args_str,
            "type": symbol_type,
            "lineno": node.lineno,
            "hash": symbol_hash,
            "summary": summary
        }

        if not summary:
            # Queue for LLM
            # We pass file_node["path"] to associate the symbol
            self.dirty_nodes.append((file_node["path"], symbol_data, segment))

        file_node["symbols"].append(symbol_data)

    def _load_prompt_template(self):
        """Loads the prompt template from prompt.md"""
        try:
            prompt_path = os.path.join(os.path.dirname(__file__), "prompt.md")
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            # Fallback if file not found
            return "Task: Summarize Python code: {source_code}"

    def _worker_task(self, file_path, items, context_summaries=""):
        """Processes multiple symbols for a single file."""
        if self.circuit_open:
            return

        try:
            with open(os.path.join(self.root_dir, file_path), 'r', encoding='utf-8') as f:
                source_code = f.read()
        except Exception as e:
            print(f"Error reading {file_path} for batch: {e}")
            return

        # Check for token overflow (approximate)
        if len(source_code) / 3 > 30000: # Simple heuristic for ~30k tokens
            print(f"File {file_path} too large for batch. Falling back to atomic mode.")
            for symbol, segment in items:
                prompt_template = self._load_prompt_template()
                # Construct atomic prompt from template (adapting template for single mode)
                prompt = f"Target Symbol: {symbol['name']}\nDependencies:\n{context_summaries}\nSource Code:\n{segment}\n\nPlease follow the summary rules and return as JSON object within a list."
                level = self._determine_thinking_level(segment)
                res = self._call_gemini(prompt, thinking_level=level)
                try:
                    data = json.loads(res)
                    symbol['summary'] = data[0]['summary'] if isinstance(data, list) else data['summary']
                except Exception:
                    symbol['summary'] = res
            return

        target_names = [item[0]['name'] for item in items]
        prompt_template = self._load_prompt_template()
        prompt = prompt_template.format(
            source_code=source_code,
            target_symbols=", ".join(target_names),
            context_summaries=context_summaries
        )

        level = self._determine_thinking_level(source_code)
        res = self._call_gemini(prompt, thinking_level=level)

        try:
            if res.startswith("Error:"):
                print(f"API Error for {file_path}: {res}")
                return

            summaries = json.loads(res)
            # Map results back to symbols
            summary_map = {s['name']: s['summary'] for s in summaries if 'name' in s and 'summary' in s}
            for symbol, _ in items:
                if symbol['name'] in summary_map:
                    symbol['summary'] = summary_map[symbol['name']]
                else:
                    print(f"Warning: No summary returned for {symbol['name']} in {file_path}")
        except Exception as e:
            print(f"Error parsing batch response for {file_path}: {e}")
            print(f"Raw response: {res[:200]}...")

    def process_llm_queue(self):
        """Process dirty nodes grouped by file to minimize API calls."""
        if not self.dirty_nodes:
            return

        # Group by file
        batches = {}
        for file_path, symbol, segment in self.dirty_nodes:
            if file_path not in batches:
                batches[file_path] = []
            batches[file_path].append((symbol, segment))

        print(f"Generating summaries for {len(self.dirty_nodes)} symbols across {len(batches)} files (Workers: {self.max_workers})...")

        # Prepare context summaries for each batch
        batch_args = []
        for fp, items in batches.items():
            file_node = self.cache.get(fp)
            ctx_summary = ""
            if file_node and file_node.get("imports"):
                dep_list = []
                current_chars = 0
                for imp_path in file_node["imports"]:
                    cached_imp = self.cache.get(imp_path)
                    if cached_imp:
                        for s in cached_imp.get("symbols", []):
                            if s.get("summary"):
                                line = f"- {s['name']}: {s['summary']}"
                                if current_chars + len(line) + 1 > MAX_CTX_CHARS:
                                    print(f"Warning: Dependency context truncated for {fp} (Limit: {MAX_CTX_CHARS} chars)")
                                    break
                                dep_list.append(line)
                                current_chars += len(line) + 1
                        if current_chars > MAX_CTX_CHARS:
                            break
                ctx_summary = "\n".join(dep_list)
            batch_args.append((fp, items, ctx_summary))

        # Concurrent Execution across files
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._worker_task, *args) for args in batch_args]
            try:
                for future in concurrent.futures.as_completed(futures):
                    if self.circuit_open:
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    try:
                        future.result()
                    except FatalError as e:
                        print(f"\n{e}")
                        self.circuit_open = True
                        executor.shutdown(wait=False, cancel_futures=True)
                        break
                    except Exception as e:
                        print(f"Error processing file batch: {e}")
            except KeyboardInterrupt:
                print("\nInterrupted by user. Shutting down...")
                executor.shutdown(wait=False, cancel_futures=True)
                raise

    def generate_markdown(self):
        """Generates the final tree view."""
        lines = ["# 🧠 逻辑索引 (Logic Index)"]
        lines.append(f"> Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("> **Symbol Types**: `[C]` Class | `[f]` Function")
        lines.append("> **Tags**: `[Doc]` From Docstring | `[Source]` Data Source | `[Sink]` Data Sink\n")

        # Sort by path
        sorted_files = sorted(self.cache.keys())
        for path in sorted_files:
            if path == "_meta": continue
            data = self.cache[path]
            if not data.get("symbols"): continue

            lines.append(f"## 📄 `{path}`")
            for sym in data["symbols"]:
                icon = "C" if sym["type"] == "class" else "f"
                summary = sym.get("summary", "No summary")
                name_display = f"{sym['name']}{sym.get('args', '')}"
                lines.append(f"- **[{icon}]** `{name_display}`: {summary}")
            lines.append("")

        return "\n".join(lines)

    def trigger_injector(self):
        """Triggers the injector to update CLAUDE.md"""
        try:
            # Resolve injector path relative to this script's location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # skills/update-logic-index/run.py -> ../../hooks/doc_manager/injector.py
            injector_path = os.path.abspath(os.path.join(script_dir, "..", "..", "hooks", "doc_manager", "injector.py"))

            if os.path.exists(injector_path):
                import subprocess
                print(f"Triggering CLAUDE.md injection via {os.path.relpath(injector_path, self.root_dir)}...")
                subprocess.run([sys.executable, injector_path], cwd=self.root_dir, check=False)
            else:
                print(f"Warning: Injector not found at {injector_path}")
        except Exception as e:
            print(f"Error triggering injector: {e}")

    def run(self):
        print("Scanning codebase...")

        try:
            # Scan files
            new_cache = {}

            for root, dirs, files in os.walk(self.root_dir):
                # In-place modify dirs to skip excluded ones
                dirs[:] = [d for d in dirs if not self._is_excluded(os.path.join(root, d))]

                for file in files:
                    full_path = os.path.join(root, file)
                    if file.endswith(".py") and not self._is_excluded(full_path):
                        result = self.parse_file(full_path)
                        if result:
                            new_cache[result["path"]] = result

            # Update cache structure but keep existing summaries until LLM fills new ones
            self.cache = new_cache

            # Process LLM
            if self.dirty_nodes:
                if not self.api_key:
                    print("Warning: GEMINI_API_KEY not found. Skipping LLM generation.")
                else:
                    self.process_llm_queue()

        except Exception as e:
            if not isinstance(e, FatalError):
                print(f"Error during run: {e}")
        finally:
            # Always Save Cache (Ensures partial results are kept)
            self._save_cache()

            # Generate Markdown
            md_content = self.generate_markdown()
            os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
            with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
                f.write(md_content)

            print(f"Logic index updated at {OUTPUT_MD}")

            # Trigger Injector (Only if not in a broken state)
            if not self.circuit_open:
                self.trigger_injector()
            else:
                print("Skipping CLAUDE.md injection due to API errors.")

if __name__ == "__main__":
    # Ensure UTF-8
    sys.stdout.reconfigure(encoding='utf-8')
    indexer = LogicIndexer(os.getcwd())
    indexer.run()
