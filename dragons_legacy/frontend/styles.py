"""
Modern CSS styles for Legend of Dragon's Legacy TUI
"""

MAIN_CSS = """
/* Main application styling */
Screen {
    background: $surface;
    color: $text;
}

/* Title styling */
.title {
    text-style: bold;
    color: $accent;
    text-align: center;
    margin: 1;
}

.subtitle {
    color: $primary;
    text-align: center;
    margin-bottom: 2;
}

/* Container styling */
.container {
    width: 100%;
    height: 100%;
    align: center middle;
}

.form-container {
    width: 60;
    max-height: 90%;
    border: solid $primary;
    padding: 2;
    background: $surface;
    overflow-y: auto;
}

/* Input styling */
Input {
    width: 100%;
    margin: 1 0;
    border: solid $primary;
    background: $surface;
    color: $text;
}

Input:focus {
    border: solid $accent;
    background: $surface;
}

Input:disabled {
    opacity: 0.5;
    border: solid grey;
}

/* Button styling */
Button {
    width: 100%;
    margin: 1 0;
    border: solid $primary;
    background: $primary;
    color: $surface;
    text-style: bold;
}

Button:hover {
    background: $accent;
    border: solid $accent;
}

Button:focus {
    background: $accent;
    border: solid $accent;
}

Button.-default {
    background: $surface;
    color: $text;
    border: solid $primary;
}

Button.-default:hover {
    background: $primary;
    color: $surface;
    border: solid $primary;
}

/* Select styling */
Select {
    width: 100%;
    margin: 1 0;
    border: solid $primary;
    background: $surface;
}

Select:focus {
    border: solid $accent;
}

/* Label styling */
.label {
    color: $text;
    margin: 1 0 0 0;
    text-style: bold;
}

.security-question {
    color: $accent;
    margin: 1 0;
    text-style: bold;
    width: 100%;
    padding: 1;
    border: solid $primary;
    background: $surface;
}

/* Error message styling */
.error {
    color: red;
    text-align: center;
    margin: 1;
    text-style: bold;
}

/* Success message styling */
.success {
    color: green;
    text-align: center;
    margin: 1;
    text-style: bold;
}

/* Link styling */
.link {
    color: $accent;
    text-style: underline;
    margin: 1;
}

.link:hover {
    color: $primary;
}

/* Loading indicator */
.loading {
    color: yellow;
    text-align: center;
    margin: 1;
    text-style: bold;
}

/* Character creation placeholder */
.todo-placeholder {
    border: dashed yellow;
    background: $surface;
    color: yellow;
    text-align: center;
    padding: 4;
    margin: 2;
    text-style: bold;
}

/* Selection row for race and gender buttons */
.selection-row {
    height: auto;
    width: 100%;
    layout: horizontal;
    margin: 1 0;
}

.selection-row Button {
    width: 1fr;
    margin: 0 1;
}

/* Race button styles */
.race-btn {
    background: $surface;
    color: $text;
    border: solid $primary;
}

.race-btn:hover {
    background: $primary;
    color: $surface;
}

.race-magmar-selected {
    background: red;
    color: white;
    border: solid red;
    text-style: bold;
}

.race-magmar-selected:hover {
    background: red;
    color: white;
    border: solid red;
}

.race-magmar-selected:focus {
    background: red;
    color: white;
    border: solid red;
}

.race-human-selected {
    background: green;
    color: white;
    border: solid green;
    text-style: bold;
}

.race-human-selected:hover {
    background: green;
    color: white;
    border: solid green;
}

.race-human-selected:focus {
    background: green;
    color: white;
    border: solid green;
}

/* Gender button styles */
.gender-btn {
    background: $surface;
    color: $text;
    border: solid $primary;
}

.gender-btn:hover {
    background: $primary;
    color: $surface;
}

.gender-selected {
    background: $accent;
    color: $surface;
    border: solid $accent;
    text-style: bold;
}

.gender-selected:hover {
    background: $accent;
    color: $surface;
    border: solid $accent;
}

.gender-selected:focus {
    background: $accent;
    color: $surface;
    border: solid $accent;
}

/* Race disabled (coming soon) */
.race-disabled {
    background: $surface;
    color: grey;
    border: dashed grey;
    opacity: 0.5;
}

.race-disabled:hover {
    background: $surface;
    color: grey;
    border: dashed grey;
}

/* ========================================
   GAME SCREEN STYLES
   ======================================== */

/* Full-screen game layout */
.game-layout {
    width: 100%;
    height: 100%;
    layout: vertical;
}

/* Top bar with map name */
.game-top-bar {
    height: 3;
    width: 100%;
    background: $primary;
    align: center middle;
    padding: 0 2;
}

.game-map-name {
    color: white;
    text-style: bold;
    text-align: center;
    width: 1fr;
}

/* Debug add-item button (top-right) */
.debug-add-btn {
    width: auto;
    min-width: 14;
    height: 3;
    background: yellow;
    color: black;
    border: solid yellow;
    text-style: bold;
    margin: 0;
}

.debug-add-btn:hover {
    background: white;
    color: black;
    border: solid white;
}

.debug-add-btn:focus {
    background: white;
    color: black;
    border: solid white;
}

/* Main 3-panel layout */
.game-main {
    height: 1fr;
    width: 100%;
    layout: horizontal;
}

/* Left panel: character stats */
.game-stats-panel {
    width: 28;
    height: 100%;
    border-right: solid $primary;
    padding: 1;
    background: $surface;
}

.game-panel-title {
    text-style: bold;
    color: $accent;
    text-align: center;
    margin-bottom: 1;
    padding: 0 0 1 0;
    border-bottom: solid $primary;
}

.game-stat-name {
    color: $accent;
    text-style: bold;
    text-align: center;
    margin: 1 0 0 0;
}

.game-stat-detail {
    color: $text;
    text-align: center;
    margin-bottom: 1;
}

.game-stat-separator {
    height: 1;
    border-bottom: dashed $primary;
    margin: 0 1;
}

.game-stat {
    color: $text;
    margin: 0 0 0 1;
    padding: 0;
}

.game-stat-hp {
    color: red;
    text-style: bold;
    margin: 1 0 0 1;
}

.game-stat-mana {
    color: dodgerblue;
    text-style: bold;
    margin: 0 0 0 1;
}

.game-stat-currency {
    text-style: bold;
    margin: 0 0 0 1;
}

.game-stat-cooldown {
    color: yellow;
    text-style: bold;
    margin: 0 0 0 1;
}

/* Center panel: game area */
.game-center-panel {
    width: 1fr;
    height: 100%;
    padding: 1;
    background: $surface;
}

.game-center-title {
    text-style: bold;
    color: $accent;
    text-align: center;
    margin-bottom: 1;
    padding: 0 0 1 0;
    border-bottom: solid $primary;
}

.game-center-content {
    height: 1fr;
    width: 100%;
    align: center middle;
    padding: 2;
}

.game-area-text {
    text-align: center;
    color: $text;
    width: 100%;
}

/* Right panel: action menu */
.game-action-panel {
    width: 28;
    height: 100%;
    border-left: solid $primary;
    padding: 1;
    background: $surface;
}

.game-action-btn {
    width: 100%;
    margin: 0 0 1 0;
    height: 3;
    background: $surface;
    color: $text;
    border: solid $primary;
}

.game-action-btn:hover {
    background: $primary;
    color: $surface;
}

.game-action-btn:focus {
    background: $accent;
    color: $surface;
    border: solid $accent;
}

/* Bottom bar */
.game-bottom-bar {
    height: 3;
    width: 100%;
    background: $surface;
    border-top: solid $primary;
    align: left middle;
    padding: 0 1;
}

.game-chat-btn {
    width: auto;
    min-width: 12;
    background: $surface;
    color: $text;
    border: solid $primary;
    margin-right: 1;
}

.game-chat-btn:hover {
    background: $accent;
    color: $surface;
    border: solid $accent;
}

.game-logout-btn {
    width: auto;
    min-width: 16;
    background: $surface;
    color: $text;
    border: solid $primary;
}

.game-logout-btn:hover {
    background: red;
    color: white;
    border: solid red;
}

/* Dynamic area inside center panel */
#dynamic_area {
    width: 100%;
    height: auto;
    padding: 0 2;
}

/* Travel buttons */
.game-travel-btn {
    width: 100%;
    margin: 1 0;
    height: 3;
    background: $surface;
    color: $text;
    border: solid green;
    text-style: bold;
}

.game-travel-btn:hover {
    background: green;
    color: white;
    border: solid green;
}

.game-travel-btn:focus {
    background: green;
    color: white;
    border: solid green;
}

/* NPC buttons */
.game-npc-btn {
    width: 100%;
    margin: 1 0;
    height: 3;
    background: $surface;
    color: $text;
    border: solid $accent;
}

.game-npc-btn:hover {
    background: $accent;
    color: $surface;
    border: solid $accent;
}

.game-npc-btn:focus {
    background: $accent;
    color: $surface;
    border: solid $accent;
}

/* Mob hunt buttons */
.game-mob-btn {
    width: 100%;
    margin: 1 0;
    height: 3;
    background: $surface;
    color: red;
    border: solid #8B0000;
    text-style: bold;
}

.game-mob-btn:hover {
    background: #8B0000;
    color: white;
    border: solid #8B0000;
}

.game-mob-btn:focus {
    background: #8B0000;
    color: white;
    border: solid #FF4444;
}

/* Online players button */
.game-player-btn {
    width: 100%;
    margin: 0 0 1 0;
    height: 3;
    background: $surface;
    color: $text;
    border: solid $primary;
}

.game-player-btn:hover {
    background: $primary;
    color: $surface;
}

/* ========================================
   ITEM STYLES
   ======================================== */

/* Item group headers */
.item-group-header {
    text-style: bold;
    text-align: center;
    margin: 1 0 0 0;
    padding: 0;
    width: 100%;
}

/* Item buttons */
.game-item-btn {
    width: 100%;
    margin: 0 0 0 0;
    height: 3;
    background: $surface;
    border: solid $primary;
}

.game-item-btn:hover {
    background: $primary;
    color: $surface;
}

.game-item-btn:focus {
    background: $primary;
    color: $surface;
    border: solid $accent;
}

/* Item rarity colors */
.item-color-white {
    color: white;
    border: solid grey;
}

.item-color-white:hover {
    color: white;
    background: grey;
    border: solid grey;
}

.item-color-green {
    color: green;
    border: solid green;
}

.item-color-green:hover {
    color: white;
    background: green;
    border: solid green;
}

.item-color-blue {
    color: dodgerblue;
    border: solid dodgerblue;
}

.item-color-blue:hover {
    color: white;
    background: dodgerblue;
    border: solid dodgerblue;
}

.item-color-purple {
    color: mediumorchid;
    border: solid mediumorchid;
}

.item-color-purple:hover {
    color: white;
    background: mediumorchid;
    border: solid mediumorchid;
}

/* ========================================
   FIGHT SCREEN STYLES
   ======================================== */

.fight-right-panel {
    width: 34;
    height: 100%;
    border-left: solid $primary;
    padding: 1;
    background: $surface;
}

.fight-section-title {
    text-style: bold;
    color: $accent;
    text-align: center;
    margin-bottom: 1;
    padding: 0 0 1 0;
    border-bottom: solid $primary;
}

.fight-participants-panel {
    width: 100%;
    height: auto;
    layout: horizontal;
}

.fight-player-side {
    width: 1fr;
    height: 16;
    layout: vertical;
    margin-right: 1;
    border-right: dashed $primary;
    padding-right: 1;
}

.fight-player-info {
    width: 100%;
    height: auto;
    margin: 0 0 1 0;
}

.fight-player-name {
    color: $accent;
    text-style: bold;
    margin: 0 0 1 0;
}

.fight-player-hp {
    color: red;
    text-style: bold;
    margin: 0;
}

.fight-player-mana {
    color: dodgerblue;
    text-style: bold;
    margin: 0;
}

.fight-mob-side {
    width: 1fr;
    height: auto;
    margin-top: 0;
    padding-top: 0;
}

.fight-mob-name {
    color: $accent;
    text-style: bold;
    margin: 0 0 1 0;
}

.fight-mob-hp {
    color: red;
    text-style: bold;
    margin: 0;
}

.fight-mob-mana {
    color: dodgerblue;
    text-style: bold;
    margin: 0;
}

/* ========================================
   FIGHT SCREEN - MOROK STYLES
   ======================================== */

/* Moroks container in participants panel */
.fight-moroks-container {
    width: 100%;
    height: auto;
    margin: 0;
    padding: 0;
}

/* Individual morok entry */
.fight-morok-entry {
    width: 100%;
    height: auto;
    margin: 0 0 1 0;
    padding: 0 1;
    border-left: solid green;
    background: $surface-darken-1;
}

/* Morok name display */
.fight-morok-name {
    color: green;
    text-style: bold;
    text-align: left;
    width: 100%;
    margin: 0;
    padding: 0;
}

/* Morok HP display */
.fight-morok-hp {
    color: red;
    text-align: left;
    width: 100%;
    margin: 0;
    padding: 0;
}

"""