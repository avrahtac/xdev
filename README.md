```markdown
# xdev

CLI toolchain for [XenevaOS](https://github.com/manasakamal/XenevaOS). Builds the OS, runs it in QEMU. Works on Windows, Linux, macOS.

Maintained by [Atharva Chitale](https://github.com/avrahtac).  
Kept separate from the main XenevaOS repo intentionally.

---

## Setup

### Windows

Download and run `xdev-setup.exe` from [Releases](../../releases). It installs MSYS2 (UCRT64) and the required packages. Needs admin.

Then set `XENEVA_PROJECT`:

```powershell
[System.Environment]::SetEnvironmentVariable("XENEVA_PROJECT", "X:\XenevaOS", "User")

```

Set X as you Drive path and Restart your terminal.

### Linux

Run this single command in your terminal to install `xdev`:

```bash
curl -fsSL [https://raw.githubusercontent.com/avrahtac/xdev/main/install.sh](https://raw.githubusercontent.com/avrahtac/xdev/main/install.sh) | bash

```

### macOS

Coming soon.

---

## Usage

```
xdev doctor          check environment and toolchain
xdev build           build kernel + bootloader + libs
xdev run             launch in QEMU
xdev fetch           git pull inside XENEVA_PROJECT
xdev flash <target>  write fat.img to a drive

```

### doctor

Verifies `XENEVA_PROJECT` and checks for: `git`, `clang`, `lld`, `qemu-system-aarch64`, `make`, `mcopy`.

Exit `0` = all good. Exit `1` = something missing.

### build

```bash
xdev build                   # full build: XEClib → Chitralekha → BootAA64 → KernelAA64
xdev build BootAA64          # bootloader only
xdev build KernelAA64        # kernel only
xdev build clean             # clean all
xdev build KernelAA64 clean  # clean one component

```

Updates `fat.img` with fresh `BOOTAA64.EFI`, `xnkrnl.exe`, and `initrd2.img` after build.

`Tools/` (Linux XR tools) is skipped on Windows.

### run

```bash
xdev run                        # 640x480, 1024M RAM, 2 cores
xdev run --resolution=1024x768  # higher res (pick it in the UEFI menu)
xdev run --no-boot-menu         # skip UEFI menu, boot at 640x480
xdev run --memory=2048M         # more RAM
xdev run --smp=4                # more cores
xdev run --headless             # no display, serial only

```

| flag | default | values |
| --- | --- | --- |
| `--resolution` | `640x480` | `640x480`, `800x600`, `1024x768` |
| `--memory` | `1024M` | any QEMU memory string |
| `--smp` | `2` | any integer |
| `--no-boot-menu` | off | — |
| `--headless` | off | — |

Unknown flags are forwarded to QEMU directly.

#### Resolution menu

The UEFI bootloader shows a resolution picker on boot:

|  | resolution |
| --- | --- |
| Enter | 640×480 |
| ↓ + Enter | 800×600 |
| ↓↓ + Enter | 1024×768 |

`--no-boot-menu` injects a `NOMENU` file into `fat.img` and skips straight to 640×480.

Recommended:

```bash
xdev run --resolution=1024x768 --memory=2048M --smp=4

```

### fetch

```bash
xdev fetch           # git pull
xdev fetch --rebase  # git pull --rebase

```

### flash

```bash
xdev flash E:        # Windows
xdev flash /dev/sdX  # Linux/macOS (uses dd, be careful)

```

USB requirements for real hardware: GPT, FAT32, ≥2 GiB.

---

## Troubleshooting

**Black screen after boot** — wait ~10s. QEMU has two tabs (ramfb and virtio-gpu); click the second one. If still black: `xdev run --no-boot-menu` to rule out menu issues.

**UI lag** — `xdev run --memory=2048M --smp=4`.

**`missing` in doctor after setup** — reopen your terminal. If still missing, check MSYS2 UCRT64 shell manually: `clang --version`.

**`clang++: not found` during build** — MSYS2 must be at `C:\msys64`, UCRT64 variant:

```
pacman -S mingw-w64-ucrt-x86_64-clang

```

**pacman timeout during setup** — the installer retries 3 times. Check your connection.

---

## Structure

```
src/xdev_cli.py           cross-platform CLI
src/xdev_installer_gui.py Windows installer GUI
src/build.cpp             C++ build engine (alternative backend)
tests/test_cli.py         pytest suite (27 tests)
tests/test_installer.py   pytest suite (4 tests)
dist/xdev.exe             packaged CLI
dist/xdev-setup.exe       packaged installer

```

## Dev

```bash
python -m pytest tests/ -v

pyinstaller --noconfirm xdev.spec
pyinstaller --noconfirm xdev-setup.spec
Copy-Item dist\xdev.exe xdev.exe -Force
Copy-Item dist\xdev-setup.exe xdev-setup.exe -Force

```

```

```