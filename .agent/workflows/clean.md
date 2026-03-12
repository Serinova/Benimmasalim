---
description: Geçici dosyaları, build çıktılarını ve logları temizleme
---
// turbo-all

# /clean Workflow

Geçici dosyaları, build çıktılarını ve loglama dosyalarını temizle.

## Adımlar

1. Frontend build cache temizle:
```powershell
Remove-Item -Recurse -Force frontend/.next -ErrorAction SilentlyContinue; Write-Host "frontend/.next temizlendi"
```

2. Python cache temizle:
```powershell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" -Path backend/app | Remove-Item -Recurse -Force; Write-Host "Python __pycache__ temizlendi"
```

3. Geçici dosyaları temizle:
```powershell
Remove-Item -Recurse -Force temp_images -ErrorAction SilentlyContinue; Remove-Item -Recurse -Force temp_analysis -ErrorAction SilentlyContinue; Write-Host "Temp klasörleri temizlendi"
```

4. Root'taki gereksiz dosyaları temizle:
```powershell
Remove-Item -Force doc_content.txt, doc_content_utf8.txt, mupdf_output.txt, read_doc.py, read_doc_mupdf.py -ErrorAction SilentlyContinue; Write-Host "Root geçici dosyalar temizlendi"
```

5. Disk alanını kontrol et:
```powershell
Get-ChildItem -Recurse -File | Sort-Object Length -Descending | Select-Object -First 10 @{N="SizeMB";E={[math]::Round($_.Length/1MB,2)}}, FullName
```

6. Sonucu raporla: "Temizlik tamamlandı — kurtarılan alan: X MB"
