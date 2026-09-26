"""Doctor visit summary: one printable page for the next doctor visit,
built from the medicine list, dose history, companion chats and alerts."""
import html
from datetime import datetime

from core import meds
from core.reminders import IST


def build(profile, taken_today, chat, alerts):
    med_list = profile["medicines"]
    name = profile["name"]
    today = datetime.now(IST).strftime("%d %b %Y")

    # dose history (demo log + what was confirmed today)
    log = profile.get("dose_log", [])
    taken = sum(1 for e in log if e["taken"])
    streak = 0
    for e in reversed(log):
        if e["taken"]:
            break
        streak += 1
    today_ok = [k.split("|")[0] + " (" + k.split("|")[1].split(" ")[0].lower() + ")" for k, v in taken_today.items() if v]

    # things for the doctor to review
    review = []
    for salt, items in meds.duplicates(med_list).items():
        who = ", ".join(f"{i['brand']} (from {i['doctor']})" for i in items)
        review.append(f"Same medicine prescribed twice: {salt.title()}: {who}. Should both continue?")
    for m in med_list:
        left = meds.days_left(m)
        if left is not None and left <= 5:
            review.append(f"{m['brand']} runs out in {left} day(s). Prescription renewal needed?")
    if streak >= 2:
        review.append(f"{streak} doses of {log[-1]['brand']} missed in a row. Is a simpler schedule possible?")

    # concerns from the daily companion (what the patient said when an alert was raised)
    concerns = []
    for i, m in enumerate(chat or []):
        if m.get("role") == "assistant" and m.get("level", "none") != "none" and i > 0:
            concerns.append((m["level"], chat[i - 1]["content"]))

    recent = [a for a in (alerts or []) if not a["type"].startswith("Pharmacy")][:6]

    # ---------- short text (for WhatsApp / SMS) ----------
    lines = [f"Sanjeevani summary for {name}, {today}",
             f"Medicines: {len(med_list)} from {len({m['doctor'] for m in med_list})} doctors.",
             f"Doses taken (recent log): {taken}/{len(log)}."]
    lines += [f"- {r}" for r in review]
    lines += [f"- Patient said: \"{c[:80]}\"" for _, c in concerns[:3]]
    short = "\n".join(lines)

    # ---------- printable page ----------
    e = html.escape
    rows = "".join(
        f"<tr><td>{e(m['brand'])}</td><td>{e(m['salt'])} {e(m['strength'])}</td>"
        f"<td>{e(m['pattern'])}</td><td>{e(m['doctor'])}</td><td>{meds.days_left(m)}</td></tr>" for m in med_list)
    review_html = "".join(f"<li>{e(r)}</li>" for r in review) or "<li>Nothing flagged.</li>"
    concern_html = "".join(f"<li><b>{e(lvl)}</b>: &ldquo;{e(txt)}&rdquo;</li>" for lvl, txt in concerns) \
        or "<li>No worrying messages.</li>"
    alert_html = "".join(f"<li>{e(a['time'])} &middot; {e(a['type'])} &middot; {e(a['message'][:110])}</li>"
                         for a in recent) or "<li>None.</li>"
    page = f"""<!doctype html><html><head><meta charset="utf-8"><title>Sanjeevani summary - {e(name)}</title>
<style>
body{{font-family:'Noto Sans',system-ui,sans-serif;color:#16241C;max-width:820px;margin:24px auto;padding:0 16px}}
h1{{color:#0F3D2E;margin-bottom:0}} h2{{color:#1F6F4A;border-bottom:2px solid #E3EDE7;padding-bottom:4px}}
table{{border-collapse:collapse;width:100%}} th,td{{border:1px solid #CFE3D8;padding:6px 8px;text-align:left}}
th{{background:#EEF5F0}} .meta{{color:#5B6B63}} .flag li{{color:#A93226}} footer{{color:#5B6B63;font-size:.85rem;margin-top:28px}}
</style></head><body>
<h1>Doctor visit summary</h1>
<p class="meta">{e(name)} &middot; {profile['age']} years &middot; {e(profile['village'])} &middot; prepared {today} by Sanjeevani</p>
<h2>Current medicines</h2>
<table><tr><th>Medicine</th><th>Salt</th><th>Morning-Afternoon-Night</th><th>Prescribed by</th><th>Days left</th></tr>{rows}</table>
<h2>Please review</h2><ul class="flag">{review_html}</ul>
<h2>Adherence</h2>
<p>Recent doses taken: <b>{taken} of {len(log)}</b>. Longest current gap: {streak} missed in a row.<br>
Confirmed today: {e(', '.join(today_ok)) or 'none yet'}.</p>
<h2>What the patient told Sanjeevani</h2><ul>{concern_html}</ul>
<h2>Recent alerts</h2><ul>{alert_html}</ul>
<footer>Generated automatically from reminders, photo checks and daily conversations. Not a diagnosis.
All prescribing decisions remain with the treating doctor.</footer>
</body></html>"""
    return short, page
