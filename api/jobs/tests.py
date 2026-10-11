from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.test import TestCase, TransactionTestCase

from .models import Job, JobEvent, JobResult
from .routing import websocket_urlpatterns


class HealthEndpointTests(TestCase):
    def test_health_reports_database(self):
        """/health/ veritabanı bağlantısını raporlar."""
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"service": "mulakat-api", "db": "ok"})


class ModelTests(TestCase):
    def setUp(self):
        self.job = Job.objects.create(title="Deneme görevi", kind="process")

    def test_events_are_ordered_by_sequence(self):
        """Olaylar sıra numarasına göre döner."""
        JobEvent.objects.create(job=self.job, seq=2, message="ikinci")
        JobEvent.objects.create(job=self.job, seq=1, message="birinci")
        self.assertEqual([e.message for e in self.job.events.all()], ["birinci", "ikinci"])

    def test_deleting_job_removes_events_and_results(self):
        """Görev silinince olayları ve sonuçları da silinir (CASCADE)."""
        event = JobEvent.objects.create(job=self.job, seq=1, message="başladı")
        JobResult.objects.create(job=self.job, source_event=event, summary="özet")
        self.job.delete()
        self.assertEqual(JobEvent.objects.count(), 0)
        self.assertEqual(JobResult.objects.count(), 0)

    def test_result_survives_event_deletion(self):
        """Dayandığı olay silinse de sonuç kalır (SET_NULL)."""
        event = JobEvent.objects.create(job=self.job, seq=1, message="tamamlandı")
        result = JobResult.objects.create(job=self.job, source_event=event, summary="özet")
        event.delete()
        result.refresh_from_db()
        self.assertIsNone(result.source_event)


class JobProgressConsumerTests(TransactionTestCase):
    async def _connect(self, job_id):
        communicator = WebsocketCommunicator(URLRouter(websocket_urlpatterns), f"/ws/jobs/{job_id}/")
        connected, code = await communicator.connect()
        return communicator, connected, code

    async def test_streams_events_in_order(self):
        """WebSocket olayları sıra numarasıyla, sırayla gönderir."""
        job = await Job.objects.acreate(title="Deneme görevi", kind="process")
        await JobEvent.objects.acreate(job=job, seq=2, message="İşleme tamamlandı")
        await JobEvent.objects.acreate(job=job, seq=1, message="Görev sıraya alındı")
        communicator, connected, _ = await self._connect(job.id)
        self.assertTrue(connected)
        self.assertEqual((await communicator.receive_json_from())["type"], "status")
        first = await communicator.receive_json_from(timeout=3)
        second = await communicator.receive_json_from(timeout=3)
        self.assertEqual([first["seq"], second["seq"]], [1, 2])
        self.assertTrue(await communicator.receive_nothing(timeout=1))
        await communicator.disconnect()

    async def test_turkish_characters_are_not_escaped(self):
        """Mesajlardaki Türkçe karakterler \\u kaçışına dönüşmez."""
        job = await Job.objects.acreate(title="Deneme görevi", kind="process")
        await JobEvent.objects.acreate(job=job, seq=1, message="Dosyalar okunuyor: çalışma.pdf")
        communicator, _, _ = await self._connect(job.id)
        await communicator.receive_from()                      # "bağlandı"
        raw = await communicator.receive_from(timeout=3)        # ham metin, JSON çözülmeden
        self.assertIn("çalışma.pdf", raw)
        self.assertNotIn("\\u", raw)
        await communicator.disconnect()

    async def test_unknown_job_is_rejected(self):
        """Olmayan görev için bağlantı 4404 koduyla reddedilir."""
        _, connected, code = await self._connect(999)
        self.assertFalse(connected)
        self.assertEqual(code, 4404)
