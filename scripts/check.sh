#!/bin/bash
echo "========================================================"
echo "🛡️ ANTIGRAVITY KALİTE KONTROL UZMANI (HALÜSİNASYON ÖNLEYİCİ) 🛡️"
echo "========================================================"
echo ""

# 🟢 1. FRONTEND: TypeScript ve Linter Kontrolü
echo "🔍 [1/2] FRONTEND YAPI VE MANTIK TESTLERİ BAŞLADI (Next.js & React)..."
cd frontend

echo "▶ Tip Kontrolü (TypeScript) Testi çalışıyor..."
npm run type-check
TS_STATUS=$?

echo "▶ Mantık ve Yazım (ESLint) Testi çalışıyor..."
npm run lint
LINT_STATUS=$?

if [ $TS_STATUS -ne 0 ] || [ $LINT_STATUS -ne 0 ]; then
  echo "❌ KANTARDA HATA ÇIKTI: Frontend tarafında kod hataları (veya unutulmuş veri tipleri) mevcut."
  echo ">>> Antigravity, lütfen yukarıdaki kırmızı hataları analiz et ve düzelt."
else
  echo "✅ FRONTEND KONTROLÜ: Mükemmel! Tip hatası veya çökme riski bulunmuyor."
fi
cd ..

echo "--------------------------------------------------------"

# 🔵 2. BACKEND: Python Sözdizimi ve Testler
echo "🔍 [2/2] BACKEND YAPI TESTLERİ BAŞLADI (FastAPI & Python)..."
cd backend

# Temel Python derleme doğrulaması (Sözdizimi Hatası arama)
echo "▶ Python Sözdizimi (Syntax) Kontrolü..."
python3 -m py_compile app/**/*.py 2>/dev/null
PY_STATUS=$?

if [ $PY_STATUS -ne 0 ]; then
  echo "❌ KANTARDA HATA ÇIKTI: Backend python dosyalarında ciddi sözdizimi hataları (girinti hatası vb.) yapılmış."
  echo ">>> Antigravity, yazdığın en son Python backend kodunu tekrar gözden geçir, çökecek!"
else
  echo "✅ BACKEND KONTROLÜ: Syntax hatası yok, kod sağlıklı çalışabilir."
fi

cd ..
echo "========================================================"
echo "🚀 ANTIGRAVITY İÇİN BİLGİ: Eğer yukarıdaki tüm adımlar '✅' onayını aldıysa işi YUSUF'a güvenle teslim edebilirsin."
echo "Eğer işlemde '❌' varsa YUSUF'a DÖNME, hataları fixleyene kadar devam et."
echo "========================================================"
