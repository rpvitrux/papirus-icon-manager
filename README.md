# Papirus Icon Manager

A comprehensive tool to manage and verify Papirus icon theme usage across all Linux package managers (APT, Snap, Flatpak).

## Features

- **Scan applications** to check which ones are using Papirus icons
- **Automatically fix icons** by updating desktop files to use Papirus alternatives
- **Intelligent suggestions** for finding suitable Papirus icon replacements
- **Safe updates** that create user overrides instead of modifying system files
- **Support for all package managers** (APT, Snap, Flatpak, user-installed apps)

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
