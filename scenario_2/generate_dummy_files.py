import os

def generate_files(output_dir, num_files=20, size_mb=10):
    """
    Generate file dummy dengan ukuran spesifik.
    
    Args:
        output_dir (str): Path folder tujuan.
        num_files (int): Jumlah file yang akan dibuat.
        size_mb (int): Ukuran setiap file dalam MB.
    """
    # Pastikan direktori tujuan ada
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Folder '{output_dir}' berhasil dibuat.")
        except OSError as e:
            print(f"Gagal membuat folder: {e}")
            return

    # Hitung ukuran dalam bytes (1 MB = 1024 * 1024 bytes)
    size_bytes = size_mb * 1024 * 1024
    
    # Buat konten buffer (misalnya karakter 'A' berulang)
    # Ini lebih cepat daripada menulis byte demi byte
    content = b'A' * size_bytes

    print(f"Mulai membuat {num_files} file masing-masing {size_mb}MB di '{output_dir}'...")

    for i in range(1, num_files + 1):
        filename = f"file_{i}.txt"
        file_path = os.path.join(output_dir, filename)
        
        try:
            with open(file_path, "wb") as f:
                f.write(content)
            print(f"Berhasil membuat: {filename}")
        except IOError as e:
            print(f"Gagal menulis file {filename}: {e}")

    print("Selesai.")

if __name__ == "__main__":
    target_folder = "test_data" 
    
    if not os.path.isabs(target_folder):
        target_folder = os.path.join(os.getcwd(), target_folder)

    generate_files(target_folder)
