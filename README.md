# xdev

A CLI toolchain for [XenevaOS](https://github.com/manasakamal/XenevaOS). 

Build the OS. Run it in QEMU.

Works on Windows and Linux. macOS support is planned.

Maintained by [Atharva Chitale](https://github.com/avrahtac). Kept separate from the main XenevaOS tree on purpose.

>**Note:** As of Oct. 2026, `xdev` is in its alpha release stage and not stable. Features may break.  If you run into problems with XenevaOS itself (kernel, UI, drivers, etc.), report them in the [XenevaOS repository](https://github.com/manasakamal/XenevaOS). Use this repository for issues with `xdev` — its CLI, toolchain setup, build commands, or QEMU launcher.
---

## Setup

### Windows

Download `xdev-setup.exe` from [Releases](https://github.com/avrahtac/xdev/releases) and run it. It installs MSYS2 (UCRT64) and the required packages. Administrator privileges are needed.

Set the path to your XenevaOS checkout:

```powershell
[System.Environment]::SetEnvironmentVariable(
    "XENEVA_PROJECT",
    "X:\XenevaOS",
    "User"
)
```

Replace `X:\XenevaOS` with your actual repository path. Restart the terminal afterwards.

### Linux

Run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/avrahtac/xdev/main/scripts/install.sh | bash
```

### macOS

Not supported yet.

---

## Usage

Start with `doctor`. It checks whether the toolchain is in place.

```bash
xdev doctor
xdev build
xdev run
```

That's the usual workflow: check, build, boot.

### Commands

| Command | What it does |
| --- | --- |
| `xdev doctor` | Check the environment |
| `xdev build` | Build XenevaOS |
| `xdev run` | Start QEMU |
| `xdev fetch` | Pull changes in the XenevaOS checkout |
| `xdev flash <target>` | Write `fat.img` to a drive |
| `xdev version` | Print version |
| `xdev help` | Show help |

## Doctor

Checks `XENEVA_PROJECT` and looks for the following tools:

`git`, `clang`, `lld`, `qemu-system-aarch64`, `make`, `mcopy`.

Exit code `0` means everything checked out. Exit code `1` means something is missing.

## Build

Build everything, or just the part you're working on.

```bash
# Full build
xdev build

# One component
xdev build BootAA64
xdev build KernelAA64

# Clean everything
xdev build clean

# Clean one component
xdev build KernelAA64 clean
```

After the build, `fat.img` is updated with the generated `BOOTAA64.EFI`, `xnkrnl.exe`, and `initrd2.img`.

`Tools/` contains Linux XR tools and is skipped on Windows.

## Run

Starts XenevaOS in QEMU. Defaults are 640×480, 1024 MB RAM, and 2 CPU cores.

```bash
# Default settings
xdev run

# Higher resolution
xdev run --resolution=1024x768

# Skip the UEFI menu
xdev run --no-boot-menu

# More memory and CPU cores
xdev run --memory=2048M --smp=4

# Serial output, no graphical display
xdev run --headless
```

### Options

| Option | Default | Values / meaning |
| --- | --- | --- |
| `--resolution` | `640x480` | `640x480`, `800x600`, `1024x768` |
| `--memory` | `1024M` | QEMU memory string |
| `--smp` | `2` | Number of CPU cores |
| `--no-boot-menu` | Off | Skip the UEFI menu |
| `--headless` | Off | No graphical display |

Unknown options are passed through to QEMU.

### Resolution menu

The UEFI bootloader has a small resolution picker:

| Input | Resolution |
| --- | --- |
| `Enter` | 640×480 |
| `↓`, then `Enter` | 800×600 |
| `↓↓`, then `Enter` | 1024×768 |

`--no-boot-menu` puts a `NOMENU` file in `fat.img` and boots directly at 640×480.

A decent starting point if the default feels cramped:

```bash
xdev run --resolution=1024x768 --memory=2048M --smp=4
```

## Fetch

Pull changes in the configured XenevaOS repository.

```bash
# Normal pull
xdev fetch

# Pull with rebase
xdev fetch --rebase
```

## Flash

Write `fat.img` to a USB drive.

**Windows**

```powershell
xdev flash E:
```

**Linux**

```bash
xdev flash /dev/sdX
```

Replace the target with the correct drive. On Linux, this uses `dd`, so double-check the device before proceeding. The wrong target means the wrong disk gets overwritten.

For real hardware, the USB drive should use GPT, FAT32, and have at least 2 GiB of capacity.

---

## Troubleshooting

**Black screen in QEMU**

Give it a few seconds. If there are two display tabs, try the `virtio-gpu` one. Still stuck? Try `xdev run --no-boot-menu`.

**Tools missing in `doctor`**

Restart the terminal. On Windows, check that MSYS2 UCRT64 is installed and that `clang --version` works in its shell.

**`clang++: not found`**

From the MSYS2 UCRT64 shell:

```bash
pacman -S mingw-w64-ucrt-x86_64-clang
```

**Slow UI**

Try giving QEMU more resources:

```bash
xdev run --memory=2048M --smp=4
```

**`pacman` timing out**

Check the connection and try again. The Windows installer retries package installation up to three times.

---

That's about it. Check the toolchain, build the thing, and boot it. Facing Issues? Feel free to raise a PR. 

