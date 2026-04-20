---
name: tool-guide
description: Use this skill to determine which MCP tool or service to use for a specific task (search, documentation, browser automation).
user-invocable: false
---

# MCP Services Usage Guide

## 1. Documentation & Code Queries
*   **Context7**: Query latest library docs and code examples.
    *   *Use case*: API syntax, configuration, version migration, library-specific debugging.
    *   *Note*: Requires `resolve-library-id` first.
*   **DeepWiki**: Query GitHub repository documentation.
    *   *Use case*: Deep-diving into open source implementations, architecture, contribution guides.

## 2. Academic Paper Search
*   **arxiv-mcp-server**: Search and read arXiv papers.
    *   *Use case*: Finding research papers, downloading and reading paper content.

## 3. Web Search
*   **WebSearch** (built-in): General web search for current events and recent information.
    *   *Use case*: Up-to-date information beyond training cutoff; not library-specific docs.

## 4. Browser Automation
*   **Playwright**: Browser control.
    *   *Use case*: Automate web operations, form filling, screenshot capture, page interaction.
