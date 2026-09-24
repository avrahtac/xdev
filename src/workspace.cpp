#include "xdev/workspace.hpp"
#include <iostream>
#include <cstdlib>

namespace fs = std::filesystem;

namespace xdev {

bool Workspace::is_valid_repository(const fs::path& path) {
    if (!fs::exists(path) || !fs::is_directory(path)) {
        return false;
    }
    // Only check for the actual OS source directories, not the old bash scripts
    bool has_kernel = fs::exists(path / "KernelAA64/Makefile");
    bool has_boot = fs::exists(path / "BootAA64/Makefile");

    return has_kernel && has_boot;
}

std::optional<WorkspaceInfo> Workspace::locate(const std::string& explicit_path) {
    fs::path candidate;

    auto check_and_return = [](const fs::path& p) -> std::optional<WorkspaceInfo> {
        if (is_valid_repository(p)) {
            return WorkspaceInfo{
                p,
                false, // We no longer care about the Linux workflow script
                true,
                true
            };
        }
        return std::nullopt;
    };

    if (!explicit_path.empty()) {
        if (auto res = check_and_return(fs::absolute(explicit_path))) return res;
    }

    const char* env_path = std::getenv("XENEVA_PROJECT");
    if (env_path && *env_path) {
        if (auto res = check_and_return(fs::absolute(env_path))) return res;
    }

    if (auto res = check_and_return(fs::current_path())) return res;
    
    if (auto res = check_and_return(fs::absolute("../XenevaOS"))) return res;

    return std::nullopt;
}

} // namespace xdev