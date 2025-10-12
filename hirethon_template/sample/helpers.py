# import datetime

# from cryptography.hazmat.backends import default_backend
# from cryptography.hazmat.primitives import hashes
# from cryptography.hazmat.primitives import serialization
# from cryptography.hazmat.primitives.asymmetric import padding, rsa
# from botocore.signers import CloudFrontSigner

# from django.conf import settings


# def _rsa_signer(message):
#     with open('cloudfront.pem', 'rb') as key_file:
#         private_key = serialization.load_pem_private_key(
#             key_file.read(),
#             password=None,
#             backend=default_backend()
#         )

#         if isinstance(private_key, rsa.RSAPrivateKey):
#             return private_key.sign(
#                 message,
#                 padding.PKCS1v15(),
#                 hashes.SHA1()
#             )
#         else:
#             raise TypeError("Loaded key is not an RSA private key")

# def generate_presigned_url(url: str, expire_date: datetime.datetime):
#     key_id = settings.CLOUDFRONT_KEY_ID
#     url = f'https://{settings.CLOUDFRONT_DOMAIN}/cicd.png'

#     cloudfront_signer = CloudFrontSigner(key_id, _rsa_signer)

#     # Create a signed url that will be valid until the specific expiry date
#     # provided using a canned policy.
#     signed_url = cloudfront_signer.generate_presigned_url(
#         url, date_less_than=expire_date)

#     return signed_url
