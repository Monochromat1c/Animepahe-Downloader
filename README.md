# Animepahe Downloader (Fork)

[![Original Repo](https://img.shields.io/badge/original-KevCui%2Fanimepahe--dl-blue)](https://github.com/KevCui/animepahe-dl)

## About

Animepahe Downloader is a command-line tool to search for and download anime episodes from [animepahe.si](https://animepahe.si) directly in your terminal. This project is a **fork/clone** of [KevCui/animepahe-dl](https://github.com/KevCui/animepahe-dl) with the addition of an enhanced `run.sh` script to streamline searching and downloading workflows for users.

## Features

- Search and download anime by name or directly via anime slug/UUID
- Download specific episodes, ranges, or all episodes at once
- Choose desired video resolution and audio language
- Easy-to-use interactive terminal interface
- Enhanced usability with the `run.sh` script for automated and guided downloads

---

## Requirements

- [jq](https://stedolan.github.io/jq/) (JSON processor)
- [fzf](https://github.com/junegunn/fzf) (Fuzzy finder)
- [Node.js](https://nodejs.org/)
- [ffmpeg](https://ffmpeg.org/)
- [openssl](https://www.openssl.org/) *(optional, for parallel threads download)*
- `curl` (already required by the script)
- Bash shell (Linux/macOS, or Git Bash/WSL on Windows)

## Installation

1. Clone this repository:

```bash
git clone https://github.com/Monochromat1c/animepahe-dl.git
cd animepahe-dl
```

2. Make the scripts executable:

```bash
chmod +x animepahe-dl.sh run.sh
```

3. Ensure all dependencies are installed and available in your PATH.

---

## Usage

### 1. Modern Run Script (Recommended)

The included `run.sh` script provides an interactive and user-friendly way to:
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

### 2. Direct Bash Script (Original)

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
- **Current fork/clone:** This repository adds the `run.sh` script for extra terminal interactivity and workflow improvements. Please see commits for specific enhancements.

## License

This project is licensed under the [WTFPL license](LICENSE), in accordance with the original project.

---

**Disclaimer:**
This tool is for personal use only. Please do not redistribute downloaded content. Respect copyright laws and only download content you have the right to access.



