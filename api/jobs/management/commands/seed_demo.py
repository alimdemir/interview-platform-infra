"""Yerel deneme için örnek (sentetik) bir görev ve ilerleme olaylarını oluşturur."""
from django.core.management.base import BaseCommand

from jobs.models import Job, JobEvent, JobResult

EVENTS = [
    ("info", "Görev sıraya alındı"),
    ("info", "Dosyalar okunuyor: 3 belge"),
    ("warning", "Bir belgede başlık bulunamadı, dosya adı kullanıldı"),
    ("info", "İşleme tamamlandı: 3 belge, 0 hata"),
    ("info", "Sonuç kaydedildi"),
]


class Command(BaseCommand):
    help = "Örnek bir görev ve olaylarını oluşturur; WebSocket adresini yazar."

    def handle(self, *args, **options):
        job, created = Job.objects.get_or_create(
            title="Örnek belge işleme görevi", kind="process",
            defaults={"status": "done", "duration_seconds": 42})
        if created:
            events = [JobEvent.objects.create(job=job, seq=i, level=level, message=msg)
                      for i, (level, msg) in enumerate(EVENTS, start=1)]
            JobResult.objects.create(job=job, source_event=events[3], summary="3 belge işlendi, 1 uyarı.")
        self.stdout.write(self.style.SUCCESS(
            f"Görev #{job.id}: {job.events.count()} olay -> ws://localhost:8000/ws/jobs/{job.id}/"))
