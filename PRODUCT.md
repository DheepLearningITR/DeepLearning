# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React + Vite + Tailwind frontend, served by nginx; FastAPI backend streaming SSE. The route board is plain HTML/CSS (no graph library). Defined in `fandesk-design.md`.

## Users

Primary: a presenter screen-sharing FanDesk on a projector or video call to a room of interns who are learning how multi-agent systems work. The interns watch; the presenter drives. Readability at a distance and a clear live sequence matter more than density.

## Product Purpose

FanDesk is a teaching demo for multi-agent AI. A supervisor agent routes each question about IPL cricket or movies to one of two specialist agents (Stats Guru over a local SQLite database, Cinema Buff over Wikipedia), or declines it. Success: after watching a few questions, an intern can explain how routing works, what a specialist agent does step by step, and what each run costs.

## Positioning

The route each request takes is visible live, as it happens: supervisor decision and reason, the specialist's tool calls (real SQL, real Wikipedia lookups), and the tokens, cost and latency of every LLM call. It shows the inside of an agent system instead of just its answer.

## Operating Context

- A live demo, run by the presenter from a script of six questions (`fandesk-design.md` §12), plus ad-hoc questions from the room.
- Can run in mock mode (scripted responses, no API key) or live against OpenRouter.
- Phoenix (traces) is opened alongside for the "deeper look" part of the demo.

## Capabilities and Constraints

- Pages: Ask (question input, sample-question chips, live route graph, event timeline, answer with cost footer), History (past requests, click to replay), header strip (today's spend vs. budget, link to Phoenix).
- Event stream shape and types are fixed in `fandesk-design.md` §5.
- Three agents only: Supervisor, Stats Guru, Cinema Buff; plus an out-of-scope path.
- Single-turn questions; no auth, no multi-turn memory.

## Brand Commitments

FanDesk has its own identity: its own name and look, no company branding.

## Evidence on Hand

No logo, imagery or brand assets exist. Content is real at runtime (IPL stats from Cricsheet, movie facts from Wikipedia); do not fabricate sample stats in static copy beyond the six scripted demo questions.

## Product Principles

1. **Layers of understanding, in order:** routing first (which agent and why), then the steps inside the agent, then cost and timing. Each layer is visible without hiding the one above it.
2. **Show the real thing:** real SQL, real page titles, real token counts and cost — never decorative stand-ins.
3. **Legible from the back of the room:** anything that teaches must be readable on a shared screen.
4. **The live moment is the hook:** the path lighting up as the request runs is the centrepiece of the demo.

## Accessibility & Inclusion

Projected/screen-shared use: high contrast, large type, and state never communicated by colour alone (routes and statuses also carry labels or shape).
