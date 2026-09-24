#include "xdev/cli.hpp"
#include "xdev/platform.hpp"
#include "xdev/doctor.hpp"
#include "xdev/fetch.hpp"
#include "xdev/build.hpp"
#include "xdev/run.hpp"
#include <iostream>
#include <string_view>

namespace xdev {

void CLI::print_help() {
    std::cout << "xdev - XenevaOS Developer Tool\n\n"
              << "Usage: xdev <command> [options]\n\n"
              << "Commands:\n"
              << "  help     Show this help message\n"
              << "  version  Show version information\n"
              << "  doctor   Check system dependencies and environment\n"
              << "  fetch    Download official Xeneva artifacts\n"
              << "  build    Invoke the Xeneva build system\n"
              << "  run      Launch XenevaOS in QEMU\n";
}

void CLI::print_version() {
    std::cout << "xdev version 0.1.0\n"
              << "Host OS: " << Platform::get_os() << "\n"
              << "Host Arch: " << Platform::get_architecture() << "\n";
}

int CLI::run(int argc, char* argv[]) {
    if (argc < 2) {
        print_help();
        return 1;
    }

    std::string_view command = argv[1];

    if (command == "help" || command == "--help" || command == "-h") {
        print_help();
        return 0;
    } else if (command == "version" || command == "--version" || command == "-v") {
        print_version();
        return 0;
    } else if (command == "doctor") {
        return Doctor::execute(); // <-- Update this
    } else if (command == "fetch") {
        return Fetch::execute();
    } else if (command == "build") {
        return Build::execute();
    } else if (command == "run") {
        return Run::execute();
    } else {
        std::cerr << "Error: Unknown command '" << command << "'\n\n";
        print_help();
        return 1;
    }
}

} // namespace xdev