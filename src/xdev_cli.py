#
# xdev - XenevaOS Toolchain CLI
# Copyright (c) 2026 Manas Kamal Choudhary and XenevaOS Team
# Distributed under the terms of the BSD 2-Clause License.
#

import sys
import os
import subprocess
import shutil
import urllib.request

XDEV_VERSION = "1.3.0"

COMMANDS_SUMMARY = """usage: xdev <command> [<args>]

commands:
  doctor                verify toolchain installation and environment dependencies
  build                 compile the XenevaOS kernel and system components
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
        ("clang", [r"C:\msys64\ucrt64\bin\clang.exe", "--version"] if os.name == 'nt' else ["clang", "--version"]),
        ("lld", [r"C:\msys64\ucrt64\bin\ld.lld.exe", "--version"] if os.name == 'nt' else ["ld.lld", "--version"]),
        ("qemu-system-aarch64", [r"C:\msys64\ucrt64\bin\qemu-system-aarch64.exe", "--version"] if os.name == 'nt' else ["qemu-system-aarch64", "--version"]),
        ("make", [r"C:\msys64\usr\bin\make.exe", "--version"] if os.name == 'nt' else ["make", "--version"]),
        ("mtools", [r"C:\msys64\ucrt64\bin\mcopy.exe", "-V"] if os.name == 'nt' else ["mcopy", "-V"])
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

def download_progress(count, block_size, total_size):
    if total_size > 0:
        percent = int(count * block_size * 100 / total_size)
        sys.stdout.write(f"\r  Downloading master image container... {min(percent, 100)}%")
        sys.stdout.flush()

def run_build(extra_args=None):
    if extra_args is None:
        extra_args = []

    xeneva_proj = get_xeneva_project()
    if not xeneva_proj:
        return 1

    make_bin = None
    if os.name == 'nt' and os.path.exists(r"C:\msys64\usr\bin\make.exe"):
        make_bin = r"C:\msys64\usr\bin\make.exe"
    else:
        make_bin = shutil.which("make")

    if not make_bin:
        sys.stderr.write("xdev: error: make binary not found\n")
        return 1

    env = os.environ.copy()
    if os.name == 'nt':
        msys_paths = [r"C:\msys64\ucrt64\bin", r"C:\msys64\usr\bin"]
        existing_path = env.get("PATH", "")
        additions = [p for p in msys_paths if os.path.exists(p) and p.lower() not in existing_path.lower()]
        if additions:
            env["PATH"] = ";".join(additions) + ";" + existing_path
        env["MSYSTEM"] = "UCRT64"

    if extra_args:
        first = extra_args[0]
        if first in ("BootAA64", "KernelAA64", "Boot", "Kernel"):
            target_args = extra_args[1:] if len(extra_args) > 1 else ["llvm"]
            cmd = [make_bin, "-C", first] + target_args
            print(f"--> RUNNING COMMAND: {' '.join(cmd)}")
            try:
                res = subprocess.run(cmd, cwd=xeneva_proj, env=env)
                return res.returncode
            except Exception as e:
                sys.stderr.write(f"xdev: error running make: {e}\n")
                return 1
        elif first == "clean" and len(extra_args) == 1:
            has_subcomponents = any(os.path.isdir(os.path.join(xeneva_proj, d)) for d in ["BootAA64", "KernelAA64"])
            if has_subcomponents:
                ret = 0
                for comp in ["Libs/XEClib", "Libs/Chitralekha", "BootAA64", "KernelAA64"]:
                    if os.path.exists(os.path.join(xeneva_proj, comp, "Makefile")):
                        print(f"--> RUNNING COMMAND: {make_bin} -C {comp} clean")
                        res = subprocess.run([make_bin, "-C", comp, "clean"], cwd=xeneva_proj, env=env)
                        if res.returncode != 0:
                            ret = res.returncode
                return ret
            else:
                cmd = [make_bin, "clean"]
                print(f"--> RUNNING COMMAND: {' '.join(cmd)}")
                res = subprocess.run(cmd, cwd=xeneva_proj, env=env)
                return res.returncode
        else:
            cmd = [make_bin] + extra_args
            print(f"--> RUNNING COMMAND: {' '.join(cmd)}")
            try:
                res = subprocess.run(cmd, cwd=xeneva_proj, env=env)
                return res.returncode
            except Exception as e:
                sys.stderr.write(f"xdev: error running make: {e}\n")
                return 1

    core_components = [
        ("Libs/XEClib", ["llvm"]),
        ("Libs/Chitralekha", ["llvm"]),
        ("BootAA64", ["llvm"]),
        ("KernelAA64", ["llvm"])
    ]

    has_os_components = os.path.exists(os.path.join(xeneva_proj, "BootAA64", "Makefile"))

    if has_os_components:
        for comp, targets in core_components:
            comp_makefile = os.path.join(xeneva_proj, comp, "Makefile")
            if os.path.exists(comp_makefile):
                print(f"xdev: building {comp}...")
                cmd = [make_bin, "-C", comp] + targets
                print(f"--> RUNNING COMMAND: {' '.join(cmd)}")
                res = subprocess.run(cmd, cwd=xeneva_proj, env=env)
                if res.returncode != 0:
                    sys.stderr.write(f"xdev: error building component {comp}\n")
                    return res.returncode

        # --- Master Image Handling & Synchronization ---
        master_img = os.path.join(xeneva_proj, "initrd3.img")
        
        if not os.path.exists(master_img):
            print("xdev: initrd3.img not found locally. Fetching latest release from GitHub...")
            initrd_url = "https://github.com/manaskamal/XenevaOS/releases/download/xenevaos-ui-alpha-0.2/initrd3.img"
            try:
                urllib.request.urlretrieve(initrd_url, master_img, reporthook=download_progress)
                print("\nxdev: download complete.")
            except Exception as e:
                print()
                sys.stderr.write(f"xdev: error downloading initrd3.img: {e}\n")

        boot_efi = os.path.join(xeneva_proj, "BootAA64", "Build", "EFI", "BOOT", "BOOTAA64.EFI")
        if not os.path.exists(boot_efi):
            boot_efi = os.path.join(xeneva_proj, "BootAA64", "BOOTAA64.efi")

        kernel_exe = os.path.join(xeneva_proj, "KernelAA64", "KernelAA64.exe")
        mcopy_bin = r"C:\msys64\ucrt64\bin\mcopy.exe" if os.name == 'nt' else shutil.which("mcopy")
        mmd_bin = r"C:\msys64\ucrt64\bin\mmd.exe" if os.name == 'nt' else shutil.which("mmd")

        if mcopy_bin and os.path.exists(master_img):
            print("xdev: synchronizing binaries into master container filesystem...")
            if mmd_bin and os.path.exists(mmd_bin):
                subprocess.run([mmd_bin, "-D", "s", "-i", master_img, "::/EFI"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([mmd_bin, "-D", "s", "-i", master_img, "::/EFI/BOOT"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run([mmd_bin, "-D", "s", "-i", master_img, "::/EFI/XENEVA"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            if os.path.exists(boot_efi):
                subprocess.run([mcopy_bin, "-o", "-i", master_img, boot_efi, "::/EFI/BOOT/BOOTAA64.EFI"])
            else:
                sys.stderr.write("xdev: error: BOOTAA64.efi not found!\n")

            if os.path.exists(kernel_exe):
                subprocess.run([mcopy_bin, "-o", "-i", master_img, kernel_exe, "::/EFI/XENEVA/xnkrnl.exe"])

            # Sync local initrd2.img layer if available to match desktop configuration
            local_initrd2 = os.path.join(xeneva_proj, "initrd2.img")
            if os.path.exists(local_initrd2):
                print("xdev: synchronizing local initrd2.img payload layer...")
                subprocess.run([mcopy_bin, "-o", "-i", master_img, local_initrd2, "::/initrd2.img"])

        print("xdev: build complete successfully.")
        return 0
    else:
        cmd = [make_bin]
        try:
            res = subprocess.run(cmd, cwd=xeneva_proj, env=env)
            return res.returncode
        except Exception as e:
            sys.stderr.write(f"xdev: error running make: {e}\n")
            return 1

def find_compiled_image(project_dir):
    candidates = [
        "initrd3.img",
        "fat.img",
        "initrd2.img",
        os.path.join("Build", "initrd3.img")
    ]
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
        probe = subprocess.run(
            [qemu_bin, "-audiodev", "help"],
            capture_output=True, text=True, timeout=5
        )
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
        subprocess.run(
            [mcopy_bin, "-o", "-i", fat_img, tmp_path, "::/NOMENU"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
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
        sys.stderr.write("xdev: error: compiled OS image not found in XENEVA_PROJECT. Run 'xdev build' first.\n")
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
                sys.stderr.write(f"xdev: error: --resolution must be 640x480, 800x600, or 1024x768\n")
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
        mcopy_bin = (
            r"C:\msys64\ucrt64\bin\mcopy.exe"
            if os.name == "nt" else shutil.which("mcopy")
        )
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