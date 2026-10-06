#include "setup.hpp"
#include "common.hpp"

namespace xdev {
    bool Setup::run_setup() {
        log_info("Running automated system setup for XenevaOS dependencies...");

#if defined(_WIN32) || defined(_WIN64)
        // Windows: Run pacman inside MSYS2 UCRT64 environment
        std::string cmd = "C:\\msys64\\usr\\bin\\bash.exe -lc \"pacman -S --needed --noconfirm mingw-w64-ucrt64-clang mingw-w64-ucrt64-lld make qemu dosfstools mtools\"";
        return execute(cmd) == 0;
#elif defined(__linux__)
        // Linux: Detect package manager dynamically
        if (fs::exists("/usr/bin/apt") || fs::exists("/bin/apt")) {
            log_info("Detected Debian/Ubuntu (apt). Installing dependencies...");
            std::string cmd = "sudo apt update && sudo apt install -y clang lld make qemu-system-arm dosfstools mtools gnu-efi";
            return execute(cmd) == 0;
        } else if (fs::exists("/usr/bin/dnf") || fs::exists("/bin/dnf")) {
            log_info("Detected Fedora/RHEL (dnf). Installing dependencies...");
            std::string cmd = "sudo dnf install -y clang lld make qemu-system-aarch64 dosfstools mtools gnu-efi-devel";
            return execute(cmd) == 0;
        } else if (fs::exists("/usr/bin/pacman") || fs::exists("/bin/pacman")) {
            log_info("Detected Arch Linux (pacman). Installing dependencies...");
            std::string cmd = "sudo pacman -S --needed clang lld make qemu-full dosfstools mtools gnu-efi";
            return execute(cmd) == 0;
        } else {
            log_error("Unsupported Linux package manager. Please install Clang, LLD, QEMU, dosfstools, mtools, and gnu-efi manually.");
            return false;
        }
#else
        log_error("Unsupported platform for automated setup.");
        return false;
#endif
    }
}