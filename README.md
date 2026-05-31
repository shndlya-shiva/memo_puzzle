# Memory Puzzle Game 🍍🍇🍉

A visually engaging, grid-based card-matching game built to challenge and improve memory. Players flip cards to find matching pairs of fruits under dynamic constraints before time runs out.

---

## 🎮 Game Stages

The game loops through three primary stages as illustrated below:


| Stage | Description |
| :--- | :--- |
| **1. Main Menu** | Choose game difficulty and theme parameters. |
| **2. Active Gameplay** | Flip cards on the grid to match fruit pairs under time limits. |
| **3. Level Cleared** | Performance evaluation with star ratings and statistics. |

---

## 🚀 Key Features

* **Dynamic Themes**: Interactive falling background animations featuring the active theme (Fruits).
* **Multiple Difficulty Levels**: Tailored grid sizing ranging from beginner to expert constraints:
  * **EASY**: \(4 \times 4\) Grid
  * **MEDIUM**: \(6 \times 6\) Grid
  * **HARD**: \(8 \times 8\) Grid
  * **EXTREME**: \(10 \times 10\) Grid
* **Live Performance Tracking**: Real-time counters tracking total **Moves Made** and a countdown **Time Limit** clock.
* **Smart Scoring System**: End-of-game screens calculate a 3-star rating based on your speed, total moves, and performance efficiency.

---

## 📁 Project Architecture

The repository contains a highly compact layout with all game logic consolidated into the primary execution script:

```text
project/
├── .vscode/
│   └── settings.json    # Workspace configuration, python interpreter, and formatting rules
├── main.py              # COMPLETE game program code (Engine, Logic, UI, & Game Loop)
└── README.md            # Project documentation
```

---

## 🛠️ How It Works

1. **Setup**: The player selects a difficulty from the main menu, initializing a randomized layout of hidden card pairs.
2. **Match Mechanics**: The user clicks to flip two cards. If the cards match (e.g., Pear and Pear), they remain face-up. If they mismatch, they automatically flip back after a brief delay.
3. **Win Condition**: The game is successfully cleared when all pairs are matched within the allocated time window.

---

## 💻 Setup and Installation

### Prerequisites
* **Python 3.13** or higher is **strictly required** to execute this program.

### 1. Clone the Repository
```bash
git clone https://github.com
cd project
```

### 2. Set Up a Virtual Environment (Recommended)
```bash
python3.13 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Required Dependencies
The engine is driven entirely by the **Pygame** framework. Install it via pip:
```bash
pip install pygame
```

### 4. Run the Game
Execute the consolidated program file to launch the game window:
```bash
python main.py
```
