---
name: FanDesk
description: A live, hand-worked cricket scoreboard for watching a multi-agent system route and score each question.
colors:
  board: "#1f4d3a"
  board-deep: "#163a2b"
  board-line: "#2f6450"
  paint: "#f4f1ea"
  paint-dim: "#b8cabf"
  lamp: "#f2b33d"
  lamp-deep: "#b9811c"
  lamp-off: "#2a5a46"
  plate: "#ffffff"
  plate-ink: "#141414"
  stamp: "#c23b27"
  ground: "#e6ebe8"
  surface: "#fbfcfb"
  ink: "#121a16"
  ink-2: "#45524b"
  ink-3: "#6a776f"
  rule: "#c8d1cc"
typography:
  display:
    fontFamily: "Barlow Condensed, Barlow, ui-sans-serif, sans-serif"
    fontSize: "1.9rem"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "0.04em"
  headline:
    fontFamily: "Barlow Condensed, Barlow, ui-sans-serif, sans-serif"
    fontSize: "1.35rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.08em"
  title:
    fontFamily: "Barlow Condensed, Barlow, ui-sans-serif, sans-serif"
    fontSize: "1.45rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "0.06em"
  plate:
    fontFamily: "Barlow Condensed, Barlow, ui-sans-serif, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 600
    lineHeight: 1
    fontFeature: "tnum"
  body-lead:
    fontFamily: "Barlow, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 400
    lineHeight: 1.625
  body:
    fontFamily: "Barlow, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.05rem"
    fontWeight: 400
    lineHeight: 1.375
  label:
    fontFamily: "Barlow Condensed, Barlow, ui-sans-serif, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 600
    letterSpacing: "0.06em"
  code:
    fontFamily: "ui-monospace, Cascadia Mono, Consolas, monospace"
    fontSize: "0.9rem"
    fontWeight: 400
    lineHeight: 1.625
rounded:
  none: "0px"
  lamp: "9999px"
spacing:
  plate-gap: "3px"
  xs: "0.5rem"
  sm: "0.75rem"
  md: "1rem"
  lg: "1.5rem"
  xl: "2.5rem"
components:
  button-ask:
    backgroundColor: "{colors.lamp}"
    textColor: "{colors.plate-ink}"
    typography: "{typography.headline}"
    rounded: "{rounded.none}"
    padding: "0 1.5rem"
  button-ask-hover:
    backgroundColor: "#f6c25c"
  button-ask-disabled:
    backgroundColor: "{colors.rule}"
    textColor: "{colors.ink-3}"
  chip-sample:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-2}"
    rounded: "{rounded.none}"
    padding: "0.375rem 0.75rem"
  input-question:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    typography: "{typography.body-lead}"
    rounded: "{rounded.none}"
    padding: "0.75rem 1rem"
  nav-tab:
    textColor: "{colors.paint-dim}"
    typography: "{typography.label}"
    padding: "0.25rem"
  nav-tab-active:
    textColor: "{colors.paint}"
  number-plate-cell:
    backgroundColor: "{colors.plate}"
    textColor: "{colors.plate-ink}"
    typography: "{typography.plate}"
    rounded: "{rounded.none}"
    width: "1.2rem"
    height: "2.25rem"
  number-plate-cell-empty:
    backgroundColor: "{colors.board-deep}"
  lamp-lit:
    backgroundColor: "{colors.lamp}"
    rounded: "{rounded.lamp}"
    size: "1.25rem"
  lamp-off:
    backgroundColor: "{colors.lamp-off}"
    rounded: "{rounded.lamp}"
    size: "1.25rem"
  status-stamp:
    backgroundColor: "{colors.stamp}"
    textColor: "{colors.paint}"
    typography: "{typography.label}"
    rounded: "{rounded.none}"
    padding: "0.125rem 0.375rem"
  route-board:
    backgroundColor: "{colors.board}"
    textColor: "{colors.paint}"
    rounded: "{rounded.none}"
    padding: "0.75rem 1.5rem 1rem"
  card-surface:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "1rem 1.5rem 1.25rem"
---

# Design System: FanDesk

## Overview

**Creative North Star: "The Heritage Scoreboard"**

FanDesk is a hand-worked cricket ground scoreboard put on a projector. One bottle-green painted board carries the live state: a fixed row per agent, an amber lamp on whoever is batting, and black-on-white enamel number plates that drop into their slots as each figure arrives. Everything that is not the board sits on a cool light-grey working ground as plain square sheets of near-white surface. The world is built to be read from across a room: an 18px root (`font-size: 112.5%`), condensed capitals for anything painted on the board, and a calm reading face for the questions, reasons, and answers.

The board is the one source of colour. The header strip and the route board are painted green; the lamp amber marks what is live, chosen, or the one thing to press; signal red appears only as a stamp for failed, blocked, declined, or out-of-scope. State is never carried by colour alone: every lamp has a status word beside it, every stamp is a word.

Motion is mechanical. Plates drop and settle, the lamp warms up through a deeper amber before it is fully lit, new rows slide in 6px. There is no glow, no bounce, and all of it switches off under reduced motion. The world refuses the dark node-graph console with glowing edges; the route is drawn as a painted rail down the left of the board, not a graph canvas.

**Key Characteristics:**
- One painted green board on a cool grey ground; colour lives on the board.
- Amber lamps and an amber rail for the live or chosen path; one amber-filled control.
- Every metric in enamel number plates or condensed tabular figures, in fixed columns.
- Square corners everywhere except the round lamps.
- Condensed uppercase for painted labels, sentence-case Barlow for reading.
- Short drop-and-settle motion, disabled under reduced motion.

## Colors

A painted-timber palette: bottle-green board, off-white lettering, amber lamps, white enamel plates, one signal red, on a cool green-grey working ground.

### Primary
- **Bottle-Green Board** (board): the header strip, the route board, and the History table head. It is a place, not a fill: it never appears as a button or card colour elsewhere. Also the link and focus-border colour on the light ground.
- **Board Shadow Green** (board-deep): the 6px frame around the route board, the empty plate slots, and the code panel behind SQL.
- **Painted Rule Green** (board-line): row dividers and the unlit rail on the board; the underline of links on the green strip.

### Secondary
- **Lamp Amber** (lamp): lit lamps, the lit rail down to the chosen agent, the active-tab bar, live status words, the Ask button fill, LLM-call latency bars, the selection colour, the focus ring, and the brief highlight flash on a jumped-to timeline row (at 25% opacity) and History row hover (15%).
- **Filament Amber** (lamp-deep): the lamp's rim and the middle frame of its warm-up. A rim and transition colour, not a text colour on light surfaces.
- **Unlit Lamp** (lamp-off): a dark lamp disc on the board.

### Tertiary
- **Signal Stamp Red** (stamp): failed, budget-blocked, declined, and out-of-scope only. Used as a paint-on-red stamp, a 2px border on the failure card, or red text that is itself a status word.

### Neutral
- **Painted Lettering** (paint): all primary text on the board and header.
- **Faded Lettering** (paint-dim): secondary text on the board: column heads, handles, inactive tabs, waiting status, the double total rule.
- **Enamel White** (plate) and **Plate Black** (plate-ink): number-plate cells; plate-ink is also the text on the amber Ask button.
- **Working Ground** (ground): page background and the empty track behind latency bars.
- **Sheet** (surface): cards, the timeline, the History table, inputs, chips.
- **Ink** (ink), **Ink Two** (ink-2), **Ink Three** (ink-3): the three ink values on the light ground: reading text, secondary text, and quiet labels/indices.
- **Hairline** (rule): the one 1px rule on the light ground: input and chip borders, timeline and table row dividers.

### Named Rules
**The Board and Ground Rule.** Green is the board. Paint it only for scoreboard furniture (header strip, route board, table head); everything else is a square surface sheet on the grey ground.

**The One Lamp Rule.** Amber means live, chosen, or press-here. The Ask button is the only amber-filled control on a screen.

**The Stamp Rule.** Red appears only for failed, blocked, declined, or out-of-scope, and always as a word.

**The Never Colour Alone Rule.** Every lamp sits beside a status word (Waiting, Working, Done, Not used, Routed, Declined); every red mark is a word.

## Typography

**Display Font:** Barlow Condensed (with Barlow, ui-sans-serif), self-hosted at 500/600/700
**Body Font:** Barlow (with ui-sans-serif, system-ui), self-hosted at 400/500/600
**Label/Mono Font:** ui-monospace stack (Cascadia Mono, Consolas) for SQL, tool names, and source tables only

**Character:** Barlow Condensed reads like signwriter's paint on timber: narrow capitals that pack a row of figures and still carry across a room. Barlow is its own family's plain-spoken reading face, so questions and answers sit calmly under the board.

### Hierarchy
- **Display** (700, 1.9rem, line-height 1, 0.04em, uppercase): the FanDesk wordmark only. The History page title uses the same face at 600, 1.8rem.
- **Headline** (600, 1.35rem, 0.08em, uppercase): panel titles painted on a panel: Route board, Ball by ball, Answer.
- **Title** (600, 1.45rem, 0.06em, uppercase): agent names and the Total row on the board.
- **Plate** (600, 1.2rem on the board narrowing to 1rem; 1.6rem in the header; tabular figures): number-plate characters. Outside plates, metrics use the same face at 500-600 with tabular figures (timeline ms, History numeric columns).
- **Body lead** (400, 1.2rem, line-height 1.625, max 68ch): the answer text and the question input. The echoed question on the board is 500, 1.3rem.
- **Body** (400, 1.05rem, line-height 1.375, max 60ch on the board): the routing reason, timeline titles (600) and notes (0.95rem).
- **Label** (600, 0.75-0.95rem, 0.06em, uppercase): column heads, status words, inline field labels (Try, Why, Sources), event counts, agent tags in the timeline.

### Named Rules
**The Paint and Print Rule.** Condensed uppercase is paint: labels, headings, names, status words, figures. Anything a person reads as a sentence (questions, reasons, answers, notes) is sentence-case Barlow.

**The Plate Rule.** Every metric (calls, tokens, cost, time) is set in Barlow Condensed tabular figures; on the board it sits in enamel plates with a fixed slot count, right-aligned, so columns never move.

## Layout

The Ask page is a two-column work area on desktop (`lg`, 64rem): a fluid left column (question bar, route board, answer card stacked with 1.5rem gaps) and a right timeline column of 22-26rem that is sticky and fills the viewport height, scrolling internally. The content max-width is 96rem with 1.5rem side padding (1rem below `sm`). Below `lg` everything stacks in reading order: question, board, answer, timeline.

The route board is a container-query component. At 45rem of board width it shows a fixed eight-column grid (rail, lamp, agent, status, calls, tokens, cost, time) with painted column heads and an extra 1.25rem gutter between plate columns; narrower, the status word moves under the agent name and the plates fall into a labelled 2x2 grid, shown only for rows that have run. The header strip wraps: wordmark and tabs, then spend plates and the Phoenix link.

Rhythm runs on quarter-rem steps of the 18px root: 3px between plate cells, 0.5-0.75rem inside rows, 1rem-1.5rem panel padding, 1.5rem between panels, 2.5rem between header groups.

## Elevation & Depth

Depth is soft and physical: a board hung on a wall and sheets laid on a table. Shadows are diffuse, low, and tinted green-black; nothing glows, nothing has a hard offset. The board gets the deepest drop, sheets a light lift, plates a tight 1px contact shadow so they read as raised enamel.

### Shadow Vocabulary
- **Board drop** (`box-shadow: 0 6px 18px -8px rgb(10 30 20 / 0.55)`): the route board only.
- **Sheet lift** (`box-shadow: 0 2px 10px -4px rgb(10 30 20 / 0.25)`): answer card, timeline panel, History table.
- **Plate contact** (`box-shadow: 0 1px 2px rgb(0 0 0 / 0.35)`): filled number-plate cells.
- **Button lift** (`box-shadow: 0 2px 4px rgb(0 0 0 / 0.2)`): the Ask button; removed when disabled; the button presses down 1px when active.

### Named Rules
**The Soft Lift Rule.** Depth comes from diffuse, tinted shadows and the board's painted frame. No glows, no hard offset shadows.

## Shapes

Every rectangle is square-cornered: board, sheets, inputs, chips, buttons, plates, stamps, the code panel. The only circles are lamps (1.25rem discs with a 2px rim) and the lamp dot in the wordmark. On the light ground there is one rule weight, a 1px hairline. On the board, rules are painted furniture with their own weights: a 6px frame, a 2px rule under the board header, 1px row dividers, a 3px routing rail, and a 5px double rule above Total.

**The Square Board Rule.** Corners are square; roundness belongs only to lamps.

## Components

### Buttons
Few and blunt; one filled control per screen.
- **Shape:** square (0px).
- **Ask (primary):** lamp amber fill, plate-black condensed caps at 1.25rem, 0.08em tracking, 1.5rem side padding (1rem on small screens), full height of the input, a trailing arrow icon hidden on small screens. Busy state reads "Scoring" with a spinner (static under reduced motion).
- **Hover / Focus:** hover brightens the fill (#f6c25c); active presses down 1px; focus is the global 3px amber outline at 2px offset. Disabled turns to the hairline grey with ink-three text and no shadow.
- **Text actions:** Show query, sources, Phoenix trace: 600-weight board-green text with a hairline-coloured underline that darkens to board green on hover. Replay in History is a condensed-caps board-green action that goes from 70% to full opacity on row hover or focus.

### Chips
- **Style:** sample questions as square surface chips with a 1px hairline border and ink-two text (0.95rem; 0.85rem in the compact state once a run is on screen).
- **State:** hover turns border and text board green; disabled while a run is scoring (50% opacity).

### Cards / Containers
- **Corner Style:** square.
- **Background:** surface sheet on the ground.
- **Shadow Strategy:** Sheet lift (see Elevation).
- **Border:** none at rest; the failure card swaps the shadow for a 2px stamp-red border.
- **Internal Padding:** 1.5rem sides, 1rem top, 1.25rem bottom; panel headers carry a condensed headline and a quiet label at the right, separated by a hairline.

### Inputs / Fields
- **Style:** square surface field, 1px hairline border, 1.2rem text, ink-three placeholder, board-green caret.
- **Focus:** border turns board green and the 3px amber focus ring shows.

### Navigation
The header strip is the top of the board: bottle green, FanDesk wordmark with its lamp dot, Ask/History tabs in condensed caps (paint-dim, paint on hover); the active tab is paint with a 4px amber bar along the strip's bottom edge. Today's spend is a large number plate with "of $budget" and a percentage beside it; a Mock mode tag is a paint-dim outlined label. On mobile the strip wraps into stacked rows.

### Route Board (signature)
The scoreboard itself: a green panel in a 6px board-deep frame. Header: "Route board", a live status label at the right (Live, Innings complete, or a red Stopped stamp), and the question echoed in quotes. Rows: Supervisor, then Stats Guru, Cinema Buff, Out of scope, each with lamp, condensed name, handles line, status word, and four plate columns. A 3px rail down the left connects the rows; it lights amber from the Supervisor down to the chosen agent only, with a stub into that row's lamp. The Supervisor's reason appears under its row, prefixed by an amber "Why" label. A Total row under the double rule repeats the plate columns; each total plate is a button that jumps to and highlights the timeline event behind it.

### Number Plate (signature)
A row of square enamel cells, 3px apart, one character per cell, right-aligned into a fixed slot count; empty slots are board-deep. Only changed characters remount and drop in (260ms, translateY -55% to 0, `cubic-bezier(0.16, 1, 0.3, 1)`). Each plate group carries an accessible label with its value.

### Lamp (signature)
A 1.25rem disc with a 2px rim. Lit: amber with a filament-amber rim, warming up from unlit through filament amber over 320ms. Off: unlit-lamp green with a board-deep rim. Always paired with a status word.

### Ball-by-Ball Timeline
A numbered list on a surface sheet: condensed tabular index, a 20px board-green line icon (stamp red for failures), a 600-weight title, an agent tag in condensed caps, a note in ink two. Steps with a duration draw a bar to their exact share of the slowest step on a ground-coloured track: board green for tool calls, amber for LLM calls, with the ms figure right-aligned. SQL opens under "Show query" in a board-deep code panel with paint-coloured mono text. New rows slide in (240ms, 6px).

## Do's and Don'ts

### Do:
- **Do** keep green for scoreboard furniture: the header strip, the route board, and table heads.
- **Do** pair every lamp and every red mark with a word; state is never colour alone.
- **Do** set every metric in Barlow Condensed tabular figures, in enamel plates with fixed slot counts on the board.
- **Do** keep corners square; only lamps are round.
- **Do** keep motion to short drop-and-settle moves (240-320ms, `cubic-bezier(0.16, 1, 0.3, 1)`) and turn it off under `prefers-reduced-motion`.
- **Do** keep the light ground to one 1px hairline and three ink values; heavier rules belong to the board.
- **Do** self-host both Barlow families; the base type size stays 18px for projection.

### Don't:
- **Don't** add a second amber-filled control beside Ask.
- **Don't** use stamp red for anything but failed, blocked, declined, or out-of-scope.
- **Don't** render the route as a dark node-graph canvas with glowing edges; the route is the rail on the board.
- **Don't** add glows, bounces, or hard offset shadows.
- **Don't** set sentences in condensed caps, or figures in proportional digits.
- **Don't** set small text in filament amber (lamp-deep) or ink three on the grey ground; both fall below 4.5:1.
