import sys
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QLineEdit, QListWidget, QMessageBox, QHBoxLayout,
    QRadioButton, QButtonGroup, QGroupBox,
    QProgressBar, QTableWidget, QTableWidgetItem
)
from PyQt5.QtCore import QThread, pyqtSignal

class DownloadWorker(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(str)
    done_signal = pyqtSignal(bool)
    progress_signal = pyqtSignal(int)  # Completed episode count
    episode_status_signal = pyqtSignal(int, int, str)  # row index, episode number, status text

    def __init__(self, queue_item):
        super().__init__()
        self.queue_item = queue_item

    def run(self):
        import subprocess
        audio_opt = self.queue_item.get("audio") or "jpn"
        base_cmd = [
            "C:\\Program Files\\Git\\bin\\bash.exe",
            "animepahe-dl.sh",
            "-s",
            str(self.queue_item["session_key"]),
            "-o",
            audio_opt,
            "-t",
            "16",
        ]
        if self.queue_item.get("resolution"):
            base_cmd.extend(["-r", self.queue_item["resolution"]])

        episodes = self.queue_item["episodes"]
        completed = 0
        all_success = True

        for idx, ep in enumerate(episodes):
            cmd = base_cmd + ["-e", str(ep)]
            self.episode_status_signal.emit(idx, ep, "Downloading")
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=True,
            )
            for line in proc.stdout:
                self.log_signal.emit(f"[Episode {ep}] {line.rstrip()}")
            proc.wait()

            if proc.returncode == 0:
                status = "Completed"
                completed += 1
                self.progress_signal.emit(completed)
            else:
                status = "Failed"
                all_success = False
            self.episode_status_signal.emit(idx, ep, status)

        if all_success:
            self.status_signal.emit("Download completed!")
        else:
            self.status_signal.emit("Download finished with errors.")
        self.done_signal.emit(all_success)

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

        # --- Session Key Selection (Search only) ---
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter anime title keyword")
        self.layout.addWidget(self.search_input)
        self.search_btn = QPushButton("Search Anime")
        self.search_btn.clicked.connect(self.search_title)
        self.layout.addWidget(self.search_btn)
        self.results_list = QListWidget()
        self.results_list.clicked.connect(self.select_searched_anime)
        self.layout.addWidget(self.results_list)

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
        self.auto_mode_radio.toggled.connect(self.toggle_manual_fields)
        self.manual_mode_radio.toggled.connect(self.toggle_manual_fields)

        # --- Manual: Episode/Resolution ---
        self.episode_input = QLineEdit()
        self.episode_input.setPlaceholderText("e.g., 1,2,5-10 for episodes; leave blank for all")
        self.episode_input.setEnabled(False)
        self.layout.addWidget(self.episode_input)
        self.resolution_input = QLineEdit()
        self.resolution_input.setPlaceholderText("e.g., 720; leave blank for highest resolution")
        self.resolution_input.setEnabled(False)
        self.layout.addWidget(self.resolution_input)
        self.audio_input = QLineEdit()
        self.audio_input.setPlaceholderText("e.g., eng/jpn/chi; leave blank for jpn audio")
        self.audio_input.setEnabled(False)
        self.layout.addWidget(self.audio_input)

        # --- Queue Controls ---
        queue_controls_layout = QHBoxLayout()
        self.add_queue_btn = QPushButton("Add to Queue")
        self.add_queue_btn.clicked.connect(self.add_to_queue)
        self.add_queue_btn.setEnabled(False)
        self.start_queue_btn = QPushButton("Start Queue")
        self.start_queue_btn.clicked.connect(self.start_queue_downloads)
        self.remove_queue_btn = QPushButton("Remove Selected")
        self.remove_queue_btn.clicked.connect(self.remove_selected_queue_item)
        self.clear_queue_btn = QPushButton("Clear Queue")
        self.clear_queue_btn.clicked.connect(self.clear_queue)

        queue_controls_layout.addWidget(self.add_queue_btn)
        queue_controls_layout.addWidget(self.start_queue_btn)
        queue_controls_layout.addWidget(self.remove_queue_btn)
        queue_controls_layout.addWidget(self.clear_queue_btn)

        queue_box = QGroupBox("Download Queue")
        queue_layout = QVBoxLayout()
        queue_layout.addLayout(queue_controls_layout)
        self.queue_list = QListWidget()
        queue_layout.addWidget(self.queue_list)
        self.queue_status_label = QLabel("")
        queue_layout.addWidget(self.queue_status_label)
        queue_box.setLayout(queue_layout)
        self.layout.addWidget(queue_box)

        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.layout.addWidget(self.progress_bar)

        # --- Episode progress table ---
        self.episode_table_label = QLabel("Episode Progress")
        self.layout.addWidget(self.episode_table_label)
        self.episode_table = QTableWidget(0, 3)
        self.episode_table.setHorizontalHeaderLabels(["Episode", "Status", "Details"])
        self.layout.addWidget(self.episode_table)

        self.setLayout(self.layout)

    def state_reset(self):
        self.session_key = None
        self.anime_title = None
        self.selected_line = None
        self.anime_folder = None
        self.min_ep = None
        self.max_ep = None
        self.download_queue = []
        self.queue_running = False
        self.current_queue_index = -1
        self.current_worker = None

    def log(self, txt):
        # Basic logging to console (GUI no longer shows log textbox)
        print(txt)

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
            self.anime_title = title
            self.status_label.setText(f"Selected: {title}\nSession Key: {self.session_key}")
            self.log(f"[KEY] Using extracted key: {self.session_key}")
            self.metadata_fetch()

    def metadata_fetch(self):
        import os, json, re
        if not self.session_key:
            self.status_label.setText("Select an anime from the search results first.")
            return
        self.metadata_label.setText("Fetching metadata...")
        # Determine intended folder directory for this session_key/title
        folder = None
        # Try to use the best title (from search or manual)
        if self.selected_line:
            line = self.selected_line
            m = re.match(r"\[([a-zA-Z0-9-]+)\] *(.*)", line)
            if m:
                folder_candidate = m.group(2).strip()
                # Match animepahe-dl.sh sanitization: allow spaces, commas, +, -, (, )
                folder_candidate = re.sub(r'[^a-zA-Z0-9 ,\+\-\(\)]', '_', folder_candidate)
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
                        self.add_queue_btn.setEnabled(True)
                        self.toggle_manual_fields()
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
                            self.add_queue_btn.setEnabled(True)
                            self.toggle_manual_fields()
                            self.mode_box.setEnabled(True)
                            self.add_queue_btn.setEnabled(True)
                            self.toggle_manual_fields()
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

    def _prepare_download_config(self):
        if not self.session_key:
            self.status_label.setText("Select an anime from the search results first.")
            return None
        if not self.anime_folder:
            self.metadata_fetch()
            if not self.anime_folder:
                return None
        auto = self.auto_mode_radio.isChecked()
        min_ep = self.min_ep
        max_ep = self.max_ep
        if auto:
            ep_val = f"{min_ep}-{max_ep}"
            res_val = None
            audio_val = "jpn"
            audio_val = audio_val.lower()
        else:
            ep_val = self.episode_input.text().strip() or f"{min_ep}-{max_ep}"
            res_val = self.resolution_input.text().strip()
            audio_val = (self.audio_input.text().strip() or "jpn")
            audio_val = audio_val.lower()
            valid = self.check_episode_valid(ep_val, min_ep, max_ep)
            if not valid:
                self.status_label.setText("Invalid episode list!")
                return None
        episodes = self._expand_episode_list(ep_val)
        if not episodes:
            self.status_label.setText("No valid episodes selected.")
            return None

        return {
            "title": self.anime_title or "Unknown",
            "session_key": self.session_key,
            "episodes": episodes,
            "resolution": res_val,
            "audio": audio_val,
            "episode_text": ep_val,
        }

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

    def _expand_episode_list(self, eptext):
        import re
        episodes = []
        for part in eptext.split(','):
            part = part.strip()
            if not part:
                continue
            if re.match(r'^[0-9]+$', part):
                episodes.append(int(part))
            elif re.match(r'^[0-9]+-[0-9]+$', part):
                a, b = map(int, part.split('-'))
                if a <= b:
                    episodes.extend(range(a, b + 1))
        return sorted(set(episodes))

    def add_to_queue(self):
        config = self._prepare_download_config()
        if not config:
            return
        self.download_queue.append(config)
        display_title = config["title"]
        ep_range = f"{config['episodes'][0]}-{config['episodes'][-1]}" if len(config['episodes']) > 1 else str(config['episodes'][0])
        res_text = config['resolution'] if config['resolution'] else "Auto"
        audio_text = config['audio'] if config['audio'] else "jpn"
        self.queue_list.addItem(f"{display_title} | Episodes {ep_range} | Res {res_text} | Audio {audio_text}")
        self.queue_status_label.setText(f"{len(self.download_queue)} item(s) in queue.")

    def remove_selected_queue_item(self):
        row = self.queue_list.currentRow()
        if row < 0:
            return
        if self.queue_running and row <= self.current_queue_index:
            self.status_label.setText("Cannot remove items already processed or in progress.")
            return
        self.queue_list.takeItem(row)
        del self.download_queue[row]
        self.queue_status_label.setText(f"{len(self.download_queue)} item(s) in queue.")

    def clear_queue(self):
        if self.queue_running:
            self.status_label.setText("Cannot clear queue while downloads are running.")
            return
        self.download_queue.clear()
        self.queue_list.clear()
        self.queue_status_label.setText("Queue cleared.")

    def start_queue_downloads(self):
        if not self.download_queue:
            self.status_label.setText("Queue is empty. Add items first.")
            return
        if self.queue_running:
            self.status_label.setText("Queue is already running.")
            return
        self.queue_running = True
        self.current_queue_index = 0
        self._start_queue_item()

    def _start_queue_item(self):
        if self.current_queue_index >= len(self.download_queue):
            self.queue_running = False
            self.queue_status_label.setText("All queued downloads completed.")
            self.progress_bar.setVisible(False)
            return

        item = self.download_queue[self.current_queue_index]
        self.queue_status_label.setText(
            f"Downloading {item['title']} ({self.current_queue_index + 1}/{len(self.download_queue)})"
        )
        episodes = item["episodes"]
        self._setup_episode_table(episodes)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(episodes))
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat(f"0/{len(episodes)} episodes")

        self.current_worker = DownloadWorker(item)
        self.current_worker.log_signal.connect(self.log)
        self.current_worker.status_signal.connect(self.status_label.setText)
        self.current_worker.progress_signal.connect(self._update_progress)
        self.current_worker.episode_status_signal.connect(self._update_episode_status)
        self.current_worker.done_signal.connect(self._queue_item_finished)
        self.current_worker.start()

    def _setup_episode_table(self, episodes):
        self.episode_table.setRowCount(len(episodes))
        for idx, ep in enumerate(episodes):
            self.episode_table.setItem(idx, 0, QTableWidgetItem(str(ep)))
            self.episode_table.setItem(idx, 1, QTableWidgetItem("Queued"))
            self.episode_table.setItem(idx, 2, QTableWidgetItem(""))
        self.episode_table.resizeColumnsToContents()

    def _update_episode_status(self, row, episode, status):
        if row < 0 or row >= self.episode_table.rowCount():
            return
        self.episode_table.setItem(row, 1, QTableWidgetItem(status))
        detail_text = "Idle"
        if status == "Downloading":
            detail_text = "In progress"
        elif status == "Completed":
            detail_text = "Done"
        elif status == "Failed":
            detail_text = "Check logs"
        self.episode_table.setItem(row, 2, QTableWidgetItem(detail_text))

    def _update_progress(self, value):
        """Update progress bar with new value"""
        if self.progress_bar.maximum() > 0:
            # Determinate mode: value is episode count
            self.progress_bar.setValue(value)
            total = self.progress_bar.maximum()
            self.progress_bar.setFormat(f"{value}/{total} episodes")
        else:
            # Indeterminate mode: value is percentage, but we can't set it
            # The bar will pulse automatically in indeterminate mode
            pass

    def _queue_item_finished(self, success):
        row_item = self.queue_list.item(self.current_queue_index)
        if row_item:
            status_text = " [Done]" if success else " [Errors]"
            if status_text not in row_item.text():
                row_item.setText(row_item.text() + status_text)
        self.current_queue_index += 1
        if self.current_queue_index < len(self.download_queue):
            self._start_queue_item()
        else:
            self.queue_running = False
            self.queue_status_label.setText("Queue finished.")
            self.progress_bar.setFormat("Completed")
            self.progress_bar.setValue(self.progress_bar.maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = AnimepaheGui()
    gui.show()
    sys.exit(app.exec_())