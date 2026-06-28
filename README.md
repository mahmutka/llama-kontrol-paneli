# llama-control-panel

> A local LLM lab — a model-agnostic **browser-based control panel** for `llama.cpp`.

A small tool that lets you tweak model-loading settings (GPU layers, context, KV cache, RoPE…)
and generation settings (temperature, top-k/p, repetition penalties, mirostat, DRY, XTC…)
**live**, and instantly see the effect of every change.
No extra dependencies — it uses **only the Python standard library**.

## ✨ Features

- **Two-section panel:** ① *Model Loading* (restarts the server) and ② *Generation* (live, instant).
- **Per-setting help:** every setting has an **ⓘ** button — click it for a window explaining what it does at length.
- **🧠 Thinking (reasoning) toggle:** for "thinking" models you can turn the thinking phase off **live** (no restart) to get direct, fast answers.
- **🎮 Live GPU VRAM meter:** a usage bar + the amount spilled to RAM (shared) + a live sparkline. **Works for AMD / Intel / NVIDIA** (uses Windows performance counters, no `nvidia-smi` needed).
- **Live log:** all `llama-server` output streams in the panel — memory overflow, crashes, etc. show up instantly.
- **Presets + "break it" chips:** Precise / Balanced / Creative presets, plus chips to intentionally break the model and watch what happens: 🌀 Chaos, 🔥 Break RoPE, 💥 Overflow VRAM.
- **Model-agnostic:** auto-selects the first `.gguf` file in `models/` (a file whose name contains `mmproj` is treated as the vision projector).

## 🧩 Architecture

```
Browser ──HTTP──► control_panel.py (port 8080) ──proxy──► llama-server.exe (port 8081)
   panel.html        (Python, stdlib)                       (with your chosen parameters)
```

`control_panel.py` serves the panel (panel.html); when you click "Start" it launches
`llama-server` in the background with your chosen settings, forwards chat requests to it,
and shows its output as a live log.

## 📦 Requirements

- **Windows** (the GPU memory meter uses Windows performance counters)
- **Python 3.8+** (no extra packages)
- **llama.cpp** binaries (into `bin/`) — **Vulkan** build for AMD/Intel, **CUDA** build for NVIDIA
- A **GGUF model** (into `models/`)

## 🚀 Setup

1. **Clone this repo:**
   ```bash
   git clone https://github.com/<your-username>/llama-control-panel.git
   cd llama-control-panel
   ```

2. **Download llama.cpp → `bin/`:**
   From the [llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases) page, download the
   build for your system (AMD/Intel = `vulkan`, NVIDIA = `cuda`) and extract all of its files
   (`llama-server.exe`, `llama-cli.exe`, `*.dll`…) into the `bin/` folder.

3. **Download a model → `models/`:**
   Get a `.gguf` model from Hugging Face (e.g. a quantized 7B–12B chat model) and put it in the
   `models/` folder. If you use a multimodal (vision) model, also drop the `mmproj-*.gguf` file
   into the same folder — it's auto-detected.

4. **Start the panel:**
   Double-click `CONTROL-PANEL.bat`. Your browser opens at `http://127.0.0.1:8080`.
   (Or manually: `python control_panel.py`)

## 🖱️ Usage

1. In **① Model Loading**, pick a model from the **Model** dropdown (lists every `.gguf` in `models/`; use ↻ refresh after adding a new file), then click **▶ Start** (the model loads onto the GPU, ~10–20 s).
2. Play with the **② Generation** settings — these are live; you see their effect as you send messages.
3. Wondering what a setting does? Click the **ⓘ** button next to it.
4. Watch the **🎮 GPU VRAM** strip at the top to see memory fill up and whether it overflows, live.

### Other launchers
- `CONTROL-PANEL.bat` — the main control panel (recommended).
- `PLAYGROUND.bat` — llama.cpp's own built-in web UI (`playground/`).
- `web-ui.bat` — plain `llama-server` web UI.
- `chat.bat` — chat in the terminal (`llama-cli`).

> All `.bat` files auto-select the first `.gguf` model in `models/`.

## 💡 A few known behaviors

- **Getting empty replies?** "Thinking" models stream the answer in a separate `reasoning_content`
  field; if *Max length* is too low, the model runs out of tokens while thinking and the reply looks
  empty. This panel shows the thinking separately, and you can fully disable it via
  **② Generation → 🧠 Thinking → OFF**.
- **Spilling a bit to VRAM beats leaving layers on the CPU.** With low `-ngl`, layers run on the CPU
  and it gets very slow; with high `-ngl` everything is on the GPU (some of it may spill to RAM, but
  the GPU still does the compute). The fastest point is usually "all layers on the GPU".

## 📄 License

[MIT](LICENSE)

## 🙏 Acknowledgements

[ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) — this panel is built on top of it.
