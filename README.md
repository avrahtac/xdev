# xdev — XenevaOS Toolchain CLI

> **Developed and maintained by [Atharva Chitale](https://github.com/avrahtac)**

`xdev` is a cross-platform CLI toolchain for [XenevaOS](https://github.com/manasakamal/XenevaOS).  
It installs dependencies, builds the OS from source, and launches it in QEMU — on any OS, on any machine, with a fixed compiler — without touching the XenevaOS main repository.

---

## Table of Contents

- [Overview](#overview)
- [Quick Setup (Windows)](#quick-setup-windows)
- [Quick Setup (Linux / macOS)](#quick-setup-linux--macos)
- [Environment Variables](#environment-variables)
- [Commands](#commands)
  - [xdev doctor](#xdev-doctor)
  - [xdev build](#xdev-build)
  - [xdev run](#xdev-run)
  - [xdev fetch](#xdev-fetch)
  - [xdev flash](#xdev-flash)
- [Screen Resolution](#screen-resolution)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

---

## Overview

XenevaOS is an AArch64 microkernel OS built with LLVM/Clang. The official build process
requires Visual Studio 2019, NASM, and an MSYS2 UCRT64 environment — a complex multi-step
setup that is easy to get wrong.

`xdev` wraps the entire workflow into five simple commands:

```
xdev doctor   →  verify your environment is ready
xdev build    →  compile the kernel, bootloader, and libs
xdev run      →  launch in QEMU (GTK window, audio, networking)
xdev fetch    →  pull the latest XenevaOS source
xdev flash    →  copy the image to a USB drive
```

`xdev` is intentionally kept separate from the XenevaOS repository: if anything breaks in
`xdev`, the main source is unaffected.

---

## Quick Setup (Windows)

### 1. Download xdev-setup.exe

Download the latest `xdev-setup.exe` from the [Releases](../../releases) page and run it.  
It will:
- Verify you have at least **5 GB** free on C:
- Install **MSYS2** (UCRT64 environment)
- Install **clang**, **lld**, **make**, **QEMU**, **mtools**, **git** via `pacman`

> **Note:** `xdev-setup.exe` requires administrator privileges. Windows UAC will prompt you.

### 2. Set the XENEVA_PROJECT environment variable

Point `XENEVA_PROJECT` at your local XenevaOS repository:

```powershell
[System.Environment]::SetEnvironmentVariable("XENEVA_PROJECT", "D:\XenevaOS", "User")
```

Restart your terminal after setting the variable.

### 3. Verify the setup

```
xdev doctor
```

All tools should show `found`. If any are `missing`, re-run `xdev-setup.exe`.

### 4. Build and run

```
xdev build
xdev run
```

---

## Quick Setup (Linux / macOS)

Install the required tools with your package manager, then set `XENEVA_PROJECT`:

**Ubuntu / Debian:**
```bash
sudo apt install clang lld make qemu-system-arm mtools git
export XENEVA_PROJECT=/path/to/XenevaOS
```

**Arch Linux:**
```bash
sudo pacman -S clang lld make qemu-system-aarch64 mtools git
export XENEVA_PROJECT=/path/to/XenevaOS
```

**macOS (Homebrew):**
```bash
brew install llvm make qemu mtools git
export XENEVA_PROJECT=/path/to/XenevaOS
```

Add the `export` line to your shell profile (`.bashrc`, `.zshrc`, etc.) to make it permanent.

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `XENEVA_PROJECT` | **Yes** | Absolute path to the XenevaOS repository root |
| `XENEVA_QEMU_FIRMWARE` | No | Override path to `edk2-aarch64-code.fd` UEFI firmware |
| `XENEVA_QEMU_MEMORY` | No | Override default guest memory (e.g. `2048M`) |

---

## Commands

### xdev doctor

Checks that all required tools are installed and `XENEVA_PROJECT` is set correctly.

```
xdev doctor
```

**Checks performed:**
- `XENEVA_PROJECT` directory exists
- `git` — version control
- `clang` — C/C++ compiler (LLVM)
- `lld` — LLVM linker
- `qemu-system-aarch64` — AArch64 emulator
- `make` — build system
- `mtools` / `mcopy` — FAT image manipulation

Returns exit code `0` if all checks pass, `1` if any fail.

---

### xdev build

Compiles the XenevaOS kernel, bootloader, and core libraries, then updates `fat.img`.

```
xdev build                        # full build (Libs → Boot → Kernel)
xdev build BootAA64               # build only the UEFI bootloader
xdev build KernelAA64             # build only the kernel
xdev build clean                  # clean all component build artifacts
xdev build KernelAA64 clean       # clean a specific component
```

**Build order (full):**
1. `Libs/XEClib` — C standard library
2. `Libs/Chitralekha` — graphics library
3. `BootAA64` — UEFI bootloader
4. `KernelAA64` — microkernel

After a successful build, `fat.img` is updated with the new `BOOTAA64.EFI`, `xnkrnl.exe`,
and `initrd2.img`.

> The `Tools/` directory (Linux-only XR host tools) is skipped automatically on Windows.

---

### xdev run

Launches XenevaOS in QEMU with a GTK display window.

```
xdev run                          # boot at 640x480 (default)
xdev run --resolution=1024x768    # boot and select 1024x768 in the UEFI menu
xdev run --no-boot-menu           # skip UEFI menu, boot at 640x480 instantly
xdev run --memory=2048M           # increase guest RAM (reduces lag)
xdev run --smp=4                  # use 4 vCPU cores (reduces UI lag)
xdev run --headless               # run without a display (serial output only)
```

**`run` options:**

| Option | Default | Description |
|---|---|---|
| `--resolution=MODE` | `640x480` | Screen resolution: `640x480`, `800x600`, `1024x768` |
| `--memory=SIZE` | `1024M` | Guest RAM: `384M`, `512M`, `1024M`, `2048M` |
| `--smp=N` | `2` | Number of virtual CPU cores |
| `--no-boot-menu` | off | Inject NOMENU marker → skip UEFI resolution picker |
| `--headless` | off | `-display none` — serial-only, no GTK window |

Any unrecognised flags are passed directly to QEMU.

**QEMU devices used:**
- `virtio-blk-pci` — block storage (fat.img)
- `virtio-net-pci` — user-mode networking (10.0.2.0/24)
- `ramfb` + `virtio-gpu-pci` — display (ramfb for boot/GOP, virtio-gpu for compositor)
- `virtio-keyboard-pci` + `virtio-tablet-pci` — input
- `virtio-rng-pci` — entropy source
- `virtio-sound-pci` — audio (`dsound` on Windows, `pa`/`sdl` on Linux)
- `usb-ehci` + `usb-kbd` — USB input fallback

---

### xdev fetch

Pulls the latest changes from the XenevaOS upstream repository.

```
xdev fetch
xdev fetch --rebase              # passed directly to git pull
```

Equivalent to `git pull` inside `XENEVA_PROJECT`.

---

### xdev flash

Writes the compiled OS image to a USB drive or raw block device.

```
xdev flash E:                    # Windows: copy fat.img to drive E:\
xdev flash /dev/sdX              # Linux/macOS: dd fat.img to /dev/sdX
```

> **Warning (Linux/macOS):** `xdev flash` uses `dd` with `conv=fsync`. Make absolutely sure
> the target device is your USB drive and not a system disk.

**USB drive requirements (for real hardware):**
- Minimum 2 GiB
- GPT partition table
- FAT32 filesystem

---

## Screen Resolution

The XenevaOS UEFI bootloader displays a resolution picker at startup. The options are:

| Key press | Resolution |
|---|---|
| Enter (no movement) | 640×480 |
| ↓ once, then Enter | 800×600 |
| ↓ twice, then Enter | 1024×768 |

When you run `xdev run --no-boot-menu`, a `NOMENU` marker file is injected into `fat.img`
and the bootloader skips the menu, booting at 640×480. This is useful for automated testing.

**Recommended for development:**
```
xdev run --resolution=1024x768 --memory=2048M --smp=4
```
Then select `1024×768` in the UEFI menu when it appears.

---

## Troubleshooting

### QEMU window opens but the UI is black / compositor doesn't appear

- The OS takes a few seconds to boot. Wait ~10 seconds.
- The QEMU window has **two tabs** (ramfb and virtio-gpu). Click the second tab after boot.
- Make sure you selected a resolution in the UEFI menu.
- Try `--resolution=640x480 --no-boot-menu` to confirm the compositor starts at all.

### UI is laggy or slow

```
xdev run --memory=2048M --smp=4
```

More RAM prevents swap pressure; more cores let the scheduler and compositor run in parallel.

### `xdev doctor` shows `missing` tools after setup

1. Close and reopen your terminal (PATH may not have refreshed).
2. Re-run `xdev-setup.exe` and check for errors during `pacman` installation.
3. Manually verify: open an MSYS2 UCRT64 shell and run `clang --version`.

### Build fails with `clang++: not found`

Make sure MSYS2 is installed at `C:\msys64`. The toolchain must be the **UCRT64** variant:
```
pacman -S mingw-w64-ucrt-x86_64-clang
```

### Network timeout during `xdev-setup.exe`

The installer retries `pacman -Sy` up to 3 times automatically. If all retries fail, check
your internet connection and try again. A cached package database is used as fallback.

---

## Project Structure

```
xdev/
├── src/
│   ├── xdev_cli.py          # cross-platform CLI (xdev build/run/fetch/flash/doctor)
│   ├── xdev_installer_gui.py# Windows setup GUI (xdev-setup.exe)
│   └── build.cpp            # C++ build engine (compiled to xdev.exe, alternative backend)
├── tests/
│   ├── test_cli.py          # 27 pytest tests for the CLI
│   └── test_installer.py    # 4 pytest tests for the installer
├── dist/
│   ├── xdev.exe             # packaged CLI (PyInstaller)
│   └── xdev-setup.exe       # packaged installer (PyInstaller)
├── xdev.spec                # PyInstaller spec for xdev.exe
├── xdev-setup.spec          # PyInstaller spec for xdev-setup.exe
├── build.bat                # builds src/build.cpp with clang++ in MSYS2 UCRT64
└── README.md                # this file
```

---

## Contributing

`xdev` is developed and maintained by **Atharva Chitale**.

Contributions are welcome. Please open an issue or pull request on this repository.

> `xdev` is intentionally kept separate from the [XenevaOS](https://github.com/manasakamal/XenevaOS)
> main repository. Changes to `xdev` cannot break the OS source tree.

### Running the test suite

```
python -m pytest tests/ -v
```

All 31 tests must pass before submitting a pull request.

### Rebuilding the executables

```powershell
pyinstaller --noconfirm xdev.spec
pyinstaller --noconfirm xdev-setup.spec
Copy-Item dist\xdev.exe xdev.exe -Force
Copy-Item dist\xdev-setup.exe xdev-setup.exe -Force
```

---

*XenevaOS is developed by Manas Kamal Choudhary and the XenevaOS team.*  
*`xdev` toolchain is developed and maintained by Atharva Chitale.*
