import os

def create_large_file(filename, size_in_mb)
    target_size_bytes = size_in_mb * 1024 * 1024
    
    sentence = "Ini adalah baris teks untuk simulasi upload file Tugas Akhir Sistem Terdistribusi MinIO. " * 5 + "\n"
    
    chunk_size = 1024 * 1024
    
    repeats = chunk_size // len(sentence)
    chunk_data = sentence * repeats
    
    print(f"Sedang membuat file '{filename}' sebesar {size_in_mb}MB...")
    print("Mohon tunggu sebentar...")

    with open(filename, 'w', encoding='utf-8') as f:
        bytes_written = 0
        while bytes_written < target_size_bytes:
            f.write(chunk_data)
            bytes_written += len(chunk_data)
            
            percent = (bytes_written / target_size_bytes) * 100
            print(f"\rProgress: {percent:.2f}%", end='')

    print(f"\n\nSUKSES! File '{filename}' berhasil dibuat.")
    print(f"Lokasi: {os.path.abspath(filename)}")
    print(f"Ukuran Akhir: {os.path.getsize(filename) / (1024*1024):.2f} MB")

nama_file = "data_test_200mb.txt"
ukuran_mb = 200

if __name__ == "__main__":
    create_large_file(nama_file, ukuran_mb)