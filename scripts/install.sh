#!/usr/bin/env bash
#
# xdev toolchain standalone installer (v0.1.0-alpha)
# CLI Engine by Atharva Chitale | XenevaOS (c) Manas Kamal Choudhary & team
# BSD 2-Clause License
#

set -e

BOLD="\033[1m"
BLUE="\033[1;34m"
GREEN="\033[1;32m"
YELLOW="\033[1;33m"
RED="\033[1;31m"
RESET="\033[0m"

msg()  { echo -e "${BLUE}==>${RESET} ${BOLD}$1${RESET}"; }
info() { echo -e "  ${BLUE}->${RESET} $1"; }
ok()   { echo -e "  ${GREEN}->${RESET} $1"; }
warn() { echo -e "  ${YELLOW}->${RESET} $1"; }
err()  { echo -e "  ${RED}->${RESET} $1"; }

# Helper to safely read user prompts when script is piped via curl | bash
prompt() {
    local text="$1"
    local var_name="$2"
    if [ -t 0 ]; then
        read -r -p "$text" "$var_name"
    elif [ -e /dev/tty ]; then
        read -r -p "$text" "$var_name" < /dev/tty
    else
        eval "$var_name='y'"
    fi
}

RAW_XDEV_URL="https://raw.githubusercontent.com/avrahtac/xdev/main/src/xdev.py"

clear 2>/dev/null || true

echo -e "${BOLD}xdev toolchain installer (v0.1.0-alpha)${RESET}"
echo -e "developed by Atharva Chitale | XenevaSs (c) Manas Kamal Choudhary & Team\n"

# -----------------------------------------------------------------------------
# 1. License Agreement
# -----------------------------------------------------------------------------
msg "BSD 2-Clause License"
cat << "EOF"

Copyright (c) 2020-2026 Manas Kamal Choudhary and XenevaOS Team
xdev (c) 2026 Atharva Chitale

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
EOF
echo ""

prompt "accept license? [y/N]: " LICENSE_ACCEPT
case "$LICENSE_ACCEPT" in
    [yY][eE][sS]|[yY]) ok "license accepted" ;;
    *) err "license rejected. bye."; exit 1 ;;
esac

# -----------------------------------------------------------------------------
# 2. Dependency Check & Universal Package Manager Fallback
# -----------------------------------------------------------------------------
msg "checking toolchain deps"
REQUIRED_TOOLS=(python3 git clang ld.lld llvm-ar make mcopy mkfs.fat curl)
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    warn "missing dependencies: ${MISSING_TOOLS[*]}"
    prompt "attempt automatic installation via package manager? [Y/n]: " AUTO_INSTALL
    
    if [[ ! "$AUTO_INSTALL" =~ ^[nN]$ ]]; then
        if command -v pacman &> /dev/null; then
            info "arch detected (pacman)"
            sudo pacman -Syu --needed --noconfirm python git clang lld llvm qemu-system-aarch64 make mtools dosfstools curl edk2-armvirt
        elif command -v dnf &> /dev/null; then
            info "fedora/rhel detected (dnf)"
            ssudo dnf install -y python3 git clang lld llvm qemu-system-aarch64 make mtools dosfstools curl edk2-aarch64
        elif command -v apt &> /dev/null; then
            info "debian/ubuntu detected (apt)"
            sudo apt update && sudo apt install -y python3 git clang lld llvm qemu-system-arm build-essential mtools dosfstools curl qemu-efi-aarch64
        elif command -v zypper &> /dev/null; then
            info "opensuse detected (zypper)"
            sudo zypper install -y python3 git clang lld qemu-extra make mtools dosfstools curl qemu-uefi-aarch64
        elif command -v apk &> /dev/null; then
            info "alpine detected (apk)"
            sudo apk add python3 git clang lld qemu-system-aarch64 make mtools dosfstools curl edk2-aarch64
        elif command -v xbps-install &> /dev/null; then
            info "void linux detected (xbps)"
            sudo xbps-install -Sy python3 git clang lld qemu-user-static make mtools dosfstools curl
        elif command -v emerge &> /dev/null; then
            info "gentoo detected (emerge)"
            sudo emerge --ask n sys-devel/clang sys-devel/lld app-emulation/qemu dev-build/make sys-fs/mtools sys-fs/dosfstools net-misc/curl
        else
            warn "could not auto-detect package manager."
            info "please install these packages manually on your distribution:"
            echo -e "     ${BOLD}${MISSING_TOOLS[*]}${RESET}\n"
            prompt "press enter once you have installed them manually (or 'q' to quit): " MANUAL_CONFIRM
            if [[ "$MANUAL_CONFIRM" =~ ^[qQ]$ ]]; then
                err "installation aborted."
                exit 1
            fi
        fi
        ok "dependencies verified"
    else
        err "missing required build tools. installation aborted."
        exit 1
    fi
else
    ok "all core dependencies present"
fi

# -----------------------------------------------------------------------------
# 3. Download & Install xdev Engine
# -----------------------------------------------------------------------------
msg "installing xdev engine"

INSTALL_DIR="/usr/local/bin"
TARGET_BIN="$INSTALL_DIR/xdev"

# Clean ghost local installations
rm -f "$HOME/.local/bin/xdev" 2>/dev/null || true

info "downloading xdev engine from GitHub..."
TMP_XDEV=$(mktemp)
curl -fsSL "$RAW_XDEV_URL" -o "$TMP_XDEV"
chmod +x "$TMP_XDEV"

if [ -w "$INSTALL_DIR" ]; then
    mv "$TMP_XDEV" "$TARGET_BIN"
else
    sudo mv "$TMP_XDEV" "$TARGET_BIN"
    sudo chmod +x "$TARGET_BIN"
fi

hash -r 2>/dev/null || true
ok "installed $TARGET_BIN"

# -----------------------------------------------------------------------------
# 4. Workspace Configuration
# -----------------------------------------------------------------------------
msg "setting workspace"
GUESS_PROJ=""
if [ -n "$XENEVA_PROJECT" ] && [ -d "$XENEVA_PROJECT" ]; then
    GUESS_PROJ="$XENEVA_PROJECT"
elif [ -d "$HOME/XenevaDevelopment/XenevaOS" ]; then
    GUESS_PROJ="$HOME/XenevaDevelopment/XenevaOS"
else
    GUESS_PROJ="$HOME/XenevaOS"
fi

prompt "XenevaOS repo path [$GUESS_PROJ]: " USER_PROJ
FINAL_PROJ="${USER_PROJ:-$GUESS_PROJ}"
FINAL_PROJ="${FINAL_PROJ/#\~/$HOME}"

if [ ! -d "$FINAL_PROJ" ]; then
    warn "'$FINAL_PROJ' does not exist"
    prompt "clone XenevaOS now from GitHub? [Y/n]: " CLONE_XENEVA
    if [[ ! "$CLONE_XENEVA" =~ ^[nN]$ ]]; then
        info "cloning XenevaOS into $FINAL_PROJ..."
        git clone https://github.com/manaskamal/XenevaOS.git "$FINAL_PROJ"
    else
        err "workspace path required. exiting."
        exit 1
    fi
fi

FINAL_PROJ="$(cd "$FINAL_PROJ" && pwd)"
ok "XENEVA_PROJECT -> $FINAL_PROJ"

# -----------------------------------------------------------------------------
# 5. Shell Environment Persistence
# -----------------------------------------------------------------------------
msg "persisting environment"
SHELL_CONFIG=""
if [ -n "$BASH_VERSION" ] || [ -f "$HOME/.bashrc" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -f "$HOME/.profile" ]; then
    SHELL_CONFIG="$HOME/.profile"
fi

if [ -n "$SHELL_CONFIG" ]; then
    if grep -q "XENEVA_PROJECT" "$SHELL_CONFIG"; then
        sed -i "/export XENEVA_PROJECT=/c\export XENEVA_PROJECT=\"$FINAL_PROJ\"" "$SHELL_CONFIG"
    else
        echo -e "\nexport XENEVA_PROJECT=\"$FINAL_PROJ\"" >> "$SHELL_CONFIG"
    fi
    ok "updated $SHELL_CONFIG"
    export XENEVA_PROJECT="$FINAL_PROJ"
fi

msg "running doctor"
echo "--------------------------------------------------"
xdev doctor
echo "--------------------------------------------------"

echo ""
ok "installation complete!"
info "restart terminal or run 'source ~/.bashrc'"
info "use 'xdev build' then 'xdev run' to test your build!"