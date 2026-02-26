#!/bin/bash
# Basit migration script - Cloud Shell'de çalıştırılacak

cd /workspace/backend || exit 1

# Migration'ı çalıştır
python -m scripts.update_coloring_book_product

echo ""
echo "✅ Migration tamamlandı!"
