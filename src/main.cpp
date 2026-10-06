#include "common.hpp"
#include "installer.hpp"
#include "setup.hpp"
#include "doctor.hpp"
#include "fetch.hpp"
#include "build.hpp"
#include "run.hpp"

void print_help() {
    std::cout << "XenevaOS Development Utility (xdev) v1.0.0\n\n"
              << "Usage:\n"
              << "  xdev <command>\n\n"
              << "Commands:\n"
              << "  install   - Automatically install MSYS2/winget toolchain (Windows)\n"
              << "  setup     - Install host dependencies (pacman/apt/dnf)\n"
              << "  doctor    - Audit environment and verify XENEVA_PROJECT\n"
              << "  fetch     - Download gnu-efi and alpha base images (initrd3.img)\n"
              << "  build     - Autonomously discover, compile, and pack fat.img & initrd2.img\n"
              << "  run       - Launch QEMU emulator with XenevaOS image\n"
              << "  help      - Display this help message\n";
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        print_help();
        return 1;
    }

    std::string command = argv[1];

    if (command == "install") {
#if defined(_WIN32) || defined(_WIN64)
        return xdev::Installer::run_installer() ? 0 : 1;
#else
        std::cout << "The 'install' command is primarily for Windows. On Linux, use scripts/install.sh" << std::endl;
        return 1;
#endif
    } else if (command == "setup") {
        return xdev::Setup::run_setup() ? 0 : 1;
    } else if (command == "doctor") {
        return xdev::Doctor::check_environment(true) ? 0 : 1;
    } else if (command == "fetch") {
        return xdev::Fetch::fetch_assets() ? 0 : 1;
    } else if (command == "build") {
        return xdev::Build::run_build() ? 0 : 1;
    } else if (command == "run") {
        return xdev::Run::execute_qemu() ? 0 : 1;
    } else if (command == "help" || command == "--help" || command == "-h") {
        print_help();
        return 0;
    } else {
        std::cerr << "Unknown command: " << command << "\n\n";
        print_help();
        return 1;
    }
}