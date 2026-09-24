#include "xdev/doctor.hpp"
#include "xdev/fetch.hpp"
#include "xdev/workspace.hpp"
#include "xdev/build.hpp"
#include "xdev/run.hpp"
#include <iostream>
#include <string>
#include <cstdlib>
#include <filesystem>

namespace fs = std::filesystem;

void print_help() {
    std::cout << "\033[1;36m========================================================\033[0m\n"
              << "          XENEVAOS DEVELOPER ORCHESTRATOR (xdev)        \n"
              << "\033[1;36m========================================================\033[0m\n"
              << "A high-performance C++20 build and test control center.\n\n"
              << "CLI Usage:\n"
              << "  xdev          Launch interactive developer dashboard\n"
              << "  xdev build    Autonomous workspace compile & disk packing\n"
              << "  xdev run      Launch QEMU AArch64 hardware simulation\n"
              << "  xdev doctor   Audit host dependencies & toolchain health\n"
              << "  xdev fetch    Acquire external ecosystem assets (gnu-efi)\n"
              << "  xdev version  Display orchestrator build metadata\n";
}

void print_dashboard() {
    // Detect workspace status
    auto ws = xdev::Workspace::locate();
    std::string ws_status = ws.has_value() ? ws->root_path.string() : "Not Found (Run 'xdev fetch' or check path)";
    
    // Check key artifacts
    bool has_fat = fs::exists("fat.img");
    bool has_initrd = fs::exists("initrd2.img");

    std::cout << "\033[H\033[2J"; // Clear screen
    std::cout << "\033[1;35m    _  ___            \033[1;36m xdev v1.0.0 [AArch64 Orchestrator]\033[0m\n";
    std::cout << "\033[1;35m   / |/ _ \\_____ ___  \033[0m ------------------------------------\n";
    std::cout << "\033[1;35m  /    / // / -_) _ \\ \033[1;32m Host:\033[0m Linux (Fedora/Dev Environment)\n";
    std::cout << "\033[1;35m /_/|_/\\_, /\\__/_//_/ \033[1;32m Engine:\033[0m C++20 Autonomous Core\n";
    std::cout << "\033[1;35m      /___/           \033[1;32m Workspace:\033[0m " << ws_status << "\n";
    std::cout << "                      \033[1;32m Target:\033[0m QEMU virt (Cortex-A72)\n";
    std::cout << "                      \033[1;32m Images:\033[0m fat.img [" << (has_fat ? "READY" : "MISSING") << "] | initrd2 [" << (has_initrd ? "READY" : "MISSING") << "]\n";
    std::cout << "\033[1;36m--------------------------------------------------------\033[0m\n";
    std::cout << " \033[1;33m[1]\033[0m Build Pipeline   - Autonomous compile, sweep & pack\n";
    std::cout << " \033[1;33m[2]\033[0m Run Simulation   - Boot QEMU AArch64 with dual-GPU\n";
    std::cout << " \033[1;33m[3]\033[0m Full Workflow    - Execute Build followed by Run\n";
    std::cout << " \033[1;33m[4]\033[0m System Doctor    - Audit host tools & toolchain\n";
    std::cout << " \033[1;33m[5]\033[0m Fetch Assets     - Download gnu-efi & base layers\n";
    std::cout << " \033[1;33m[6]\033[0m Documentation    - View command reference & help\n";
    std::cout << " \033[1;31m[7]\033[0m Quit Control Center\n";
    std::cout << "\033[1;36m--------------------------------------------------------\033[0m\n";
    std::cout << "Select command [1-7]: ";
}

void run_interactive_dashboard() {
    int choice = 0;
    while (true) {
        print_dashboard();
        if (!(std::cin >> choice)) break;

        std::cout << "\n\033[1;33m--------------------------------------------------------\033[0m\n";
        if (choice == 1) {
            xdev::Build::execute();
        } else if (choice == 2) {
            xdev::Run::execute();
        } else if (choice == 3) {
            if (xdev::Build::execute() == 0) {
                xdev::Run::execute();
            }
        } else if (choice == 4) {
            xdev::Doctor::execute();
        } else if (choice == 5) {
            xdev::Fetch::execute();
        } else if (choice == 6) {
            print_help();
        } else if (choice == 7) {
            std::cout << "\033[1;32mExiting xdev control center. Happy coding!\033[0m\n";
            break;
        } else {
            std::cout << "\033[1;31mInvalid option selected.\033[0m\n";
        }

        std::cout << "\n\033[2mPress Enter to return to dashboard...\033[0m";
        std::cin.ignore();
        std::cin.get();
    }
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        run_interactive_dashboard();
        return 0;
    }

    std::string cmd = argv[1];

    if (cmd == "help" || cmd == "--help" || cmd == "-h") {
        print_help();
    } else if (cmd == "version" || cmd == "--version") {
        std::cout << "xdev version 1.0.0 (C++20 Autonomous Engine)\n";
    } else if (cmd == "doctor") {
        return xdev::Doctor::execute();
    } else if (cmd == "fetch") {
        return xdev::Fetch::execute();
    } else if (cmd == "build") {
        return xdev::Build::execute();
    } else if (cmd == "run") {
        return xdev::Run::execute();
    } else {
        std::cerr << "Unknown command: " << cmd << "\n\n";
        print_help();
        return 1;
    }

    return 0;
}