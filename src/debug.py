import sys
import pkg_resources
import importlib

print("=" * 50)
print("Python Debug Information")
print("=" * 50)
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path}")

print("\n" + "=" * 50)
print("Installed Packages")
print("=" * 50)

# List all installed packages
installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
for package, version in sorted(installed_packages.items()):
    print(f"{package}: {version}")

print("\n" + "=" * 50)
print("Aiogram Import Test")
print("=" * 50)

try:
    import aiogram
    print(f"✓ aiogram imported successfully")
    print(f"  Version: {aiogram.__version__}")
    print(f"  Location: {aiogram.__file__}")
    
    # Try to check available modules
    print("\nChecking aiogram modules:")
    try:
        from aiogram.client.default import DefaultBotProperties
        print("✓ aiogram.client.default.DefaultBotProperties available")
    except ImportError as e:
        print(f"✗ aiogram.client.default.DefaultBotProperties: {e}")
        
    try:
        from aiogram import Bot
        print("✓ aiogram.Bot available")
    except ImportError as e:
        print(f"✗ aiogram.Bot: {e}")
        
except ImportError as e:
    print(f"✗ Failed to import aiogram: {e}")

print("\n" + "=" * 50)
print("Environment Variables")
print("=" * 50)
import os
for key in ['BOT_TOKEN', 'SUPER_ADMIN_ID', 'ADMIN_GROUP_ID', 'DATABASE_URL']:
    value = os.getenv(key)
    if value:
        masked = value[:10] + "..." if len(value) > 10 else value
        print(f"{key}: {masked}")
    else:
        print(f"{key}: Not set")
