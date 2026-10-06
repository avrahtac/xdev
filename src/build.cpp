#include "build.hpp"
#include "common.hpp"
#include <fstream>
#include <vector>

namespace xdev {
    bool Build::run_build() {
        log_info("Starting Autonomous Discovery Build & Pack Engine...");

        fs::path repo_root = get_xeneva_root();
        if (repo_root.empty() || !fs::exists(repo_root)) {
            log_error("XENEVA_PROJECT environment variable is missing or invalid. Run 'xdev doctor' first.");
            return false;
        }

        fs::current_path(repo_root);

        // 1. Ensure gnu-efi is available
        if (!fs::exists("gnu-efi")) {
            fs::path artifact_gnu_efi = repo_root.parent_path() / "xdev" / "artifacts" / "gnu-efi";
            if (fs::exists(artifact_gnu_efi)) {
                try {
                    fs::create_directory_symlink(artifact_gnu_efi, "gnu-efi");
                } catch (...) {
                    fs::copy(artifact_gnu_efi, "gnu-efi", fs::copy_options::recursive);
                }
            } else {
                log_warn("gnu-efi folder not found locally. Ensure 'xdev fetch' was run or gnu-efi is cloned.");
            }
        }

        // 2. Autonomous Makefile Discovery & Compilation
        log_info("Sweeping workspace for Makefiles to build core & components...");
        
        std::vector<std::string> priority_dirs = {"Libs/XEClib", "Libs/Chitralekha", "BootAA64", "KernelAA64"};
        for (const auto& dir : priority_dirs) {
            if (fs::exists(dir + "/Makefile")) {
                log_info(" -> Building core component: " + dir);
#if defined(_WIN32) || defined(_WIN64)
                std::string cmd = "C:\\msys64\\usr\\bin\\bash.exe -lc \"export PATH=/ucrt64/bin:/usr/bin:$PATH && make -C " + dir + " clean llvm\"";
#else
                std::string cmd = "make -C " + dir + " clean llvm";
#endif
                if (execute(cmd) != 0) {
                    log_error("Failed to build priority component: " + dir);
                    return false;
                }
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

                log_info(" -> Auto-building discovered target: " + parent_str);
#if defined(_WIN32) || defined(_WIN64)
                std::string cmd = "C:\\msys64\\usr\\bin\\bash.exe -lc \"export PATH=/ucrt64/bin:/usr/bin:$PATH && make -C " + parent_str + " clean llvm\"";
#else
                std::string cmd = "make -C " + parent_str + " clean llvm";
#endif
                execute(cmd);
            }
        }

        // 3. Prepare Resources Tree
        fs::create_directories("Resources/resources");

        // 4. Autonomous Binary Sweeper & Deployer
        log_info("Sweeping repository for compiled .exe and .dll artifacts...");
        for (const auto& entry : fs::recursive_directory_iterator(".")) {
            std::string path_str = entry.path().string();
            
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
        log_info("Creating FAT32 initrd2.img and packing all resources...");
        execute("dd if=/dev/zero of=initrd2.img bs=1M count=128 status=none");
        execute("mkfs.vfat -F 32 initrd2.img > /dev/null 2>&1");

        if (fs::exists("Resources/resources")) {
            for (const auto& entry : fs::directory_iterator("Resources/resources")) {
                execute("mcopy -o -s -i initrd2.img " + entry.path().string() + " ::/");
            }
        }
        
        if (fs::exists("Process/Init/init.exe")) {
            execute("mcopy -o -i initrd2.img Process/Init/init.exe ::/init.exe");
        }

        // 6. Assemble fat.img (ESP)
        log_info("Creating 512MB EFI System Partition (fat.img)...");
        execute("dd if=/dev/zero of=fat.img bs=1M count=512 status=none");
        execute("mkfs.vfat -F 32 fat.img > /dev/null 2>&1");
        execute("mmd -i fat.img ::/EFI ::/EFI/BOOT ::/EFI/XENEVA");

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
            log_error("Could not locate core bootloader or kernel binaries.");
            return false;
        }

        log_info(" -> Packaging Bootloader: " + boot_efi);
        log_info(" -> Packaging Kernel: " + kernel_bin);

        execute("mcopy -o -i fat.img " + boot_efi + " ::/EFI/BOOT/BOOTAA64.EFI");
        execute("mcopy -o -i fat.img " + kernel_bin + " ::/EFI/XENEVA/xnkrnl.exe");
        execute("mcopy -o -i fat.img initrd2.img ::/initrd2.img");

        std::ofstream nomenu("NOMENU");
        nomenu.close();
        execute("mcopy -o -i fat.img NOMENU ::/NOMENU");
        fs::remove("NOMENU");

        log_info("Build complete! Autonomous discovery successfully packaged everything.");
        return true;
    }
}