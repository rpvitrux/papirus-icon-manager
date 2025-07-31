#!/usr/bin/env python3
"""
Papirus Icon Manager for Linux
A comprehensive tool to manage and verify Papirus icon theme usage across all package managers.
Supports APT, Snap, and Flatpak applications on any Linux distribution.
"""

import os
import sys
import glob
import subprocess
import configparser
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
import logging
import argparse
import json

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    GTK_AVAILABLE = True
except ImportError:
    print("Warning: GTK not available. Will use basic file checking instead.")
    GTK_AVAILABLE = False

class PapirusIconManager:
    """Main class for managing Papirus icons across Linux systems."""
    
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.setup_logging()
        
        self.papirus_paths = self._find_papirus_paths()
        self.desktop_paths = {
            'apt': ['/usr/share/applications/', '/usr/local/share/applications/'],
            'flatpak_system': ['/var/lib/flatpak/exports/share/applications/'],
            'flatpak_user': [os.path.expanduser('~/.local/share/flatpak/exports/share/applications/')],
            'snap': ['/var/lib/snapd/desktop/applications/'],
            'user': [os.path.expanduser('~/.local/share/applications/')]
        }
        self.icon_extensions = ['.svg', '.png', '.xpm', '.ico']
        
        if GTK_AVAILABLE:
            self.icon_theme = Gtk.IconTheme.get_default()
        
        # Generic icon suggestions based on app types
        self.generic_icon_mapping = {
            'browser': ['web-browser', 'applications-internet', 'internet-web-browser'],
            'editor': ['text-editor', 'accessories-text-editor', 'applications-development'],
            'media': ['multimedia-player', 'applications-multimedia', 'media-player'],
            'system': ['applications-system', 'preferences-system', 'system-software-update'],
            'terminal': ['utilities-terminal', 'terminal', 'applications-utilities'],
            'files': ['file-manager', 'folder', 'applications-accessories'],
            'office': ['applications-office', 'office-writer', 'text-x-generic'],
            'graphics': ['applications-graphics', 'image-x-generic', 'graphics-viewer'],
            'network': ['applications-internet', 'network-workgroup', 'applications-system'],
            'development': ['applications-development', 'text-editor', 'utilities-terminal'],
            'game': ['applications-games', 'input-gaming', 'applications-other'],
            'audio': ['applications-multimedia', 'audio-x-generic', 'multimedia-player'],
            'video': ['applications-multimedia', 'video-x-generic', 'multimedia-player']
        }
        
        # Keywords for pattern matching
        self.app_type_patterns = {
            'browser': ['browser', 'firefox', 'chrome', 'chromium', 'web', 'safari', 'opera'],
            'editor': ['editor', 'vim', 'nano', 'code', 'atom', 'vscode', 'sublime', 'gedit'],
            'media': ['player', 'vlc', 'mpv', 'music', 'video', 'audio', 'spotify', 'media'],
            'system': ['settings', 'control', 'monitor', 'disk', 'system', 'update', 'upgrade'],
            'terminal': ['terminal', 'console', 'shell', 'bash', 'cmd'],
            'files': ['files', 'nautilus', 'dolphin', 'thunar', 'manager', 'explorer'],
            'office': ['writer', 'calc', 'word', 'excel', 'document', 'office', 'libreoffice'],
            'graphics': ['gimp', 'image', 'photo', 'graphics', 'paint', 'inkscape', 'krita'],
            'network': ['network', 'wifi', 'ethernet', 'connection', 'vpn'],
            'development': ['develop', 'ide', 'compiler', 'debug', 'git'],
            'game': ['game', 'steam', 'play', 'gaming'],
            'audio': ['audio', 'sound', 'music', 'podcast', 'radio'],
            'video': ['video', 'movie', 'film', 'stream', 'youtube']
        }
        
    def setup_logging(self):
        """Setup logging based on debug mode."""
        if self.debug_mode:
            logging.basicConfig(
                level=logging.DEBUG,
                format='[DEBUG] %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format='%(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
        self.logger = logging.getLogger(__name__)
        
    def debug_log(self, message):
        """Log debug messages only in debug mode."""
        if self.debug_mode:
            print(f"    DEBUG: {message}")
            
    def info_log(self, message):
        """Log info messages in both modes."""
        print(message)
        
    def _find_papirus_paths(self) -> List[str]:
        """Find all Papirus icon theme installations."""
        possible_paths = [
            '/usr/share/icons/Papirus',
            '/usr/share/icons/Papirus-Dark',
            '/usr/share/icons/Papirus-Light',
            '/usr/share/icons/ePapirus',
            '/usr/share/icons/ePapirus-Dark',
            os.path.expanduser('~/.icons/Papirus'),
            os.path.expanduser('~/.icons/Papirus-Dark'),
            os.path.expanduser('~/.icons/Papirus-Light'),
            os.path.expanduser('~/.local/share/icons/Papirus'),
            os.path.expanduser('~/.local/share/icons/Papirus-Dark'),
            os.path.expanduser('~/.local/share/icons/Papirus-Light')
        ]
        
        existing_paths = []
        for path in possible_paths:
            if os.path.exists(path):
                existing_paths.append(path)
                self.debug_log(f"Found Papirus theme at: {path}")
        
        if not existing_paths:
            self.info_log("Warning: No Papirus icon themes found on system")
        
        return existing_paths
    
    def _get_current_icon_theme(self) -> Optional[str]:
        """Get the currently active icon theme."""
        try:
            # Try GNOME/GTK settings first
            result = subprocess.run(['gsettings', 'get', 'org.gnome.desktop.interface', 'icon-theme'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                theme = result.stdout.strip().strip("'\"")
                self.debug_log(f"Current icon theme (GNOME): {theme}")
                return theme
        except FileNotFoundError:
            pass
            
        # Try other desktop environments...
        for de, cmd in [
            ('Cinnamon', ['gsettings', 'get', 'org.cinnamon.desktop.interface', 'icon-theme']),
            ('MATE', ['gsettings', 'get', 'org.mate.interface', 'icon-theme']),
            ('XFCE', ['xfconf-query', '-c', 'xsettings', '-p', '/Net/IconThemeName'])
        ]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    theme = result.stdout.strip().strip("'\"")
                    self.debug_log(f"Current icon theme ({de}): {theme}")
                    return theme
            except FileNotFoundError:
                continue
        
        self.debug_log("Could not determine current icon theme")
        return None
    
    def _get_package_type(self, filepath):
        """Determine package type from file path."""
        if '/snap' in filepath:
            return 'SNAP'
        elif '/flatpak' in filepath:
            return 'FLATPAK'
        elif filepath.startswith(os.path.expanduser('~')):
            return 'USER'
        else:
            return 'APT'
    
    def _parse_desktop_file(self, filepath):
        """Parse desktop file and extract app info."""
        try:
            config = configparser.ConfigParser(interpolation=None)
            config.read(filepath, encoding='utf-8')
            
            if 'Desktop Entry' not in config:
                return None
            
            entry = config['Desktop Entry']
            
            # Skip if not an application
            if entry.get('Type', '').lower() != 'application':
                return None
            
            # Skip if NoDisplay is true
            if entry.get('NoDisplay', '').lower() == 'true':
                return None
            
            name = entry.get('Name', os.path.basename(filepath))
            icon = entry.get('Icon', '')
            
            return {
                'name': name,
                'icon': icon,
                'exec': entry.get('Exec', ''),
                'categories': entry.get('Categories', ''),
                'comment': entry.get('Comment', ''),
                'file_path': filepath,
                'package_type': self._get_package_type(filepath)
            }
            
        except Exception as e:
            self.debug_log(f"Error parsing {filepath}: {e}")
            return None
    
    def _resolve_icon_path(self, icon_name):
        """Resolve the actual path of an icon using GTK."""
        if not GTK_AVAILABLE or not icon_name:
            self.debug_log(f"GTK_AVAILABLE={GTK_AVAILABLE}, icon_name='{icon_name}'")
            return None
        
        try:
            # Only remove actual file extensions, not reverse-DNS parts
            if icon_name.endswith(('.png', '.svg', '.xpm', '.ico')):
                icon_base = os.path.splitext(icon_name)[0]
            else:
                icon_base = icon_name
            
            self.debug_log(f"Resolving icon '{icon_name}' (base: '{icon_base}')")
            
            # If it's already a full path, return it
            if icon_name.startswith('/') and os.path.exists(icon_name):
                self.debug_log(f"Icon is full path and exists: {icon_name}")
                return icon_name
            
            # Use GTK IconTheme to resolve
            icon_info = self.icon_theme.lookup_icon(icon_base, 48, 0)
            if icon_info:
                resolved_path = icon_info.get_filename()
                self.debug_log(f"GTK resolved '{icon_base}' to: {resolved_path}")
                return resolved_path
            else:
                self.debug_log(f"GTK could not resolve '{icon_base}'")
                return None
            
        except Exception as e:
            self.debug_log(f"Exception resolving icon {icon_name}: {e}")
            return None
    
    def _get_theme_name_from_path(self, icon_path):
        """Extract theme name from icon path."""
        if not icon_path:
            return "unknown"
        
        # Common theme indicators in paths
        theme_indicators = {
            '/Papirus/': 'Papirus',
            '/Papirus-Dark/': 'Papirus-Dark', 
            '/Papirus-Light/': 'Papirus-Light',
            '/ePapirus/': 'ePapirus',
            '/ePapirus-Dark/': 'ePapirus-Dark',
            '/hicolor/': 'hicolor',
            '/Adwaita/': 'Adwaita',
            '/gnome/': 'GNOME',
            '/breeze/': 'Breeze',
            '/oxygen/': 'Oxygen'
        }
        
        for indicator, theme_name in theme_indicators.items():
            if indicator in icon_path:
                return theme_name
        
        # Try to extract from /usr/share/icons/THEME_NAME/ pattern
        if '/icons/' in icon_path:
            parts = icon_path.split('/icons/')
            if len(parts) > 1:
                theme_part = parts[1].split('/')[0]
                return theme_part
        
        return "unknown theme"

    def _is_papirus_icon(self, icon_path):
        """Check if the resolved icon path is from Papirus theme."""
        if not icon_path:
            self.debug_log("No icon path to check")
            return False
        
        self.debug_log(f"Checking if '{icon_path}' is Papirus")
        
        # Check if the path contains any Papirus directory
        for papirus_path in self.papirus_paths:
            if papirus_path in icon_path:
                self.debug_log(f"Found match with Papirus path: {papirus_path}")
                return True
        
        # Also check for common Papirus paths that might not be in our detected list
        papirus_indicators = [
            '/Papirus/',
            '/Papirus-Dark/',
            '/Papirus-Light/',
            '/ePapirus/',
            '/ePapirus-Dark/'
        ]
        
        for indicator in papirus_indicators:
            if indicator in icon_path:
                self.debug_log(f"Found match with Papirus indicator: {indicator}")
                return True
        
        self.debug_log("No Papirus match found")
        return False
    
    def _detect_app_type(self, app_info):
        """Detect app type using multiple methods."""
        app_types = []
        
        # Method 1: Desktop Categories
        categories = app_info['categories'].lower()
        category_mapping = {
            'webbrowser': 'browser',
            'texteditor': 'editor',
            'audioplayer': 'audio',
            'videoplayer': 'video',
            'graphics': 'graphics',
            'office': 'office',
            'development': 'development',
            'system': 'system',
            'network': 'network',
            'game': 'game',
            'consoleonly': 'terminal'
        }
        
        for cat_keyword, app_type in category_mapping.items():
            if cat_keyword in categories:
                app_types.append(app_type)
        
        # Method 2: App name and description pattern matching
        text_to_check = f"{app_info['name']} {app_info['comment']} {app_info['exec']}".lower()
        
        for app_type, keywords in self.app_type_patterns.items():
            if any(keyword in text_to_check for keyword in keywords):
                app_types.append(app_type)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(app_types))
    
    def _find_papirus_icon(self, icon_name):
        """Check if an icon exists in Papirus themes."""
        if not icon_name:
            return None
        
        icon_base = os.path.splitext(icon_name)[0]
        
        # Common icon sizes and categories to check
        sizes = ['scalable', '64x64', '48x48', '32x32', '24x24', '22x22', '16x16']
        categories = ['apps', 'mimetypes', 'actions', 'devices', 'places', 'status', 'categories']
        extensions = ['.svg', '.png']
        
        for papirus_path in self.papirus_paths:
            for size in sizes:
                for category in categories:
                    for ext in extensions:
                        potential_path = os.path.join(papirus_path, size, category, f"{icon_base}{ext}")
                        if os.path.exists(potential_path):
                            return potential_path
        
        return None
    
    def _suggest_papirus_alternatives(self, app_info):
        """Suggest Papirus alternatives using intelligent matching."""
        suggestions = []
        
        # First, try exact icon name
        icon_name = app_info['icon']
        if self._find_papirus_icon(icon_name):
            return [icon_name]  # Already has exact match
        
        # Try variations of the current icon name
        icon_base = os.path.splitext(icon_name)[0]
        variations = [
            icon_base,
            icon_base.lower(),
            icon_base.replace('-', '_'),
            icon_base.replace('_', '-'),
            icon_base.replace(' ', '-'),
            icon_base.replace(' ', '_')
        ]
        
        # For reverse-DNS names, try extracting the app name
        if '.' in icon_base:
            parts = icon_base.split('.')
            if len(parts) > 1:
                app_name = parts[-1]  # Last part usually is the app name
                variations.extend([
                    app_name,
                    app_name.lower(),
                    f"utilities-{app_name}",
                    f"applications-{app_name}",
                    f"{app_name}-icon"
                ])
        
        # Check all variations
        for variation in variations:
            if self._find_papirus_icon(variation):
                suggestions.append(variation)
        
        # If no direct matches, suggest generic icons based on app type
        if not suggestions:
            app_types = self._detect_app_type(app_info)
            self.debug_log(f"Detected app types for {app_info['name']}: {app_types}")
            
            for app_type in app_types:
                if app_type in self.generic_icon_mapping:
                    for generic_icon in self.generic_icon_mapping[app_type]:
                        if self._find_papirus_icon(generic_icon):
                            suggestions.append(generic_icon)
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(suggestions))
    
    def scan_all_applications(self):
        """Scan all applications and check their icon status."""
        self.info_log("Scanning all applications for Papirus icon usage...")
        self.info_log("=" * 60)
        
        if not self.papirus_paths:
            self.info_log("ERROR: No Papirus icon themes found on your system!")
            self.info_log("Install Papirus with: sudo apt install papirus-icon-theme")
            return
        
        if not self.debug_mode:
            self.info_log(f"Found Papirus installations:")
            for path in self.papirus_paths:
                self.info_log(f"  - {path}")
            self.info_log("")
        
        total_apps = 0
        papirus_apps = []
        non_papirus_apps = []
        
        # Iterate over all desktop paths from all package types
        for package_type, paths in self.desktop_paths.items():
            for desktop_dir in paths:
                if not os.path.exists(desktop_dir):
                    continue
                
                self.info_log(f"Checking {desktop_dir}...")
                
                for desktop_file in glob.glob(os.path.join(desktop_dir, "*.desktop")):
                    app_info = self._parse_desktop_file(desktop_file)
                    
                    if not app_info:
                        continue
                    
                    total_apps += 1
                    
                    if self.debug_mode:
                        self.debug_log(f"Processing app '{app_info['name']}' with icon '{app_info['icon']}'")
                    
                    # Resolve the actual icon path
                    icon_path = self._resolve_icon_path(app_info['icon'])
                    is_using_papirus = self._is_papirus_icon(icon_path)
                    
                    if self.debug_mode:
                        self.debug_log(f"Final result - is_using_papirus: {is_using_papirus}")
                        self.info_log("")
                    
                    if is_using_papirus:
                        papirus_apps.append({
                            'app_info': app_info,
                            'resolved_path': icon_path
                        })
                        if self.debug_mode:
                            self.info_log(f"  ✓ {app_info['name']} ({app_info['package_type']}) - Using Papirus")
                            self.info_log(f"    Icon: {app_info['icon']} → {os.path.basename(icon_path) if icon_path else 'unknown'}")
                            self.info_log(f"    Path: {icon_path}")
                        else:
                            self.info_log(f"  ✓ {app_info['name']} ({app_info['package_type']}) - Using Papirus")
                    else:
                        # Check if Papirus alternatives exist
                        papirus_alternatives = self._suggest_papirus_alternatives(app_info)
                        
                        # Determine status message
                        if not icon_path:
                            status_msg = "Could not resolve icon (missing from theme)"
                        else:
                            status_msg = f"Using {self._get_theme_name_from_path(icon_path)}"
                        
                        if self.debug_mode:
                            self.info_log(f"  ✗ {app_info['name']} ({app_info['package_type']}) - NOT using Papirus")
                            self.info_log(f"    Icon: {app_info['icon']}")
                            self.info_log(f"    Status: {status_msg}")
                            if icon_path:
                                self.info_log(f"    Current path: {icon_path}")
                            if papirus_alternatives:
                                self.info_log(f"    Papirus alternatives: {', '.join(papirus_alternatives[:3])}")
                            else:
                                self.info_log(f"    No Papirus alternatives found")
                        else:
                            self.info_log(f"  ✗ {app_info['name']} ({app_info['package_type']}) - NOT using Papirus")
                            if papirus_alternatives:
                                self.info_log(f"    Suggested fix: Use '{papirus_alternatives[0]}'")
                        
                        non_papirus_apps.append({
                            'app_info': app_info,
                            'resolved_path': icon_path,
                            'papirus_alternatives': papirus_alternatives
                        })
        
        self._print_summary(total_apps, papirus_apps, non_papirus_apps)
        return non_papirus_apps  # Return apps that need fixing
    
    def _print_summary(self, total_apps, papirus_apps, non_papirus_apps):
        """Print summary of scan results."""
        self.info_log("=" * 60)
        self.info_log("SUMMARY:")
        self.info_log(f"Total applications checked: {total_apps}")
        self.info_log(f"Using Papirus icons: {len(papirus_apps)}")
        self.info_log(f"NOT using Papirus icons: {len(non_papirus_apps)}")
        
        if total_apps > 0:
            percentage = (len(papirus_apps) / total_apps) * 100
            self.info_log(f"Papirus coverage: {percentage:.1f}%")
        
        if non_papirus_apps and not self.debug_mode:
            self.info_log(f"\nApplications that could be improved:")
            by_package_type = {}
            for app_data in non_papirus_apps:
                pkg_type = app_data['app_info']['package_type']
                if pkg_type not in by_package_type:
                    by_package_type[pkg_type] = []
                by_package_type[pkg_type].append(app_data)
            
            for pkg_type, apps in by_package_type.items():
                self.info_log(f"\n{pkg_type} applications ({len(apps)}):")
                for app_data in apps[:5]:  # Show max 5 per type in summary
                    app = app_data['app_info']
                    alternatives = app_data['papirus_alternatives']
                    self.info_log(f"  • {app['name']}")
                    if alternatives:
                        self.info_log(f"    → Could use: {alternatives[0]}")
                    else:
                        self.info_log(f"    → No suitable Papirus icon found")
                
                if len(apps) > 5:
                    self.info_log(f"  ... and {len(apps) - 5} more")
    
    def apply_fixes(self, apps_to_fix, auto_apply=False):
        """Apply icon fixes to applications."""
        if not apps_to_fix:
            self.info_log("No applications need icon fixes!")
            return
        
        self.info_log(f"\nFound {len(apps_to_fix)} applications that could use Papirus icons.")
        
        if not auto_apply:
            response = input("Do you want to apply fixes? (y/n): ").lower().strip()
            if response not in ['y', 'yes']:
                self.info_log("Fixes cancelled.")
                return
        
        fixed_count = 0
        failed_count = 0
        
        for app_data in apps_to_fix:
            app_info = app_data['app_info']
            alternatives = app_data['papirus_alternatives']
            
            if not alternatives:
                continue
            
            best_alternative = alternatives[0]
            
            if not auto_apply:
                self.info_log(f"\nApp: {app_info['name']}")
                self.info_log(f"Current icon: {app_info['icon']}")
                self.info_log(f"Suggested icon: {best_alternative}")
                
                choice = input("Apply this fix? (y/n/s=skip): ").lower().strip()
                if choice in ['n', 'no', 's', 'skip']:
                    continue
            
            if self._update_desktop_file_icon(app_info['file_path'], best_alternative):
                fixed_count += 1
                self.info_log(f"✓ Fixed: {app_info['name']} → {best_alternative}")
            else:
                failed_count += 1
                self.info_log(f"✗ Failed: {app_info['name']}")
        
        self.info_log(f"\nResults: {fixed_count} fixed, {failed_count} failed")
    
    def _update_desktop_file_icon(self, desktop_file_path, new_icon_name):
        """Update the icon in a desktop file."""
        try:
            # Check if we need sudo for system files
            needs_sudo = not os.access(desktop_file_path, os.W_OK)
            
            if needs_sudo:
                # Create user override instead of modifying system file
                user_apps_dir = os.path.expanduser('~/.local/share/applications/')
                os.makedirs(user_apps_dir, exist_ok=True)
                
                override_file = os.path.join(user_apps_dir, os.path.basename(desktop_file_path))
                
                # Copy original file to user directory
                shutil.copy2(desktop_file_path, override_file)
                desktop_file_path = override_file
                self.debug_log(f"Created user override: {override_file}")
            
            # Create backup
            backup_path = f"{desktop_file_path}.backup"
            if not os.path.exists(backup_path):
                shutil.copy2(desktop_file_path, backup_path)
                self.debug_log(f"Created backup: {backup_path}")
            
            # Read and update the file
            config = configparser.ConfigParser()
            config.read(desktop_file_path, encoding='utf-8')
            
            if 'Desktop Entry' in config:
                old_icon = config['Desktop Entry'].get('Icon', '')
                config['Desktop Entry']['Icon'] = new_icon_name
                
                with open(desktop_file_path, 'w', encoding='utf-8') as f:
                    config.write(f)
                
                self.debug_log(f"Updated icon in {desktop_file_path} from '{old_icon}' to '{new_icon_name}'")
                return True
            
        except Exception as e:
            self.debug_log(f"Failed to update {desktop_file_path}: {e}")
            return False
        
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Manage Papirus icons across all Linux package managers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 papirus_manager.py --scan
  python3 papirus_manager.py --scan --fix
  python3 papirus_manager.py --scan --fix --auto
  python3 papirus_manager.py --scan --debug
        """
    )
    
    parser.add_argument('--scan', action='store_true', 
                       help='Scan all applications for Papirus icon coverage')
    parser.add_argument('--fix', action='store_true',
                       help='Apply fixes for missing Papirus icons')
    parser.add_argument('--auto', action='store_true',
                       help='Apply fixes automatically without prompting')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with verbose logging')
    
    args = parser.parse_args()
    
    if not args.scan:
        parser.print_help()
        return
    
    manager = PapirusIconManager(debug_mode=args.debug)
    
    if not manager.papirus_paths:
        print("ERROR: No Papirus icon themes found. Please install Papirus first.")
        print("Install with: sudo apt install papirus-icon-theme")
        return
    
    # Scan applications
    apps_needing_fixes = manager.scan_all_applications()
    
    # Apply fixes if requested
    if args.fix and apps_needing_fixes:
        manager.apply_fixes(apps_needing_fixes, auto_apply=args.auto)

if __name__ == "__main__":
    main()
