---
version: 1
slug: "fandesk-frontend-src-pages-ask-tsx"
primary_target: "fandesk/frontend/src/pages/Ask.tsx"
related_targets: ["fandesk/frontend/src/pages/History.tsx","fandesk/frontend/src/components"]
---

# FanDesk frontend — surface brief

Scope: whole FanDesk web app (Ask page, History page, header strip). Mode: Operate.
Audience/job: presenter screen-sharing to interns; interns must follow routing → agent steps → cost, in that order, from across a room.
Constraints: React + Vite + Tailwind; React Flow allowed for the route graph; fonts self-hosted (no hosted stylesheets); readable on a projector; state never by colour alone.
Memorable moment: the chosen agent's lamp lighting on the route board and its number plates dropping in as the request runs.
Unresolved: none.

## Direction contract

THESIS: FanDesk scores every question live like a hand-worked cricket ground scoreboard: one board, a fixed row per agent, a lamp on whoever is "batting", numbers slotted in as they happen. It refuses the category default of a dark node-graph console with glowing edges.

OWN-WORLD: Bottle-green painted board (#1F4D3A family) for the header strip and the route board; painted off-white lettering; amber indicator lamps for the live/active agent; black-on-white enamel number plates for every metric (calls, tokens, cost, ms); a cool light-grey working ground; signal red only for failed/blocked/out-of-scope stamps. Condensed scoreboard caps (Barlow Condensed) for board labels and plates, Barlow for reading text. Square corners, one hairline weight, three ink values on the light ground.

STORY: The intern sees the question go in, watches the Supervisor row light and its reason appear, sees one agent row's lamp light while the others stay dark, follows the ball-by-ball timeline of tool calls with real SQL and page titles, then reads the answer and its plate footer of total cost.

FIRST VIEWPORT: Green header strip (FanDesk wordmark left; Ask/History tabs; today's spend vs budget as plates; Phoenix link right). Below, a two-column work area: left (≈60%) the question bar with sample chips on top, then the route board — Supervisor row, then Stats Guru, Cinema Buff, Out of scope rows each with lamp, name, status word and plates — then the answer card with plate footer. Right (≈40%) the ball-by-ball timeline, step bars drawn to exact latency. Ask button is the one filled amber control.

FORM: Heritage Scoreboard (hand-operated stadium scoreboard), position 5 on the ordered grounded list; seed key 3a2e98ad. Raises: labanotation (latency-true step bars), split-flap (fixed columns, values change in place cell by cell), centre-rail (one hairline, three ink values), monochrome (every footer total links to its event). Signature interaction: lamp lights + number plates drop in per event; motion grammar is a short mechanical drop/settle, no glow, no bounce, disabled under reduced motion.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
