import subprocess
import os
import time
from datetime import datetime

def auto_git_push():
    repo_url = os.environ.get("GIT_REPO_URL")
    git_email = os.environ.get("GIT_EMAIL")
    git_name = os.environ.get("GIT_NAME")

    if not repo_url or not git_email or not git_name:
        print("❌ Gitの環境変数が設定されていません。")
        return

    # Git設定
    subprocess.run(["git", "config", "--global", "user.email", git_email])
    subprocess.run(["git", "config", "--global", "user.name", git_name])

    # ステージング
    subprocess.run(["git", "add", "data"])

    # コミット
    commit_msg = f"Auto backup: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    subprocess.run(["git", "commit", "-m", commit_msg])

    # Push
    result = subprocess.run(["git", "push", repo_url, "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("✅ 自動バックアップをGitHubにPushしました。")
    else:
        print("❌ GitHubへのPushに失敗しました:")
        print(result.stderr)

# 1日に1回Pushする（例：6時間おきに実行）
if __name__ == "__main__":
    while True:
        auto_git_push()
        time.sleep(6 * 60 * 60)  # 6時間 = 21600秒
