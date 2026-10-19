"""Danh gia mini: so sanh LLM thuan, Search + LLM va Research Agent tren cung bo cau hoi.
Chay tu thu muc goc du an:  python eval/run_eval.py
Can: gateway OpenClaw dang chay; bien OLLAMA_MODEL = ten model trong Ollama."""
import csv, json, os, re, shutil, subprocess, sys, time, uuid, pathlib
from openai import OpenAI

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "results"
OFFICIAL = ("nvd.nist.gov", "osv.dev", "github.com/advisories", "cisa.gov")
OPENCLAW = shutil.which("openclaw") or "openclaw"

QUESTION = ("{cve} trong goi {ecosystem} {package}: muc do nghiem trong (critical/high/medium/low) "
            "la gi, nhung phien ban nao da va? Ghi ro nguon kem link.")

METHODS = {
    "B1 LLM thuan": None,
    "B2 Search + LLM": "Chi dung web_search dung 1 lan, khong dung web_fetch, khong dung skill nao. "
                       "Tra loi tu cac doan trich tim duoc. ",
    "B3 Research Agent": "Dung skill cve-research. ",
}


def ask_llm_only(question: str) -> str:
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    r = client.chat.completions.create(model=os.environ["OLLAMA_MODEL"],
                                       messages=[{"role": "user", "content": question}])
    return r.choices[0].message.content or ""


def ask_openclaw(message: str) -> str:
    cmd = [OPENCLAW, "agent", "--agent", "main", "--session-id", f"eval-{uuid.uuid4().hex[:8]}",
           "--message", message]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    return p.stdout + ("\n[stderr] " + p.stderr if p.returncode else "")


def score(answer: str, truth: dict) -> dict:
    text = answer.lower()
    sev_ok = truth["severity"].lower() in text
    found = [v for v in truth["fixed_versions"] if v.lower() in text]
    links = re.findall(r"https?://[^\s)\]>\"']+", answer)
    facts = 1 + len(truth["fixed_versions"])
    return {
        "severity_ok": int(sev_ok),
        "fixed_found": f"{len(found)}/{len(truth['fixed_versions'])}",
        "coverage": round((int(sev_ok) + len(found)) / facts, 2),
        "n_links": len(set(links)),
        "official_link": int(any(o in l for l in links for o in OFFICIAL)),
    }


def main():
    OUT.mkdir(exist_ok=True)
    tests = json.loads((ROOT / "testset.json").read_text(encoding="utf-8"))
    rows = []
    for t in tests:
        q = QUESTION.format(cve=t["cve_id"], ecosystem=t["ecosystem"], package=t["package"])
        for name, prefix in METHODS.items():
            start = time.time()
            try:
                ans = ask_llm_only(q) if prefix is None else ask_openclaw(prefix + q)
            except Exception as e:  # ghi loi lai, khong dung ca dot chay
                ans = f"[loi] {e}"
            secs = round(time.time() - start, 1)
            safe = t["cve_id"] + "_" + name.split()[0]
            (OUT / f"{safe}.md").write_text(ans, encoding="utf-8")
            row = {"cve": t["cve_id"], "group": t.get("group", ""), "method": name, "seconds": secs, **score(ans, t)}
            rows.append(row)
            print(row, flush=True)

    with open(OUT / "results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("\n=== Tong hop ===")
    for name in METHODS:
        rs = [r for r in rows if r["method"] == name]
        n = len(rs)
        print(f"{name:20s} dung muc do {sum(r['severity_ok'] for r in rs)}/{n} | "
              f"bao phu TB {sum(r['coverage'] for r in rs) / n:.2f} | "
              f"co link chinh thuc {sum(r['official_link'] for r in rs)}/{n} | "
              f"thoi gian TB {sum(r['seconds'] for r in rs) / n:.0f}s")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
