"""Konteynerin içinden /health/ ucuna istek atıp durum kodunu ve yanıtı yazdırır.

Kullanım: docker exec <konteyner> python healthcheck.py [adres]
"""
import sys
import urllib.error
import urllib.request

url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/health/"
try:
    with urllib.request.urlopen(url, timeout=5) as resp:
        print(resp.status, resp.read().decode())
except urllib.error.HTTPError as exc:  # uygulama yanıt verdi ama hata koduyla
    print(exc.code, exc.read().decode())
    sys.exit(1)
except OSError as exc:  # uygulamaya hiç ulaşılamadı
    print("bağlantı yok:", exc.__class__.__name__)
    sys.exit(2)
