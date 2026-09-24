#include "xdev/fetch.hpp"
#include "xdev/process.hpp"
#include <iostream>
#include <filesystem>

namespace fs = std::filesystem;

namespace xdev {

bool Fetch::download_file(const std::string& url, const std::string& destination) {
    if (fs::exists(destination) && fs::file_size(destination) > 0) {
        std::cout << "  [ OK ] Already cached: " << destination << "\n";
        return true;
    }

    std::cout << "  [DOWNLOADING] " << url << "\n";
    std::string cmd = "curl -L --fail --create-dirs -o \"" + destination + "\" \"" + url + "\"";
    
    int code = Process::run_interactive(cmd);
    if (code == 0 && fs::exists(destination) && fs::file_size(destination) > 0) {
        std::cout << "  [ OK ] Saved to " << destination << "\n";
        return true;
    }

    std::cerr << "  [FAIL] Failed to download: " << url << "\n";
    return false;
}

int Fetch::execute() {
    std::cout << "xdev Fetch - Ecosystem Artifact Manager\n";
    std::cout << "----------------------------------------\n";

    // 1. Establish cache directory
    std::string artifact_dir = "artifacts";
    try {
        fs::create_directories(artifact_dir);
    } catch (const std::exception& e) {
        std::cerr << "Error creating artifacts directory: " << e.what() << "\n";
        return 1;
    }

    bool success = true;

    // 2. Fetch official Alpha 0.2 initrd ramdisk
    std::string initrd_url = "https://github.com/manaskamal/XenevaOS/releases/download/xenevaos-ui-alpha-0.2/initrd3.img";
    std::string initrd_dest = artifact_dir + "/initrd3.img";
    if (!download_file(initrd_url, initrd_dest)) {
        success = false;
    }

    // 3. Fetch gnu-efi repository if developer environment
    if (!fs::exists("artifacts/gnu-efi")) {
        std::cout << "  [CLONING] gnu-efi headers into " << artifact_dir << "/gnu-efi...\n";
        int res = Process::run_interactive("git clone --depth 1 https://github.com/vathpela/gnu-efi.git artifacts/gnu-efi");
        if (res != 0) {
            std::cerr << "  [WARN] Failed to clone gnu-efi headers.\n";
        }
    } else {
        std::cout << "  [ OK ] Already cached: " << artifact_dir << "/gnu-efi\n";
    }

    std::cout << "----------------------------------------\n";
    if (success) {
        std::cout << "Result: All target artifacts fetched and ready.\n";
        return 0;
    } else {
        std::cerr << "Result: One or more artifacts failed to download.\n";
        return 1;
    }
}

} // namespace xdev