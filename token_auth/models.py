import secrets
from django.db import models


class ApiToken(models.Model):
    """
    Simple API token model for authentication
    """
    token = models.CharField(max_length=64, unique=True, primary_key=True)
    name = models.CharField(max_length=100, help_text="Token description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'api_tokens'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_token():
        """Generate secure random token"""
        return secrets.token_urlsafe(32)

    def __str__(self):
        return f"{self.name} - {self.token[:8]}..."
