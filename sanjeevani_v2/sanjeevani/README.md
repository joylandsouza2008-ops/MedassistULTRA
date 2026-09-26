# 🌿 Sanjeevani

**One voice-first AI agent from emergency to recovery to everyday care.**
Built by **Team Orbit**, St Joseph Engineering College, Mangaluru, for the *Agentic AI For Billions* track.

## The problem

- India loses tens of thousands of people to snakebite every year, mostly farmers. Many die because the family goes to the nearest clinic, which has no antivenom.
- After discharge, families get a paper they can't read and medicines they can't afford.
- Elderly people take tablets from several doctors, forget doses, take the wrong strip, or take the same medicine twice under two brand names.

The common problem: **people don't know where the right medicine is, how to take it, or when something is going wrong.**

## What Sanjeevani does

| Who | What the agent does |
|---|---|
| 🚨 **Emergency** (snakebite, dog bite, chest pain) | Understands a voice note in Kannada / Hindi / English, finds the nearest hospital that **actually has** the treatment in stock, alerts the hospital, ambulance and family automatically, and guides safe first aid on the way. |
| 🏥 **After discharge** | Reads the discharge paper or prescription photo, builds a morning / afternoon / night timetable, shows cheaper Jan Aushadhi generics, reserves medicines at a nearby pharmacy, books the follow-up. |
| 💬 **Daily companion** | A caring AI that chats with the patient every day (typed or spoken, in Kannada / Hindi / English): how they feel, sleep, food, medicines. Danger signs (chest pain, a fall, breathlessness) trigger SOS to the family; worrying signs (missed medicines, not eating) send the family a note; talk of self-harm shows the free Tele-MANAS helpline 14416. |
| ⏰ **Reminders & doctor summary** | Schedules the next 24 hours of medicine reminders on the patient's phone (ntfy), so it rings at medicine time even with the website closed. Builds a one-page, printable doctor visit summary: medicines, duplicates, missed doses, running-out medicines and worries from daily chats, and shares a short version with the family on WhatsApp. |
| 🌊 **Disaster mode** (floods, landslides) | Reads hundreds of calls, WhatsApp notes and SMS in Kannada / Hindi / English, scores who is in most danger (trapped, unconscious, snakebite, elderly, water rising), groups reports into rescue zones, and tells the control room which teams to send first (boat, NDRF, medical, antivenom, food). An officer confirms every dispatch. |
| 👵 **Elderly care** | Daily voice check-in at medicine time, photo check of the strip before each tablet (right medicine? expired? already taken?), missed-dose alerts to family, duplicate-medicine detection across doctors, running-out alerts with pharmacy reservation, and a HELP button that switches to emergency mode. |

**Trust by design:** Sanjeevani never diagnoses and never changes a prescription. Anything medical (duplicates, substitutions) is sent to a pharmacist or doctor to confirm. If it can't read a strip, it says so instead of guessing.

## How it works

```
 WhatsApp voice / photo / phone call          (real product)
 Web app screens                              (this demo)
              │
              ▼
      ┌──────────────────┐
      │  Sanjeevani agent │  understand → decide → act → follow up
      └──────────────────┘
        │        │       │
   AI (NVIDIA NIM)  Rules   Shared database
   - read prescription   - hospitals + antivenom / vaccine stock
   - read strip photo    - pharmacies + medicine stock
   - understand voice    - medicines, salts, generic prices
              │
              ▼
   Alerts: hospital, ambulance (108), family, pharmacist
```

## Run it on your laptop

```bash
git clone https://github.com/<your-username>/sanjeevani.git
cd sanjeevani
pip install -r requirements.txt
streamlit run app.py
```

It opens at `http://localhost:8501`. It works **without an API key** in demo mode (sample data instead of AI reading).

### Turn on the AI (NVIDIA NIM)

1. Get a free key at [build.nvidia.com](https://build.nvidia.com) (starts with `nvapi-`).
2. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and paste the key.

`secrets.toml` is in `.gitignore`. **Never put your API key in the code or push it to GitHub.**

### Put it online (free)

1. Push this repo to GitHub (public).
2. Go to [share.streamlit.io](https://share.streamlit.io), pick the repo, main file `app.py`.
3. Add the API key under *Advanced settings → Secrets*.
4. Open the link on a phone for the demo.

## Automatic location

The app asks for location permission as soon as it opens (one tap on **Allow**). After that, the live GPS position is used everywhere: nearest hospital, map, and the Google Maps link sent to the family.

## Family SOS (SMS, alarms, calls)

When an emergency is detected, Sanjeevani reaches the family automatically, with a Google Maps link to the location:

| Channel | Cost | Setup |
|---|---|---|
| Real SMS from your own Android phone's SIM | Free (uses your SIM plan) | Install *SMS Gateway for Android*, Cloud mode, put its username/password in secrets |
| Loud urgent alarm on family phones | Free | Family installs the *ntfy* app and subscribes to your `NTFY_TOPIC` |
| Automatic phone call that speaks the alert | Paid (Twilio) | Optional |
| One-tap Call / SMS / WhatsApp buttons | Free | Nothing |

Family numbers go in the sidebar under **🆘 SOS contacts** (or `SOS_CONTACTS` in secrets). See `.streamlit/secrets.toml.example`.

## Sanjeevani API

The same agent brain as an API, so WhatsApp bots, IVR phone systems, hospital software or a mobile app can use it.

```bash
python -m uvicorn api.main:app --reload
```

Open `http://127.0.0.1:8000/docs` to try every endpoint in the browser.

| Endpoint | What it does |
|---|---|
| `POST /emergency` | Message + location → emergency type, nearest hospital that has the treatment, first aid |
| `GET /hospitals?need=antivenom_vials&village=Kinnigoli` | Hospitals nearest first, filtered by what they have |
| `PATCH /hospitals/{id}/stock` | Hospitals update their stock |
| `POST /medicines/check` | Timetable, duplicate medicines, generic savings |
| `POST /sar/reports` | Add a flood/landslide report, get its priority |
| `GET /sar/zones` | Rescue zones, most urgent first, with teams to send |
| `POST /webhook/whatsapp` | Ready for a Twilio WhatsApp number: replies with the hospital and first aid |

## Demo script (3 minutes)

1. **Emergency:** village *Kinnigoli* → click *Snakebite (Kannada)*. The nearest centre (Mulki) has no antivenom, so Sanjeevani sends the family to Surathkal and alerts everyone.
2. **After discharge:** *Use sample discharge paper* → timetable, generic savings, reserve, follow-up.
3. **Elderly care:** *Photo check* → pick the wrong strip → warning. *Missed doses* → family alerted. *Duplicate medicines* → two amlodipine brands caught. *Running out* → reserve Clopirel. Press **HELP** → emergency mode.
4. **Dashboard:** show every action the agent took.

## Project structure

```
app.py                  Home page
pages/                  Home, Emergency, After discharge, Elderly care, Disaster mode, Dashboard
api/main.py             Sanjeevani API (FastAPI)
core/sar.py             Disaster mode: report scoring and rescue zones
core/ai.py              All AI calls (with fallback so the demo never breaks)
core/emergency.py       Emergency detection, hospital matching, first aid
core/meds.py            Timetable, duplicates, generics, run-out prediction
core/geo.py             Distance and travel time
core/state.py           Alert log
data/                   Fake demo data (hospitals, pharmacies, medicines, patients)
```

## Future scope

- WhatsApp + phone-call (IVR) interface with speech-to-text and spoken replies in Kannada, Tulu, Hindi
- Live stock updates from hospitals and Jan Aushadhi Kendras
- Ayushman Bharat hospital integration, ASHA worker pilots in Dakshina Kannada

## Disclaimer

All hospitals, stock levels, medicine brands, prices and patients in this repo are **made-up demo data**. First-aid text is general guidance only. This is a hackathon prototype, not a medical device.
