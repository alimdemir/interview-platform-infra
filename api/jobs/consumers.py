import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .models import Job, JobEvent


class JobProgressConsumer(AsyncJsonWebsocketConsumer):
    """Bir görevin ilerleme olaylarını sırayla gönderir; arayüz sayfayı yenilemeden güncellenir."""

    @classmethod
    async def encode_json(cls, content):
        # Türkçe karakterler \u kaçışına dönüşmesin (json.dumps varsayılanı ensure_ascii=True)
        return json.dumps(content, ensure_ascii=False)

    async def connect(self):
        self.job_id = self.scope["url_route"]["kwargs"]["job_id"]
        if not await self.job_exists():
            await self.close(code=4404)  # olmayan görev: bağlantı kabul edilmez
            return
        await self.accept()
        await self.send_json({"type": "status", "message": "bağlandı"})
        for event in await self.get_events():
            await asyncio.sleep(0.3)  # olayların zaman içinde gelmesini taklit eder
            await self.send_json({"type": "event", **event})

    @database_sync_to_async
    def job_exists(self):
        return Job.objects.filter(pk=self.job_id).exists()

    @database_sync_to_async
    def get_events(self):
        qs = JobEvent.objects.filter(job_id=self.job_id).order_by("seq")
        return [{"seq": e.seq, "level": e.get_level_display(), "message": e.message} for e in qs]
