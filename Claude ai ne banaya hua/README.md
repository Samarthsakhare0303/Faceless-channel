# 🎬 Faceless YouTube Bot — 100% Free

Automate your faceless YouTube channel using **GitHub Actions as free cloud compute**.  
No monthly fees. No paid APIs. Works with your **Google One (Jio) storage**.

---

## 🆓 Free Stack — Verified

| Tool | What it does | Cost |
|------|-------------|------|
| **Groq API** (llama-3.3-70b) | Writes the video script | Free (no credit card) |
| **Edge TTS** | Voiceover — 300+ natural voices | Completely free, no account |
| **Pexels API** | Stock footage | Free (20K req/month) |
| **Faster-Whisper** | Auto-captions | Open source, runs on CPU |
| **FFmpeg** | Video editing & assembly | Free |
| **GitHub Actions** (public repo) | Cloud rendering | Unlimited free for public repos |
| **Google Drive** | Video storage | Your Google One (Jio) space |

**Total monthly cost: ₹0**

---

## ⚡ Quick Start (10 minutes)

### Step 1 — Fork this repo
1. Click **Fork** on this GitHub repo
2. Make it **Public** (required for unlimited free GitHub Actions minutes)

### Step 2 — Get your free API keys

**Groq (script generation):**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up free (no credit card)
3. Create an API key

**Pexels (stock footage):**
1. Go to [pexels.com/api](https://www.pexels.com/api/)
2. Sign up free and request an API key (instant approval)

### Step 3 — Add GitHub Secrets
Go to your repo → **Settings → Secrets and variables → Actions → New repository secret**

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `GROQ_API_KEY` | Your Groq API key |
| `PEXELS_API_KEY` | Your Pexels API key |
| `GDRIVE_CREDENTIALS` | Google Drive service account JSON *(see below)* |
| `GDRIVE_FOLDER_ID` | Your Drive folder ID *(see below)* |

### Step 4 — Set up Google Drive (5 minutes)
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a project
3. Enable **Google Drive API** (search in the search bar)
4. Go to **IAM & Admin → Service Accounts → Create Service Account**
5. Name it anything (e.g. `youtube-bot`)
6. Click **Keys → Add Key → JSON** — download the file
7. Open the JSON file, copy **all** the contents
8. Paste it as the `GDRIVE_CREDENTIALS` GitHub Secret
9. In Google Drive, create a folder (e.g. `YouTube Videos`)
10. Right-click the folder → **Share** → paste the `client_email` from the JSON
11. Give it **Editor** access
12. Copy the folder ID from the URL: `drive.google.com/drive/folders/`**THIS_PART**
13. Add that as the `GDRIVE_FOLDER_ID` GitHub Secret

### Step 5 — Generate your first video
Go to **Actions → Generate Faceless Video → Run workflow**

Fill in:
- **Topic**: `10 shocking facts about the human brain`
- **Voice**: `en-US-AriaNeural` (or pick from list below)
- **Keywords**: Leave blank (auto-detected) or add e.g. `brain science, neuroscience`

Click **Run workflow** and watch it go! (~5–10 minutes)

---

## 🎙️ Voice Options (Edge TTS — all free)

### English
| Voice | Style |
|-------|-------|
| `en-US-AriaNeural` | Warm female (default, great for most content) |
| `en-US-GuyNeural` | Deep male (serious/news content) |
| `en-US-JennyNeural` | Friendly female |
| `en-GB-SoniaNeural` | British female |
| `en-AU-NatashaNeural` | Australian female |
| `en-IN-NeerjaNeural` | Indian female |
| `en-IN-PrabhatNeural` | Indian male |

Run `edge-tts --list-voices` locally to see all 300+ voices.

---

## 🔗 n8n Integration (Local Automation)

Import `n8n/n8n_workflow.json` into your local n8n.

**Trigger a video from n8n:**
```json
POST http://localhost:5678/webhook/generate-video
{
  "topic": "5 ways to make passive income in 2025",
  "voice": "en-US-GuyNeural",
  "keywords": "money, passive income, investing",
  "callback_url": "http://YOUR_N8N_IP:5678/webhook/video-done"
}
```

**What happens:**
1. n8n sends this to GitHub via their API
2. GitHub Actions starts the video rendering (~5–10 min)
3. Video uploads to your Google Drive automatically
4. GitHub Actions calls your n8n callback webhook with the Drive link
5. n8n emails/notifies you the video is ready

**GitHub API credential in n8n:**
- Type: `HTTP Header Auth`
- Header name: `Authorization`  
- Value: `Bearer YOUR_GITHUB_PERSONAL_ACCESS_TOKEN`
  
  Get token: GitHub → Settings → Developer Settings → Personal access tokens → Fine-grained → New token → select your repo → `Contents: Read` + `Actions: Write`

---

## 📁 GitHub Storage vs Google Drive

| | GitHub Artifacts | Google Drive |
|--|-----------------|-------------|
| Retention | 7 days (auto-deleted) | Permanent |
| Limit | ~500 MB per run | Your Google One space |
| Access | GitHub UI only | Easy to access/share |
| **Use for** | Backup/fallback | Primary storage ✅ |

> **Recommendation**: Use Google Drive as primary. GitHub artifact is just a 7-day backup in case Drive upload fails.

---

## 🎬 Output Specs

| Property | Value |
|----------|-------|
| Resolution | 1920×1080 (1080p) |
| FPS | 30 |
| Video codec | H.264 |
| Audio codec | AAC 128kbps |
| Captions | Burned-in, white text + black outline |
| Duration | ~90–120 seconds (auto based on script) |

---

## 💡 Tips for YouTube Monetization

1. **Consistency** — Run the workflow daily (use n8n schedule trigger)
2. **Niches that work well**: facts, history, psychology, science, money, motivation
3. **Give Pexels credit** in your video description (required by their terms)
4. **Voice variety** — alternate between voices to keep content fresh
5. **Thumbnails** — GitHub Actions can also generate thumbnails using ImageMagick (ask!)

---

## 🐛 Troubleshooting

**"No footage downloaded"** → Check `PEXELS_API_KEY` secret is set correctly  
**"Groq failed"** → Free tier rate limit hit; script will use topic text directly  
**"Drive upload failed"** → Check service account has Editor access to the folder  
**Video has no sound** → Verify `VOICE` is a valid Edge TTS voice name  
**Action takes >30 min** → Whisper model downloading; first run is slower
