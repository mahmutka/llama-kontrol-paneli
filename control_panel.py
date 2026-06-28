# -*- coding: utf-8 -*-
"""
llama.cpp CONTROL PANEL  (local LLM lab)
----------------------------------------
A small tool that lets you play, from the browser, with both GENERATION
settings (temperature, top_k, ...) and MODEL LOADING settings (-ngl, RoPE
frequency, KV cache type, context, ...). Uses only the Python standard
library (NO extra install).

Model-agnostic: it auto-selects the first .gguf file in models/ (a file
whose name contains "mmproj" is treated as the vision projector).

How it works:
  * This script runs on PANEL_PORT (8080) and serves the UI (panel.html).
  * When you click "Start", it launches llama-server.exe in the background
    on LLAMA_PORT (8081) with the parameters you chose.
  * Chat requests are forwarded from the panel to llama-server (proxy).
  * All llama-server output is captured and shown in the live LOG panel,
    so you can instantly see the model "break" or memory overflow.
"""
import os, sys, json, time, threading, collections, subprocess, urllib.request
from urllib.error import URLError, HTTPError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BASE    = os.path.dirname(os.path.abspath(__file__))
LLAMA   = os.path.join(BASE, "bin", "llama-server.exe")
PANEL_PORT = 8080
LLAMA_PORT = 8081


def find_models():
    """Treat the first .gguf in models/ as the model, the one named 'mmproj' as the projector."""
    mdir = os.path.join(BASE, "models")
    model = mmproj = None
    if os.path.isdir(mdir):
        ggufs = sorted(f for f in os.listdir(mdir) if f.lower().endswith(".gguf"))
        mains = [f for f in ggufs if "mmproj" not in f.lower()]
        mmps  = [f for f in ggufs if "mmproj" in f.lower()]
        if mains:
            model = os.path.join(mdir, mains[0])
        if mmps:
            mmproj = os.path.join(mdir, mmps[0])
    return model, mmproj


MODEL, MMPROJ = find_models()


def list_models():
    """All .gguf files in models/, split into main models and mmproj projectors."""
    mdir = os.path.join(BASE, "models")
    models, mmprojs = [], []
    if os.path.isdir(mdir):
        for f in sorted(os.listdir(mdir)):
            if not f.lower().endswith(".gguf"):
                continue
            (mmprojs if "mmproj" in f.lower() else models).append(f)
    return models, mmprojs


def resolve_paths(cfg):
    """Pick the model/mmproj to launch: the one chosen in the UI, else the auto-detected default."""
    mdir = os.path.join(BASE, "models")
    chosen = os.path.basename((cfg.get("model") or "").strip())
    model = os.path.join(mdir, chosen) if chosen else MODEL
    mmp = os.path.basename((cfg.get("mmproj_file") or "").strip())
    mmproj = os.path.join(mdir, mmp) if mmp else MMPROJ
    return model, mmproj

STATE = {
    "proc": None,
    "config": {},
    "logs": collections.deque(maxlen=600),
    "log_seq": 0,
    "gpu": {"ok": False, "dedicated": 0, "shared": 0, "total": 0, "ts": 0},
    "gpu_want": 0.0,
}
LOCK = threading.Lock()

# ---- GPU memory monitoring (works for AMD/Intel/NVIDIA: Windows perf counters) ----
CREATE_NO_WINDOW = 0x08000000

# Per-adapter "Dedicated Usage" (VRAM) + "Shared Usage" (RAM used when VRAM overflows).
# Picks the adapter using the most VRAM (the card running the model) and prints both as bytes.
PS_GPU = (
    "$g=@{};"
    "(Get-Counter '\\GPU Adapter Memory(*)\\Dedicated Usage',"
    "'\\GPU Adapter Memory(*)\\Shared Usage' -EA SilentlyContinue).CounterSamples|"
    "%{ if($_.Path -match 'memory\\((.+?)\\)\\\\(.+)$'){ $id=$Matches[1];$n=$Matches[2];"
    "if(-not $g.ContainsKey($id)){$g[$id]=@{d=0.0;s=0.0}};"
    "if($n -like 'dedicated*'){$g[$id].d=$_.CookedValue};"
    "if($n -like 'shared*'){$g[$id].s=$_.CookedValue} } };"
    "$b=$g.Values|Sort-Object {$_.d} -Descending|Select-Object -First 1;"
    "if($b){('{0} {1}' -f [long]$b.d,[long]$b.s)}else{'0 0'}"
)


def detect_vram_total():
    """Real VRAM size (bytes). Read from the registry because Win32 AdapterRAM is capped at 4 GB."""
    try:
        import winreg
        base = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, base)
        best, i = 0, 0
        while True:
            try:
                sub = winreg.EnumKey(k, i); i += 1
            except OSError:
                break
            try:
                sk = winreg.OpenKey(k, sub)
                val, _ = winreg.QueryValueEx(sk, "HardwareInformation.qwMemorySize")
                if isinstance(val, int) and val > best:
                    best = val
            except OSError:
                pass
        return best
    except Exception:
        return 0


def gpu_sample_once():
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", PS_GPU],
            capture_output=True, text=True, timeout=8, creationflags=CREATE_NO_WINDOW,
        )
        parts = out.stdout.split()
        if len(parts) >= 2:
            return int(parts[0]), int(parts[1])
    except Exception:
        pass
    return None


def gpu_sampler():
    """Only samples when the browser has asked within the last 5 s (quiet while idle)."""
    while True:
        if time.time() - STATE["gpu_want"] < 5:
            r = gpu_sample_once()
            if r:
                STATE["gpu"].update(dedicated=r[0], shared=r[1], ok=True, ts=time.time())
            time.sleep(1.2)
        else:
            time.sleep(1.0)


def log(line):
    line = line.rstrip("\n")
    STATE["logs"].append(line)
    STATE["log_seq"] += 1


def _reader(proc):
    for raw in iter(proc.stdout.readline, ""):
        if raw == "" and proc.poll() is not None:
            break
        log(raw)
    log("──────── [llama-server PROCESS EXITED] ────────")


def stop_server():
    with LOCK:
        p = STATE["proc"]
        if p and p.poll() is None:
            log("──────── [STOPPING...] ────────")
            try:
                p.terminate()
                try:
                    p.wait(timeout=6)
                except Exception:
                    p.kill()
            except Exception as e:
                log("stop error: %s" % e)
        STATE["proc"] = None


def build_args(cfg):
    model, mmproj = resolve_paths(cfg)
    a = [LLAMA, "-m", model, "--host", "127.0.0.1", "--port", str(LLAMA_PORT)]
    if cfg.get("mmproj", True) and mmproj and os.path.exists(mmproj):
        a += ["--mmproj", mmproj]
    else:
        a += ["--no-mmproj"]
    a += ["-ngl", str(cfg.get("ngl", 40))]
    a += ["-c",   str(cfg.get("ctx", 4096))]
    a += ["-b",   str(cfg.get("batch", 2048))]
    a += ["-ub",  str(cfg.get("ubatch", 512))]
    if str(cfg.get("threads", "")).strip():
        a += ["-t", str(cfg["threads"])]
    if str(cfg.get("threads_batch", "")).strip():
        a += ["-tb", str(cfg["threads_batch"])]
    a += ["-fa", cfg.get("flash_attn", "auto")]
    if str(cfg.get("rope_base", "")).strip():
        a += ["--rope-freq-base", str(cfg["rope_base"])]
    if str(cfg.get("rope_scale", "")).strip():
        a += ["--rope-freq-scale", str(cfg["rope_scale"])]
    if cfg.get("ctk"):
        a += ["-ctk", cfg["ctk"]]
    if cfg.get("ctv"):
        a += ["-ctv", cfg["ctv"]]
    # --- thinking budget (turning it on/off is done live per-request via chat_template_kwargs) ---
    if str(cfg.get("rbudget", "")).strip():
        a += ["--reasoning-budget", str(cfg["rbudget"])]
    # --- other server flags ---
    if str(cfg.get("parallel", "")).strip():
        a += ["-np", str(cfg["parallel"])]
    if cfg.get("nkvo"):
        a += ["-nkvo"]
    if cfg.get("mlock"):
        a += ["--mlock"]
    if cfg.get("no_mmap"):
        a += ["--no-mmap"]
    return a


def start_server(cfg):
    model, _ = resolve_paths(cfg)
    if not model or not os.path.exists(model):
        log("ERROR: no .gguf model found in models/. Download a model and put it there.")
        return False
    stop_server()
    args = build_args(cfg)
    log("")
    log("════════ [STARTING] ════════")
    log(" ".join('"%s"' % x if " " in x else x for x in args))
    log("════════════════════════════")
    try:
        proc = subprocess.Popen(
            args, cwd=BASE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace", bufsize=1,
        )
    except Exception as e:
        log("START ERROR: %s" % e)
        return False
    with LOCK:
        STATE["proc"] = proc
        STATE["config"] = cfg
    threading.Thread(target=_reader, args=(proc,), daemon=True).start()
    return True


def llama_health():
    try:
        with urllib.request.urlopen("http://127.0.0.1:%d/health" % LLAMA_PORT, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def is_running():
    p = STATE["proc"]
    return bool(p and p.poll() is None)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass  # silence the noise

    # -------- helpers --------
    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n) if n else b""

    # -------- GET --------
    def do_GET(self):
        if self.path in ("/", "/index.html", "/panel.html"):
            try:
                with open(os.path.join(BASE, "panel.html"), "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
            return

        if self.path.startswith("/api/status"):
            self._send_json({
                "running": is_running(),
                "healthy": llama_health() if is_running() else False,
                "config": STATE["config"],
                "log_seq": STATE["log_seq"],
            })
            return

        if self.path.startswith("/api/logs"):
            self._send_json({"lines": list(STATE["logs"]), "seq": STATE["log_seq"]})
            return

        if self.path.startswith("/api/gpu"):
            STATE["gpu_want"] = time.time()   # wake the sampler thread
            self._send_json(STATE["gpu"])
            return

        if self.path.startswith("/api/models"):
            models, mmprojs = list_models()
            self._send_json({
                "models": models,
                "mmprojs": mmprojs,
                "default": os.path.basename(MODEL) if MODEL else "",
                "current": os.path.basename(STATE["config"].get("model", "")) if STATE["config"].get("model") else "",
            })
            return

        self._send_json({"error": "not found"}, 404)

    # -------- POST --------
    def do_POST(self):
        if self.path == "/api/start":
            cfg = json.loads(self._read_body() or b"{}")
            ok = start_server(cfg)
            self._send_json({"ok": ok})
            return

        if self.path == "/api/stop":
            stop_server()
            self._send_json({"ok": True})
            return

        if self.path in ("/v1/chat/completions", "/v1/completions", "/completion"):
            self._proxy_stream(self.path, self._read_body())
            return

        self._send_json({"error": "not found"}, 404)

    # -------- forward to llama-server (streaming) --------
    def _proxy_stream(self, path, body):
        if not is_running():
            self._send_json({"error": "Server is off. Click 'Start' first."}, 503)
            return
        url = "http://127.0.0.1:%d%s" % (LLAMA_PORT, path)
        req = urllib.request.Request(
            url, data=body, method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            up = urllib.request.urlopen(req, timeout=900)
        except HTTPError as e:
            detail = e.read().decode("utf-8", "replace")
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(detail)))
            self.end_headers()
            self.wfile.write(detail.encode("utf-8"))
            return
        except URLError as e:
            self._send_json({"error": "could not reach llama-server: %s" % e}, 502)
            return

        self.send_response(200)
        ctype = up.headers.get("Content-Type", "text/event-stream")
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.end_headers()
        try:
            for line in up:           # stream SSE line by line (low latency)
                self.wfile.write(line)
                self.wfile.flush()
        except Exception:
            pass


def main():
    print("=" * 60)
    print(" llama.cpp CONTROL PANEL  (local LLM lab)")
    print(" Open in your browser:  http://127.0.0.1:%d" % PANEL_PORT)
    print(" Press Ctrl+C in this window to quit")
    print("=" * 60)
    if not os.path.exists(LLAMA):
        print("\n[!] WARNING: bin/llama-server.exe missing. Download a llama.cpp release and extract it into bin/.\n")
    if not MODEL:
        print("\n[!] WARNING: no .gguf model in models/. Download a model and put it there.\n")
    else:
        print(" Selected model: %s" % os.path.basename(MODEL))
        if MMPROJ:
            print(" Vision projector: %s" % os.path.basename(MMPROJ))
    STATE["gpu"]["total"] = detect_vram_total()
    threading.Thread(target=gpu_sampler, daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", PANEL_PORT), Handler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop_server()
        srv.server_close()
        print("\nShut down.")


if __name__ == "__main__":
    main()
