"""Prints a VAPID key pair as single-line values for apps/api/.env.

    python scripts/generate_vapid_keys.py
"""
import base64

from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def main() -> None:
    vapid = Vapid()
    vapid.generate_keys()

    private = b64url(
        vapid.private_key.private_numbers().private_value.to_bytes(32, "big")
    )
    public = b64url(
        vapid.public_key.public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )
    )

    print(f"VAPID_PUBLIC_KEY={public}")
    print(f"VAPID_PRIVATE_KEY={private}")
    print("VAPID_SUBJECT=mailto:you@example.com")


if __name__ == "__main__":
    main()
