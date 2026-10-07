#
# Copyright (c) 2026 Manas Kamal Choudhary and XenevaOS Team
# All rights reserved.
#

import sys
import os
import subprocess
import threading
import queue
import ctypes
import shutil
import time
import tkinter as tk
from tkinter import filedialog, messagebox

# --- UAC Elevation ---
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_and_elevate():
    if not is_admin():
        params = " ".join([f'"{arg}"' for arg in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        sys.exit()

LICENSE_TEXT = """BSD 2-CLAUSE LICENSE AGREEMENT

Copyright (c) 2026, Manas Kamal Choudhary and XenevaOS Team
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

# --- Modern UI Theme Colors ---
BG_MAIN = "#1e1e1e"
BG_SIDEBAR = "#252526"
ACCENT = "#0078D4"
ACCENT_HOVER = "#005A9E"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#cccccc"
BG_INPUT = "#333333"

# Winget "No update available / already installed" exit codes
WINGET_NO_UPDATE_CODES = {0, 2316632107, -1978236885, 0x8A15002B}

class XdevSetupWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("XenevaOS Setup")
        self.root.geometry("720x580")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_MAIN)

        self.ui_queue = queue.Queue()
        self.repo_path = tk.StringVar()
        self.current_step = 1

        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=BG_SIDEBAR, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="XenevaOS", font=("Segoe UI", 16, "bold"), bg=BG_SIDEBAR, fg=TEXT_PRIMARY).pack(pady=(20, 5), anchor="w", padx=20)
        tk.Label(self.sidebar, text="Toolchain Setup", font=("Segoe UI", 10), bg=BG_SIDEBAR, fg=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 30))

        self.step_labels = []
        steps = ["1. License Agreement", "2. Repository Path", "3. Installation"]
        for step in steps:
            lbl = tk.Label(self.sidebar, text=step, font=("Segoe UI", 10), bg=BG_SIDEBAR, fg="#555555")
            lbl.pack(anchor="w", padx=20, pady=10)
            self.step_labels.append(lbl)

        # Main Content Container
        self.container = tk.Frame(self.root, bg=BG_MAIN)
        self.container.pack(side="right", fill="both", expand=True)

        self.frames = {}
        for F in (LicensePage, DirectoryPage, InstallPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.update_sidebar(0)
        self.show_frame("LicensePage")
        self.root.after(50, self.process_queue)

    def update_sidebar(self, active_index):
        for i, lbl in enumerate(self.step_labels):
            if i == active_index:
                lbl.config(fg=TEXT_PRIMARY, font=("Segoe UI", 10, "bold"))
            elif i < active_index:
                lbl.config(fg=TEXT_SECONDARY, font=("Segoe UI", 10))
            else:
                lbl.config(fg="#555555", font=("Segoe UI", 10))

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def create_button(self, parent, text, command, is_primary=True):
        bg_color = ACCENT if is_primary else BG_INPUT
        hover_color = ACCENT_HOVER if is_primary else "#444444"
        
        btn = tk.Button(parent, text=text, command=command, bg=bg_color, fg=TEXT_PRIMARY, 
                        activebackground=hover_color, activeforeground=TEXT_PRIMARY,
                        relief="flat", font=("Segoe UI", 9, "bold"), padx=20, pady=6, cursor="hand2")
        
        btn.bind("<Enter>", lambda e, b=btn, c=hover_color: b.config(bg=c) if b['state'] == 'normal' else None)
        btn.bind("<Leave>", lambda e, b=btn, c=bg_color: b.config(bg=c) if b['state'] == 'normal' else None)
        return btn

    def set_button_state(self, btn, state, is_primary=True):
        if state == "disabled":
            btn.config(state="disabled", bg="#333333", fg="#777777", cursor="arrow")
        else:
            btn.config(state="normal", bg=ACCENT if is_primary else BG_INPUT, fg=TEXT_PRIMARY, cursor="hand2")

    def start_install(self):
        self.update_sidebar(2)
        self.show_frame("InstallPage")
        threading.Thread(target=self.run_setup, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                msg_type, status, text = self.ui_queue.get_nowait()
                install_page = self.frames["InstallPage"]
                
                if msg_type == "STATUS":
                    install_page.status_lbl.config(text=status)
                
                elif msg_type == "LOG":
                    install_page.log_area.config(state="normal")
                    install_page.log_area.insert("end", text)
                    install_page.log_area.see("end")
                    install_page.log_area.config(state="disabled")

                elif msg_type == "COMPLETE":
                    install_page.status_lbl.config(text="Installation finished successfully.", fg="#4caf50")
                    messagebox.showinfo("Success", f"XenevaOS toolchain setup is complete!\n\nRepository linked to:\n{self.repo_path.get()}")
                    self.root.quit()
                
                elif msg_type == "ERROR":
                    install_page.status_lbl.config(text="Setup failed.", fg="#f44336")
                    messagebox.showerror("Error", "Installation failed. Please check the terminal logs.")
        except queue.Empty:
            pass
        self.root.after(50, self.process_queue)

    def check_c_drive_space(self, min_gb=5.0):
        """Verify whether C drive free disk space is greater than min_gb."""
        target_path = "C:\\" if os.name == 'nt' else "/"
        try:
            total, used, free = shutil.disk_usage(target_path)
            free_gb = free / (1024 ** 3)
            return free_gb > min_gb, free_gb
        except Exception as e:
            self.ui_queue.put(("LOG", None, f"> [WARN] Disk space check error: {e}. Assuming space is sufficient.\n"))
            return True, min_gb + 1.0

    def execute_command(self, cmd_str, status_msg, stream=True, allowed_exit_codes=None, timeout=None):
        if allowed_exit_codes is None:
            allowed_exit_codes = {0}

        self.ui_queue.put(("STATUS", status_msg, None))
        self.ui_queue.put(("LOG", None, f"\n[{status_msg}]\n> {cmd_str}\n"))
        
        if not stream:
            try:
                result = subprocess.run(
                    cmd_str, shell=True, capture_output=True, text=True, 
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                    timeout=timeout
                )
                if result.returncode not in allowed_exit_codes:
                    self.ui_queue.put(("LOG", None, f"[ERROR] {result.stderr}\n"))
                    raise subprocess.CalledProcessError(result.returncode, cmd_str)
                self.ui_queue.put(("LOG", None, f"{result.stdout}\n"))
                return
            except subprocess.TimeoutExpired as te:
                self.ui_queue.put(("LOG", None, f"\n[TIMEOUT] Command timed out after {timeout} seconds: {cmd_str}\n"))
                raise te

        process = subprocess.Popen(
            cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
            text=True, creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )
        
        if timeout is not None:
            start_time = time.time()
            out_queue = queue.Queue()

            def reader():
                try:
                    for line in iter(process.stdout.readline, ''):
                        out_queue.put(line)
                finally:
                    process.stdout.close()

            reader_thread = threading.Thread(target=reader, daemon=True)
            reader_thread.start()

            while reader_thread.is_alive() or not out_queue.empty():
                try:
                    line = out_queue.get(timeout=0.1)
                    self.ui_queue.put(("LOG", None, line))
                except queue.Empty:
                    pass

                if time.time() - start_time > timeout:
                    process.kill()
                    process.wait()
                    self.ui_queue.put(("LOG", None, f"\n[TIMEOUT] Command timed out after {timeout} seconds: {cmd_str}\n"))
                    raise subprocess.TimeoutExpired(cmd_str, timeout)

            process.wait()
        else:
            for line in process.stdout:
                self.ui_queue.put(("LOG", None, line))
            process.wait()

        if process.returncode not in allowed_exit_codes:
            self.ui_queue.put(("LOG", None, f"\n[ERROR] Exited with code {process.returncode}\n"))
            raise subprocess.CalledProcessError(process.returncode, cmd_str)

        # Before running pacman commands, update pacman.conf to ignore core runtime locks and mirror timeouts
    

    def init_pacman_keys_and_sync(self, max_retries=3, timeout_seconds=120):
        """
        Initializes pacman keyring and synchronizes package repositories,
        handling potential network timeouts gracefully with retries and fallback.
        """
        bash_bin = r"C:\msys64\usr\bin\bash.exe"
        if not os.path.exists(bash_bin):
            bash_bin = "bash"

        # 1. Local Key Initialization & Population
        self.ui_queue.put(("STATUS", "Initializing pacman local keyring...", None))
        cmd_keys = f'{bash_bin} -lc "pacman-key --init && pacman-key --populate msys2"'
        try:
            self.execute_command(
                cmd_keys,
                "Initializing pacman local keys...",
                stream=True,
                timeout=timeout_seconds
            )
        except subprocess.TimeoutExpired:
            self.ui_queue.put(("LOG", None, "> [WARN] pacman-key initialization timed out; continuing with existing keyring...\n"))
        except subprocess.CalledProcessError as e:
            self.ui_queue.put(("LOG", None, f"> [WARN] pacman-key finished with code {e.returncode}. Continuing with repository sync...\n"))

        # 2. Repository Synchronization with graceful retry on network timeouts
        cmd_sync = f'{bash_bin} -lc "pacman -Sy --noconfirm"'
        synced = False
        for attempt in range(1, max_retries + 1):
            try:
                status_msg = f"Syncing MSYS2 repositories (attempt {attempt}/{max_retries})..."
                self.execute_command(
                    cmd_sync,
                    status_msg,
                    stream=True,
                    timeout=timeout_seconds
                )
                synced = True
                self.ui_queue.put(("LOG", None, "> MSYS2 repository sync completed successfully.\n"))
                break
            except subprocess.TimeoutExpired:
                self.ui_queue.put(("LOG", None, f"> [WARN] Network timeout occurred during repository sync on attempt {attempt}/{max_retries}.\n"))
                if attempt < max_retries:
                    self.ui_queue.put(("LOG", None, "> Retrying repository sync in 3 seconds...\n"))
                    time.sleep(3)
                else:
                    self.ui_queue.put(("LOG", None, "> [WARN] All repository sync attempts timed out due to network issues.\n"))
                    self.ui_queue.put(("LOG", None, "> Attempting to proceed with cached package databases...\n"))
            except subprocess.CalledProcessError as cpe:
                self.ui_queue.put(("LOG", None, f"> [WARN] Sync command returned code {cpe.returncode} on attempt {attempt}/{max_retries}.\n"))
                if attempt < max_retries:
                    time.sleep(3)
                else:
                    self.ui_queue.put(("LOG", None, "> [WARN] Proceeding with existing package databases.\n"))

    def run_setup(self):
        try:
            # 1. Permanent Installation Directory
            target_install_dir = r"C:\Program Files\xdev"
            os.makedirs(target_install_dir, exist_ok=True)

            self.ui_queue.put(("STATUS", "Deploying xdev CLI binaries...", None))
            self.ui_queue.put(("LOG", None, f"\n[Installing xdev to {target_install_dir}]\n"))

            # 2. Deploy xdev.exe to C:\Program Files\xdev\
            installer_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            src_xdev = os.path.join(installer_dir, "xdev.exe")
            dst_xdev = os.path.join(target_install_dir, "xdev.exe")

            if os.path.exists(src_xdev):
                shutil.copy2(src_xdev, dst_xdev)
                self.ui_queue.put(("LOG", None, f"> Deployed xdev.exe to {dst_xdev}\n"))
            else:
                self.ui_queue.put(("LOG", None, f"> Note: xdev.exe not found at {src_xdev}.\n"))

            # 3. Configure Repository Environment Variable
            cmd_setx = f'setx XENEVA_PROJECT "{self.repo_path.get()}"'
            self.execute_command(cmd_setx, "Configuring XENEVA_PROJECT environment variable...", stream=False)

            # 4. Register Path via winreg to prevent 1024-char corruption and force global recognition
            self.ui_queue.put(("STATUS", "Configuring System PATH environment variables...", None))
            msys_bin = r"C:\msys64\ucrt64\bin"

            import winreg
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_ALL_ACCESS)
            try:
                user_path, _ = winreg.QueryValueEx(reg_key, "Path")
            except FileNotFoundError:
                user_path = ""

            path_additions = []
            if target_install_dir.lower() not in user_path.lower():
                path_additions.append(target_install_dir)
            if msys_bin.lower() not in user_path.lower():
                path_additions.append(msys_bin)

            if path_additions:
                new_user_path = user_path.rstrip(';') + ';' + ';'.join(path_additions) if user_path else ';'.join(path_additions)
                winreg.SetValueEx(reg_key, "Path", 0, winreg.REG_EXPAND_SZ, new_user_path)
                winreg.CloseKey(reg_key)

                # Broadcast system setting change to Explorer & Windows Shells
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                SMTO_ABORTIFHUNG = 0x0002
                result = ctypes.c_ulong()
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 
                    SMTO_ABORTIFHUNG, 2000, ctypes.byref(result)
                )
                self.ui_queue.put(("LOG", None, f"> Added to System PATH: {', '.join(path_additions)}\n"))
            else:
                winreg.CloseKey(reg_key)
                self.ui_queue.put(("LOG", None, "> System PATH entries already present.\n"))

            # 5. Git Check / Install
            cmd_git = "winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity"
            self.execute_command(
                cmd_git, 
                "Ensuring Git is installed...", 
                stream=True, 
                allowed_exit_codes=WINGET_NO_UPDATE_CODES
            )

            # 5b. Pre-check C: Drive Disk Space (> 5 GB required) before MSYS2 download
            self.ui_queue.put(("STATUS", "Verifying C: drive available disk space...", None))
            has_space, free_gb = self.check_c_drive_space(min_gb=5.0)
            if not has_space:
                err_msg = f"Insufficient disk space on C: drive: {free_gb:.2f} GB available, >5.0 GB required."
                self.ui_queue.put(("STATUS", "Setup aborted: Insufficient disk space on C: drive.", None))
                self.ui_queue.put(("LOG", None, f"\n[ERROR] {err_msg}\n"))
                raise RuntimeError(err_msg)
            else:
                self.ui_queue.put(("LOG", None, f"> Disk space pre-check passed: {free_gb:.2f} GB free on C: drive (>5 GB required).\n"))

            # 6. MSYS2 Check / Install
            if not os.path.exists(r"C:\msys64"):
                cmd_msys = "winget install --id MSYS2.MSYS2 -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity"
                self.execute_command(
                    cmd_msys, 
                    "Installing MSYS2...", 
                    stream=True, 
                    allowed_exit_codes=WINGET_NO_UPDATE_CODES
                )
            else:
                self.ui_queue.put(("LOG", None, "> MSYS2 found at C:\\msys64. Skipping Winget install.\n"))

            # 7. Pacman Keys & Repository Synchronization (handles potential network timeouts)
            self.init_pacman_keys_and_sync(max_retries=3, timeout_seconds=120)

            # 8. Toolchain Install
            cmd_tools = r'C:\msys64\usr\bin\bash.exe -lc "pacman -Syu --needed --noconfirm mingw-w64-ucrt-x86_64-clang mingw-w64-ucrt-x86_64-lld mingw-w64-ucrt-x86_64-qemu mingw-w64-ucrt-x86_64-mtools make dosfstools"'
            self.execute_command(cmd_tools, "Installing Toolchain (Clang, LLD, QEMU, mtools)...", stream=True)

            self.ui_queue.put(("COMPLETE", None, None))
        except Exception:
            self.ui_queue.put(("ERROR", None, None))
    
class LicensePage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_MAIN)
        self.controller = controller

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)

        tk.Label(self, text="License Agreement", font=("Segoe UI", 16, "bold"), bg=BG_MAIN, fg=TEXT_PRIMARY).grid(
            row=0, column=0, sticky="w", padx=25, pady=(20, 10)
        )

        text_frame = tk.Frame(self, bg=BG_INPUT)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=5)

        license_box = tk.Text(text_frame, wrap="word", font=("Consolas", 8), bg=BG_INPUT, fg=TEXT_SECONDARY, relief="flat", padx=10, pady=10)
        license_box.insert("1.0", LICENSE_TEXT)
        license_box.config(state="disabled")

        scrollbar = tk.Scrollbar(text_frame, command=license_box.yview, bg=BG_INPUT)
        license_box.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        license_box.pack(side="left", fill="both", expand=True)

        footer_frame = tk.Frame(self, bg=BG_MAIN)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=20)

        self.agree_var = tk.IntVar(value=0)
        self.agree_check = tk.Checkbutton(
            footer_frame, text="I accept the agreement", variable=self.agree_var, command=self.toggle_next, 
            bg=BG_MAIN, fg=TEXT_PRIMARY, selectcolor=BG_INPUT, activebackground=BG_MAIN, activeforeground=TEXT_PRIMARY, font=("Segoe UI", 10)
        )
        self.agree_check.pack(side="left", anchor="w")

        self.next_btn = controller.create_button(footer_frame, "Next", lambda: [controller.update_sidebar(1), controller.show_frame("DirectoryPage")])
        self.next_btn.pack(side="right")
        self.controller.set_button_state(self.next_btn, "disabled")

    def toggle_next(self):
        if self.agree_var.get() == 1:
            self.controller.set_button_state(self.next_btn, "normal")
        else:
            self.controller.set_button_state(self.next_btn, "disabled")


class DirectoryPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_MAIN)
        self.controller = controller

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self.columnconfigure(0, weight=1)

        tk.Label(self, text="Repository Location", font=("Segoe UI", 16, "bold"), bg=BG_MAIN, fg=TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=25, pady=(20, 10))

        content_frame = tk.Frame(self, bg=BG_MAIN)
        content_frame.grid(row=1, column=0, sticky="nw", padx=25, pady=10)

        tk.Label(content_frame, text="Select the directory where your XenevaOS source code is located.\nThis path is required to configure the build environment.", 
                 font=("Segoe UI", 10), bg=BG_MAIN, fg=TEXT_SECONDARY, justify="left").pack(anchor="w", pady=(0, 20))

        dir_frame = tk.Frame(content_frame, bg=BG_MAIN)
        dir_frame.pack(fill="x", expand=True)

        self.path_entry = tk.Entry(dir_frame, textvariable=self.controller.repo_path, font=("Segoe UI", 10), bg=BG_INPUT, fg=TEXT_PRIMARY, relief="flat", width=35)
        self.path_entry.pack(side="left", ipady=5, padx=(0, 10))

        browse_btn = controller.create_button(dir_frame, "Browse...", self.browse_dir, is_primary=False)
        browse_btn.pack(side="left")

        footer_frame = tk.Frame(self, bg=BG_MAIN)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=25, pady=20)

        back_btn = controller.create_button(footer_frame, "Back", lambda: [controller.update_sidebar(0), controller.show_frame("LicensePage")], is_primary=False)
        back_btn.pack(side="left")

        self.install_btn = controller.create_button(footer_frame, "Install", self.controller.start_install)
        self.install_btn.pack(side="right")
        controller.set_button_state(self.install_btn, "disabled")

        self.controller.repo_path.trace_add("write", self.check_path)

    def browse_dir(self):
        selected_dir = filedialog.askdirectory(title="Select XenevaOS Repository")
        if selected_dir:
            self.controller.repo_path.set(selected_dir)

    def check_path(self, *args):
        self.controller.set_button_state(self.install_btn, "normal" if self.controller.repo_path.get().strip() else "disabled")


class InstallPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=BG_MAIN)
        self.controller = controller

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        tk.Label(self, text="Installing Toolchain", font=("Segoe UI", 16, "bold"), bg=BG_MAIN, fg=TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=25, pady=(20, 5))
        
        self.status_lbl = tk.Label(self, text="Preparing to install...", font=("Segoe UI", 10), bg=BG_MAIN, fg=TEXT_SECONDARY)
        self.status_lbl.grid(row=1, column=0, sticky="w", padx=25, pady=(0, 15))

        log_frame = tk.Frame(self, bg="#111111")
        log_frame.grid(row=2, column=0, sticky="nsew", padx=25, pady=(0, 25))

        self.log_area = tk.Text(log_frame, wrap="word", font=("Consolas", 9), bg="#111111", fg="#00FF00", relief="flat", padx=10, pady=10)
        self.log_area.config(state="disabled")
        self.log_area.pack(side="left", fill="both", expand=True)


if __name__ == "__main__":
    check_and_elevate()
    root = tk.Tk()
    app = XdevSetupWizard(root)
    root.mainloop()