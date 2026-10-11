from django.db import models


class Job(models.Model):
    """Uzun süren bir arka plan işi (veri toplama, belge işleme, model çıkarımı)."""

    KIND_CHOICES = [("collect", "Veri toplama"), ("process", "Belge işleme"), ("inference", "Model çıkarımı")]
    STATUS_CHOICES = [("queued", "Sırada"), ("running", "Çalışıyor"), ("done", "Tamamlandı"), ("failed", "Hata")]

    title = models.CharField(max_length=120)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Görev sonucu"
        verbose_name_plural = "Görev sonuçları"
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        verbose_name = "Görev"
        verbose_name_plural = "Görevler"

    def __str__(self):
        return f"{self.title} ({self.get_kind_display()})"


class JobEvent(models.Model):
    """Görevin ilerlemesi sırasında üretilen olay; WebSocket ile arayüze akar."""

    LEVEL_CHOICES = [("info", "Bilgi"), ("warning", "Uyarı"), ("error", "Hata")]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="events")
    seq = models.PositiveIntegerField()
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default="info")
    message = models.TextField()

    class Meta:
        verbose_name = "Görev olayı"
        verbose_name_plural = "Görev olayları"
        ordering = ["job", "seq"]
        indexes = [models.Index(fields=["job", "seq"])]


class JobResult(models.Model):
    """Görevin çıktısı; dayandığı olay silinse de sonuç kaybolmaz."""

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="results")
    source_event = models.ForeignKey(JobEvent, on_delete=models.SET_NULL, null=True, blank=True)
    summary = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Görev sonucu"
        verbose_name_plural = "Görev sonuçları"
