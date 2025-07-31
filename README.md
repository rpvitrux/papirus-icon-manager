# Papirus Icon Manager

A comprehensive tool to manage and verify Papirus icon theme usage across all Linux package managers (APT, Snap, Flatpak).

## Features

- **Scan applications** to check which ones are using Papirus icons
- **Automatically fix icons** by updating desktop files to use Papirus alternatives
- **Intelligent suggestions** for finding suitable Papirus icon replacements
- **Safe updates** that create user overrides instead of modifying system files
- **Support for all package managers** (APT, Snap, Flatpak, user-installed apps)

## Requirements

- Python 3.6+
- GTK 3 development libraries (for icon resolution)
- Papirus icon theme installed

## Installation

1. Install Papirus icon theme:
```bash
sudo apt install papirus-icon-theme
```

2. Install GTK development libraries:
```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

3. Download the script:
```bash
wget https://raw.githubusercontent.com/cassius66/papirus-icon-manager/main/papirus_icon_manager.py
chmod +x papirus_icon_manager.py
```

## Usage

### Scan applications
```bash
python3 papirus_icon_manager.py --scan
```

### Scan and fix icons automatically
```bash
python3 papirus_icon_manager.py --scan --fix --auto
```

### Scan and fix icons with prompts
```bash
python3 papirus_icon_manager.py --scan --fix
```

### Debug mode (verbose output)
```bash
python3 papirus_icon_manager.py --scan --debug
```

## How it works

1. **Scans** all desktop files from system and user application directories
2. **Resolves** icon paths using GTK's icon theme system
3. **Identifies** which applications are not using Papirus icons
4. **Suggests** appropriate Papirus alternatives using intelligent matching
5. **Updates** desktop files safely by creating user overrides

## License

MIT License - see LICENSE file for details.
