# Mini CVE Research Agent (OpenClaw + Ollama)

Bài tập dựng thử Research Agent cho đề tài NCKH. Hướng dẫn từng bước nằm trong tài liệu
"Mini CVE Research Agent trên OpenClaw + Ollama".

## Cài nhanh (Windows, PowerShell)

    cd F:\Nhom9\NC\mini-cve-agent
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install -r requirements.txt

Đưa skill vào workspace OpenClaw (đổi đường dẫn nếu workspace ở chỗ khác):

    mkdir "$HOME\.openclaw\workspace\skills" -Force
    New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace\skills\cve-lookup" -Target "F:\Nhom9\NC\mini-cve-agent\skills\cve-lookup"
    New-Item -ItemType Junction -Path "$HOME\.openclaw\workspace\skills\cve-research" -Target "F:\Nhom9\NC\mini-cve-agent\skills\cve-research"
    openclaw gateway restart

Nếu giải nén ở thư mục khác F:\Nhom9\NC\mini-cve-agent, sửa đường dẫn python.exe trong hai file SKILL.md.

## Cấu hình an toàn

- Gateway OpenClaw (cổng 18789) và Ollama (cổng 11434) chỉ nghe trên 127.0.0.1.
- openclaw.json, .env không được commit (đã có trong .gitignore).
- Chỉ cho phép agent chạy python.exe của dự án với các script trong skills/.
