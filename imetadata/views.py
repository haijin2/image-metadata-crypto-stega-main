import os
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponseBadRequest
from PIL import Image
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from .utils import (
    extract_metadata, divide_metadata, generate_rsa_keys,
    embed_metadata_2lsb, extract_metadata_2lsb,
    apply_dct, apply_inverse_dct
)

#Output the Encryption Page
def home_view(request):
    return redirect('encrypt')

def encrypt_view(request):
    if request.method == 'POST' and request.FILES.get('image'):
        try:
            # Get the uploaded image file
            uploaded_image = request.FILES['image']
            
            # Store the uploaded image in the MEDIA_ROOT
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            uploaded_image_path = fs.save(uploaded_image.name, uploaded_image)
            image_path = os.path.join(settings.MEDIA_ROOT, uploaded_image_path)

            # Extract metadata from the image
            metadata = extract_metadata(image_path)
            metadata_blocks = divide_metadata(metadata)

            # Generate AES key
            aes_key = os.urandom(16)  # AES key for encryption
            aes_cipher = AES.new(aes_key, AES.MODE_CBC)

            # Encrypt metadata blocks using AES encryption
            encrypted_blocks = b''.join(
                aes_cipher.encrypt(pad(block.encode(), AES.block_size)) for block in metadata_blocks
            )

            # Generate RSA keys
            rsa_keys = generate_rsa_keys()
            public_key = rsa_keys["public"]
            private_key = rsa_keys["private"]

            # Encrypt AES key using RSA encryption
            aes_key_int = int.from_bytes(aes_key, byteorder='big')
            encrypted_aes_key = pow(aes_key_int, public_key[0], public_key[1])

            # Embed the encrypted metadata into the image using 2nd LSB
            image_array = np.array(Image.open(image_path))
            stego_image = embed_metadata_2lsb(image_array, encrypted_blocks)

            # Apply DCT for compression
            compressed_image = apply_dct(stego_image)

            # Save the encrypted image
            encrypted_image_path = os.path.join(settings.MEDIA_ROOT, 'encrypted_image.png')
            Image.fromarray(compressed_image.astype(np.uint8)).save(encrypted_image_path)

            # Save RSA private key to a file for decryption
            private_key_path = os.path.join(settings.MEDIA_ROOT, 'private_key.pem')
            with open(private_key_path, 'w') as f:
                f.write(str(private_key))

            # Provide download links for the encrypted image and private key
            return render(request, 'encrypt_result.html', {
                'encrypted_image_path': f'/media/encrypted_image.png',
                'private_key_path': f'/media/private_key.pem',
                'message': 'Encryption successful! Download the files below.'
            })
        except Exception as e:
            return render(request, 'encrypt_result.html', {'error': f'Error during encryption: {str(e)}'})

    # Render encryption page for GET requests
    return render(request, 'encrypt.html')

def decrypt_view(request):
    if request.method == 'POST' and request.FILES.get('image') and request.POST.get('private_key'):
        try:
            # Get uploaded image and private key
            encrypted_image = request.FILES['image']
            private_key_input = request.POST['private_key']

            # Validate image format
            if not encrypted_image.name.endswith(('.png', '.bmp')):
                return HttpResponseBadRequest("Invalid file format. Please upload a PNG or BMP image.")

            # Load and convert image
            encrypted_image_path = os.path.join(settings.MEDIA_ROOT, encrypted_image.name)
            with open(encrypted_image_path, 'wb') as f:
                f.write(encrypted_image.read())
            
            img = Image.open(encrypted_image_path).convert('RGB')
            encrypted_image_array = np.array(img)

            # Apply inverse DCT
            decompressed_image = apply_inverse_dct(encrypted_image_array)

            # Extract metadata
            encrypted_metadata = extract_metadata_2lsb(decompressed_image, length=256)

            # Decrypt AES key using RSA
            private_key = eval(private_key_input)
            aes_key_int = pow(int.from_bytes(encrypted_metadata[:256], byteorder='big'), private_key[0], private_key[1])
            aes_key = aes_key_int.to_bytes(16, byteorder='big')

            # Decrypt metadata using AES
            aes_cipher = AES.new(aes_key, AES.MODE_CBC)
            decrypted_metadata = unpad(aes_cipher.decrypt(encrypted_metadata[256:]), AES.block_size).decode()

            return render(request, 'decrypt_result.html', {
                'message': 'Decryption successful!',
                'decrypted_metadata': decrypted_metadata
            })

        except Exception as e:
            return render(request, 'decrypt.html', {'error': f"Error during decryption: {str(e)}"})
    
    return render(request, 'decrypt.html')

#Download the files
def download_file(request, file_path):
    file_full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    response = FileResponse(open(file_full_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
    return response
