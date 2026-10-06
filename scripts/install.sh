#!/usr/bin/env bash
#
# Copyright (c) 2026 Manas Kamal Choudhary and XenevaOS Team
# All rights reserved.
#

set -e

echo "================================================================="
echo "               BSD 2-CLAUSE LICENSE AGREEMENT                    "
echo "================================================================="
echo "Copyright (c) 2026, Manas Kamal Choudhary and XenevaOS Team"
echo "All rights reserved."
echo ""
echo "Redistribution and use in source and binary forms, with or without"
echo "modification, are permitted provided that the following conditions"
echo "are met:"
echo ""
echo "1. Redistributions of source code must retain the above copyright"
echo "   notice, this list of conditions and the following disclaimer."
echo "2. Redistributions in binary form must reproduce the above copyright"
echo "   notice, this list of conditions and the following disclaimer in"
echo "   the documentation and/or other materials provided with the"
echo "   distribution."
echo "================================================================="
echo ""

read -p "Do you accept the terms of the BSD 2-Clause License? [y/N]: " response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "[INFO] License accepted. Proceeding with installation..."
    
    # Ensure build directory and binary exist
    if [ ! -f "xdev" ]; then
        echo "[INFO] Compiling xdev..."
        make
    fi

    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
    
    cp xdev "$INSTALL_DIR/xdev"
    chmod +x "$INSTALL_DIR/xdev"
    
    echo "[INFO] Installation complete! 'xdev' has been installed to $INSTALL_DIR/xdev"
    echo "[INFO] Ensure $INSTALL_DIR is present in your PATH variable."
else
    echo "[ERROR] License agreement declined. Installation aborted."
    exit 1
fi