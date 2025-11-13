
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Deploy Script
Her defe deploy edende avtomatik commit ve push edir
"""

import subprocess
import sys
import os
from datetime import datetime

# Windows ucun encoding problemi hell et
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def run_command(command, check=True, cwd=None):
    """Komanda isledir ve neticeni qaytarir"""
    try:
        # Cari qovlugu muayyen et
        if cwd is None:
            cwd = os.getcwd()
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=cwd,
            errors='replace'  # Encoding xetalarini replace et
        )
        if check and result.returncode != 0:
            print(f"[XETA] Komanda ugursuz oldu: {command}")
            print(f"[XETA] Xeta: {result.stderr}")
            sys.exit(1)
        return result
    except Exception as e:
        print(f"[XETA] Komanda isledilerken xeta: {e}")
        sys.exit(1)

def main():
    print("=" * 50)
    print("  GitHub Deploy Script")
    print("=" * 50)
    print()
    
    # Cari qovlugu muayyen et
    repo_path = os.path.abspath(os.getcwd())
    print(f"[INFO] Cari qovluq: {repo_path}")
    
    # Git repository-nin yerini tap - sadə yanaşma
    # Windows ucun path-i normalize et
    repo_path = os.path.normpath(repo_path)
    
    # .git qovluğunu tap
    current_path = repo_path
    git_found = False
    while current_path and current_path != os.path.dirname(current_path):
        git_dir = os.path.join(current_path, '.git')
        if os.path.exists(git_dir):
            repo_path = current_path
            git_found = True
            print(f"[INFO] Git repository tapildi: {repo_path}")
            break
        current_path = os.path.dirname(current_path)
    
    if not git_found:
        print("[XETA] Bu qovluq Git repository deyil!")
        print(f"[XETA] .git qovlugu tapilmadi")
        input("Davam etmek ucun Enter basin...")
        sys.exit(1)
    
    print(f"[INFO] Git repository qovlugu: {repo_path}")
    
    # Git repository yoxlaması
    result = run_command("git status", check=False, cwd=repo_path)
    if result.returncode != 0:
        print("[XETA] Git repository yoxlanila bilmedi!")
        print(f"[XETA] Xeta: {result.stderr}")
        input("Davam etmek ucun Enter basin...")
        sys.exit(1)
    
    # Remote repository yoxla ve duzelt
    result = run_command("git remote get-url origin", check=False, cwd=repo_path)
    if result.returncode != 0:
        print("[INFO] Remote repository teyin edilmemis!")
        print("[INFO] Remote repository elave edilir...")
        run_command("git remote add origin https://github.com/kral14/mezuniyyet.git", cwd=repo_path)
    else:
        remote_url = result.stdout.strip()
        print(f"[INFO] Movcud remote: {remote_url}")
        if remote_url != "https://github.com/kral14/mezuniyyet.git":
            print("[INFO] Remote URL duzeldilir...")
            run_command("git remote set-url origin https://github.com/kral14/mezuniyyet.git", cwd=repo_path)
    
    # Cari branch-i al
    result = run_command("git branch --show-current", cwd=repo_path)
    current_branch = result.stdout.strip()
    print(f"[INFO] Cari branch: {current_branch}")
    
    # Commit mesajı yarat (tarix və vaxt ilə)
    commit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Her defe deploy edende yeni commit yarat (deyisiklik olsun ya olmasin)
    print("[INFO] Butun deyisiklikler elave edilir...")
    run_command("git add .", cwd=repo_path)
    
    # Deyisiklikleri yoxla
    result = run_command("git status --porcelain", cwd=repo_path)
    if result.stdout.strip():
        print("[INFO] Deyisiklikler tapildi, commit yaradilir...")
    else:
        print("[INFO] Yeni deyisiklik yoxdur, bos commit yaradilir...")
    
    # Commit yarat (her defe)
    commit_message = f"Deploy: {commit_date} - Avtomatik deploy commit"
    print(f"[INFO] Commit yaradilir: {commit_date}")
    
    result = run_command(f'git commit -m "{commit_message}" --allow-empty', check=False, cwd=repo_path)
    if result.returncode != 0:
        # Commit mesajinda xususi simvollar ola biler, yeniden cehd et
        commit_message = f"Deploy: {commit_date} - Avtomatik deploy commit"
        result = run_command(f'git commit -m "{commit_message}" --allow-empty', check=False, cwd=repo_path)
        if result.returncode != 0:
            print("[XETA] Commit yaradila bilmedi!")
            print(f"[XETA] Xeta: {result.stderr}")
            input("Davam etmek ucun Enter basin...")
            sys.exit(1)
    
    print(f"[SUCCESS] Commit yaradildi: {commit_date}")
    
    # Remote-dan son deyisiklikleri cek
    print("[INFO] Remote repository-den deyisiklikler cekilir...")
    run_command(f"git fetch origin {current_branch}", check=False, cwd=repo_path)
    
    # Local ve remote arasinda ferq yoxla
    result = run_command(f"git rev-list --count HEAD..origin/{current_branch}", check=False, cwd=repo_path)
    if result.returncode == 0 and result.stdout.strip() and int(result.stdout.strip()) > 0:
        print("[INFO] Remote-da yeni commit-ler var, pull edilir...")
        result = run_command(f"git pull origin {current_branch} --no-edit", check=False, cwd=repo_path)
        if result.returncode != 0:
            print("[XETA] Pull ugursuz oldu! Konfliktler ola biler.")
            print(f"[XETA] Xeta: {result.stderr}")
            input("Davam etmek ucun Enter basin...")
            sys.exit(1)
    
    # Push et
    print("[INFO] Deyisiklikler GitHub-a gonderilir...")
    result = run_command(f"git push origin {current_branch}", check=False, cwd=repo_path)
    if result.returncode != 0:
        print("[XETA] Push ugursuz oldu!")
        print(f"[XETA] Xeta: {result.stderr}")
        input("Davam etmek ucun Enter basin...")
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("  [SUCCESS] Deploy tamamlandi!")
    print("=" * 50)
    print(f"[INFO] Repository: https://github.com/kral14/mezuniyyet.git")
    print(f"[INFO] Branch: {current_branch}")
    print()
    input("Davam etmek ucun Enter basin...")

if __name__ == "__main__":
    main()

