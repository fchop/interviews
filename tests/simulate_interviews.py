"""
Simulate complete interviews against a running app to check configurations for problems.

A simulated participant (an LLM with a persona) answers every interviewer question until the
interview ends. Each transcript is checked for common issues (several questions in one message,
wrong language, leaked labels like "Interviewer:", off-topic flags on reasonable answers, no end).

Usage (from the repository root, with OPENAI_API_KEY set):
    .venv/Scripts/python tests/simulate_interviews.py --endpoint http://127.0.0.1:8000/next \
        --configs Qual_Interview_4.2 Qual_Interview_4.2_DE --runs 3 --out tests/sim_report.md
"""
import argparse, json, re, time, urllib.request, pathlib, datetime, os
from openai import OpenAI

PERSONAS = {
    "en": [
        ("cooperative adult", "You are a 34-year-old adult who did the task carefully. You moved the slider a little after each spin, more after several spins of the same colour, and you kept a rough count of colours. Answer in 1-3 full sentences, in your own everyday words, in English."),
        ("terse adult", "You are a 52-year-old adult who is a bit impatient. You answer briefly, sometimes with just a few words, sometimes 'I don't know' or 'I just went with my gut'. Occasionally say you'd like to move on. Answer in English."),
        ("confused adult", "You are a 23-year-old adult who found the task confusing. You often answer vaguely ('I guessed', 'randomly'), use odd comparisons (e.g. like checking the weather), and sometimes misunderstand the question. Answer in 1-2 sentences in English."),
    ],
    "de": [
        ("kooperativer Erwachsener", "Du bist 34 Jahre alt und hast die Aufgabe sorgfältig gemacht. Du hast den Regler nach jeder Drehung ein Stück bewegt, nach mehreren gleichen Farben mehr, und grob die Farben gezählt. Antworte in 1-3 ganzen Sätzen in Alltagssprache auf Deutsch."),
        ("knapper Erwachsener", "Du bist 52 Jahre alt und etwas ungeduldig. Du antwortest kurz, manchmal nur mit wenigen Wörtern, manchmal 'weiß nicht' oder 'nach Gefühl'. Sag gelegentlich, dass du lieber weitermachen möchtest. Antworte auf Deutsch."),
        ("verwirrter Erwachsener", "Du bist 23 Jahre alt und fandest die Aufgabe verwirrend. Du antwortest oft vage ('geraten', 'zufällig'), benutzt schräge Vergleiche (z.B. wie beim Wetter schauen) und verstehst die Frage manchmal falsch. Antworte in 1-2 Sätzen auf Deutsch."),
    ],
    "en_child": [
        ("cooperative child", "You are an 8-year-old child. You moved the slider towards the colour that came up, a bit for one spin and a lot when the same colour came many times. Answer like an 8-year-old: short, simple sentences, in English."),
        ("shy child", "You are an 8-year-old child who is shy. You give very short answers like 'dunno', 'a bit', 'yes', 'the green one'. Sometimes say you don't understand. Answer in English."),
        ("chatty child", "You are an 8-year-old child who likes to talk and sometimes drifts off topic (mentions your cat or school) but then comes back to the wheel game. Answer in 2-3 simple sentences in English."),
    ],
    "de_child": [
        ("kooperatives Kind", "Du bist 8 Jahre alt. Du hast den Regler zu der Farbe geschoben, die gekommen ist, ein bisschen bei einer Drehung und viel, wenn dieselbe Farbe oft kam. Antworte wie ein 8-jähriges Kind: kurze, einfache Sätze, auf Deutsch."),
        ("schüchternes Kind", "Du bist 8 Jahre alt und schüchtern. Du gibst sehr kurze Antworten wie 'weiß nicht', 'ein bisschen', 'ja', 'das grüne'. Manchmal sagst du, dass du die Frage nicht verstehst. Antworte auf Deutsch."),
        ("redseliges Kind", "Du bist 8 Jahre alt, redest gern und schweifst manchmal ab (erzählst von deiner Katze oder der Schule), kommst dann aber zum Rad-Spiel zurück. Antworte in 2-3 einfachen Sätzen auf Deutsch."),
    ],
}

def persona_group(config):
    child = "age_" in config
    de = config.endswith("_DE")
    return ("de_child" if child else "de") if de else ("en_child" if child else "en")

ENGLISH_MARKERS = re.compile(r"\b(the|you|your|when|how|what|which|slider|spin|wheel|colour|color)\b", re.I)
GERMAN_MARKERS = re.compile(r"\b(Sie|du|wie|was|Regler|Drehung|Rad|Farbe|grün|gelb|haben|hast)\b")

def check_message(cfg, msg):
    issues = []
    body = msg.replace("---END---", "")
    if body.count("?") > 1:
        issues.append("multiple questions in one message")
    if re.match(r"\s*(Interviewer|Interviewee|Assistant|AI)\s*:", body):
        issues.append("leaked speaker label")
    de = cfg.endswith("_DE")
    if de and len(ENGLISH_MARKERS.findall(body)) >= 4 and len(GERMAN_MARKERS.findall(body)) < 2:
        issues.append("English in German interview")
    if not de and len(GERMAN_MARKERS.findall(body)) >= 4 and len(ENGLISH_MARKERS.findall(body)) < 2:
        issues.append("German in English interview")
    if len(body) > 700:
        issues.append(f"very long message ({len(body)} chars)")
    if "{" in body and "}" in body:
        issues.append("unfilled template placeholder")
    return issues

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://127.0.0.1:8000/next")
    ap.add_argument("--configs", nargs="+", required=True)
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out", default="tests/sim_report.md")
    ap.add_argument("--max-turns", type=int, default=30)
    ap.add_argument("--participant-model", default="gpt-6-luna")
    args = ap.parse_args()

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    report = [f"# Simulated interview report ({stamp})\n", f"Endpoint: `{args.endpoint}` · participant model: `{args.participant_model}`\n"]
    summary_rows = []

    def post(sid, cfg, msg):
        body = json.dumps({"session_id": sid, "interview_id": cfg, "user_message": msg}).encode("utf-8")
        req = urllib.request.Request(args.endpoint, data=body, headers={"Content-Type": "application/json; charset=utf-8"})
        if "/Prod" in args.endpoint:
            body = json.dumps({"route": "next", "payload": {"session_id": sid, "interview_id": cfg, "user_message": msg}}).encode("utf-8")
            req = urllib.request.Request(args.endpoint, data=body, headers={"Content-Type": "application/json"})
        return json.load(urllib.request.urlopen(req, timeout=180))

    for cfg in args.configs:
        personas = PERSONAS[persona_group(cfg)]
        for run in range(args.runs):
            name, system = personas[run % len(personas)]
            sid = f"sim-{stamp}-{cfg}-{run+1}"
            transcript, issues, off_topic, ended, error = [], [], 0, False, None
            t0 = time.time()
            try:
                r = post(sid, cfg, "")
                q = r["message"]
                transcript.append(("AI", q)); issues += [(1, i) for i in check_message(cfg, q)]
                history = [{"role": "system", "content": system + " Never mention that you are an AI. Answer only with what the participant would type."}]
                for turn in range(2, args.max_turns + 1):
                    history.append({"role": "user", "content": q.replace("---END---", "")})
                    a = client.chat.completions.create(model=args.participant_model, messages=history, max_completion_tokens=200, extra_body={"reasoning_effort": "none"}).choices[0].message.content.strip()
                    history.append({"role": "assistant", "content": a})
                    transcript.append(("P", a))
                    r = post(sid, cfg, a)
                    if "message" not in r:
                        error = f"server error: {str(r)[:300]}"; break
                    q = r["message"]
                    transcript.append(("AI", q))
                    for i in check_message(cfg, q):
                        issues.append((turn, i))
                    if "understood" in q.lower() and "own words" in q.lower() or q.startswith("Sorry, I did not quite") or q.startswith("Entschuldigung, das habe ich nicht") or "nicht ganz verstanden" in q:
                        off_topic += 1
                        issues.append((turn, f"off-topic flag after participant said: {a[:80]!r}"))
                    if "---END---" in q:
                        ended = True; break
            except Exception as e:
                error = repr(e)[:300]
            n_q = sum(1 for s, _ in transcript if s == "AI")
            summary_rows.append((cfg, run + 1, name, n_q, ended, off_topic, len(issues), error, round(time.time() - t0)))
            report.append(f"\n## {cfg} — run {run+1} ({name})\n")
            report.append(f"AI messages: {n_q} · ended properly: {ended} · off-topic flags: {off_topic} · {round(time.time()-t0)}s" + (f" · **ERROR: {error}**" if error else "") + "\n")
            if issues:
                report.append("\n**Flags:**\n" + "\n".join(f"- turn {t}: {i}" for t, i in issues) + "\n")
            report.append("\n<details><summary>Transcript</summary>\n\n" + "\n\n".join(("**AI:** " if s == "AI" else "> **P:** ") + m for s, m in transcript) + "\n\n</details>\n")

    table = ["\n## Summary\n", "| config | run | persona | AI msgs | ended | off-topic | flags | error | s |", "|---|---|---|---|---|---|---|---|---|"]
    table += [f"| {c} | {r} | {p} | {n} | {'yes' if e else 'NO'} | {o} | {f} | {err or ''} | {s} |" for c, r, p, n, e, o, f, err, s in summary_rows]
    out = pathlib.Path(args.out)
    out.write_text("\n".join(report[:2] + table + report[2:]), encoding="utf-8")
    print("\n".join(table))
    print("report:", out)

if __name__ == "__main__":
    main()
