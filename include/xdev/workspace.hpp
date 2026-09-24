#pragma once
#include <string>
#include <filesystem>
#include <optional>

namespace xdev {

struct WorkspaceInfo {
    std::filesystem::path root_path;
    bool has_linux_workflow;
    bool has_kernel_aa64;
    bool has_boot_aa64;
};

class Workspace {
public:
    // Discovers the active XenevaOS repository root
    static std::optional<WorkspaceInfo> locate(const std::string& explicit_path = "");

    // Validates whether a specific directory contains the required Xeneva markers
    static bool is_valid_repository(const std::filesystem::path& path);
};

} // namespace xdev