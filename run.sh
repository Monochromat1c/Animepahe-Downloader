#!/bin/bash
# version 1.8 - Title Search

# Define colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

DOWNLOAD_DIR="${HOME}/Downloads"
mkdir -p "$DOWNLOAD_DIR"

# Auto-refresh anime list
echo "[INFO] Refreshing anime list..."
./animepahe-dl.sh --list > /dev/null 2>&1

if [[ ! -f anime.list ]]; then
    echo "[ERROR] Failed to refresh anime list!"
else
    echo "[INFO] Anime list updated: $(wc -l < anime.list) entries"
fi


search_title() {
    local LIST_FILE="anime.list"

    if [[ ! -f "$LIST_FILE" ]]; then
        echo -e "${RED}[ERROR] anime.list not found. Run ./animepahe-dl.sh once to generate it.${NC}"
        exit 1
    fi

    echo -e "${BLUE}=== Anime Title Search ===${NC}"
    read -p "$(echo -e "${GREEN}Enter title keyword:${NC} ")" query

    # Show matching lines
    matches=$(grep -i "$query" "$LIST_FILE")
    
    if [[ -z "$matches" ]]; then
        echo -e "${RED}[ERROR] No matches found for '$query'.${NC}"
        exit 1
    fi

    echo -e "\n${CYAN}Matches found:${NC}"
    IFS=$'\n' read -rd '' -a arr <<< "$matches"

    for i in "${!arr[@]}"; do
        echo -e "${YELLOW}$((i+1)).${NC} ${arr[$i]}"
    done

    # Ask user to choose
    while true; do
        read -p "$(echo -e "${GREEN}Choose anime number:${NC} ")" choice
        if [[ "$choice" =~ ^[0-9]+$ ]] && (( choice>=1 && choice<=${#arr[@]} )); then
            break
        fi
        echo -e "${RED}[ERROR] Invalid choice.${NC}"
    done

    selected="${arr[$((choice-1))]}"

    # Extract the key (assuming format "TITLE | KEY")
    KEY=$(echo "$selected" | sed -E 's/^\[([A-Za-z0-9\-]+)\].*/\1/')

	if [[ -z "$KEY" ]]; then
		echo -e "${RED}[ERROR] Failed to extract anime key. Check anime.list format.${NC}"
		exit 1
	fi


    echo -e "${GREEN}Selected:${NC} ${CYAN}$selected${NC}"
    echo -e "${GREEN}Extracted Key:${NC} $KEY"
}


# ---------------------------------
# Ask for session key (search only)
# ---------------------------------
ask_key() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${CYAN}AnimePahe Key Selection${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo -e "${YELLOW}- Please search for an anime title (recommended)${NC}"
    search_title
}


# ---------------------------------
# Fetch metadata
# ---------------------------------
fetch_metadata() {
    echo -e "\n${YELLOW}* Fetching episode data...${NC}"

    ANIMEPAHE_DL_OUTPUT_DIR="$DOWNLOAD_DIR" ./animepahe-dl.sh -s "$KEY" -e 1 -r 360 -o jpn -t 1 -l >/dev/null 2>&1

    ANIME_FOLDER=$(ls -d */ 2>/dev/null | grep -v "animepahe-dl" | head -1)
    ANIME_FOLDER="${ANIME_FOLDER%/}"

    if [[ -z "$ANIME_FOLDER" ]]; then
        echo -e "${RED}[FATAL ERROR] Could not find metadata folder.${NC}"
        exit 1
    fi

    SOURCE_FILE="$ANIME_FOLDER/.source.json"

    if [[ ! -f "$SOURCE_FILE" ]]; then
        echo -e "${RED}[FATAL ERROR] Metadata not found. Check session key.${NC}"
        exit 1
    fi

    # NEW FIX — detect actual episode numbers
    if jq -e '.episodes' "$SOURCE_FILE" >/dev/null; then
        MIN_EP=$(jq -r '.episodes[].episode' "$SOURCE_FILE" | sort -n | head -1)
        MAX_EP=$(jq -r '.episodes[].episode' "$SOURCE_FILE" | sort -n | tail -1)
    elif jq -e '.data' "$SOURCE_FILE" >/dev/null; then
        MIN_EP=$(jq -r '.data[].episode' "$SOURCE_FILE" | sort -n | head -1)
        MAX_EP=$(jq -r '.data[].episode' "$SOURCE_FILE" | sort -n | tail -1)
    else
        echo -e "${RED}[FATAL ERROR] No episodes or data in $SOURCE_FILE.${NC}"
        exit 1
    fi

    echo -e "${GREEN}* Metadata found. Episodes: ${MIN_EP}-${MAX_EP}${NC}"
}


# ---------------------------------
# Ask mode: Auto or Manual
# ---------------------------------
ask_mode() {
    echo -e "\n${BLUE}--- Download Mode ---${NC}"
    echo -e " ${CYAN}1) Automatic Mode${NC}"
    echo -e "    ${YELLOW}- Downloads ALL episodes${NC}"
    echo -e "    ${YELLOW}- Uses highest available resolution${NC}"
    echo -e ""
    echo -e " ${CYAN}2) Manual Mode${NC}"
    echo -e "    ${YELLOW}- Choose episodes manually${NC}"
    echo -e "    ${YELLOW}- Choose resolution manually${NC}"

    while true; do
        read -p "$(echo -e "${GREEN}Select mode (1=Auto, 2=Manual):${NC} ")" MODE
        case $MODE in
            1) AUTO_MODE=true; break ;;
            2) AUTO_MODE=false; break ;;
            *) echo -e "${RED}[ERROR] Invalid choice. Enter 1 or 2.${NC}" ;;
        esac
    done
}

# ---------------------------------
# Manual: Ask episode selection
# ---------------------------------
ask_episode() {
    echo -e "\n${BLUE}--- Episode Selection ---${NC}"
    echo -e " ${CYAN}Available episodes:${NC} ${YELLOW}${MIN_EP}-${MAX_EP}${NC}"
    echo -e " ${CYAN}Press ENTER for ALL episodes${NC}"

    while true; do
        read -p "$(echo -e "${GREEN}Episode(s) to download:${NC} ")" EPISODE

        if [[ -z "$EPISODE" ]]; then
            EPISODE="1-$MAX_EP"
            echo -e "${YELLOW}[AUTO] Using all episodes: ${EPISODE}${NC}"
            break
        fi

        IFS=',' read -ra LIST <<< "$EPISODE"
        ok=true
        for ep in "${LIST[@]}"; do
            if [[ "$ep" =~ ^[0-9]+$ ]]; then
                (( ep >= MIN_EP && ep <= MAX_EP )) || ok=false
            elif [[ "$ep" =~ ^[0-9]+-[0-9]+$ ]]; then
                start="${ep%-*}"
                end="${ep#*-}"
                (( start >= 1 && end <= MAX_EP && start <= end )) || ok=false
            else
                ok=false
            fi
        done

        if $ok; then break; else
            echo -e "${RED}[ERROR] Invalid input.${NC}"
        fi
    done
}

# ---------------------------------
# Manual: Ask resolution
# ---------------------------------
ask_resolution() {
    echo -e "\n${BLUE}--- Resolution Selection ---${NC}"
    echo -e " ${CYAN}Press ENTER for AUTO highest resolution${NC}"

    while true; do
        read -p "$(echo -e "${GREEN}Resolution (e.g., 720):${NC} ")" RESOLUTION

        if [[ -z "$RESOLUTION" ]]; then
            RESOLUTION=""
            AUTO_RES=true
            break
        fi

        if [[ "$RESOLUTION" =~ ^[0-9]+$ ]]; then
            AUTO_RES=false
            break
        else
            echo -e "${RED}[ERROR] Invalid resolution.${NC}"
        fi
    done
}

# ---------------------------------
# Manual: Ask audio language
# ---------------------------------
ask_audio() {
    echo -e "\n${BLUE}--- Audio Selection ---${NC}"
    echo -e " ${CYAN}Press ENTER for default 'jpn' audio${NC}"

    while true; do
        read -p "$(echo -e "${GREEN}Audio language code (e.g., jpn, eng):${NC} ")" AUDIO

        if [[ -z "$AUDIO" ]]; then
            AUDIO="jpn"
            break
        fi

        if [[ "$AUDIO" =~ ^[a-zA-Z]+$ ]]; then
            AUDIO=${AUDIO,,}
            break
        else
            echo -e "${RED}[ERROR] Invalid audio code. Letters only.${NC}"
        fi
    done
}

# ---------------------------------
# Main
# ---------------------------------
ask_key
fetch_metadata
ask_mode

if [[ "$AUTO_MODE" = true ]]; then
    EPISODE="$MIN_EP-$MAX_EP"
    AUTO_RES=true
    echo -e "\n${YELLOW}* AUTO MODE ENABLED${NC}"
    echo -e "${CYAN}Downloading ALL episodes in highest resolution...${NC}"
    echo -e "${CYAN}Episode range: $EPISODE${NC}"

    ANIMEPAHE_DL_OUTPUT_DIR="$DOWNLOAD_DIR" ./animepahe-dl.sh -s "$KEY" -e "$EPISODE" -o jpn -t 16
    exit
fi

# Manual mode:
ask_episode
ask_resolution
ask_audio

echo -e "\n${YELLOW}* Starting Manual Download...${NC}"

if [[ "$AUTO_RES" = true ]]; then
    ANIMEPAHE_DL_OUTPUT_DIR="$DOWNLOAD_DIR" ./animepahe-dl.sh -s "$KEY" -e "$EPISODE" -o "$AUDIO" -t 16
else
    ANIMEPAHE_DL_OUTPUT_DIR="$DOWNLOAD_DIR" ./animepahe-dl.sh -s "$KEY" -e "$EPISODE" -r "$RESOLUTION" -o "$AUDIO" -t 16
fi
