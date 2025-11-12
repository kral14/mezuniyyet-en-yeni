
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Deploy Script
Hər dəfə deploy edəndə avtomatik commit və push edir
"""

import subprocess
import sys
import os
from datetime import datetime

def run_command(command, check=True, cwd=None):
    """Komanda işlədir və nəticəni qaytarır"""
    try:
        # Cari qovluğu müəyyən et
        if cwd is None:
            cwd = os.getcwd()
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=cwd,
            errors='ignore'  # Encoding xətalarını ignore et
        )
        if check and result.returncode != 0:
            print(f"[XƏTA] Komanda uğursuz oldu: {command}")
            print(f"[XƏTA] Xəta: {result.stderr}")
            sys.exit(1)
        return result
    except Exception as e:
        print(f"[XƏTA] Komanda işlədilərkən xəta: {e}")
        sys.exit(1)

def main():
    print("=" * 50)
    print("  GitHub Deploy Script")
    print("=" * 50)
    print()
    
    # Cari qovluğu müəyyən et
    repo_path = os.getcwd()
    print(f"[INFO] Cari qovluq: {repo_path}")
    
    # Git repository-nin yerini tap (git rev-parse istifadə et)
    result = run_command("git rev-parse --git-dir", check=False, cwd=repo_path)
    if result.returncode != 0:
        # Parent qovluqlarda axtar
        current_path = repo_path
        git_found = False
        while current_path and current_path != os.path.dirname(current_path):
            git_dir = os.path.join(current_path, '.git')
            if os.path.exists(git_dir):
                repo_path = current_path
                git_found = True
                print(f"[INFO] Git repository tapıldı: {repo_path}")
                break
            current_path = os.path.dirname(current_path)
        
        if not git_found:
            print("[XƏTA] Bu qovluq Git repository deyil!")
            print(f"[XƏTA] .git qovluğu tapılmadı")
            input("Davam etmək üçün Enter basın...")
            sys.exit(1)
    else:
        # git rev-parse uğurlu oldu, git dir-in parent qovluğunu al
        git_dir = result.stdout.strip()
        # Normalize path (Windows üçün)
        git_dir = os.path.normpath(git_dir)
        
        if os.path.isdir(git_dir):
            repo_path = os.path.dirname(git_dir)
        elif git_dir.endswith('.git'):
            repo_path = os.path.dirname(git_dir)
        else:
            # Əgər git_dir fayldırsa (worktree və s.), parent qovluğu al
            repo_path = os.path.dirname(git_dir)
        
        # Repository root-u müəyyən et
        result_root = run_command("git rev-parse --show-toplevel", check=False, cwd=repo_path)
        if result_root.returncode == 0:
            repo_path = result_root.stdout.strip()
            repo_path = os.path.normpath(repo_path)
        
        print(f"[INFO] Git repository qovluğu: {repo_path}")
    
    # Git repository yoxlaması
    result = run_command("git status", check=False, cwd=repo_path)
    if result.returncode != 0:
        print("[XƏTA] Git repository yoxlanıla bilmədi!")
        print(f"[XƏTA] Xəta: {result.stderr}")
        input("Davam etmək üçün Enter basın...")
        sys.exit(1)
    
    # Remote repository yoxla və düzəlt
    result = run_command("git remote get-url origin", check=False, cwd=repo_path)
    if result.returncode != 0:
        print("[INFO] Remote repository təyin edilməyib!")
        print("[INFO] Remote repository əlavə edilir...")
        run_command("git remote add origin https://github.com/kral14/mezuniyyet.git", cwd=repo_path)
    else:
        remote_url = result.stdout.strip()
        print(f"[INFO] Mövcud remote: {remote_url}")
        if remote_url != "https://github.com/kral14/mezuniyyet.git":
            print("[INFO] Remote URL düzəldilir...")
            run_command("git remote set-url origin https://github.com/kral14/mezuniyyet.git", cwd=repo_path)
    
    # Cari branch-i al
    result = run_command("git branch --show-current", cwd=repo_path)
    current_branch = result.stdout.strip()
    print(f"[INFO] Cari branch: {current_branch}")
    
    # Commit mesajı yarat (tarix və vaxt ilə)
    commit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Hər dəfə deploy edəndə yeni commit yarat (dəyişiklik olsun ya olmasın)
    print("[INFO] Bütün dəyişikliklər əlavə edilir...")
    run_command("git add .", cwd=repo_path)
    
    # Dəyişiklikləri yoxla
    result = run_command("git status --porcelain", cwd=repo_path)
    if result.stdout.strip():
        print("[INFO] Dəyişikliklər tapıldı, commit yaradılır...")
    else:
        print("[INFO] Yeni dəyişiklik yoxdur, boş commit yaradılır...")
    
    # Commit yarat (hər dəfə)
    commit_message = f"Deploy: {commit_date} - Avtomatik deploy commit"
    print(f"[INFO] Commit yaradılır: {commit_date}")
    
    result = run_command(f'git commit -m "{commit_message}" --allow-empty', check=False, cwd=repo_path)
    if result.returncode != 0:
        # Commit mesajında xüsusi simvollar ola bilər, yenidən cəhd et
        commit_message = f"Deploy: {commit_date} - Avtomatik deploy commit"
        result = run_command(f'git commit -m "{commit_message}" --allow-empty', check=False, cwd=repo_path)
        if result.returncode != 0:
            print("[XƏTA] Commit yaradıla bilmədi!")
            print(f"[XƏTA] Xəta: {result.stderr}")
            input("Davam etmək üçün Enter basın...")
            sys.exit(1)
    
    print(f"[SUCCESS] Commit yaradıldı: {commit_date}")
    
    # Remote-dan son dəyişiklikləri çək
    print("[INFO] Remote repository-dən dəyişikliklər çəkilir...")
    run_command(f"git fetch origin {current_branch}", check=False, cwd=repo_path)
    
    # Local və remote arasında fərq yoxla
    result = run_command(f"git rev-list --count HEAD..origin/{current_branch}", check=False, cwd=repo_path)
    if result.returncode == 0 and result.stdout.strip() and int(result.stdout.strip()) > 0:
        print("[INFO] Remote-da yeni commit-lər var, pull edilir...")
        result = run_command(f"git pull origin {current_branch} --no-edit", check=False, cwd=repo_path)
        if result.returncode != 0:
            print("[XƏTA] Pull uğursuz oldu! Konfliktlər ola bilər.")
            print(f"[XƏTA] Xəta: {result.stderr}")
            input("Davam etmək üçün Enter basın...")
            sys.exit(1)
    
    # Push et
    print("[INFO] Dəyişikliklər GitHub-a göndərilir...")
    result = run_command(f"git push origin {current_branch}", check=False, cwd=repo_path)
    if result.returncode != 0:
        print("[XƏTA] Push uğursuz oldu!")
        print(f"[XƏTA] Xəta: {result.stderr}")
        input("Davam etmək üçün Enter basın...")
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("  [SUCCESS] Deploy tamamlandı!")
    print("=" * 50)
    print(f"[INFO] Repository: https://github.com/kral14/mezuniyyet.git")
    print(f"[INFO] Branch: {current_branch}")
    print()
    input("Davam etmək üçün Enter basın...")

if __name__ == "__main__":
    main()

