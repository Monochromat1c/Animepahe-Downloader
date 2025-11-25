import sys
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QLineEdit, QListWidget, QMessageBox, QDialog, QHBoxLayout,
    QRadioButton, QButtonGroup, QGroupBox, QTextEdit, QInputDialog,
    QProgressBar
)
from PyQt5.QtCore import QThread, pyqtSignal

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    done_signal = pyqtSignal(bool)
    progress_signal = pyqtSignal(int)  # Emit progress value (episode count or percentage)
    
    def __init__(self, cmd, total_episodes=None):
        super().__init__()
        self.cmd = cmd
        self.total_episodes = total_episodes

    def run(self):
        import subprocess
        import re
        proc = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True)
        completed_episodes = set()
        for line in proc.stdout:
            self.log_signal.emit(line.rstrip())
            # Only advance progress when we see .mp4 written, 'completed', or 'finished', not just 'Downloading Episode'
            if self.total_episodes and self.total_episodes > 0:
                # Look for episode numbers on real completion (mp4 written or similar only)
                mp4_match = re.search(r'(Episode\s+)?([0-9]+)\.mp4', line)
                if mp4_match:
                    ep_num = int(mp4_match.group(2))
                    if ep_num not in completed_episodes:
                        completed_episodes.add(ep_num)
                        self.progress_signal.emit(len(completed_episodes))
                elif re.search(r'completed|finished', line, re.IGNORECASE):
                    # In ambiguous log cases, just increment
                    if len(completed_episodes) < self.total_episodes:
                        self.progress_signal.emit(len(completed_episodes) + 1)
        proc.wait()
        # Set progress to max when done
        if self.total_episodes and self.total_episodes > 0:
            self.progress_signal.emit(self.total_episodes)
        else:
            self.progress_signal.emit(100)
        if proc.returncode == 0:
            self.status_signal.emit("Download completed!")
            self.done_signal.emit(True)
        else:
            self.status_signal.emit("Download failed (see log)")
            self.done_signal.emit(False)

class AnimepaheGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Animepahe Downloader GUI")
        self.layout = QVBoxLayout()
        self.state_reset()

        # --- Refresh anime list ---
        self.refresh_btn = QPushButton("Refresh Anime List")
        self.refresh_btn.clicked.connect(self.refresh_anime_list)
        self.layout.addWidget(self.refresh_btn)
        self.status_label = QLabel("")
        self.layout.addWidget(self.status_label)

        # --- Session Key Selection ---
        key_box = QGroupBox("AnimePahe Session/Key Selection")
        key_box_layout = QHBoxLayout()
        self.key_mode_manual = QRadioButton("Manual")
        self.key_mode_search = QRadioButton("Search Title")
        self.key_mode_manual.setChecked(True)
        self.key_button_group = QButtonGroup()
        self.key_button_group.addButton(self.key_mode_manual)
        self.key_button_group.addButton(self.key_mode_search)
        key_box_layout.addWidget(self.key_mode_manual)
        key_box_layout.addWidget(self.key_mode_search)
        key_box.setLayout(key_box_layout)
        self.layout.addWidget(key_box)

        self.session_key_input = QLineEdit()
        self.session_key_input.setPlaceholderText("Paste/Enter session key")
        self.layout.addWidget(self.session_key_input)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter anime title keyword (for search mode)")
        self.search_input.setEnabled(False)
        self.layout.addWidget(self.search_input)
        self.search_btn = QPushButton("Search Anime")
        self.search_btn.clicked.connect(self.search_title)
        self.search_btn.setEnabled(False)
        self.layout.addWidget(self.search_btn)
        self.results_list = QListWidget()
        self.results_list.setEnabled(False)
        self.results_list.clicked.connect(self.select_searched_anime)
        self.layout.addWidget(self.results_list)

        # Switch input modes
        self.key_mode_manual.toggled.connect(self.toggle_key_mode)
        self.key_mode_search.toggled.connect(self.toggle_key_mode)

        # --- Fetch metadata ---
        self.metadata_label = QLabel()
        self.layout.addWidget(self.metadata_label)

        # --- Download Mode ---
        self.mode_box = QGroupBox("Download Mode")
        mode_box_layout = QHBoxLayout()
        self.auto_mode_radio = QRadioButton("Auto: All, Highest Res")
        self.manual_mode_radio = QRadioButton("Manual: Choose options")
        self.mode_btn_group = QButtonGroup()
        self.mode_btn_group.addButton(self.auto_mode_radio)
        self.mode_btn_group.addButton(self.manual_mode_radio)
        mode_box_layout.addWidget(self.auto_mode_radio)
        mode_box_layout.addWidget(self.manual_mode_radio)
        self.mode_box.setLayout(mode_box_layout)
        self.layout.addWidget(self.mode_box)
        self.auto_mode_radio.setChecked(True)
        self.mode_box.setEnabled(False)

        # --- Manual: Episode/Resolution ---
        self.episode_input = QLineEdit()
        self.episode_input.setPlaceholderText("e.g., 1,2,5-10 for episodes; leave blank for all episodes (default)")
        self.episode_input.setEnabled(False)
        self.layout.addWidget(self.episode_input)
        self.resolution_input = QLineEdit()
        self.resolution_input.setPlaceholderText("e.g., 720; leave blank for highest resolution (default)")
        self.resolution_input.setEnabled(False)
        self.layout.addWidget(self.resolution_input)

        self.audio_input = QLineEdit()
        self.audio_input.setPlaceholderText("e.g., jpn, eng, chi; leave blank for jpn (default)")
        self.audio_input.setEnabled(False)
        self.layout.addWidget(self.audio_input)

        # --- Download ---
        self.download_btn = QPushButton("Start Download")
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setEnabled(False)
        self.layout.addWidget(self.download_btn)

        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.layout.addWidget(self.progress_bar)

        # --- Log ---
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.layout.addWidget(self.log_output)

        self.setLayout(self.layout)

    def state_reset(self):
        self.session_key = None
        self.anime_title = None
        self.selected_line = None
        self.anime_folder = None
        self.min_ep = None
        self.max_ep = None

    def log(self, txt):
        self.log_output.append(txt)
        self.log_output.ensureCursorVisible()

    def refresh_anime_list(self):
        import os
        self.status_label.setText("[INFO] Refreshing anime list...")
        self.log("[INFO] Running animepahe-dl.sh to generate/update anime.list...")
        
        # Run animepahe-dl.sh which will generate anime.list
        # The script generates the list first, then tries to use fzf (which we can ignore)
        # We check if anime.list exists after running, regardless of return code
        proc = subprocess.run(
            ["C:\\Program Files\\Git\\bin\\bash.exe", "animepahe-dl.sh"],
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            timeout=60  # Timeout after 60 seconds if something hangs
        )
        
        # Check if anime.list was created/updated
        # Note: The script might error at fzf stage, but list is already generated by then
        if os.path.exists("anime.list"):
            # Count lines to show how many entries
            try:
                with open("anime.list", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
                self.status_label.setText(f"Anime list refreshed successfully! ({line_count} entries)")
                self.log(f"[INFO] Anime list updated with {line_count} entries!")
            except Exception as e:
                self.status_label.setText("Anime list refreshed (could not count entries)")
                self.log(f"[INFO] Anime list updated! (Error counting: {e})")
        else:
            # List wasn't created, show error
            self.status_label.setText("Error: Failed to generate anime.list")
            error_msg = proc.stderr.decode(errors='ignore') if proc.stderr else "Unknown error"
            if not error_msg.strip():
                error_msg = proc.stdout.decode(errors='ignore') if proc.stdout else "No error message available"
            self.log(f"[ERROR] Failed to refresh list: {error_msg}")

    def toggle_key_mode(self):
        if self.key_mode_manual.isChecked():
            self.session_key_input.setEnabled(True)
            self.search_input.setEnabled(False)
            self.search_btn.setEnabled(False)
            self.results_list.setEnabled(False)
        else:
            self.session_key_input.setEnabled(False)
            self.search_input.setEnabled(True)
            self.search_btn.setEnabled(True)
            self.results_list.setEnabled(True)

    def search_title(self):
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, "Missing Input", "Please enter a keyword.")
            return
        self.results_items = []   # keep (key, title, full_line) for selection
        results = []
        try:
            import re
            with open("anime.list", encoding="utf-8") as f:
                for line in f:
                    if keyword.lower() in line.lower():
                        # Format: [key] Title - extract key and title separately
                        m = re.match(r"\[([a-zA-Z0-9-]+)\]\s*(.*)", line.strip())
                        if m:
                            key = m.group(1).strip()
                            raw_title = m.group(2).strip()
                            # Only show title, never the key
                            title = raw_title if raw_title else line.strip()
                            self.results_items.append((key, title, line.strip()))
                            results.append(title)
                        else:
                            # Fallback: if regex doesn't match, show full line but try to extract key
                            fallback_key = re.search(r"\[([a-zA-Z0-9-]+)\]", line.strip())
                            if fallback_key:
                                key = fallback_key.group(1)
                                # Try to remove the key part from display
                                display = re.sub(r"\[([a-zA-Z0-9-]+)\]\s*", "", line.strip(), count=1)
                                title = display if display else line.strip()
                            else:
                                key = None
                                title = line.strip()
                            self.results_items.append((key, title, line.strip()))
                            results.append(title)
        except FileNotFoundError:
            self.status_label.setText("anime.list not found! Please refresh first.")
            return
        self.results_list.clear()
        if results:
            self.results_list.addItems(results)
            self.status_label.setText(f"Found {len(results)} results. Select one to continue.")
        else:
            self.status_label.setText("No matches found.")

    def select_searched_anime(self):
        row = self.results_list.currentRow()
        if row < 0 or not hasattr(self, 'results_items'):
            return
        entry = self.results_items[row]
        key = entry[0]
        title = entry[1]
        if not key:
            self.session_key = None
            self.status_label.setText("Failed to extract key from selection!")
        else:
            self.session_key = key
            self.selected_line = entry[2]
            self.status_label.setText(f"Selected: {title}\nSession Key: {self.session_key}")
            self.log(f"[KEY] Using extracted key: {self.session_key}")
            self.metadata_fetch()

    def metadata_fetch(self):
        import os, json, re
        if not self.session_key:
            if not self.session_key_input.text().strip():
                self.status_label.setText("Session key required.")
                return
            self.session_key = self.session_key_input.text().strip()
        self.metadata_label.setText("Fetching metadata...")
        # Determine intended folder directory for this session_key/title
        folder = None
        # Try to use the best title (from search or manual)
        if self.selected_line:
            line = self.selected_line
            m = re.match(r"\[([a-zA-Z0-9-]+)\] *(.*)", line)
            if m:
                folder_candidate = m.group(2).strip()
                # Use only safe characters for folder name
                folder_candidate = re.sub(r'[^a-zA-Z0-9 _\-\(\)\+]', '_', folder_candidate)
                if os.path.isdir(folder_candidate):
                    folder = folder_candidate
        # Otherwise, search for any existing folders matching session_key
        if not folder:
            # Use <something> directory where .source.json contains this session_key
            for d in os.listdir('.'):
                if os.path.isdir(d):
                    src = os.path.join(d, '.source.json')
                    if os.path.exists(src):
                        try:
                            with open(src, encoding="utf-8") as sf:
                                jdata = json.load(sf)
                                # check slug/key in either top-level or nested data
                                found = False
                                if 'episodes' in jdata:
                                    found = any(str(self.session_key) == str(e.get('session') or e.get('id') or '') for e in jdata['episodes'])
                                if not found and 'data' in jdata:
                                    found = any(str(self.session_key) == str(e.get('session') or e.get('id') or '') for e in jdata['data'])
                                if found:
                                    folder = d
                                    break
                        except Exception:
                            pass
        anime_folder = folder
        source_file = os.path.join(anime_folder, '.source.json') if anime_folder else None
        if anime_folder and os.path.exists(source_file):
            # Reuse present metadata
            try:
                with open(source_file, encoding="utf-8") as sf:
                    data = json.load(sf)
                    ep_field = 'episodes' if 'episodes' in data else 'data' if 'data' in data else None
                    if ep_field:
                        eps = [int(e['episode']) for e in data[ep_field] if 'episode' in e]
                        min_ep = min(eps)
                        max_ep = max(eps)
                        self.metadata_label.setText(f"Episodes available: {min_ep}-{max_ep}")
                        self.anime_folder = anime_folder
                        self.min_ep = min_ep
                        self.max_ep = max_ep
                        self.mode_box.setEnabled(True)
                        self.download_btn.setEnabled(True)
                        self.auto_mode_radio.toggled.connect(self.toggle_manual_fields)
                        self.manual_mode_radio.toggled.connect(self.toggle_manual_fields)
                        return
            except Exception as e:
                self.metadata_label.setText(f"[ERROR] Failed to parse metadata: {e}")
                self.log(f"[META] {e}")
                return
        # If we get here, metadata doesn't exist - run fetch
        proc = subprocess.run(
            ["C:\\Program Files\\Git\\bin\\bash.exe", "animepahe-dl.sh", "-s", self.session_key, "-e", "1", "-r", "360", "-o", "jpn", "-t", "1", "-l"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        # Now search for correct folder again (it should exist after fetch)
        dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('animepahe-dl')]
        dirs.sort(key=os.path.getmtime, reverse=True)
        anime_folder = None
        for d in dirs:
            src = os.path.join(d, '.source.json')
            if os.path.exists(src):
                with open(src, encoding="utf-8") as sf:
                    try:
                        jdata = json.load(sf)
                        ep_field = 'episodes' if 'episodes' in jdata else 'data' if 'data' in jdata else None
                        found = False
                        if ep_field:
                            found = any(str(self.session_key) == str(e.get('session') or e.get('id') or '') for e in jdata[ep_field])
                        if found:
                            eps = [int(e['episode']) for e in jdata[ep_field] if 'episode' in e]
                            min_ep = min(eps)
                            max_ep = max(eps)
                            self.metadata_label.setText(f"Episodes available: {min_ep}-{max_ep}")
                            self.anime_folder = d
                            self.min_ep = min_ep
                            self.max_ep = max_ep
                            self.mode_box.setEnabled(True)
                            self.download_btn.setEnabled(True)
                            self.auto_mode_radio.toggled.connect(self.toggle_manual_fields)
                            self.manual_mode_radio.toggled.connect(self.toggle_manual_fields)
                            return
                    except Exception as e:
                        continue
        self.metadata_label.setText("[ERROR] Could not find metadata folder.")
        self.log(proc.stderr.decode(errors='ignore'))

    def toggle_manual_fields(self):
        manual = self.manual_mode_radio.isChecked()
        self.episode_input.setEnabled(manual)
        self.resolution_input.setEnabled(manual)
        self.audio_input.setEnabled(manual)

    def start_download(self):
        if not self.session_key:
            if not self.session_key_input.text().strip():
                self.status_label.setText("Session key required.")
                return
            self.session_key = self.session_key_input.text().strip()
        if not self.anime_folder:
            self.metadata_fetch()
            if not self.anime_folder:
                return
        auto = self.auto_mode_radio.isChecked()
        min_ep = self.min_ep
        max_ep = self.max_ep
        if auto:
            ep_val = f"{min_ep}-{max_ep}"
            res_val = None
            audio_val = "jpn"
        else:
            ep_val = self.episode_input.text().strip() or f"{min_ep}-{max_ep}"
            res_val = self.resolution_input.text().strip()
            audio_val = self.audio_input.text().strip() or "jpn"
            valid = self.check_episode_valid(ep_val, min_ep, max_ep)
            if not valid:
                self.status_label.setText("Invalid episode list!")
                return
        self.log(f"[START] Downloading {ep_val} (res: {res_val if res_val else 'auto'}, audio: {audio_val})")
        cmd = ["C:\\Program Files\\Git\\bin\\bash.exe", "animepahe-dl.sh", "-s", str(self.session_key), "-e", ep_val, "-o", audio_val, "-t", "16"]
        if res_val:
            cmd.extend(["-r", res_val])
        
        # Calculate total episodes for progress tracking
        total_eps = self._count_episodes(ep_val, min_ep, max_ep)
        
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        if total_eps > 0:
            self.progress_bar.setMaximum(total_eps)
            self.progress_bar.setFormat("Downloading: %p% (%v/%m episodes)")
        else:
            # Indeterminate mode if we can't determine episode count
            self.progress_bar.setMaximum(0)
            self.progress_bar.setFormat("Downloading...")
        
        self.worker = DownloadWorker(cmd, total_episodes=total_eps)
        self.worker.log_signal.connect(self.log)
        self.worker.status_signal.connect(self.status_label.setText)
        self.worker.progress_signal.connect(self._update_progress)
        self.worker.done_signal.connect(self._download_finished)
        self.worker.start()

    def check_episode_valid(self, eptext, min_ep, max_ep):
        # Accepts: '1,2,3', '1-4', '3', etc.
        import re
        for part in eptext.split(','):
            part = part.strip()
            if re.match(r'^[0-9]+$', part):
                i = int(part)
                if i < min_ep or i > max_ep:
                    return False
            elif re.match(r'^[0-9]+-[0-9]+$', part):
                a, b = map(int, part.split('-'))
                if a < min_ep or b > max_ep or a > b:
                    return False
            else:
                return False
        return True

    def _count_episodes(self, eptext, min_ep, max_ep):
        """Count total number of episodes from episode string like '1,2,5-10'"""
        import re
        count = 0
        for part in eptext.split(','):
            part = part.strip()
            if re.match(r'^[0-9]+$', part):
                count += 1
            elif re.match(r'^[0-9]+-[0-9]+$', part):
                a, b = map(int, part.split('-'))
                count += (b - a + 1)
        return count

    def _update_progress(self, value):
        """Update progress bar with new value"""
        if self.progress_bar.maximum() > 0:
            # Determinate mode: value is episode count
            self.progress_bar.setValue(value)
        else:
            # Indeterminate mode: value is percentage, but we can't set it
            # The bar will pulse automatically in indeterminate mode
            pass

    def _download_finished(self, success):
        """Handle download completion"""
        self.download_btn.setEnabled(True)
        if success:
            self.progress_bar.setValue(self.progress_bar.maximum())
            self.progress_bar.setFormat("Completed: 100%")
        else:
            self.progress_bar.setFormat("Failed")
        # Keep progress bar visible for a moment, then hide after a delay
        # For now, just keep it visible so user can see final status

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AnimepaheGui()
    gui.show()
    sys.exit(app.exec_())