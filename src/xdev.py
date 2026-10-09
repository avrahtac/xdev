#!/usr/bin/env python3
#
# xdev - XenevaOS Toolchain CLI (Linux Engine)
# Copyright (c) 2026 Manas Kamal Choudhary and XenevaOS Team
# Maintained by Atharva Chitale | BSD 2-Clause License
#

import sys
import os
import subprocess
import shutil
import urllib.request

XDEV_VERSION = "3.9.0"
RELEASE_INITRD_URL = "https://github.com/manaskamal/XenevaOS/releases/download/xenevaos-ui-alpha-0.2/initrd3.img"

COMMANDS_SUMMARY = """usage: xdev <command> [<args>]

commands:
  doctor                verify toolchain installation and environment dependencies
  clean                 wipe all build artifacts, object files, and generated images
  build                 compile XenevaOS kernel, components, and pack fat.img
  run [options]         launch XenevaOS inside QEMU emulator
  fetch                 pull latest source/repository changes
  flash <target>        write target images to bootable storage / disk images
  help                  display this help message

run options:
  --resolution=MODE     screen resolution: 640x480, 800x600, 1024x768 (default: 640x480)
  --memory=SIZE         guest RAM: 384M, 512M, 1024M, 2048M (default: 1024M)
  --smp=N               number of vCPU cores (default: 2, reduces UI lag)
  --no-boot-menu        skip UEFI resolution menu and boot with default resolution
  --headless            run without a display window (serial output only)
"""

def print_help():
    print(COMMANDS_SUMMARY.strip())

def get_xeneva_project():
    proj = os.environ.get("XENEVA_PROJECT")
    if not proj:
        cwd = os.getcwd()
        if os.path.exists(os.path.join(cwd, "KernelAA64")) or os.path.exists(os.path.join(cwd, "BootAA64")):
            return cwd
        sys.stderr.write("xdev: error: XENEVA_PROJECT environment variable is not set. Run 'source ~/.bashrc'.\n")
        return None
    if not os.path.isdir(proj):
        sys.stderr.write(f"xdev: error: XENEVA_PROJECT directory not found: {proj}\n")
        return None
    return proj

def run_clean(extra_args=None):
    xeneva_proj = get_xeneva_project()
    if not xeneva_proj:
        return 1

    print("xdev: cleaning build artifacts, caches, and images...")
    
    for img in ["fat.img", "initrd2.img", "initrd3.img"]:
        img_path = os.path.join(xeneva_proj, img)
        if os.path.exists(img_path):
            os.remove(img_path)
            print(f"  -> removed {img}")

    make_bin = shutil.which("make")
    if make_bin:
        skip_keywords = ["gnu-efi", ".git", "Tools"]
        for root, dirs, files in os.walk(xeneva_proj):
            if any(kw in root for kw in skip_keywords):
                continue
            if "Makefile" in files:
                rel_dir = os.path.relpath(root, xeneva_proj)
                subprocess.run([make_bin, "-C", rel_dir, "clean"], cwd=xeneva_proj, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    print("xdev: workspace successfully wiped clean!")
    return 0

def ensure_release_initrd(xeneva_proj):
    initrd_path = os.path.join(xeneva_proj, "initrd3.img")
    
    if os.path.exists(initrd_path) and os.path.getsize(initrd_path) > 10 * 1024 * 1024:
        size_mb = os.path.getsize(initrd_path) // (1024 * 1024)
        print(f"xdev: verified existing release initrd3.img ({size_mb} MB)")
        return initrd_path

    print(f"xdev: downloading release initrd3.img from {RELEASE_INITRD_URL}...")
    
    curl_bin = shutil.which("curl")
    if curl_bin:
        cmd = [curl_bin, "-L", "-f", "-#", "-o", initrd_path, RELEASE_INITRD_URL]
        res = subprocess.run(cmd)
        if res.returncode == 0 and os.path.exists(initrd_path) and os.path.getsize(initrd_path) > 10 * 1024 * 1024:
            size_mb = os.path.getsize(initrd_path) // (1024 * 1024)
            print(f"\nxdev: successfully downloaded initrd3.img via curl ({size_mb} MB)")
            return initrd_path

    try:
        req = urllib.request.Request(RELEASE_INITRD_URL, headers={'User-Agent': 'xdev-cli'})
        with urllib.request.urlopen(req) as response, open(initrd_path, 'wb') as out_file:
            total_size = int(response.info().get('Content-Length', 0))
            downloaded = 0
            block_size = 1024 * 128
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    sys.stdout.write(f"\rxdev: downloading... {downloaded // (1024*1024)}MB / {total_size // (1024*1024)}MB ({pct:.1f}%)")
                    sys.stdout.flush()
        print()
        size_mb = os.path.getsize(initrd_path) // (1024 * 1024)
        print(f"xdev: successfully downloaded initrd3.img ({size_mb} MB)")
        return initrd_path
    except Exception as e:
        sys.stderr.write(f"xdev: error downloading release initrd3.img: {e}\n")
        return None

def run_doctor():
    all_ok = True
    xeneva_proj = get_xeneva_project()
    if xeneva_proj:
        print(f"XENEVA_PROJECT: {xeneva_proj}")
    else:
        print("XENEVA_PROJECT: not set or invalid")
        all_ok = False

    tools = ["git", "clang", "ld.lld", "qemu-system-aarch64", "make", "mcopy", "mkfs.fat", "curl"]
    for t in tools:
        if shutil.which(t):
            print(f"  found {t:<20} -> {shutil.which(t)}")
        else:
            print(f"  missing {t}")
            all_ok = False
    return 0 if all_ok else 1

def copy_file_to_ramdisk(mcopy_bin, mmd_bin, ramdisk_path, src_file, target_rel_path):
    target_rel_path = target_rel_path.strip("/")
    if not target_rel_path:
        return

    if "/" in target_rel_path:
        sub_dirs = target_rel_path.rsplit("/", 1)[0].split("/")
        curr_dir = ""
        for sd in sub_dirs:
            curr_dir += f"/{sd}"
            subprocess.run([mmd_bin, "-D", "s", "-i", ramdisk_path, f"::{curr_dir}"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    subprocess.run([mcopy_bin, "-o", "-i", ramdisk_path, src_file, f"::/{target_rel_path}"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_build(extra_args=None):
    if extra_args is None:
        extra_args = []

    xeneva_proj = get_xeneva_project()
    if not xeneva_proj:
        return 1

    make_bin = shutil.which("make")
    mcopy_bin = shutil.which("mcopy")
    mkfs_bin = shutil.which("mkfs.fat")
    mmd_bin = shutil.which("mmd")

    if not (make_bin and mcopy_bin and mkfs_bin and mmd_bin):
        sys.stderr.write("xdev: error: required build tools are missing.\n")
        return 1

    env = os.environ.copy()
    env["TOOLCHAIN"] = "llvm"
    env["BOARD"] = "qemu_virt"

    # --- 1. ENSURE GNU-EFI ---
    gnu_efi_dir = os.path.join(xeneva_proj, "gnu-efi")
    if not os.path.exists(gnu_efi_dir):
        artifact_gnu_efi = os.path.join(os.path.dirname(xeneva_proj), "xdev", "artifacts", "gnu-efi")
        if os.path.exists(artifact_gnu_efi):
            try:
                os.symlink(artifact_gnu_efi, gnu_efi_dir)
            except Exception:
                shutil.copytree(artifact_gnu_efi, gnu_efi_dir)
        else:
            print("xdev: auto-cloning gnu-efi...")
            subprocess.run(["git", "clone", "https://github.com/vathpela/gnu-efi.git", gnu_efi_dir])

    # --- 2. PRIORITY AND AUTONOMOUS COMPILATION ---
    priority_dirs = ["Libs/XEClib", "Libs/Chitralekha", "BootAA64", "KernelAA64"]
    built_dirs = set()

    print("xdev: compiling priority core components...")
    for pdir in priority_dirs:
        pdir_path = os.path.join(xeneva_proj, pdir)
        if os.path.exists(os.path.join(pdir_path, "Makefile")):
            print(f" -> Building priority component: {pdir}")
            subprocess.run([make_bin, "-C", pdir_path, "llvm"], cwd=xeneva_proj, env=env)
            built_dirs.add(os.path.abspath(pdir_path))

    print("xdev: sweeping workspace for additional target Makefiles...")
    skip_keywords = ["gnu-efi", "Build", "CMakeFiles", "Tools"]
    for root, dirs, files in os.walk(xeneva_proj):
        if any(kw in root for kw in skip_keywords):
            continue
        if "Makefile" in files:
            abs_root = os.path.abspath(root)
            if abs_root not in built_dirs:
                rel_dir = os.path.relpath(root, xeneva_proj)
                print(f" -> Auto-building discovered target: {rel_dir}")
                subprocess.run([make_bin, "-C", rel_dir, "llvm"], cwd=xeneva_proj, env=env)

    # --- 3. PREPARE RESOURCES & SWEEP ARTIFACTS ---
    resources_root = os.path.join(xeneva_proj, "Resources")
    resources_sub = os.path.join(resources_root, "resources")
    os.makedirs(resources_sub, exist_ok=True)

    print("xdev: sweeping repository for compiled .dll drivers...")
    for root, dirs, files in os.walk(xeneva_proj):
        if "Resources" in root:
            continue
        for file in files:
            if file.lower().endswith(".dll"):
                src_path = os.path.join(root, file)
                dest_path = os.path.join(resources_sub, file)
                shutil.copy2(src_path, dest_path)

    # --- 4. ASSEMBLE LOCAL RAMDISK (initrd2.img) ---
    initrd2_img = os.path.join(xeneva_proj, "initrd2.img")
    print("xdev: assembling 256 MB FAT32 ramdisk (initrd2.img)...")
    initrd2_size_bytes = 256 * 1024 * 1024
    with open(initrd2_img, "wb") as f:
        f.truncate(initrd2_size_bytes)
    subprocess.run([mkfs_bin, "-F", "32", initrd2_img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # --- 5. OBTAIN RELEASE BASE RAMDISK (initrd3.img) ---
    initrd3_img = ensure_release_initrd(xeneva_proj)

    target_ramdisks = [initrd2_img]
    if initrd3_img and os.path.exists(initrd3_img):
        target_ramdisks.append(initrd3_img)

    # --- 6. HARVEST RESOURCES & ICONS (PRESERVE BOTH ::/icons/ AND ::/) ---
    if os.path.isdir(resources_root):
        print("xdev: harvesting Resources/ (icons, fonts, configs) into ramdisks...")
        for root, dirs, files in os.walk(resources_root):
            for file in files:
                full_src = os.path.join(root, file)
                rel_from_res = os.path.relpath(full_src, resources_root).replace("\\", "/")
                file_lower = file.lower()

                if file_lower.endswith(('.bmp', '.jpg', '.jpeg', '.png', '.ttf', '.cnf', '.dll')):
                    # Path variations to populate
                    target_paths = set()
                    
                    # 1. Exact relative path inside Resources/ (e.g. icons/GoIcon.bmp)
                    target_paths.add(rel_from_res)

                    # 2. Strip 'resources/' prefix if present (e.g. resources/icons/GoIcon.bmp -> icons/GoIcon.bmp)
                    if rel_from_res.startswith("resources/"):
                        target_paths.add(rel_from_res[len("resources/"):])

                    # 3. Direct root placement (e.g. ::/GoIcon.bmp)
                    target_paths.add(file)

                    for dest_path in target_paths:
                        for rd in target_ramdisks:
                            copy_file_to_ramdisk(mcopy_bin, mmd_bin, rd, full_src, dest_path)

    # --- 7. HARVEST PROCESSES (.exe BINARIES) ---
    process_dir = os.path.join(xeneva_proj, "Process")
    if os.path.isdir(process_dir):
        print("xdev: harvesting Process/ .exe userland binaries into ramdisks...")
        for root, dirs, files in os.walk(process_dir):
            for file in files:
                if file.lower().endswith(".exe"):
                    full_exe = os.path.join(root, file)
                    for rd in target_ramdisks:
                        copy_file_to_ramdisk(mcopy_bin, mmd_bin, rd, full_exe, file)

    # --- 8. DYNAMICALLY SIZE AND ASSEMBLE fat.img (ESP Boot Partition) ---
    sz2 = os.path.getsize(initrd2_img) if os.path.exists(initrd2_img) else 0
    sz3 = os.path.getsize(initrd3_img) if (initrd3_img and os.path.exists(initrd3_img)) else 0
    
    required_fat_bytes = sz2 + sz3 + (256 * 1024 * 1024)
    fat_size_bytes = max(1024 * 1024 * 1024, required_fat_bytes)
    fat_size_mb = fat_size_bytes // (1024 * 1024)

    fat_img = os.path.join(xeneva_proj, "fat.img")
    print(f"xdev: assembling {fat_size_mb} MB FAT32 boot image (fat.img)...")
    with open(fat_img, "wb") as f:
        f.truncate(fat_size_bytes)
    subprocess.run([mkfs_bin, "-F", "32", "-n", "BOOTIMG", fat_img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run([mmd_bin, "-i", fat_img, "::/EFI"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([mmd_bin, "-i", fat_img, "::/EFI/BOOT"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([mmd_bin, "-i", fat_img, "::/EFI/XENEVA"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    boot_efi = ""
    kernel_bin = ""
    for root, dirs, files in os.walk(xeneva_proj):
        for file in files:
            if file.lower() == "bootaa64.efi" and not boot_efi:
                boot_efi = os.path.join(root, file)
            if file.lower() in ("kernelaa64.exe", "xnkrnl.exe") and not kernel_bin:
                full_p = os.path.join(root, file)
                if os.path.getsize(full_p) > 1000:
                    kernel_bin = full_p

    if not boot_efi or not kernel_bin:
        sys.stderr.write("xdev: error: could not locate core bootloader or kernel binaries.\n")
        return 1

    print(f" -> Packaging Bootloader: {os.path.relpath(boot_efi, xeneva_proj)}")
    print(f" -> Packaging Kernel: {os.path.relpath(kernel_bin, xeneva_proj)}")

    subprocess.run([mcopy_bin, "-o", "-i", fat_img, boot_efi, "::/EFI/BOOT/BOOTAA64.EFI"])
    subprocess.run([mcopy_bin, "-o", "-i", fat_img, kernel_bin, "::/EFI/XENEVA/xnkrnl.exe"])

    print(f" -> Packaging local Ramdisk: initrd2.img ({sz2 // (1024*1024)} MB)")
    subprocess.run([mcopy_bin, "-o", "-i", fat_img, initrd2_img, "::/initrd2.img"])

    if initrd3_img and os.path.exists(initrd3_img):
        print(f" -> Packaging release Ramdisk: initrd3.img ({sz3 // (1024*1024)} MB)")
        subprocess.run([mcopy_bin, "-o", "-i", fat_img, initrd3_img, "::/initrd3.img"])

    print("xdev: build complete successfully!")
    return 0

def run_qemu(extra_args=None):
    if extra_args is None:
        extra_args = []
    xeneva_proj = get_xeneva_project()
    if not xeneva_proj:
        return 1

    candidates = ["fat.img", os.path.join("Build", "fat.img")]
    img_path = next((os.path.join(xeneva_proj, c) for c in candidates if os.path.isfile(os.path.join(xeneva_proj, c))), None)
    if not img_path:
        sys.stderr.write("xdev: error: fat.img not found. Run 'xdev build' first.\n")
        return 1

    qemu_bin = shutil.which("qemu-system-aarch64")
    if not qemu_bin:
        sys.stderr.write("xdev: error: qemu-system-aarch64 binary not found\n")
        return 1

    firmware = next((c for c in [os.environ.get("XENEVA_QEMU_FIRMWARE"), "/usr/share/edk2/aarch64/QEMU_EFI.fd", "/usr/share/qemu-efi-aarch64/QEMU_EFI.fd", "/usr/share/AAVMF/AAVMF_CODE.fd"] if c and os.path.isfile(c)), None)

    cmd = [qemu_bin, "-machine", "virt,gic-version=2,highmem=off", "-cpu", "cortex-a72", "-smp", "2", "-m", "1024M"]
    if firmware:
        cmd.extend(["-bios", firmware])

    cmd.extend([
        "-drive", f"file={img_path},format=raw,if=none,id=blk0",
        "-device", "virtio-blk-pci,drive=blk0,disable-legacy=on",
        "-netdev", "user,id=net0,ipv4=on,net=10.0.2.0/24,host=10.0.2.2,dhcpstart=10.0.2.15,dns=10.0.2.3",
        "-device", "virtio-net-pci,netdev=net0",
        "-device", "ramfb,id=ramfb",
        "-device", "virtio-gpu-pci,disable-legacy=on,id=gpu0",
        "-device", "virtio-keyboard-pci", "-device", "virtio-tablet-pci",
        "-device", "usb-ehci", "-device", "usb-kbd",
        "-device", "virtio-rng-pci,disable-legacy=on,id=rng0",
        "-audiodev", "pa,id=snd0", "-device", "virtio-sound-pci,audiodev=snd0,disable-legacy=on",
        "-serial", "stdio", "-serial", "null",
        "-display", "gtk,zoom-to-fit=on,show-tabs=on"
    ])
    cmd.extend(extra_args)

    try:
        res = subprocess.run(cmd, cwd=xeneva_proj)
        return res.returncode
    except Exception as e:
        sys.stderr.write(f"xdev: error running qemu: {e}\n")
        return 1

def run_fetch(extra_args=None):
    proj = get_xeneva_project()
    if proj: return subprocess.run(["git", "pull"] + (extra_args or []), cwd=proj).returncode
    return 1

def run_flash(extra_args=None):
    if not extra_args:
        sys.stderr.write("xdev: error: target device required (usage: xdev flash <target>)\n")
        return 1
    proj = get_xeneva_project()
    if not proj: return 1
    candidates = ["fat.img", os.path.join("Build", "fat.img")]
    img_path = next((os.path.join(proj, c) for c in candidates if os.path.isfile(os.path.join(proj, c))), None)
    return subprocess.run(["sudo", "dd", f"if={img_path}", f"of={extra_args[0]}", "bs=4M", "status=progress", "conv=fsync"]).returncode

def main():
    argv = sys.argv[1:]
    if not argv:
        print_help()
        sys.exit(0)

    cmd = argv[0].lower()
    extra_args = argv[1:]

    if cmd in ("help", "--help", "-h"):
        print_help()
    elif cmd == "doctor":
        sys.exit(run_doctor())
    elif cmd == "clean":
        sys.exit(run_clean(extra_args))
    elif cmd == "build":
        sys.exit(run_build(extra_args))
    elif cmd == "run":
        sys.exit(run_qemu(extra_args))
    elif cmd == "fetch":
        sys.exit(run_fetch(extra_args))
    elif cmd == "flash":
        sys.exit(run_flash(extra_args))
    else:
        sys.stderr.write(f"xdev: error: unknown command '{cmd}'. See 'xdev help'.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()