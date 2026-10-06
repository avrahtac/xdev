
import os
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox

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


class XdevSetupWizard:
    def __init__(self, root):
        self.root = root
        self.root.title("XenevaOS xdev Setup")
        self.root.geometry("580x500")
        self.root.resizable(False, False)

        self.ui_queue = queue.Queue()

        # Apply Windows system style
        style = ttk.Style()
        style.theme_use("vista")

        # Top Header Banner
        header_frame = tk.Frame(root, bg="#ffffff", height=60)
        header_frame.pack(fill="x", side="top")
        
        title_lbl = tk.Label(
            header_frame, 
            text="XenevaOS Toolchain Setup", 
            font=("Segoe UI", 12, "bold"), 
            bg="#ffffff", 
            anchor="w"
        )
        title_lbl.pack(padx=20, pady=(10, 2), fill="x")
        
        subtitle_lbl = tk.Label(
            header_frame, 
            text="Please read the following license agreement before installing xdev.", 
            font=("Segoe UI", 8), 
            bg="#ffffff", 
            anchor="w"
        )
        subtitle_lbl.pack(padx=20, pady=(0, 10), fill="x")

        divider1 = ttk.Separator(root, orient="horizontal")
        divider1.pack(fill="x")

        # License Text Frame
        content_frame = ttk.Frame(root)
        content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        license_box = tk.Text(content_frame, wrap="word", font=("Consolas", 8), height=14)
        license_box.insert("1.0", LICENSE_TEXT)
        license_box.config(state="disabled")

        scrollbar = ttk.Scrollbar(content_frame, command=license_box.yview)
        license_box.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        license_box.pack(side="left", fill="both", expand=True)

        # Agreement Checkbox
        self.agree_var = tk.BooleanVar()
        self.agree_check = ttk.Checkbutton(
            root,
            text="I accept the terms in the License Agreement",
            variable=self.agree_var,
            command=self.on_checkbox_toggle
        )
        self.agree_check.pack(anchor="w", padx=20, pady=(0, 5))

        # Progress Status & Bar
        self.status_lbl = ttk.Label(root, text="Click Install to begin setup.", font=("Segoe UI", 8))
        self.status_lbl.pack(anchor="w", padx=20, pady=(5, 2))

        self.progress_bar = ttk.Progressbar(root, orient="horizontal", length=540, mode="determinate")
        self.progress_bar.pack(padx=20, pady=(0, 10))

        divider2 = ttk.Separator(root, orient="horizontal")
        divider2.pack(fill="x")

        # Bottom Button Bar
        bottom_frame = ttk.Frame(root)
        bottom_frame.pack(fill="x", side="bottom", pady=12, padx=20)

        self.install_btn = ttk.Button(bottom_frame, text="Install", state="disabled", command=self.start_install)
        self.install_btn.pack(side="right", padx=5)

        self.cancel_btn = ttk.Button(bottom_frame, text="Cancel", command=root.quit)
        self.cancel_btn.pack(side="right", padx=5)

        self.root.after(100, self.process_queue)

    def on_checkbox_toggle(self):
        if self.agree_var.get():
            self.install_btn.config(state="normal")
        else:
            self.install_btn.config(state="disabled")

    def start_install(self):
        self.install_btn.config(state="disabled")
        self.agree_check.config(state="disabled")
        threading.Thread(target=self.run_setup, daemon=True).start()

    def process_queue(self):
        try:
            while True:
                msg_type, val, text = self.ui_queue.get_nowait()
                if msg_type == "PROGRESS":
                    self.progress_bar['value'] = val
                    self.status_lbl.config(text=text)
                elif msg_type == "COMPLETE":
                    self.progress_bar['value'] = 100
                    self.status_lbl.config(text="Installation finished successfully.")
                    messagebox.showinfo("Setup", "XenevaOS toolchain setup completed successfully!")
                    self.root.quit()
                elif msg_type == "ERROR":
                    self.status_lbl.config(text="Setup failed.")
                    messagebox.showerror("Setup Error", f"Installation failed:\n{text}")
                    self.install_btn.config(state="normal")
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def run_setup(self):
        try:
            # 1. Check Winget
            self.ui_queue.put(("PROGRESS", 15, "Checking winget availability..."))
            subprocess.run(["winget", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 2. Check / Install Git
            self.ui_queue.put(("PROGRESS", 35, "Ensuring Git is installed..."))
            subprocess.run("winget install --id Git.Git -e --silent --accept-package-agreements", shell=True)

            # 3. Check / Install MSYS2
            self.ui_queue.put(("PROGRESS", 55, "Ensuring MSYS2 environment exists..."))
            if not os.path.exists(r"C:\msys64"):
                subprocess.run("winget install --id MSYS2.MSYS2 -e --silent --accept-package-agreements", shell=True)

            # 4. Install toolchain via pacman
            self.ui_queue.put(("PROGRESS", 80, "Installing Clang, LLD, QEMU, dosfstools, mtools..."))
            pacman_cmd = r'C:\msys64\usr\bin\bash.exe -lc "pacman -S --needed --noconfirm mingw-w64-ucrt64-clang mingw-w64-ucrt64-lld make qemu dosfstools mtools"'
            subprocess.run(pacman_cmd, shell=True, check=True)

            self.ui_queue.put(("COMPLETE", 100, "Done"))

        except Exception as e:
            self.ui_queue.put(("ERROR", 0, str(e)))


if __name__ == "__main__":
    root = tk.Tk()
    app = XdevSetupWizard(root)
    root.mainloop()