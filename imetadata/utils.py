import cv2
import numpy as np
from PIL import Image
from Crypto.Util.Padding import pad, unpad
from Crypto.Util import number
from scipy.fftpack import dct, idct
import piexif

# Extract metadata from an image
def extract_metadata(image_path):
    exif_data = piexif.load(image_path)
    metadata = {tag: str(value) for tag, value in exif_data["0th"].items()}
    return str(metadata)

# Divide metadata into blocks
def divide_metadata(metadata, block_size=16):
    return [metadata[i:i + block_size] for i in range(0, len(metadata), block_size)]

# Generate RSA key pair using large primes
def generate_rsa_keys(bits=2048):
    p = number.getPrime(bits // 2)
    q = number.getPrime(bits // 2)
    n = p * q
    phi = (p - 1) * (q - 1)
    e = 65537  # Common public exponent
    d = pow(e, -1, phi)
    return {"public": (e, n), "private": (d, n)}

# Embed encrypted metadata into 2nd LSB
def embed_metadata_2lsb(image_array, encrypted_data):
    data_bits = ''.join(format(byte, '08b') for byte in encrypted_data)
    index = 0
    for i in range(image_array.shape[0]):
        for j in range(image_array.shape[1]):
            for k in range(3):  # RGB channels
                if index < len(data_bits):
                    image_array[i, j, k] = (image_array[i, j, k] & 0xFC) | (int(data_bits[index]) << 1) | (int(data_bits[index + 1]) if index + 1 < len(data_bits) else 0)
                    index += 2
    return image_array

# Extract metadata from 2nd LSB
def extract_metadata_2lsb(image_array, length):
    bits = []
    for i in range(image_array.shape[0]):
        for j in range(image_array.shape[1]):
            for k in range(3):  # RGB channels
                bits.append((image_array[i, j, k] >> 1) & 1)
                bits.append(image_array[i, j, k] & 1)
                if len(bits) >= length * 8:
                    break
    byte_data = bytearray()
    for i in range(0, len(bits), 8):
        byte_data.append(int(''.join(map(str, bits[i:i+8])), 2))
    return bytes(byte_data)

# Apply DCT to compress the image
def apply_dct(image_array):
    return dct(dct(image_array, axis=0, norm='ortho'), axis=1, norm='ortho')

# Apply inverse DCT to decompress the image
def apply_inverse_dct(image_array):
    # Debug: Check input data type and shape
    print(f"apply_inverse_dct - Input array dtype: {image_array.dtype}, shape: {image_array.shape}")
    
    # Ensure the array is of an appropriate type
    if not np.issubdtype(image_array.dtype, np.integer):
        image_array = image_array.astype(np.float32)
    
    # Perform the inverse DCT (example)
    transformed_array = np.zeros_like(image_array)
    for i in range(image_array.shape[0]):
        for j in range(image_array.shape[1]):
            transformed_array[i, j] = cv2.idct(image_array[i, j])
    
    # Debug: Check output data type and shape
    print(f"apply_inverse_dct - Output array dtype: {transformed_array.dtype}, shape: {transformed_array.shape}")
    return transformed_array.astype(np.uint8)

