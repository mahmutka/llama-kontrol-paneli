# llama-kontrol-paneli

> Yerel LLM laboratuvarı — `llama.cpp` üzerinde **tarayıcıdan çalışan**, modelden bağımsız bir kontrol paneli.

Modeli yükleme ayarlarıyla (GPU katmanı, bağlam, KV cache, RoPE…) ve üretim ayarlarıyla
(temperature, top-k/p, tekrar cezaları, mirostat, DRY, XTC…) **canlı** oynayabileceğin;
yaptığın her değişikliğin etkisini **anında** görebileceğin küçük bir araç.
Ekstra kütüphane gerektirmez — **yalnızca Python standart kütüphanesi** kullanır.

## ✨ Özellikler

- **İki bölümlü panel:** ① *Model Yükleme* (sunucuyu yeniden başlatır) ve ② *Üretim* (canlı, anında).
- **Her ayar için açıklama:** her ayarın yanında bir **ⓘ** butonu — tıklayınca ne işe yaradığını uzun uzun anlatan bir pencere açılır.
- **🧠 Düşünme (reasoning) aç/kapat:** "düşünen" modellerde düşünme aşamasını **canlı** (yeniden başlatmadan) kapatıp doğrudan/hızlı cevap alabilirsin.
- **🎮 Canlı GPU VRAM göstergesi:** VRAM doluluğu çubuğu + RAM'e taşma (shared) miktarı + anlık sparkline grafiği. **AMD / Intel / NVIDIA fark etmez** (Windows performans sayaçları kullanılır, `nvidia-smi` gerekmez).
- **Canlı log:** `llama-server`'ın tüm çıktısı panelde akar — bellek taşması, çökme vb. anında görünür.
- **Hazır profiller + "bozma" çipleri:** Kesin / Dengeli / Yaratıcı profilleri ve modeli kasten bozup ne olduğunu görmek için 🌀 Kaos, 🔥 RoPE'yi boz, 💥 Bellek taşır gibi çipler.
- **Modelden bağımsız:** `models/` klasöründeki ilk `.gguf` dosyasını otomatik seçer (adında `mmproj` geçen dosyayı görsel projektör olarak ayırır).

## 🧩 Mimari

```
Tarayıcı ──HTTP──► kontrol_paneli.py (port 8080) ──proxy──► llama-server.exe (port 8081)
   panel.html        (Python, stdlib)                         (senin seçtiğin parametrelerle)
```

`kontrol_paneli.py` paneli (panel.html) sunar; "Başlat" deyince arka planda `llama-server`'ı
seçtiğin ayarlarla çalıştırır, sohbet isteklerini ona yönlendirir ve çıktısını canlı log olarak gösterir.

## 📦 Gereksinimler

- **Windows** (GPU bellek göstergesi Windows performans sayaçlarını kullanır)
- **Python 3.8+** (ek paket yok)
- **llama.cpp** ikili dosyaları (`bin/` içine) — AMD/Intel için **Vulkan**, NVIDIA için **CUDA** sürümü
- Bir **GGUF model** (`models/` içine)

## 🚀 Kurulum

1. **Bu depoyu klonla:**
   ```bash
   git clone https://github.com/<kullanıcı-adın>/llama-kontrol-paneli.git
   cd llama-kontrol-paneli
   ```

2. **llama.cpp indir → `bin/`:**
   [llama.cpp Releases](https://github.com/ggml-org/llama.cpp/releases) sayfasından sistemine uygun
   sürümü (AMD/Intel = `vulkan`, NVIDIA = `cuda`) indir ve içindeki tüm dosyaları (`llama-server.exe`,
   `llama-cli.exe`, `*.dll`…) `bin/` klasörüne çıkar.

3. **Bir model indir → `models/`:**
   Hugging Face'ten bir `.gguf` model indir (ör. quantize edilmiş 7B–12B bir sohbet modeli) ve
   `models/` klasörüne koy. Çok-kipli (görsel) bir model kullanıyorsan `mmproj-*.gguf` dosyasını da
   aynı klasöre koy — otomatik algılanır.

4. **Paneli başlat:**
   `KONTROL-PANELI.bat` dosyasına çift tıkla. Tarayıcı `http://127.0.0.1:8080` adresinde açılır.
   (Veya elle: `python kontrol_paneli.py`)

## 🖱️ Kullanım

1. Panelde **① Model Yükleme → ▶ Başlat** de (model GPU'ya yüklenir, ~10–20 sn).
2. **② Üretim** ayarlarıyla oyna — bunlar canlıdır, mesaj gönderdikçe etkisini görürsün.
3. Bir ayarın ne yaptığını merak edersen yanındaki **ⓘ** butonuna tıkla.
4. Üstteki **🎮 GPU VRAM** şeridinden belleğin nasıl dolduğunu, taşıp taşmadığını canlı izle.

### Ek başlatıcılar
- `KONTROL-PANELI.bat` — asıl kontrol paneli (önerilen).
- `OYUN-ALANI.bat` — llama.cpp'nin kendi dahili web arayüzü (`playground/`).
- `web-arayuz.bat` — sade `llama-server` web arayüzü.
- `sohbet.bat` — terminalde sohbet (`llama-cli`).

> Tüm `.bat` dosyaları `models/` içindeki ilk `.gguf` modeli otomatik seçer.

## 💡 İyi bilinen birkaç davranış

- **Boş yanıt mı geliyor?** "Düşünen" modeller cevabı ayrı bir `reasoning_content` akışında üretir;
  *Maks. uzunluk* çok düşükse model düşünürken token biter ve cevap boş görünür. Bu panel düşünmeyi
  ayrı gösterir ve istersen **② Üretim → 🧠 Düşünme → KAPAT** ile tamamen kapatabilirsin.
- **VRAM'e biraz taşmak, katmanı CPU'ya bırakmaktan iyidir.** `-ngl` düşükken katmanlar CPU'da
  çalışır ve çok yavaşlar; yüksek `-ngl` ile her şey GPU'da olur (gerekirse bir kısmı RAM'e taşar ama
  hesabı yine GPU yapar). En hızlısı genelde "tüm katmanlar GPU'da" noktasıdır.

## 📄 Lisans

[MIT](LICENSE)

## 🙏 Teşekkür

[ggml-org/llama.cpp](https://github.com/ggml-org/llama.cpp) — bu panel onun üzerine kurulu.
