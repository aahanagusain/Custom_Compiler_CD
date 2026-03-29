"""
NoveLang Compiler — Quick Start Script
Run this file to install dependencies and start the server.
"""
import subprocess
import sys
import os

def main():
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
    req_file = os.path.join(backend_dir, 'requirements.txt')
    server_file = os.path.join(backend_dir, 'server.py')

    print("\n" + "=" * 60)
    print("   ⚡  NoveLang AI Compiler — Setup & Launch")
    print("=" * 60)

    # Install dependencies
    print("\n📦 Installing dependencies...")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', req_file, '-q'])
    print("✅ Dependencies installed!")

    # Start server
    print("\n🚀 Starting NoveLang server...")
    print("🌐 Open http://localhost:5000 in your browser\n")
    subprocess.call([sys.executable, server_file])

if __name__ == '__main__':
    main()
