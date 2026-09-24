#include "xdev/run.hpp"
#include "xdev/workspace.hpp"
#include "xdev/process.hpp"
#include <iostream>
#include <string>
#include <filesystem>

namespace fs = std::filesystem;

namespace xdev {

int Run::execute() {
    std::cout << "xdev Run - Launching XenevaOS with Exact Official QEMU Config\n";
    std::cout << "-------------------------------------------------\n";

    auto ws = Workspace::locate();
    if (!ws.has_value()) {
        std::cerr << "  [FAIL] Could not locate XenevaOS repository.\n";
        return 1;
    }

    fs::current_path(ws->root_path);

    // Note: The official script names the ESP image 'fat.img'
    if (!fs::exists("fat.img")) {
        std::cerr << "  [FAIL] fat.img not found. Please run 'xdev build' first.\n";
        return 1;
    }

    std::string efi_fw = "/usr/share/qemu-efi-aarch64/QEMU_EFI.fd";
    if (!fs::exists(efi_fw)) {
        efi_fw = "/usr/share/edk2/aarch64/QEMU_EFI.fd"; 
        if (!fs::exists(efi_fw)) {
            std::cerr << "  [FAIL] UEFI Firmware not found.\n";
            return 1;
        }
    }

    std::cout << "  [ OK ] Booting QEMU with exact machine/gic/virtio-blk flags...\n\n";

    // Exact flags from official build_and_run_qemu.sh
    std::string qemu_cmd = 
        "qemu-system-aarch64 "
        "-machine virt,gic-version=2,highmem=off "
        "-cpu cortex-a72 -m 1024M "
        "-bios " + efi_fw + " "
        "-drive file=fat.img,format=raw,if=none,id=blk0 "
        "-device virtio-blk-pci,drive=blk0,disable-legacy=on "
        "-netdev user,id=net0,ipv4=on,net=10.0.2.0/24,host=10.0.2.2,dhcpstart=10.0.2.15,dns=10.0.2.3 "
        "-device virtio-net-pci,netdev=net0 "
        "-device ramfb,id=ramfb "
        "-device virtio-keyboard-pci "
        "-device virtio-tablet-pci "
        "-device virtio-gpu-pci,disable-legacy=on,id=gpu0 "
        "-device usb-ehci -device usb-kbd "
        "-serial stdio";

    return Process::run_interactive(qemu_cmd);
}

} // namespace xdev