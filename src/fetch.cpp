#include "fetch.hpp"
#include "common.hpp"

namespace xdev {
    bool Fetch::fetch_assets() {
        log_info("Fetching required XenevaOS assets and images...");

        fs::path xeneva_root = get_xeneva_root();
        if (xeneva_root.empty()) {
            log_error("XENEVA_PROJECT environment variable is not set. Run 'xdev doctor' first.");
            return false;
        }

        // Create a build/assets directory inside the project root if it doesn't exist
        fs::path asset_dir = xeneva_root / "build" / "assets";
        if (!fs::exists(asset_dir)) {
            fs::create_directories(asset_dir);
        }

        fs::path initrd3_path = asset_dir / "initrd3.img";

        // Check if initrd3.img already exists
        if (fs::exists(initrd3_path)) {
            log_info("initrd3.img is already present at: " + initrd3_path.string());
            return true;
        }

        log_info("Downloading initrd3.img from GitHub Releases...");
        std::string url = "https://github.com/manaskamal/XenevaOS/releases/download/xenevaos-ui-alpha-0.2/initrd3.img";
        
        // Use curl or powershell (Invoke-WebRequest) depending on platform
#if defined(_WIN32) || defined(_WIN64)
        std::string download_cmd = "powershell -Command \"Invoke-WebRequest -Uri '" + url + "' -OutFile '" + initrd3_path.string() + "'\"";
#else
        std::string download_cmd = "curl -L -o \"" + initrd3_path.string() + "\" \"" + url + "\"";
#endif

        if (execute(download_cmd) != 0) {
            log_error("Failed to download initrd3.img from release URL.");
            return false;
        }

        log_info("Successfully downloaded initrd3.img!");
        return true;
    }
}