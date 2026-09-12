from django.test import TestCase, Client
from django.urls import reverse

class HealthCheckAndHomeTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_check_endpoint(self):
        """
        Verify GET /api/health/ returns 200 OK and expected JSON payload.
        """
        response = self.client.get(reverse('api-health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "service": "django-backend"
            }
        )

    def test_home_page_renders_successfully(self):
        """
        Verify GET / returns 200 OK and contains brand text.
        """
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Smart Parking")
        self.assertContains(response, "Availability Platform")
        self.assertContains(response, "Find available parking, compare options, and make smarter parking decisions.")
