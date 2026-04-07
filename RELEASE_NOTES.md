# Release Notes

## v0.3.2 - Change of AI-model
claude-haiku-4-5-20251001
## v0.3.0 — Session Management
*2026-04-06*

### What's new
- Each user now gets their own conversation history. Opening the chat in multiple browser windows or devices no longer results in shared context.

### Technical details
- Session IDs are generated client-side using `Math.random()` and sent with each `/chat` request
- Flask maintains a `sessions` dictionary mapping session IDs to individual conversation histories

---

## v0.2.0 — HAOS Add-on & Remote Access
*2026-04-06*

### What's new
- Packaged as a native Home Assistant OS add-on (Docker container)
- Accessible via Nabu Casa remote URL through HA ingress
- Add-on available as a custom GitHub repository — update directly from HA's add-on store
- Switched AI backend from OpenAI to Anthropic (Claude)
- Web chat interface accessible from mobile browser
- Add-on panel added to HA sidebar

### Technical details
- HAOS secrets managed via `config.json` options instead of `.env`
- Ingress support added with `panel_icon` and `panel_title`
- Flask runs in main thread when inside container, with terminal chat loop for local development
- Relative fetch path (`chat` instead of `/chat`) required for ingress routing

---

## v0.1.0 — Foundation
*2026-03-28*

### What's new
- Flask webhook server receiving button triggers
- OpenAI integration with basic yes/no toggle logic
- Home Assistant REST API integration for reading device states
- Devices filtered to `light` and `switch` domains
- Device context (name, entity_id, last_changed) saved to `devices.json` at startup
- Terminal chat loop for local testing
- Secrets managed via `.env` file
- Function calling for real-time device state (`get_device_state`)
- Device control (`set_device_state`) with support for:
  - on/off
  - brightness (0–255)
  - color temperature (Kelvin)
  - RGB color
