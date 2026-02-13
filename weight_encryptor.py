import hashlib
import os
import platform
import secrets
import uuid
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


@dataclass
class EncryptedWeights:
    ciphertext: bytes
    nonce: bytes
    salt: bytes
    hardware_fingerprint: str
    checksum: str


class WeightEncryptor:
    """
    Binds encrypted weights to a specific hardware fingerprint using AES-GCM.
    Hardware fingerprint may be overridden with the THALOS_HARDWARE_ID env var.
    The `iterations` parameter controls PBKDF2 rounds for key derivation (security vs. CPU time);
    the default of 200,000 mirrors OWASP guidance. Lower values reduce CPU cost but weaken security.
    """

    def __init__(self, iterations: int = 200_000):
        """
        :param iterations: PBKDF2 iteration count used to derive the AES key from the hardware
            fingerprint. Increasing hardens brute-force resistance at the cost of CPU time; decreasing
            reduces security.
        """
        self.iterations = iterations

    def hardware_fingerprint(self) -> str:
        override = os.getenv("THALOS_HARDWARE_ID")
        if override:
            return override
        node = uuid.getnode()
        return f"{platform.node()}-{node:012x}"

    def _derive_key(self, salt: bytes) -> bytes:
        fingerprint = self.hardware_fingerprint().encode("utf-8")
        return hashlib.pbkdf2_hmac("sha256", fingerprint, salt, self.iterations, dklen=32)

    def encrypt(
        self,
        weights: bytes,
        associated_data: Optional[bytes] = None,
        salt: Optional[bytes] = None,
    ) -> EncryptedWeights:
        if salt is None:
            salt = secrets.token_bytes(16)
        nonce = secrets.token_bytes(12)
        key = self._derive_key(salt)
        aes = AESGCM(key)
        ciphertext = aes.encrypt(nonce, weights, associated_data)
        return EncryptedWeights(
            ciphertext=ciphertext,
            nonce=nonce,
            salt=salt,
            hardware_fingerprint=self.hardware_fingerprint(),
            checksum=self.checksum(weights),
        )

    def decrypt(self, payload: EncryptedWeights, associated_data: Optional[bytes] = None) -> bytes:
        if payload.hardware_fingerprint != self.hardware_fingerprint():
            raise ValueError("Hardware fingerprint mismatch; decryption attempted on different hardware.")
        key = self._derive_key(payload.salt)
        aes = AESGCM(key)
        plaintext = aes.decrypt(payload.nonce, payload.ciphertext, associated_data)
        if self.checksum(plaintext) != payload.checksum:
            raise ValueError("Checksum verification failed after decrypting weights.")
        return plaintext

    @staticmethod
    def checksum(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()
