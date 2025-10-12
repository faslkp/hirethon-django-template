# from django.db import models

# # custom s3 storage
# from storages.backends.s3boto3 import S3Boto3Storage

# class PrivateImageStorage(S3Boto3Storage):
#     location = 'private'
#     default_acl = 'private'
#     file_overwrite = False
#     custom_domain = False

# # Create your models here.
# class Image(models.Model):
#     image = models.ImageField(upload_to='images/')
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     url_expire_date = models.DateTimeField(null=True, blank=True)
#     signed_url = models.URLField(null=True, blank=True)


