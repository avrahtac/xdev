#
# xdev - XenevaOS Toolchain CLI
# Copyright (c) 2026 Manas Kamal Choudhary and XenevaOS Team
# Distributed under the terms of the BSD 2-Clause License.
#

import sys
import os
import subprocess
import shutil

XDEV_VERSION = "0.1.0-alpha"

COMMANDS_SUMMARY = """usage: xdev <command> [<args>]

commands:
  doctor                verify toolchain installation and environment dependencies
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

def run_update():
    """Download and overwrite xdev.exe with the latest GitHub release."""
    import urllib.request
    import json

    print("xdev: checking for updates...")
    api_url = ""
    
    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'xdev-cli'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            latest_version = data.get("tag_name", "")
            
            if latest_version == XDEV_VERSION:
                print(f"xdev: already up-to-date ({XDEV_VERSION}).")
                return 0
            
            print(f"xdev: new version found: {latest_version} (current: {XDEV_VERSION})")
            for asset in data.get("assets", []):
                if asset["name"] == "xdev-setup.exe":
                    download_url = asset["browser_download_url"]
                    print(f"xdev: downloading latest setup from {download_url}...")
                    installer_path = os.path.join(os.environ.get("TEMP", "."), "xdev-setup.exe")
                    urllib.request.urlretrieve(download_url, installer_path)
                    print("xdev: launching updater...")
                    subprocess.Popen([installer_path, "/SILENT"])
                    return 0
    except Exception as e:
        sys.stderr.write(f"xdev: error checking for updates: {e}\n")
        return 1
    
def get_xeneva_project():
    proj = os.environ.get("XENEVA_PROJECT")
    if not proj:
        sys.stderr.write("xdev: error: XENEVA_PROJECT environment variable is not set\n")
        return None
    if not os.path.isdir(proj):
        sys.stderr.write(f"xdev: error: XENEVA_PROJECT directory not found: {proj}\n")
        return None
    return proj

def run_doctor():
    all_ok = True

    xeneva_proj = os.environ.get("XENEVA_PROJECT")
    if xeneva_proj and os.path.isdir(xeneva_proj):
        print(f"XENEVA_PROJECT: {xeneva_proj}")
    elif xeneva_proj:
        print(f"XENEVA_PROJECT: {xeneva_proj} (not a valid directory)")
        all_ok = False
    else:
        print("XENEVA_PROJECT: not set")
        all_ok = False

    tools = [
        ("git", ["git", "--version"]),
        ("clang", [r"C:\msys64\ucrt64\bin\clang.exe" if os.name == 'nt' else "clang", "--version"]),
        ("lld", [r"C:\msys64\ucrt64\bin\ld.lld.exe" if os.name == 'nt' else "ld.lld", "--version"]),
        ("qemu-system-aarch64", [r"C:\msys64\ucrt64\bin\qemu-system-aarch64.exe" if os.name == 'nt' else "qemu-system-aarch64", "--version"]),
        ("make", [r"C:\msys64\usr\bin\make.exe" if os.name == 'nt' else "make", "--version"]),
        ("mtools", [r"C:\msys64\ucrt64\bin\mcopy.exe" if os.name == 'nt' else "mcopy", "-V"]),
        ("mkfs.fat", [r"C:\msys64\usr\bin\mkfs.fat.exe" if os.name == 'nt' else "mkfs.fat", "-v"])
    ]

    for name, cmd in tools:
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                first_line = res.stdout.splitlines()[0] if res.stdout else "available"
                print(f"  found {name:<20} -> {first_line}")
            else:
                print(f"  missing {name}")
                all_ok = False
        except (FileNotFoundError, OSError):
            print(f"  missing {name}")
            all_ok = False

    return 0 if all_ok else 1

def run_build(extra_args=None):
    if extra_args is None:
        extra_args = []

    xeneva_proj = get_xeneva_project()
    if not xeneva_proj:
        return 1

    make_bin = r"C:\msys64\usr\bin\make.exe" if (os.name == 'nt' and os.path.exists(r"C:\msys64\usr\bin\make.exe")) else shutil.which("make")
    mcopy_bin = r"C:\msys64\ucrt64\bin\mcopy.exe" if os.name == 'nt' else shutil.which("mcopy")
    mkfs_bin = r"C:\msys64\usr\bin\mkfs.fat.exe" if os.name == 'nt' else shutil.which("mkfs.fat")
    mmd_bin = r"C:\msys64\ucrt64\bin\mmd.exe" if os.name == 'nt' else shutil.which("mmd")

    if not (make_bin and mcopy_bin and mkfs_bin and mmd_bin):
        sys.stderr.write("xdev: error: build tools missing in environment.\n")
        return 1

    env = os.environ.copy()
    if os.name == 'nt':
        msys_paths = [r"C:\msys64\ucrt64\bin", r"C:\msys64\usr\bin"]
        existing_path = env.get("PATH", "")
        additions = [p for p in msys_paths if os.path.exists(p) and p.lower() not in existing_path.lower()]
        if additions:
            env["PATH"] = ";".join(additions) + ";" + existing_path
        env["MSYSTEM"] = "UCRT64"

    # --- 1. ENSURE GNU-EFI ---
    gnu_efi_dir = os.path.join(xeneva_proj, "gnu-efi")
    if not os.path.exists(gnu_efi_dir):
        artifact_gnu_efi = os.path.join(os.path.dirname(xeneva_proj), "xdev", "artifacts", "gnu-efi")
        if os.path.exists(artifact_gnu_efi):
            try:
                os.symlink(artifact_gnu_efi, gnu_efi_dir)
            except Exception:
                shutil.copytree(artifact_gnu_efi, gnu_efi_dir)

    # --- 2. PRIORITY AND AUTONOMOUS COMPILATION ---
    priority_dirs = ["Libs/XEClib", "Libs/Chitralekha", "BootAA64", "KernelAA64"]
    built_dirs = set()

    print("xdev: compiling priority core components...")
    for pdir in priority_dirs:
        pdir_path = os.path.join(xeneva_proj, pdir)
        if os.path.exists(os.path.join(pdir_path, "Makefile")):
            print(f" -> Building priority component: {pdir}")
            subprocess.run([make_bin, "-C", pdir, "llvm"], cwd=xeneva_proj, env=env)
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

    # --- 3. PREPARE RESOURCES AND SWEEP ARTIFACTS ---
    resources_dir = os.path.join(xeneva_proj, "Resources", "resources")
    os.makedirs(resources_dir, exist_ok=True)

    print("xdev: sweeping repository for compiled .dll drivers...")
    for root, dirs, files in os.walk(xeneva_proj):
        if "Resources" in root:
            continue
        for file in files:
            if file.lower().endswith(".dll"):
                src_path = os.path.join(root, file)
                dest_path = os.path.join(resources_dir, file)
                shutil.copy2(src_path, dest_path)

    # --- 4. ASSEMBLE initrd2.img ---
    initrd_img = os.path.join(xeneva_proj, "initrd2.img")
    print("xdev: assembling 128 MB FAT32 ramdisk (initrd2.img)...")
    initrd_size = 128 * 1024 * 1024
    with open(initrd_img, "wb") as f:
        f.truncate(initrd_size)
    subprocess.run([mkfs_bin, "-F", "32", initrd_img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Pack Resources/resources payload
    if os.path.isdir(resources_dir):
        print("xdev: packing Resources/resources payload into initrd2.img...")
        for root, dirs, files in os.walk(resources_dir):
            for file in files:
                full_src = os.path.join(root, file)
                rel_path = os.path.relpath(full_src, resources_dir).replace("\\", "/")
                
                if "/" in rel_path:
                    sub_dir = rel_path.rsplit("/", 1)[0]
                    subprocess.run([mmd_bin, "-D", "s", "-i", initrd_img, f"::/{sub_dir}"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                subprocess.run([mcopy_bin, "-o", "-i", initrd_img, full_src, f"::/{rel_path}"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Dynamic Executable Harvest: Copy all Process/ .exe binaries directly to root (::/)
    process_dir = os.path.join(xeneva_proj, "Process")
    if os.path.isdir(process_dir):
        print("xdev: harvesting Process/ .exe binaries to root ::/...")
        for root, dirs, files in os.walk(process_dir):
            for file in files:
                if file.lower().endswith(".exe"):
                    full_exe = os.path.join(root, file)
                    print(f"  -> discovered and packing: {file}")
                    subprocess.run([mcopy_bin, "-o", "-i", initrd_img, full_exe, f"::/{file}"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # --- 5. ASSEMBLE fat.img (ESP) ---
    fat_img = os.path.join(xeneva_proj, "fat.img")
    print("xdev: assembling 512 MB FAT32 boot image (fat.img)...")
    fat_size = 512 * 1024 * 1024
    with open(fat_img, "wb") as f:
        f.truncate(fat_size)
    subprocess.run([mkfs_bin, "-F", "32", "-n", "BOOTIMG", fat_img], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # EFI Directory structure
    subprocess.run([mmd_bin, "-i", fat_img, "::/EFI"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([mmd_bin, "-i", fat_img, "::/EFI/BOOT"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run([mmd_bin, "-i", fat_img, "::/EFI/XENEVA"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Locate bootloader and kernel
    boot_efi = ""
    kernel_bin = ""

    for root, dirs, files in os.walk(xeneva_proj):
        for file in files:
            if file.lower() in ("bootaa64.efi",) and not boot_efi:
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
    subprocess.run([mcopy_bin, "-o", "-i", fat_img, initrd_img, "::/initrd2.img"])

    # Skip boot menu flag 
    #_inject_nomenu_marker(fat_img, mcopy_bin)

    print("xdev: build complete! Autonomous discovery successfully packaged everything.")
    return 0

def find_compiled_image(project_dir):
    candidates = ["fat.img", os.path.join("Build", "fat.img")]
    for rel in candidates:
        full = os.path.join(project_dir, rel)
        if os.path.isfile(full):
            return full
    return None

def find_qemu_binary():
    bins = [
        ("qemu-system-aarch64", r"C:\msys64\ucrt64\bin\qemu-system-aarch64.exe" if os.name == 'nt' else None),
        ("qemu-system-x86_64", r"C:\msys64\ucrt64\bin\qemu-system-x86_64.exe" if os.name == 'nt' else None)
    ]
    for name, default_path in bins:
        if default_path and os.path.isfile(default_path):
            return name, default_path
        which_path = shutil.which(name)
        if which_path:
            return name, which_path
    return None, None

def find_uefi_firmware():
    candidates = [
        os.environ.get("XENEVA_QEMU_FIRMWARE"),
        r"C:\msys64\ucrt64\share\qemu\edk2-aarch64-code.fd",
        "/usr/share/edk2/aarch64/QEMU_EFI.fd",
        "/usr/share/qemu-efi-aarch64/QEMU_EFI.fd"
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None

def _probe_qemu_audio(qemu_bin):
    try:
        probe = subprocess.run([qemu_bin, "-audiodev", "help"], capture_output=True, text=True, timeout=5)
        output = probe.stdout + probe.stderr
        for backend in ("dsound", "pa", "sdl", "wav"):
            if backend in output:
                return backend
    except Exception:
        pass
    return "none"

def _inject_nomenu_marker(fat_img, mcopy_bin):
    import tempfile
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix="NOMENU") as tmp:
            tmp_path = tmp.name
        subprocess.run([mcopy_bin, "-o", "-i", fat_img, tmp_path, "::/NOMENU"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.unlink(tmp_path)
    except Exception:
        pass

def run_qemu(extra_args=None):
    if extra_args is None:
        extra_args = []

    xeneva_proj = get_xeneva_project()
    if not xeneva_proj:
        return 1

    img_path = find_compiled_image(xeneva_proj)
    if not img_path:
        sys.stderr.write("xdev: error: fat.img not found in XENEVA_PROJECT. Run 'xdev build' first.\n")
        return 1

    qemu_name, qemu_bin = find_qemu_binary()
    if not qemu_bin:
        sys.stderr.write("xdev: error: QEMU binary not found\n")
        return 1

    resolution = "640x480"
    memory = "1024M"
    smp = "2"
    no_boot_menu = False
    headless = False
    qemu_passthrough = []
    for arg in extra_args:
        if arg.startswith("--resolution="):
            val = arg.split("=", 1)[1]
            if val not in ("640x480", "800x600", "1024x768"):
                sys.stderr.write("xdev: error: --resolution must be 640x480, 800x600, or 1024x768\n")
                return 1
            resolution = val
        elif arg.startswith("--memory="):
            memory = arg.split("=", 1)[1]
        elif arg.startswith("--smp="):
            smp = arg.split("=", 1)[1]
        elif arg == "--no-boot-menu":
            no_boot_menu = True
        elif arg == "--headless":
            headless = True
        else:
            qemu_passthrough.append(arg)

    if no_boot_menu:
        mcopy_bin = r"C:\msys64\ucrt64\bin\mcopy.exe" if os.name == "nt" else shutil.which("mcopy")
        if mcopy_bin and os.path.isfile(img_path):
            _inject_nomenu_marker(img_path, mcopy_bin)

    cmd = [qemu_bin]
    if "aarch64" in qemu_name:
        firmware = find_uefi_firmware()
        if firmware:
            cmd.extend(["-bios", firmware])

        audio_backend = _probe_qemu_audio(qemu_bin)

        cmd.extend([
            "-machine", "virt,gic-version=2,highmem=off",
            "-cpu", "cortex-a72",
            "-smp", smp,
            "-m", memory,
            "-drive", f"file={img_path},format=raw,if=none,id=blk0",
            "-device", "virtio-blk-pci,drive=blk0,disable-legacy=on",
            "-netdev", "user,id=net0,ipv4=on,net=10.0.2.0/24,host=10.0.2.2,"
                       "dhcpstart=10.0.2.15,dns=10.0.2.3,"
                       "ipv6=on,ipv6-net=fec0::/64,ipv6-host=fec0::2",
            "-device", "virtio-net-pci,netdev=net0",
            "-device", "ramfb,id=ramfb",
            "-device", "virtio-gpu-pci,disable-legacy=on,id=gpu0",
            "-device", "virtio-keyboard-pci",
            "-device", "virtio-tablet-pci",
            "-device", "usb-ehci",
            "-device", "usb-kbd",
            "-device", "virtio-rng-pci,disable-legacy=on,id=rng0",
            "-audiodev", f"{audio_backend},id=snd0",
            "-device", "virtio-sound-pci,audiodev=snd0,disable-legacy=on",
            "-serial", "stdio",
            "-serial", "null",
        ])

        if headless:
            cmd.extend(["-display", "none", "-no-reboot"])
        else:
            cmd.extend(["-display", "gtk,zoom-to-fit=on,show-tabs=on"])

    else:
        cmd.extend([
            "-m", memory,
            "-smp", smp,
            "-drive", f"file={img_path},format=raw",
            "-serial", "stdio",
        ])
        if not headless:
            cmd.extend(["-display", "gtk,zoom-to-fit=on"])

    cmd.extend(qemu_passthrough)

    try:
        res = subprocess.run(cmd, cwd=xeneva_proj)
        return res.returncode
    except Exception as e:
        sys.stderr.write(f"xdev: error running qemu: {e}\n")
        return 1

def run_fetch(extra_args=None):
    if extra_args is None:
        extra_args = []

    xeneva_proj = get_xeneva_project()
    if not xeneva_proj:
        return 1

    cmd = ["git", "pull"] + extra_args
    try:
        res = subprocess.run(cmd, cwd=xeneva_proj)
        return res.returncode
    except Exception as e:
        sys.stderr.write(f"xdev: fetch error: {e}\n")
        return 1

def run_flash(extra_args=None):
    if extra_args is None:
        extra_args = []

    if not extra_args:
        sys.stderr.write("xdev: error: target storage device/drive required (usage: xdev flash <target>)\n")
        return 1

    target = extra_args[0]
    xeneva_proj = get_xeneva_project()
    if not xeneva_proj:
        return 1

    img_path = find_compiled_image(xeneva_proj)
    if not img_path:
        sys.stderr.write("xdev: error: compiled OS image not found to flash\n")
        return 1

    if os.name == 'nt' and (len(target) == 2 and target[1] == ':' or len(target) == 3 and target[1:3] == ':\\'):
        drive = target[0].upper() + ":\\"
        if not os.path.exists(drive):
            sys.stderr.write(f"xdev: error: target drive not found: {drive}\n")
            return 1
        try:
            shutil.copy2(img_path, os.path.join(drive, os.path.basename(img_path)))
            print(f"xdev: successfully flashed {os.path.basename(img_path)} to {drive}")
            return 0
        except Exception as e:
            sys.stderr.write(f"xdev: flash error: {e}\n")
            return 1
    elif os.name != 'nt':
        cmd = ["dd", f"if={img_path}", f"of={target}", "bs=4M", "status=progress", "conv=fsync"]
        try:
            res = subprocess.run(cmd)
            return res.returncode
        except Exception as e:
            sys.stderr.write(f"xdev: dd error: {e}\n")
            return 1
    else:
        sys.stderr.write(f"xdev: error: invalid target device: {target}\n")
        return 1

def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print_help()
        sys.exit(0)

    cmd = argv[0].lower()
    extra_args = argv[1:]

    if cmd in ("help", "--help", "-h"):
        print_help()
        sys.exit(0)
    elif cmd == "doctor":
        sys.exit(run_doctor())
    elif cmd == "build":
        sys.exit(run_build(extra_args))
    elif cmd == "run":
        sys.exit(run_qemu(extra_args))
    elif cmd == "fetch":
        sys.exit(run_fetch(extra_args))
    elif cmd == "flash":
        sys.exit(run_flash(extra_args))
    else:
        sys.stderr.write(f"xdev: error: unknown command '{cmd}'\n")
        sys.stderr.write("see 'xdev help' for a list of valid commands.\n")
        sys.exit(1)

if __name__ == "__main__":
    main()