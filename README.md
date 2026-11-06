# WORLD TRANSLATOR BOT

Telegram-ൽ text, voice/audio, image, PDF, DOCX, TXT എന്നിവ കൈകാര്യം ചെയ്യാൻ Python 3.11+ ഉപയോഗിച്ചുള്ള translation bot. Bot-ന്റെ display name **WORLD TRANSLATOR** ആണ്. Inline keyboard-ുകളിൽ Telegram-ന്റെ supported blue/green/red button styles ഉപയോഗിക്കുന്നു.

## സവിശേഷതകൾ

- Text translation, automatic source-language detection, source/target language തിരഞ്ഞെടുക്കൽ, swap, retry.
- Voice note/audio-യിൽ നിന്ന് Faster-Whisper ഉപയോഗിച്ച് locally speech-to-text.
- Image OCR-നായി Tesseract; OCR ചെയ്ത text-ും translation-ും തിരികെ നൽകുന്നു.
- PDF, DOCX, TXT-ൽ നിന്ന് text extract ചെയ്ത് translated output file സൃഷ്ടിക്കുന്നു. DOCX output-ൽ paragraph text നിലനിർത്തും; source document-ന്റെ എല്ലാ formatting-വും പുനഃസൃഷ്ടിക്കില്ല. PDF/TXT input-ിന് translated TXT output ആണ്.
- Scanned PDF-കൾക്ക് selectable text ഇല്ലെങ്കിൽ OCR ആവശ്യമെന്ന് അറിയിക്കും.
- Translation: ആദ്യം optional self-hosted LibreTranslate endpoint; അത് നൽകിയിട്ടില്ലെങ്കിൽ Argos Translate local models. Argos-ന്റെ model catalog-ിൽ ആവശ്യമായ language pair ലഭ്യമാണോ എന്നതിനെ ആശ്രയിച്ചിരിക്കും. Model ആദ്യ ഉപയോഗത്തിൽ download/install ചെയ്യാം.
- SQLite, Firebase, MongoDB, cloud translation API keys എന്നിവ ഇല്ല. വിജയകരമായ translation history സൂക്ഷിക്കില്ല. Language preferences, retry ചെയ്യേണ്ട നിലവിലെ failed text എന്നിവ process memory-യിൽ മാത്രം താൽക്കാലികമായി നിലനിൽക്കും; restart-ൽ മായും.

## ആവശ്യമായത്

- Python 3.11+
- Telegram bot token ([@BotFather](https://t.me/BotFather) വഴി സൃഷ്ടിക്കുക)
- Voice transcription-ന് FFmpeg; image OCR-ന് Tesseract executable සහ language-data packages.
- Voice/Argos model-ുകൾ download ചെയ്യാൻ deployment-ൽ internet access, disk, memory, CPU എന്നിവ ആവശ്യമാണ്. കുറഞ്ഞ resource hosting-ൽ ആദ്യ voice request/ആദ്യ language pair മന്ദഗതിയിലാകാം.

## Local setup

```bash
git clone <your-repository-url>
cd WORLD-TRANSLATOR-BOT
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` തുറന്ന് `BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN` എന്നിടത്ത് BotFather നൽകിയ token ഇടുക. `.env` `.gitignore`-ൽ ഉള്ളതിനാൽ GitHub-ലേക്ക് commit ചെയ്യരുത്.

Linux-ൽ OCR/audio tools ആവശ്യമെങ്കിൽ:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg tesseract-ocr tesseract-ocr-eng
```

പിന്നീട്:

```bash
python main.py
```

BotFather-ൽ `/setname` ഉപയോഗിച്ച് display name `WORLD TRANSLATOR` ആക്കാം; `/setdescription` വഴി description, `/setabouttext` വഴി about text നൽകാം. Username BotFather-ൽ പ്രത്യേകം തിരഞ്ഞെടുക്കണം.

## Environment variables

| Variable | നിർബന്ധമോ | അർത്ഥം |
|---|---|---|
| `BOT_TOKEN` | അതെ | BotFather token. Source code-ൽ hardcode ചെയ്യരുത്. |
| `LIBRETRANSLATE_URL` | ഇല്ല | സ്വന്തമായി host ചെയ്ത LibreTranslate-ന്റെ base URL; നൽകാത്തപക്ഷം Argos fallback. |
| `WHISPER_MODEL` | ഇല്ല | Faster-Whisper model; default `tiny`, memory കുറവ്. |
| `MAX_DOWNLOAD_MB` | ഇല്ല | Bot സ്വീകരിക്കുന്ന പരമാവധി download വലുപ്പം; default 20 MB. |
| `TESSERACT_LANGUAGES` | ഇല്ല | Tesseract language codes-ന്റെ `+`-joined പട്ടിക. Installed languages മാത്രം ഉപയോഗിക്കും. |
| `LOG_LEVEL` | ഇല്ല | Python log level; default `INFO`. User-ന്റെ message text log ചെയ്യില്ല. |

## Render deployment

1. ഈ project ഒരു Git repository-യിലേക്ക് push ചെയ്യുക.
2. Render-ൽ **Web Service** ആയി Dockerfile deploy ചെയ്യുക; Blueprint ഉപയോഗിച്ചാൽ `render.yaml` തിരഞ്ഞെടുക്കുക. App Render നൽകുന്ന `PORT`-ൽ bind ചെയ്യുകയും `/health` health endpoint നൽകുകയും ചെയ്യും.
3. Render environment/secrets settings-ൽ `BOT_TOKEN` ചേർക്കുക. `render.yaml`-ൽ ഇത് secret prompt ആയി അടയാളപ്പെടുത്തിയിരിക്കുന്നു (`sync: false`). Token source code, README, public issue എന്നിവയിൽ ഇടരുത്.
4. Deploy കഴിഞ്ഞ് service URL-ലും `/health` path-ലും `200 OK` ലഭിക്കുന്നുണ്ടോ പരിശോധിക്കുക. ആദ്യ Faster-Whisper/Argos model download-ന് സമയംയും disk-ഉം ആവശ്യമായേക്കാം.

`render.yaml`-ൽ `free` plan ആണ്. Free Web Service-ുകൾ idle ആകുമ്പോൾ താൽക്കാലികമായി sleep ചെയ്യാം. Polling bot എല്ലായ്പ്പോഴും online വേണമെങ്കിൽ Render-ന്റെ നിലവിലെ uptime/plan പരിധികൾ പരിശോധിക്കുക.

## Koyeb deployment

1. GitHub repository ബന്ധിപ്പിക്കുക അല്ലെങ്കിൽ source repository നൽകുക.
2. Build-ന് repositoryയിലെ `Dockerfile` തിരഞ്ഞെടുക്കുക.
3. Service type/background worker ആയി run ചെയ്ത് start command `python main.py` (Dockerfile default) ഉപയോഗിക്കുക.
4. Koyeb secrets/environment variables-ൽ `BOT_TOKEN` ചേർക്കുക. Optional variables-ийг প্রয়োজনമുണ്ടെങ്കിൽ മാത്രം ചേർക്കുക.
5. Logs പരിശോധിക്കുക; Telegram long polling ആണ് ഉപയോഗിക്കുന്നത്. Webhook domain ആവശ്യമില്ല.

Platform UI, plan, resource limits മാറാവുന്നതിനാൽ deploy സമയത്തെ provider instructions-നുസരിച്ച് ക്രമീകരിക്കുക. Voice/translation model-ുകൾ ഭാരമേറിയതാണ്; CPU/RAM/disk പരിധി deployment തിരഞ്ഞെടുക്കുമ്പോൾ പരിഗണിക്കുക.

## GitHub-ലേക്ക് upload ചെയ്യൽ

```bash
git init -b main
git add .
git commit -m "Initial WORLD TRANSLATOR bot"
```

GitHub-ൽ repository സൃഷ്ടിച്ച ശേഷം അതിന്റെ URL ഉപയോഗിച്ച്:

```bash
git remote add origin <github-repository-url>
git push -u origin main
```

ആദ്യമായി private repository തിരഞ്ഞെടുക്കുന്നത് നല്ലതാണ്. `.env` commit ആയിട്ടില്ലെന്ന് പരിശോധിക്കുക: `git status --short`.

## Telegram button colors സംബന്ധിച്ച്

Bot API പിന്തുണയ്ക്കുന്ന `primary` (നീല), `success` (പച്ച), `danger` (ചുവപ്പ്) styles inline buttons-ിൽ പ്രയോഗിച്ചിട്ടുണ്ട്. ഏതു shade കാണിക്കണമെന്നത് Telegram app theme/client നിയന്ത്രിക്കുന്നു; സ്വന്തം ഇഷ്ടമുള്ള RGB/HEX നിറം, message bubble നിറം, Telegram chat-ന്റെ മുഴുവൻ layout എന്നിവ bot-ന് മാറ്റാൻ സാധിക്കില്ല. പഴയ Telegram client-ുകളിൽ button styling കാണാതിരിക്കാം. Custom emoji-യ്ക്ക് വേറിട്ട Telegram Premium നിബന്ധനകൾ ഉണ്ടായേക്കാം; ഈ project അത് ആശ്രയിക്കുന്നില്ല.

## Troubleshooting

- **`BOT_TOKEN is missing`**: `.env`-ൽ token ചേർത്തോ, hosting environment variable ശരിയായി നൽകിയോ പരിശോധിക്കുക.
- **Bot പ്രതികരിക്കുന്നില്ല**: token ശരിയാണോ, ഒരേ token ഉപയോഗിച്ച് മറ്റൊരു polling instance ഓടുന്നില്ലേയെന്ന് പരിശോധിക്കുക.
- **Language pair ലഭ്യമല്ല**: Argos catalog-ിൽ ആ pair അല്ലെങ്കിൽ English pivot ലഭ്യമല്ലായിരിക്കാം. വേറെ pair പരീക്ഷിക്കുക അല്ലെങ്കിൽ നിങ്ങളുടെ self-hosted LibreTranslate URL `LIBRETRANSLATE_URL` ആയി നൽകുക.
- **ആദ്യ translation വളരെ മന്ദം**: Argos model download/install നടക്കാം. Network/disk പരിശോധിച്ച് വീണ്ടും ശ്രമിക്കുക.
- **Voice transcribe പരാജയം**: ആദ്യ run-ൽ Faster-Whisper weights download ചെയ്യും; FFmpeg install ചെയ്തിട്ടുണ്ടോ, RAM/disk മതിയോ പരിശോധിക്കുക.
- **OCR-ൽ അക്ഷരങ്ങൾ കാണുന്നില്ല**: ബന്ധപ്പെട്ട Tesseract language package ഇൻസ്റ്റാൾ ചെയ്ത് `TESSERACT_LANGUAGES` ക്രമീകരിക്കുക; വെളിച്ചമുള്ള, വ്യക്തമായ image നൽകുക.
- **Scanned PDF**: PDF-ൽ selectable text ഇല്ലെങ്കിൽ OCR ചെയ്ത് searchable PDF സൃഷ്ടിച്ചതിന് ശേഷം നൽകുക.
- **Inline buttons നിറമില്ല**: Telegram app update ചെയ്യുക. Button style client-ൽ പിന്തുണയ്ക്കണം.

## സുരക്ഷയും സ്വകാര്യതയും

Token environment-ൽ മാത്രം നൽകുക. Temporary file-ുകൾ ഓരോ request-നും temporary directory-യിൽ സൃഷ്ടിച്ച് processing കഴിഞ്ഞാൽ നീക്കം ചെയ്യുന്നു. Database ഇല്ല. വിജയിച്ച translation text സംരക്ഷിക്കുന്നില്ല. Retry-ക്കായി നിലവിലെ failed text process memory-യിൽ മാത്രം താൽക്കാലികമായി വയ്ക്കുന്നു. Public hosting ഉപയോഗിക്കുമ്പോൾ host logs/access policies സ്വയം പരിശോധിക്കുക.
