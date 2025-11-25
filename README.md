# Animepahe Downloader (Fork)

[![Original Repo](https://img.shields.io/badge/original-KevCui%2Fanimepahe--dl-blue)](https://github.com/KevCui/animepahe-dl)

## About

Animepahe Downloader is a tool to search for and download anime episodes from [animepahe.si](https://animepahe.si). This project is a **fork/clone** of [KevCui/animepahe-dl](https://github.com/KevCui/animepahe-dl) with the addition of:
- A modern **PyQt5 GUI** for easy point-and-click downloads
- An enhanced `run.sh` script for streamlined terminal workflows

## Features

- **Modern GUI Interface** - User-friendly graphical interface with search, progress tracking, and real-time logs
- Search and download anime by name or directly via anime slug/UUID
- Download specific episodes, ranges, or all episodes at once
- Choose desired video resolution and audio language
- Real-time download progress bar with episode tracking
- Easy-to-use interactive terminal interface
- Enhanced usability with the `run.sh` script for automated and guided downloads

---

## Requirements

### For GUI (Python):
- Python 3.6+
- [PyQt5](https://pypi.org/project/PyQt5/) - Install with: `pip install PyQt5`

### For all methods:
- [jq](https://stedolan.github.io/jq/) (JSON processor)
- [fzf](https://github.com/junegunn/fzf) (Fuzzy finder) - *Not required for GUI*
- [Node.js](https://nodejs.org/)
- [ffmpeg](https://ffmpeg.org/)
- [openssl](https://www.openssl.org/)
- `curl` (already required by the script)
- Bash shell (Linux/macOS, or Git Bash/WSL on Windows) - *Required for running the backend scripts*

## Installation

1. Clone this repository:

```bash
git clone https://github.com/Monochromat1c/animepahe-dl.git
cd animepahe-dl
```

2. Install Python GUI dependencies (if using GUI):

```bash
pip install PyQt5
```

3. Make the scripts executable:

```bash
chmod +x animepahe-dl.sh run.sh
```

4. Ensure all dependencies are installed and available in your PATH.

---

## Usage

### 1. Graphical User Interface (GUI) - Recommended

The modern PyQt5 GUI provides the easiest way to download anime with a point-and-click interface.

**Start:**

```bash
python animepahe_gui.py
```

**Features:**
- **Anime List Refresh** - Update the anime database with one click
- **Title Search** - Search for anime by keyword with clean, key-free results
- **Session Key Input** - Enter session keys manually or extract from search results
- **Metadata Fetching** - Automatically fetch episode information with smart caching
- **Download Modes:**
  - **Automatic Mode** - Download all episodes in highest resolution
  - **Manual Mode** - Choose specific episodes and resolution
- **Real-time Progress** - Progress bar showing episode download status
- **Live Logs** - See download progress and status messages in real-time
- **Non-blocking** - GUI remains responsive during downloads

The GUI maintains full feature parity with the terminal scripts while providing a significantly improved user experience.

### 2. Modern Run Script (Terminal)

The included `run.sh` script provides an interactive and user-friendly terminal interface:
- Refresh/rebuild anime list
- Search anime titles
- Select anime based on list or key
- Automatically fetch episode metadata
- Choose automatic/all vs manual download mode
- Optionally specify episodes and video resolution interactively

**Start:**

```bash
./run.sh
```

The script will guide you through the steps using colored prompts.

### 3. Direct Bash Script (Original)

You can use the original `animepahe-dl.sh` script directly:

```bash
./animepahe-dl.sh [options]
```

**Options:**

- `-a <name>`: Anime name to search
- `-s <slug>`: Anime slug/UUID (from anime.list)
- `-e <ep1,ep2,ep3-ep4...>`: Episode numbers/ranges/all
- `-r <resolution>`: Video resolution (e.g., 720, 1080)
- `-o <language>`: Audio language (e.g., jpn, eng)
- `-t <threads>`: Number of parallel download threads
- `-l`: Only display m3u8 playlist (do not download)

See `./animepahe-dl.sh --help` for a detailed option list and examples.


**Example:**

```bash
./animepahe-dl.sh -a "one punch man" -e 1-3 -r 1080
```

---

## Credits

- **Original codebase:** [github.com/KevCui/animepahe-dl](https://github.com/KevCui/animepahe-dl)
  - Major credit and thanks to [KevCui](https://github.com/KevCui) and contributors for the base script and core download logic.
- **Current fork/clone:** This repository adds:
  - A modern **PyQt5 GUI** (`animepahe_gui.py`) for graphical user interface
  - The `run.sh` script for enhanced terminal interactivity and workflow improvements
  - Progress tracking, metadata caching, and improved user experience features

## License

This project is licensed under the [WTFPL license](LICENSE), in accordance with the original project.

---

**Disclaimer:**
This tool is for personal use only. Please do not redistribute downloaded content. Respect copyright laws and only download content you have the right to access.



