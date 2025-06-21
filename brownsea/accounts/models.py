from django.contrib.auth.models import User
from django.db import models


class SSOProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=255, choices=[("google", "Google")])
    sub = models.CharField(max_length=255, db_index=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["provider", "sub"], name="unique_sso_profile")]

    def __str__(self):
        return f"{self.provider}: {self.sub} - {self.user}"
