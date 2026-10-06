#include "doctor.hpp"
#include "setup.hpp"
#include "common.hpp"

namespace xdev {
    bool Doctor::check_environment(bool auto_fix) {
        log_info("Running environment diagnostics (xdev doctor)...");

        bool all_passed = true;

        // 1. Check XENEVA_PROJECT environment variable
        fs::path xeneva_root = get_xeneva_root();
        if (xeneva_root.empty() || !fs::exists(xeneva_root)) {
            log_error("XENEVA_PROJECT environment variable is missing or points to an invalid path!");
            log_warn("Please set it using: export XENEVA_PROJECT=/path/to/xenevaos (or setx on Windows)");
            all_passed = false;
        } else {
            log_info("XENEVA_PROJECT verified at: " + xeneva_root.string());
        }

        // 2. Check binary tools availability
#if defined(_WIN32) || defined(_WIN64)
        int qemu_check = execute("C:\\msys64\\usr\\bin\\bash.exe -lc \"which qemu-system-aarch64 >nul 2>&1\"");
#else
        int qemu_check = execute("which qemu-system-aarch64 >/dev/null 2>&1");
#endif

        if (qemu_check != 0) {
            log_warn("Required tool 'qemu-system-aarch64' not found in path.");
            all_passed = false;
        } else {
            log_info("QEMU AArch64 system emulator found.");
        }

        // 3. Trigger automatic setup if checks failed
        if (!all_passed) {
            if (auto_fix) {
                log_warn("Some dependencies are missing. Automatically triggering 'xdev setup'...");
                if (Setup::run_setup()) {
                    log_info("Setup completed successfully. Re-running diagnostics...");
                    return check_environment(false); // Re-run once without looping
                } else {
                    log_error("Automated setup failed.");
                    return false;
                }
            } else {
                return false;
            }
        }

        log_info("All system diagnostics passed successfully!");
        return true;
    }
}