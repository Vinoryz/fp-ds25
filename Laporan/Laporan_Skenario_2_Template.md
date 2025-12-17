# Laporan Akhir - Skenario 2: Node Failure & Self-Healing

## 1. Pendahuluan
### 1.1 Tujuan Eksperimen

Menguji ketahanan (resilience), ketersediaan (availability), dan performa (performance) klaster MinIO ketika node mengalami kegagalan (failure), serta kemampuan sistem untuk pulih (self-healing).

### 1.2 Deskripsi Lingkungan

Kami melakukan percobaan pada environment:
- Jumlah Node: 6 (minio1, minio2, minio3, minio4, minio5, minio6).
- Setup Storage: Distributed Mode (Erasure Coding enabled).
- Tools: `sequential.py` script, docker-compose.yaml, Docker, virtual environment, 20 dummy file dengan size tepat 10MB.

## 2. Metodologi Pengujian
Jelaskan langkah-langkah yang dilakukan oleh script `sequential.py`:
1.  **Initialization**: Koneksi ke cluster dan persiapan bucket.
2.  **Phase 1 (Baseline Upload)**: Upload 20 file dummy (10MB each) ke bucket saat kondisi sehat.
3.  **Phase 2 (Baseline Verification)**: Verifikasi integritas data (MD5 checksum) saat kondisi sehat.
4.  **Phase 3 (Failure Simulation)**: Mematikan salah satu node (`minio3`) menggunakan `docker stop`.
5.  **Phase 4 (Read Availability - 1 Node Mati)**: Mencoba membaca dan verifikasi data *segera* setelah node mati.
6.  **Phase 5 (Read Availability - 1 Node Mati - Steady State)**: Mencoba membaca dan verifikasi data *setelah* node mati.
7.  **Phase 6 (Read Availability - 2 Node Mati)**: Mencoba membaca dan verifikasi data *segera* setelah node mati.
8.  **Phase 7 (Read Availability - 2 Node Mati - Steady State)**: Mencoba membaca dan verifikasi data *setelah* node mati.
9.  **Phase 8 (Read Availability - 3 Node Mati)**: Mencoba membaca dan verifikasi data *segera* setelah node mati.
10.  **Phase 9 (Read Availability - 3 Node Mati - Steady State)**: Mencoba membaca dan verifikasi data *setelah* node mati.
11.  **Phase xx (Steady State)**: Melakukan pembacaan ulang untuk memastikan konsistensi.
12.  **Phase xx (Recovery)**: Menghidupkan kembali node (`docker start`) dan memastikan node bergabung kembali.

## 3. Hasil Eksperimen

### 3.1 Phase 1 & 2: Baseline Performance
*   **Observasi**: Apakah semua file berhasil ter-upload dan terverifikasi?

Ketika semua masih menyala dengan baik, MinIO berhasil mengupload 20 file dummy ke bucket. MinIO tidak kesulitan untuk menghubungi setiap node dari minio1 sampai minio6. Operasi write dan read dan write berhasil dijalankan dengan waktu yang lumayan cepat. Total waktu yang diperlukan untuk mengupload 20 file dummy dengan size 10MB adalah sekitar 2.43 detik. Total waktu yang diperlukan untuk membaca 20 file dummy dengan size 10MB adalah sekitar 1.30 detik.

Data yang dibaca juga terverifikasi checksumnya dengan file asli. Artinya tidak ada corruption dalam upload file.

*   *Bukti*: Sertakan screenshot atau kutipan log dari script (`[RESULT] Uploaded 20/20 files...`).

### 3.2 Phase 3: Simulasi Kegagalan
*   **Tindakan**: `docker stop minio3`.
*   **Observasi**: Konfirmasi bahwa container benar-benar berhenti.

### 3.3 Phase 4 & 5: Read Availability dalam Kondisi 1 Node Mati
*   **Observasi Utama**: Apakah data masih bisa diakses (Read) meskipun 1 node mati?

Ketika minio3 mati, MinIO seharusnya tetap dapat melayani permintaan BACA (Read) selama jumlah node yang masih hidup memenuhi kuorum baca (Read Quorum). Pada konfigurasi 6 node dengan 4 data block dan 2 parity block, kehilangan 1 node tidak seharusnya mengganggu proses pembacaan. Ke depannya juga akan ada skenario tambahan untuk mematikan lebih dari satu node, yaitu 2 node dan 3 node.

Namun, ditemukan bahwa MinIO tetap mencoba menghubungi node yang mati (minio3) selama beberapa kali request saat membaca file. Akibatnya, terjadi jeda yang cukup panjang sebelum MinIO mengembalikan file kepada client.

MinIO tidak langsung menandai suatu node sebagai offline setelah satu kali timeout. Hal ini dilakukan untuk menghindari kesalahan deteksi, misalnya ketika node hanya mengalami latency tinggi akibat traffic atau kondisi sementara lainnya. Karena itu, MinIO menggunakan ambang batas timeout dalam bentuk durasi waktu, yang berdasarkan hasil pengujian berada pada kisaran 45–60 detik, untuk mencegah terjadinya rekonstruksi data yang mahal secara tidak perlu.

Sebelumnya, kami sempat berasumsi bahwa threshold ditentukan oleh jumlah request ke node yang diduga mati. Namun setelah melakukan percobaan dengan mengubah nilai timeout menjadi 5 detik, kami menemukan bahwa threshold sebenarnya ditentukan oleh durasi waktu, bukan jumlah request. Jika pada docker-compose tidak ditambahkan environment variable:

MINIO_DRIVE_MAX_TIMEOUT: "5s"

maka timeout maksimum bawaan MinIO adalah 10 detik (berdasarkan observasi).

Jika dalam rentang waktu tersebut suatu node tidak merespons, MinIO akan menyusun data menggunakan node-node yang masih dapat dihubungi. Proses penyusunan data dari 5 node maupun dari 6 node pada dasarnya sama cepatnya, perbedaannya hanya beberapa milidetik dan tidak terlihat oleh pengguna.

Gambar Log MinIO saat timeout 5 detik:
![image-timeout-5s](assets/timeout_5s.png)

Gambar Log MinIO saat timeout 10 detik:
![image-timeout-10s](assets/timeout_10s.png)

Gambar Log MinIO saat timeout 15 detik:
![image-timeout-15s](assets/timeout_15s.png)

Dari log tersebut dapat dilihat bahwa pada timeout 5 detik, 10 detik, dan 15 detik, jumlah request yang dilakukan MinIO berbeda. Namun yang konsisten adalah selisih waktu (durasi) dari kegagalan request ke node yang diduga mati hingga MinIO akhirnya menandai node tersebut sebagai offline. Selain itu, ketika timeout diubah menjadi 15 detik, MinIO tetap melakukan timeout pada 10 detik, sehingga dapat disimpulkan bahwa nilai maksimum timeout yang digunakan MinIO secara internal adalah 10 detik.

*   **Analisis Integritas**: Apakah hash MD5 file yang didownload cocok dengan file asli?

Checksum verification berhasil dilakukan. Pada skenario ini, MinIO dapat memverifikasi integritas data menggunakan hash MD5. Hasil pengujian menunjukkan bahwa hash MD5 dari file yang diunduh sama dengan hash file aslinya. Dengan demikian, tidak terdapat corruption pada proses pembacaan file, meskipun data hanya diambil dari 5 node dari total 6 node yang seharusnya tersedia.

### 3.3 Phase 6 & 7: Read Availability dalam Kondisi 2 Node Mati
*   **Observasi Utama**: Apakah data masih bisa diakses (Read) meskipun 2 node mati?

*   **Analisis Integritas**: Apakah hash MD5 file yang didownload cocok dengan file asli?

### 3.4 Phase 8 & 9: Read Availability dalam Kondisi 3 Node Mati
*   **Observasi Utama**: Apakah data masih bisa diakses (Read) meskipun 3 node mati?

*   **Analisis Integritas**: Apakah hash MD5 file yang didownload cocok dengan file asli?

### 3.x Phase xx: Node Recovery
*   **Tindakan**: `docker start minio3`.
*   **Observasi**: Apakah node berhasil *rejoin* ke cluster? Apakah ada error saat startup?

## 4. Analisis dan Pembahasan

### 4.1 Erasure Coding dan Toleransi Kegagalan
*   Jelaskan teori Erasure Coding di MinIO.
*   *Talking Point*: Bagaimana data dipecah menjadi data blocks dan parity blocks. Jika setup gunakan 4 node (misal 2 data + 2 parity), kita bisa mentolerir kehilangan hingga 2 node untuk Read. Kehilangan 1 node (minio3) masih dalam batas toleransi.

### 4.2 Konsistensi Data (Consistency)
*   Bahas mengenai *Strict Consistency* yang ditawarkan MinIO.
*   *Talking Point*: Meski node mati, klien tidak mendapatkan data yang korup atau *partial*. Klien either mendapatkan data full (valid) atau error. Hasil eksperimen menunjukkan data valid (MD5 match).

### 4.3 Dampak terhadap Performa (Opsional)
*   Bandingkan waktu akses (latency) antara Phase 2 (Healthy) dan Phase 4 (Degraded) jika ada perbedaan signifikan di log.

## 5. Kesimpulan
*   Rangkum apakah MinIO berhasil lulus ujian Skenario 2.
*   *Draft Kesimpulan*: Skenario 2 berhasil membuktikan bahwa arsitektur terdistribusi MinIO tahan terhadap kegagalan satu node. Operasi baca tetap berjalan normal, dan integritas data terjaga berkat mekanisme Erasure Coding.
