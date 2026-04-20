# VLM Model Parametreleri - Detaylı Dokümantasyon

Bu dokümantasyon, VLM (Vision Language Model) arayüzündeki "Gelişmiş" panelinde bulunan inference parametrelerinin açıklamasını ve önerilen değer aralıklarını içerir.

## Parametreler

### 1. max_new_tokens

**Açıklama:**
Modelin üretebileceği maksimum yeni token sayısını belirler. Bu parametre, model yanıtının uzunluğunu doğrudan kontrol eder.

**Etkisi:**
- **Düşük değerler (1-128)**: Çok kısa, öz yanıtlar üretir. Hızlı işlem süresi ve düşük GPU bellek kullanımı.
- **Orta değerler (256-512)**: Dengeli uzunlukta yanıtlar. Çoğu görev için yeterli.
- **Yüksek değerler (1024-4096)**: Uzun, detaylı yanıtlar. Daha fazla GPU bellek ve işlem süresi gerektirir.

**Önerilen Değerler:**
- **Caption/OCR görevleri**: 128-256
- **VQA (Görsel Soru-Cevap)**: 256-512
- **Detaylı açıklamalar**: 512-1024
- **Uzun analizler**: 1024-2048

**Varsayılan**: 256

**Not**: Token sayısı yaklaşık olarak kelime sayısının 0.75 katıdır (İngilizce için).

---

### 2. temperature

**Açıklama:**
Model çıktısının rastgelelik (entropi) seviyesini kontrol eder. Düşük değerler daha deterministik, yüksek değerler daha yaratıcı ama tutarsız sonuçlar üretir.

**Etkisi:**
- **0.0-0.3**: Yüksek determinizm. Aynı girdi için benzer çıktılar. Teknik, kesin görevler için uygun.
- **0.4-0.7**: Dengeli rastgelelik. Yaratıcılık ve tutarlılık arasında denge.
- **0.8-1.0**: Yüksek rastgelelik. Çok yaratıcı ama tutarsız olabilir.

**Önerilen Değerler:**
- **Caption/OCR (kesin görevler)**: 0.1-0.3
- **VQA (dengeli)**: 0.2-0.5
- **Yaratıcı içerik üretimi**: 0.6-0.8

**Varsayılan**: 0.2

**Teknik Detay**: Temperature, logit değerlerini ölçeklendirir. `logit_adjusted = logit / temperature` formülü kullanılır.

---

### 3. top_p (Nucleus Sampling)

**Açıklama:**
Token seçiminde kümülatif olasılık eşiği. Model, olasılık dağılımında belirli bir yüzdeyi kapsayan token'ları dikkate alır.

**Etkisi:**
- **Düşük değerler (0.1-0.5)**: Sadece en olası token'ları seçer. Daha tutarlı ama dar çeşitlilik.
- **Orta değerler (0.7-0.9)**: Dengeli seçim. İyi çeşitlilik ve tutarlılık.
- **Yüksek değerler (0.95-1.0)**: Geniş token havuzu. Daha çeşitli ama bazen alakasız çıktılar.

**Önerilen Değerler:**
- **Kesin görevler (OCR, Detection)**: 0.7-0.9
- **Genel kullanım**: 0.9-0.95
- **Yaratıcı görevler**: 0.95-1.0

**Varsayılan**: 1.0

**Not**: `temperature` ile birlikte kullanılır. Genellikle ikisinden biri yeterlidir.

---

### 4. presence_penalty

**Açıklama:**
Yeni konuları teşvik eder. Daha önce kullanılmış token'ları cezalandırarak modeli farklı konulara yönlendirir.

**Etkisi:**
- **Negatif değerler (-2.0 - 0.0)**: Mevcut konuları güçlendirir. Tekrarı artırır.
- **0.0**: Etkisiz. Varsayılan davranış.
- **Pozitif değerler (0.1-2.0)**: Yeni konuları teşvik eder. Tekrarı azaltır.

**Önerilen Değerler:**
- **Çoğu durum**: 0.0
- **Tekrarı azaltmak**: 0.1-0.3
- **Çok çeşitli yanıtlar**: 0.4-0.6

**Varsayılan**: 0.0

**Kullanım Senaryosu**: Model aynı kelimeleri/fikirleri tekrar ediyorsa artırın.

---

### 5. frequency_penalty

**Açıklama:**
Tekrar eden kelimeleri cezalandırır. Aynı token'ın sık kullanımını azaltır.

**Etkisi:**
- **Negatif değerler (-2.0 - 0.0)**: Tekrarı artırır.
- **0.0**: Etkisiz. Varsayılan davranış.
- **Pozitif değerler (0.1-2.0)**: Tekrarı azaltır. Daha çeşitli kelime kullanımı.

**Önerilen Değerler:**
- **Çoğu durum**: 0.0
- **Tekrarı azaltmak**: 0.1-0.3
- **Aşırı tekrar varsa**: 0.4-0.6

**Varsayılan**: 0.0

**Not**: `presence_penalty` ile benzer ama farklı. `presence_penalty` konu değişikliğini, `frequency_penalty` kelime tekrarını kontrol eder.

---

## Görev Bazında Önerilen Ayarlar

### Caption (Görsel Açıklama)

```
max_new_tokens: 128-256
temperature: 0.1-0.3
top_p: 0.9-1.0
presence_penalty: 0.0
frequency_penalty: 0.0
```

**Gerekçe**: Kısa, tutarlı, kesin açıklamalar için düşük temperature ve orta token limiti.

---

### VQA (Görsel Soru-Cevap)

```
max_new_tokens: 256-512
temperature: 0.2-0.5
top_p: 0.9-0.95
presence_penalty: 0.0-0.1
frequency_penalty: 0.0
```

**Gerekçe**: Dengeli, anlaşılır yanıtlar için orta temperature ve yeterli token limiti.

---

### OCR (Metin Tanıma)

```
max_new_tokens: 128-256
temperature: 0.1-0.2
top_p: 0.8-0.9
presence_penalty: 0.0
frequency_penalty: 0.0
```

**Gerekçe**: Kesin, tekrarlanabilir çıktı için düşük temperature ve dar top_p.

---

### Detection (Nesne Tespiti)

```
max_new_tokens: 256-512
temperature: 0.1-0.3
top_p: 0.9-1.0
presence_penalty: 0.0
frequency_penalty: 0.0
```

**Gerekçe**: Yapılandırılmış JSON çıktı için düşük rastgelelik ve yeterli token limiti.

---

## Genel Öneriler

### Başlangıç İçin (Varsayılan)

```
max_new_tokens: 256
temperature: 0.2
top_p: 1.0
presence_penalty: 0.0
frequency_penalty: 0.0
```

Bu ayarlar çoğu görev için iyi bir başlangıç noktasıdır.

---

### Hızlı Test İçin

```
max_new_tokens: 128
temperature: 0.1
top_p: 0.9
presence_penalty: 0.0
frequency_penalty: 0.0
```

Daha hızlı yanıtlar için optimize edilmiş ayarlar.

---

### Yaratıcı İçerik İçin

```
max_new_tokens: 512
temperature: 0.7
top_p: 0.95
presence_penalty: 0.2
frequency_penalty: 0.1
```

Daha yaratıcı ve çeşitli çıktılar için.

---

## Parametreler Arası İlişkiler

### Temperature vs Top_p

- **Temperature**: Tüm token olasılıklarını etkiler. Daha genel kontrol.
- **Top_p**: Sadece olası token havuzunu sınırlar. Daha hedefli kontrol.
- **Öneri**: Genellikle ikisinden biri yeterlidir. Temperature daha yaygın kullanılır.

### Presence vs Frequency Penalty

- **Presence Penalty**: Konu değişikliğini teşvik eder (semantik seviye).
- **Frequency Penalty**: Kelime tekrarını azaltır (sözdizimi seviyesi).
- **Öneri**: Çoğu durumda 0.0 yeterlidir. Tekrar sorunu varsa artırın.

---

## Performans Etkileri

### İşlem Hızı

- **Düşük max_new_tokens**: Daha hızlı yanıt
- **Düşük temperature**: Daha hızlı token seçimi
- **Yüksek penalty değerleri**: Minimal etki

### GPU Bellek Kullanımı

- **Yüksek max_new_tokens**: Daha fazla bellek
- **Temperature ve top_p**: Minimal etki
- **Penalty değerleri**: Etkisiz

---

## Hata Ayıklama İpuçları

### Model çok kısa yanıt veriyorsa
- `max_new_tokens` değerini artırın (256 → 512)

### Yanıtlar çok rastgele/tutarsızsa
- `temperature` değerini düşürün (0.7 → 0.3)
- `top_p` değerini düşürün (1.0 → 0.9)

### Model aynı kelimeleri tekrar ediyorsa
- `presence_penalty` artırın (0.0 → 0.2)
- `frequency_penalty` artırın (0.0 → 0.2)

### Yanıtlar çok deterministik/sıkıcıysa
- `temperature` artırın (0.2 → 0.5)
- `top_p` artırın (0.9 → 0.95)

---

## Kaynaklar

- OpenAI API Documentation: [Text Generation Parameters](https://platform.openai.com/docs/api-reference/completions)
- vLLM Documentation: [Sampling Parameters](https://docs.vllm.ai/en/latest/serving/decoding_params.html)

---

**Son Güncelleme**: 2024
**Versiyon**: 1.0

