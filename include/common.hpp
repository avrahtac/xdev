#pragma once

#include <iostream>
#include <string>
#include <filesystem>
#include <cstdlib>

namespace fs = std::filesystem;

namespace xdev {
    // Logging helpers
    inline void log_info(const std::string& msg) {
        std::cout << "\033[32m[INFO]\033[0m " << msg << std::endl;
    }

    inline void log_warn(const std::string& msg) {
        std::cout << "\033[33m[WARN]\033[0m " << msg << std::endl;
    }

    inline void log_error(const std::string& msg) {
        std::cerr << "\033[31m[ERROR]\033[0m " << msg << std::endl;
    }

    // Helper to execute shell commands and return exit code
    inline int execute(const std::string& cmd) {
        return std::system(cmd.c_str());
    }

    // Get XENEVA_PROJECT environment variable path safely
    inline fs::path get_xeneva_root() {
        const char* env_p = std::getenv("XENEVA_PROJECT");
        if (!env_p) {
            return fs::path();
        }
        return fs::path(env_p);
    }
}