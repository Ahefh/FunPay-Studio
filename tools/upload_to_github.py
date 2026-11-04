"""
FunPay Studio - GitHub Repository Publisher
Allows uploading the showcase landing repository without exposing source code.
Uses standard GitHub REST API (no local git client required).
"""
import base64
import json
import os
import sys
import urllib.request
import urllib.error

def upload_repo(token: str, repo_name: str = "FunPay-Studio", description: str = "⚡️ FunPay Studio (FPS) — Автономная среда для автоматизации продаж и аналитики FunPay"):
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "FunPayStudio-Uploader"
    }

    # 1. Get authenticated user
    try:
        req = urllib.request.Request("https://api.github.com/user", headers=headers)
        with urllib.request.urlopen(req) as resp:
            user_data = json.loads(resp.read().decode("utf-8"))
            username = user_data.get("login")
            print(f"[+] Авторизован как GitHub пользователь: {username}")
    except urllib.error.HTTPError as e:
        print(f"[-] Ошибка авторизации токена GitHub: {e.code} {e.reason}")
        return False

    # 2. Check or create repository
    repo_url = f"https://api.github.com/repos/{username}/{repo_name}"
    exists = False
    try:
        req = urllib.request.Request(repo_url, headers=headers)
        with urllib.request.urlopen(req) as resp:
            exists = True
            print(f"[!] Репозиторий {username}/{repo_name} уже существует. Будет выполнено обновление файлов.")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            exists = False
        else:
            print(f"[-] Ошибка проверки репозитория: {e}")
            return False

    if not exists:
        create_payload = {
            "name": repo_name,
            "description": description,
            "private": False,
            "has_issues": True,
            "has_projects": True,
            "has_wiki": False
        }
        req = urllib.request.Request(
            "https://api.github.com/user/repos",
            data=json.dumps(create_payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"[+] Репозиторий {username}/{repo_name} успешно создан!")
        except urllib.error.HTTPError as e:
            print(f"[-] Не удалось создать репозиторий: {e.read().decode('utf-8')}")
            return False

    # 3. Upload files from github_release directory
    release_dir = r"C:\Bots\FunPayStudio\github_release"
    files_to_upload = ["README.md", "LICENSE"]

    for filename in files_to_upload:
        file_path = os.path.join(release_dir, filename)
        if not os.path.exists(file_path):
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        b64_content = base64.b64encode(content.encode("utf-8")).decode("ascii")

        # Check existing file sha (needed for update)
        file_api_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{filename}"
        sha = None
        try:
            req = urllib.request.Request(file_api_url, headers=headers)
            with urllib.request.urlopen(req) as resp:
                cur_data = json.loads(resp.read().decode("utf-8"))
                sha = cur_data.get("sha")
        except urllib.error.HTTPError:
            sha = None

        commit_payload = {
            "message": f"Release: Initial publication of {filename} (FunPay Studio 2026)",
            "content": b64_content
        }
        if sha:
            commit_payload["sha"] = sha

        req = urllib.request.Request(
            file_api_url,
            data=json.dumps(commit_payload).encode("utf-8"),
            headers=headers,
            method="PUT"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"[+] Файл {filename} успешно опубликован в репозитории!")
        except urllib.error.HTTPError as e:
            print(f"[-] Ошибка загрузки {filename}: {e.read().decode('utf-8')}")
            return False

    print(f"\n[🚀] УСПЕШНО ОПУБЛИКОВАНО: https://github.com/{username}/{repo_name}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        token = sys.argv[1].strip()
        repo = sys.argv[2].strip() if len(sys.argv) > 2 else "FunPay-Studio"
        upload_repo(token, repo)
    else:
        print("Использование: python upload_to_github.py <GITHUB_PERSONAL_ACCESS_TOKEN> [repo_name]")
