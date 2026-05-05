# AI Dungeon Master Project

By Cullen Walker

## Overview

This project implements an AI-driven Dungeon Master system using local Ollama llms. The system simulates a tabletop RPG where a player interacts with a dynamically generated world that has the basics of the setting established through the use of a static lorebook. It is intended as a more open-ended sandbox experience that allows the player to explore the setting and take actions on their own initiative with their own character goals. Wether it be talking to a tavernkeep, fighting a city guard, or climbing some inland mountains the AI DM is made to keep up with your actions and remember the story you have been telling so far.

The system is designed to:
- Maintain game state across interactions
- Adjudicate player actions
- Perform dice-based skill checks
- Retrieve relevant lore using RAG
- Generate immersive narrative responses
- Remember as much of the previous context as possible

---

# 1. Base System Functionality

## System Description

The AI Dungeon Master operates as a multi-phase system:

- **Action Adjudication Phase**  
  Determines whether a player action requires a roll or direct narration.

- **Pending Check Phase**  
  Allows the player to negotiate or modify a roll by talking to the DM before executing it.

- **Roll Resolution Phase**  
  Executes dice rolls and determines success/failure.

- **Narration Phase**  
  Generates narrative responses based on outcomes.

## Scenarios Supported

The system supports the following gameplay scenarios:

- Tavern and social interactions with NPCs
- Exploration of environments and locations
- Skill-based actions (stealth, persuasion, perception, etc.)
- Dice roll resolution with DC checks
- Dynamic narration of outcomes
- NPC interaction with persistent relationship tracking
- Location tracking and contextual awareness
- Player-driven decision making without forced outcomes

The main default scenario has your character stepping off a boat onto the island of Eos, which has many lorebook entries to maintain a explorable Greek-inspired setting. Much of the gameplay loop is made to be sandbox-like and player-driven (this was mainly done out of personal preference), so its up to you to make your own goals and explore the isle.

---

# 2. Prompt Engineering and Model Parameters

## Prompt Design Strategy

The system uses structured prompts to guide behavior:

- **System Prompt**
  - Defines tone, style, and constraints
  - Ensures immersive, grounded narration

- **Action Prompt**
  - Determines whether a roll is required
  - Outputs structured JSON for system control

- **Pending Prompt**
  - Handles player negotiation for roll modification

- **Narration Prompt**
  - Generates descriptive output based on results (this was by far the most tweaked in the course of development)

## Example Prompt Types

- Role-based prompts (DM behavior)
- Context-aware prompts (location, memory, summary)
- JSON-constrained prompts for structured output

## Parameter Choices

| Parameter | Value | Purpose |
|----------|------|--------|
| Temperature | 0.2–0.7 | Balanced creativity and consistency |
| num_predict | 250–3000 | Controls output length |
| repeat_penalty | 1.1 | Reduces repetition |
| top_p | 0.8–0.95 | Improves diversity |
| think | selectively enabled | Enables reasoning for narration |

---

# 3. Tools Usage (15 pts)

The system integrates multiple tools:

## Dice Rolling System
- Implements d20-based rolling
- Supports modifiers, advantage, and disadvantage
- Used for skill checks and action resolution

## Character Sheet System
- JSON-based structure
- Stores abilities, skills, and modifiers
- Used during roll calculations

## GUI System (PySide6)
- Displays chat interface
- Shows character stats
- Provides interactive controls (e.g., roll button)

## Session State Management
- Tracks:
  - Current location
  - Pending checks
  - Automatic story summary
  - Session memory

---

# 4. Planning & Reasoning

## Multi-Step Reasoning

The system demonstrates planning through:

- Separation of decision phases
- Structured reasoning for:
  - Action adjudication
  - Roll necessity
  - Outcome determination

## Reasoning Features

- Context-aware decision making
- Conditional branching (roll vs narration)
- State-driven narrative continuity

## Thinking Models

- Supports reasoning-enabled models (DeepSeek-R1)
- Uses structured prompts to guide reasoning behavior
- Controls thinking to avoid recursive loops

---

# 5. RAG Implementation

## Retrieval-Augmented Generation

The system uses ChromaDB to store and retrieve lore.

### Workflow:
1. Lore is ingested from markdown files
2. Text is chunked and embedded
3. Query is generated from:
   - Player input
   - Current location
4. Relevant lore is retrieved and injected into context

## Use Cases

- Location-based storytelling
- NPC background recall
- World consistency

---

# 6. Additional Tools / Innovation

## Session Memory System

The system includes a temporary memory layer that tracks:

- NPC relationships (friend, enemy, ally, etc.)
- Changes to locations
- Player impact on the world

This memory:
- Updates dynamically after each interaction
- Is injected into context for future responses
- Exists only for the current session

## Story Summary System

- Maintains a compressed summary of the entire story
- Updates each turn
- Ensures long-term coherence without exceeding token limits

## Character Creation System

- GUI-based character setup
- Allows custom or default character selection
- Dynamically generates character sheet for the session

---

# 7. Code Quality & Modular Design
## Project Structure

The project was designed to be modular from the start. Most processes do not interact with each other more than needed, meaning that adding new features can be as simple as adding another generation after or before the narration.

## Design Principles

- Modular architecture
- Separation of concerns
- Reusable components
- Clear data flow between systems

## Best Practices

- JSON-based data handling
- Debug mode for tracing execution
- Controlled context injection
- Git-based version control

---

# Conclusion

This project demonstrates a complete AI RPG system that integrates:

- Natural language understanding
- Multi-step reasoning
- Tool-based execution
- Persistent game state
- Retrieval-augmented context

As of last update, all systems described here should work in at least their most basic forms. Activate debug mode in /config.py to see the behind the scenes systems updating during play.