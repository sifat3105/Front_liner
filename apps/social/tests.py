from django.test import SimpleTestCase, override_settings
from django.urls import resolve

from apps.social.views import (
    InstagramWebhook,
    TikTokCallback,
    TikTokWebhook,
    WhatsAppBusinessAccountListView,
)


class SocialRoutesTests(SimpleTestCase):
    def test_tiktok_callback_route_exists(self):
        match = resolve("/api/social/tiktok/callback/")
        self.assertIs(match.func.view_class, TikTokCallback)

    def test_instagram_webhook_route_exists(self):
        match = resolve("/api/social/instagram/webhook/")
        self.assertIs(match.func.view_class, InstagramWebhook)

    def test_tiktok_webhook_route_exists(self):
        match = resolve("/api/social/tiktok/webhook/")
        self.assertIs(match.func.view_class, TikTokWebhook)

    @override_settings(
        SECURE_SSL_REDIRECT=False,
        ALLOWED_HOSTS=["testserver", "localhost", "127.0.0.1"],
    )
    def test_facebook_pages_requires_authentication(self):
        response = self.client.get("/api/social/facebook/pages/")
        self.assertEqual(response.status_code, 403)

    def test_whatsapp_accounts_route_exists(self):
        match = resolve("/api/social/whatsapp/accounts/")
        self.assertIs(match.func.view_class, WhatsAppBusinessAccountListView)
