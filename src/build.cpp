#include "xdev/build.hpp"
#include "xdev/workspace.hpp"
#include "xdev/process.hpp"
#include <iostream>
#include <fstream>
#include <filesystem>
#include <string>
#include <vector>

namespace fs = std::filesystem;

namespace xdev {

int Build::execute() {
    std::cout << "[+] Starting Autonomous Discovery Build & Pack Engine...\n";

    auto ws = Workspace::locate();
    if (!ws.has_value()) {
        std::cerr << "[FAIL] Could not locate XenevaOS repository workspace.\n";
        return 1;
    }

    fs::path repo_root = ws->root_path;
    fs::current_path(repo_root);

    // 1. Ensure gnu-efi is available
    if (!fs::exists("gnu-efi")) {
        fs::path artifact_gnu_efi = fs::absolute("../xdev/artifacts/gnu-efi");
        if (fs::exists(artifact_gnu_efi)) {
            try { fs::create_directory_symlink(artifact_gnu_efi, "gnu-efi"); } 
            catch (...) { fs::copy(artifact_gnu_efi, "gnu-efi", fs::copy_options::recursive); }
        } else {
            std::cerr << "[FAIL] gnu-efi not found. Run 'xdev fetch' first.\n";
            return 1;
        }
    }

    // 2. Autonomous Makefile Discovery & Compilation
    std::cout << "[+] Sweeping workspace for Makefiles to build core & components...\n";
    
    std::vector<std::string> priority_dirs = {"Libs/XEClib", "Libs/Chitralekha", "BootAA64", "KernelAA64"};
    for (const auto& dir : priority_dirs) {
        if (fs::exists(dir + "/Makefile")) {
            std::cout << "  -> Building core component: " << dir << "\n";
            Process::run("make -C " + dir + " clean llvm");
        }
    }

    for (const auto& entry : fs::recursive_directory_iterator(".")) {
        std::string path_str = entry.path().string();
        
        if (path_str.find("gnu-efi") != std::string::npos || 
            path_str.find("Build") != std::string::npos ||
            path_str.find("CMakeFiles") != std::string::npos) {
            continue;
        }

        if (entry.path().filename() == "Makefile") {
            fs::path parent = entry.path().parent_path();
            std::string parent_str = parent.string();
            
            if (parent_str == "./BootAA64" || parent_str == "./KernelAA64" || 
                parent_str == "./Libs/XEClib" || parent_str == "./Libs/Chitralekha") {
                continue;
            }

            std::cout << "  -> Auto-building discovered target: " << parent_str << "\n";
            Process::run("make -C " + parent_str + " clean llvm");
        }
    }

    // 3. Prepare Resources Tree
    fs::create_directories("Resources/resources");

    // 4. Autonomous Binary Sweeper & Deployer (Excluding Resources folder to avoid self-copy crashes)
    std::cout << "[+] Sweeping repository for compiled .exe and .dll artifacts...\n";
    for (const auto& entry : fs::recursive_directory_iterator(".")) {
        std::string path_str = entry.path().string();
        
        // Skip scanning inside the Resources directory itself
        if (path_str.find("Resources") != std::string::npos) {
            continue;
        }

        if (entry.is_regular_file()) {
            std::string ext = entry.path().extension().string();
            if (ext == ".exe" || ext == ".dll") {
                fs::path dest = fs::path("Resources/resources") / entry.path().filename();
                fs::copy_file(entry.path(), dest, fs::copy_options::overwrite_existing);
            }
        }
    }

    // 5. Assemble initrd2.img dynamically
    std::cout << "[+] Creating FAT32 initrd2.img and packing all resources...\n";
    Process::run("dd if=/dev/zero of=initrd2.img bs=1M count=128 status=none");
    Process::run("mkfs.vfat -F 32 initrd2.img > /dev/null 2>&1");

    if (fs::exists("Resources/resources")) {
        for (const auto& entry : fs::directory_iterator("Resources/resources")) {
            Process::run("mcopy -o -s -i initrd2.img " + entry.path().string() + " ::/");
        }
    }
    
    if (fs::exists("Process/Init/init.exe")) {
        Process::run("mcopy -o -i initrd2.img Process/Init/init.exe ::/init.exe");
    }

    // 6. Assemble fat.img (ESP)
    std::cout << "[+] Creating 512MB EFI System Partition (fat.img)...\n";
    Process::run("dd if=/dev/zero of=fat.img bs=1M count=512 status=none");
    Process::run("mkfs.vfat -F 32 fat.img > /dev/null 2>&1");

    Process::run("mmd -i fat.img ::/EFI ::/EFI/BOOT ::/EFI/XENEVA");

    std::string boot_efi = "";
    std::string kernel_bin = "";

    for (const auto& entry : fs::recursive_directory_iterator(".")) {
        std::string filename = entry.path().filename().string();
        if ((filename == "BOOTAA64.efi" || filename == "BOOTAA64.EFI") && boot_efi.empty()) {
            boot_efi = entry.path().string();
        }
        if ((filename == "KernelAA64.exe" || filename == "xnkrnl.exe") && entry.file_size() > 1000 && kernel_bin.empty()) {
            kernel_bin = entry.path().string();
        }
    }

    if (boot_efi.empty() || kernel_bin.empty()) {
        std::cerr << "[FAIL] Could not locate core bootloader or kernel binaries.\n";
        return 1;
    }

    std::cout << "  -> Packaging Bootloader: " << boot_efi << "\n";
    std::cout << "  -> Packaging Kernel:     " << kernel_bin << "\n";

    Process::run("mcopy -o -i fat.img " + boot_efi + " ::/EFI/BOOT/BOOTAA64.EFI");
    Process::run("mcopy -o -i fat.img " + kernel_bin + " ::/EFI/XENEVA/xnkrnl.exe");
    Process::run("mcopy -o -i fat.img initrd2.img ::/initrd2.img");

    std::ofstream nomenu("NOMENU");
    nomenu.close();
    Process::run("mcopy -o -i fat.img NOMENU ::/NOMENU");
    fs::remove("NOMENU");

    std::cout << "\n-------------------------------------------------\n";
    std::cout << "Result: Build complete! Autonomous discovery successfully packaged everything.\n";
    return 0;
}

} // namespace xdev
