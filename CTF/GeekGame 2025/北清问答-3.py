import base64
import struct
from typing import Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.ec import \
    EllipticCurvePrivateKey
from nacl.encoding import URLSafeBase64Encoder
from nacl.signing import SigningKey, VerifyKey

# openssl ecparam -name secp256k1 -genkey -noout -out token.priv
with open('token.priv', 'rb') as f:
    TOKEN_SIGNING_KEY: EllipticCurvePrivateKey = serialization.load_pem_private_key(
        f.read(),
        password=None,
    )  # type: ignore


def sign_token_old(uid: int) -> str:
    sig = base64.urlsafe_b64encode(TOKEN_SIGNING_KEY.sign(
        str(uid).encode(),
        ec.ECDSA(hashes.SHA256()),
    )).decode()
    return f'{uid}:{sig}'


def gen_keys() -> tuple[str, str]:
    sk = SigningKey.generate()
    vk = sk.verify_key

    sk_enc = sk.encode(encoder=URLSafeBase64Encoder).decode('utf-8')
    vk_enc = vk.encode(encoder=URLSafeBase64Encoder).decode('utf-8')

    return sk_enc, vk_enc


def load_sk(sk_enc: str) -> SigningKey:
    return SigningKey(sk_enc.strip().encode('utf-8'), encoder=URLSafeBase64Encoder)


def load_vk(vk_enc: str) -> VerifyKey:
    return VerifyKey(vk_enc.strip().encode('utf-8'), encoder=URLSafeBase64Encoder)


def sign_token(sk: SigningKey, uid: int) -> str:
    assert uid >= 0
    encoded = struct.pack('<Q', int(uid)).rstrip(b'\x00')
    sig = sk.sign(encoded, encoder=URLSafeBase64Encoder).decode()
    return f'GgT-{sig}'


def verify_token(vk: VerifyKey, token: str) -> Optional[int]:
    if not token.startswith('GgT-'):
        return None

    try:
        verified = vk.verify(token[4:].encode(
            'utf-8'), encoder=URLSafeBase64Encoder)
    except Exception:
        return None

    uid = struct.unpack('<Q', verified.ljust(8, b'\x00'))[0]
    return uid


def main() -> None:
    sk_hex, vk_hex = gen_keys()
    print('sk:', sk_hex)
    print('vk:', vk_hex)

    sk = load_sk(sk_hex)
    vk = load_vk(vk_hex)

    # print('token for uid 1:', sign_token(sk, 1))
    print('token for uid 1234567890:', sign_token(sk, 1234567890))
    print('new token length:', len(sign_token(sk, 1234567890)))
    print('old token for uid 1234567890:', sign_token_old(1234567890))
    print('old token length:', len(sign_token_old(1234567890)))

    for uid in [0, 1, 4514, 0x1919810]:
        token = sign_token(sk, uid)
        assert verify_token(vk, token) == uid

    assert verify_token(vk, 'GGT-InvalidPrefix') is None
    assert verify_token(vk, 'GgT-InvalidBase64Token') is None
    assert verify_token(vk, 'GgT-InvalidBase64Token==') is None
    assert verify_token(vk, 'GgT-♿我喜欢你♿') is None


if __name__ == '__main__':
    main()
