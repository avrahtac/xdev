/*
 * Copyright (c) 2026 Manas Kamal Choudhary and XenevaOS Team
 * All rights reserved.
 */

#include "installer.hpp"
#include "common.hpp"
#include <iostream>
#include <string>

namespace xdev {

    void print_bsd2_license() {
        std::cout << "=================================================================\n";
        std::cout << "               BSD 2-CLAUSE LICENSE AGREEMENT                    \n";
        std::cout << "=================================================================\n";
        std::cout << "Copyright (c) 2026, Manas Kamal Choudhary and XenevaOS Team\n";
        std::cout << "All rights reserved.\n\n";
        std::cout << "Redistribution and use in source and binary forms, with or without\n";
        std::cout << "modification, are permitted provided that the following conditions\n";
        std::cout << "are met:\n\n";
        std::cout << "1. Redistributions of source code must retain the above copyright\n";
        std::cout << "   notice, this list of conditions and the following disclaimer.\n";
        std::cout << "2. Redistributions in binary form must reproduce the above copyright\n";
        std::cout << "   notice, this list of conditions and the following disclaimer in\n";
        std::cout << "   the documentation and/or other materials provided with the\n";
        std::cout << "   distribution.\n\n";
        std::cout << "THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS\n";
        std::cout << "\"AS IS\" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT\n";
        std::cout << "LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS\n";
        std::cout << "FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE\n";
        std::cout << "COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,\n";
        std::cout << "INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,\n";
        std::cout << "BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;\n";
        std::cout << "LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER\n";
        std::cout << "CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT\n";
        std::cout << "LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN\n";
        std::cout << "ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE\n";
        std::cout << "POSSIBILITY OF SUCH DAMAGE.\n";
        std::cout << "=================================================================\n\n";
    }

    bool Installer::run_installer() {
        print_bsd2_license();

        std::string response;
        std::cout << "Do you accept the terms of the BSD 2-Clause License? [y/N]: ";
        std::getline(std::cin, response);

        if (response != "y" && response != "Y" && response != "yes" && response != "YES") {
            log_error("License agreement declined. Installation aborted.");
            return false;
        }

        log_info("License accepted. Proceeding with installation...");

#if defined(_WIN32) || defined(_WIN64)
        if (execute("winget --version >nul 2>&1") != 0) {
            log_error("winget is required but not found.");
            return false;
        }

        if (execute("git --version >nul 2>&1") != 0) {
            log_info("Installing Git...");
            execute("winget install --id Git.Git -e --silent --accept-package-agreements");
        }

        if (!fs::exists("C:\\msys64")) {
            log_info("Installing MSYS2...");
            execute("winget install --id MSYS2.MSYS2 -e --silent --accept-package-agreements");
        }

        log_info("Configuring toolchain packages...");
        std::string pacman_cmd = "C:\\msys64\\usr\\bin\\bash.exe -lc \"pacman -Syu --noconfirm && pacman -S --noconfirm mingw-w64-ucrt64-clang mingw-w64-ucrt64-lld make qemu dosfstools mtools\"";
        if (execute(pacman_cmd) != 0) {
            log_error("Failed to install toolchain packages through pacman.");
            return false;
        }

        log_info("Windows installation completed successfully!");
#else
        fs::create_directories(fs::path(std::getenv("HOME")) / ".local" / "bin");
        if (fs::exists("xdev")) {
            fs::copy_file("xdev", fs::path(std::getenv("HOME")) / ".local" / "bin" / "xdev", fs::copy_options::overwrite_existing);
            execute("chmod +x ~/.local/bin/xdev");
            log_info("Installed to ~/.local/bin/xdev!");
        } else {
            log_warn("Compiled 'xdev' binary not found. Run 'make' first.");
        }
#endif

        return true;
    }
}