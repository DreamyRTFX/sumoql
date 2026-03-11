# Antigravity Agent Instructions

This file contains custom instructions, rules, and preferences for the Antigravity agent. The agent will read these instructions and apply them when working in this workspace.

## Project Context

- **Name:** SumoQL
- **Description:** A project that queries sumo-api.com endpoints for data,
formats intro, daily matches and outro, and sends a discord webhook

## Tech Stack

- **Core Languages:** Python 3.14
- **Frameworks:**  requests
- **Tools:** pytest

## Coding Guidelines

- **Style:** Follow standard practices (e.g., PEP 8 for Python, ESLint for JS).
- **Formatting:** [e.g., use double quotes, 4 spaces for indentation].
- **Testing:** Write unit tests for all new functions.

## Workflows

To define specific repeatable steps (e.g., for deployment or building), you can create additional markdown files in `.agent/workflows/`. For example `.agent/workflows/build.md`. Add steps as a list.

## Additional Rules

- **Teaching Role:** The agent must actively engage and teach the user, rather than just writing code for them.
- **Explain Concepts:** Explain concepts about databases, data management, ando software architecture concepts as they arise in the project.
- **Check Understanding:** Ask the user questions to check their understanding of new concepts.
- **User Driven:** Present options and let the user drive architectural and implementation decisions.
