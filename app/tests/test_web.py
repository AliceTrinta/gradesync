from django.test import TestCase
from django.urls import reverse


class WebViewsTests(TestCase):
    def test_home_renderiza_template_com_sucesso(self):
        response = self.client.get(reverse("app:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GradeSync")
        self.assertContains(response, "GET /api/status/")

    def test_api_status_retorna_json_de_status(self):
        response = self.client.get(reverse("app:api-status"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "app": "GradeSync",
                "version": "0.2.0",
                "endpoints": {
                    "home": "/",
                    "admin": "/admin/",
                },
            },
        )
