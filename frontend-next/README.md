# VLM Frontend - Next.js

Modern, TypeScript tabanlı Next.js frontend uygulaması. FastAPI gateway (http://localhost:9000) ile haberleşir.

## 🚀 Kurulum

```bash
cd frontend-next
npm install
```

## 🔧 Yapılandırma

`.env.local` dosyası oluşturun (opsiyonel):

```bash
NEXT_PUBLIC_VLM_GATEWAY_URL=http://localhost:9000
```

Varsayılan olarak `http://localhost:9000` kullanılır.

## ▶️ Çalıştırma

### Development

```bash
npm run dev
```

Uygulama **http://localhost:3000** adresinde açılır.

### Production Build

```bash
npm run build
npm start
```

## 📁 Proje Yapısı

```
frontend-next/
├── app/                 # Next.js App Router
│   ├── layout.tsx       # Root layout
│   └── page.tsx         # Ana sayfa
├── components/          # React bileşenleri
│   ├── Sidebar.tsx      # Model/görev seçimi ve ayarlar
│   ├── ChatArea.tsx     # Chat mesaj alanı
│   ├── ChatInput.tsx    # Mesaj input
│   ├── MessageBubble.tsx # Mesaj bubble
│   └── ImageUpload.tsx  # Görsel yükleme
├── lib/                 # Utility fonksiyonlar
│   ├── api-client.ts   # FastAPI gateway client
│   └── app-context.tsx # React Context (state management)
├── types/               # TypeScript type definitions
│   ├── api.ts          # API types
│   └── state.ts        # State types
└── styles/              # CSS
    └── globals.css     # Global styles
```

## 🔌 API Entegrasyonu

Frontend, mevcut FastAPI gateway'in tüm endpoint'lerini kullanır:

- `GET /health` - Gateway durumu
- `GET /models` - Model listesi
- `POST /models/{key}/serve` - Model başlat
- `POST /models/stop` - Model durdur
- `POST /threads` - Thread oluştur
- `GET /threads` - Thread listesi
- `DELETE /threads/{id}` - Thread sil
- `POST /threads/{id}/messages` - Mesaj gönder

## 🎨 Özellikler

- ✅ Modern, responsive UI
- ✅ TypeScript ile type-safe
- ✅ React Context ile state management
- ✅ Streamlit'teki tüm özellikler korundu
- ✅ Modüler bileşen yapısı
- ✅ Dark mode desteği (CSS variables)

## 📝 Notlar

- Backend gateway'in çalışıyor olması gerekir (http://localhost:9000)
- vLLM sunucusunun çalışıyor olması önerilir (http://localhost:8000)
- CORS ayarları backend'de yapılmış olmalı

