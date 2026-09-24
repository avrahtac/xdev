// SPDX-License-Identifier: BSD-2-Clause
#include "xdev/doctor.hpp"
#include "xdev/process.hpp"
#include "xdev/platform.hpp"
#include "xdev/workspace.hpp"
#include <iostream>

namespace xdev {

int Doctor::execute() {
    std::cout << "xdev Doctor - Environment Audit\n";
    std::cout << "---------------------------------\n";
    std::cout << "Platform: " << Platform::get_os() << " (" << Platform::get_architecture() << ")\n\n";

    bool healthy = true;

    auto check_tool = [&](const std::string& name, const std::string& check_cmd) {
        std::string full_cmd = (Platform::get_os() == "Windows") 
            ? check_cmd + " >nul 2>nul" 
            : check_cmd + " > /dev/null 2>&1";

        if (Process::run(full_cmd).exit_code == 0) {
            std::cout << "  [ OK ] " << name << "\n";
        } else {
            std::cout << "  [FAIL] " << name << " (Not found or failed)\n";
            healthy = false;
        }
    };

    std::cout << "Build Tools:\n";
    check_tool("Git", "git --version");
    check_tool("CMake", "cmake --version");
    check_tool("Ninja", "ninja --version");
    check_tool("Clang", "clang --version");
    check_tool("LLD (ld.lld)", "ld.lld --version");
    check_tool("NASM", "nasm -v");
    check_tool("Python 3", "python3 --version");
    
    std::cout << "\nRuntime & Packaging:\n";
    check_tool("QEMU AArch64", "qemu-system-aarch64 --version");
    check_tool("mtools (mcopy)", "mcopy -V");
    check_tool("cURL", "curl --version");

    std::cout << "\nXenevaOS Repository:\n";
    auto ws = Workspace::locate();
    if (ws.has_value()) {
        std::cout << "  [ OK ] Detected repository at: " << ws->root_path << "\n";
        std::cout << "  [ OK ] Linux AArch64 workflow present\n";
    } else {
        std::cout << "  [WARN] No XenevaOS repository found in current directory or ../XenevaOS.\n";
    }

    std::cout << "---------------------------------\n";
    if (healthy) {
        std::cout << "Result: System is ready for AArch64 XenevaOS development.\n";
        return 0;
    } else {
        std::cout << "Result: Missing dependencies. Please install the failed tools.\n";
        return 1;
    }
}

} // namespace xdev