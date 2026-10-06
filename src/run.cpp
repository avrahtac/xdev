#include "run.hpp"
#include "common.hpp"

namespace xdev {
    bool Run::execute_qemu() {
        log_info("Preparing to launch XenevaOS in QEMU (AArch64)...");

        fs::path repo_root = get_xeneva_root();
        if (repo_root.empty() || !fs::exists(repo_root)) {
            log_error("XENEVA_PROJECT environment variable is missing or invalid. Run 'xdev doctor' first.");
            return false;
        }

        fs::current_path(repo_root);

        if (!fs::exists("fat.img")) {
            log_error("'fat.img' not found. Please run 'xdev build' first.");
            return false;
        }

        // Locate UEFI firmware files if available, or let QEMU use default/bundled ones
        // QEMU command for AArch64 UEFI boot
        std::string qemu_cmd = "qemu-system-aarch64 -M virt,gic-version=3 -cpu cortex-a57 -m 2G "
                               "-drive if=pflash,format=raw,file=fat.img,readonly=off "
                               "-net none -display gtk";

        log_info("Executing QEMU command:");
        std::cout << " > " << qemu_cmd << std::endl;

        return execute(qemu_cmd) == 0;
    }
}