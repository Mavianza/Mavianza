# Pengaturan profil

Repo tujuan adalah repo publik `Mavianza/Mavianza`. Simpan isi paket pada root branch utama, termasuk direktori `.github`. GitHub menampilkan `README.md` di [profil Mavianza](https://github.com/Mavianza).

Workflow **Perbarui statistik profil** berjalan setiap hari sekitar 03.17 WITA, ketika skrip atau workflow berubah di branch utama, dan saat dipicu lewat tombol **Run workflow** pada tab **Actions**. Workflow menggunakan token bawaan GitHub Actions dan menyimpan kedua SVG dalam satu commit saat hasil berubah.

## Data

- **Streak aktif** menghitung hari UTC berturut-turut dengan kontribusi. Jika hari berjalan masih kosong, perhitungan berakhir pada kemarin. Rekor dan total mencakup 365 hari terakhir. Kalender berasal dari GitHub dan mengikuti akses yang diberikan GitHub pada token.
- **Bahasa repositori** menjumlahkan byte kode yang dihitung GitHub untuk repo publik milik akun ini. Fork dan repo profil dikecualikan. Jika ada lebih dari lima bahasa, empat bahasa terbesar ditampilkan bersama kelompok Lainnya.
- Hasil lama tetap tersedia jika permintaan GitHub gagal. Pada publikasi pertama, kedua panel menampilkan status menunggu hingga workflow berhasil. GitHub dapat menonaktifkan jadwal pada repo publik yang tidak aktif selama 60 hari. Workflow dapat diaktifkan kembali dari tab **Actions**.

## Pemeriksaan

```bash
python3 -m unittest discover -s tests
```

Tes memakai respons GitHub sintetis untuk memeriksa alur pembaruan, pergantian hari, filter repositori, pengelompokan bahasa, dan kegagalan yang mempertahankan hasil lama.

## Desain

Banner memakai pixel art 16-bit dengan fokus kuat pada nama. Skala desainnya 3 untuk energi, 3 untuk variasi komposisi, dan 2 untuk gerak.

- Kisi 5×7 memberi bentuk piksel pada nama. Teks penjelas memakai huruf sistem supaya mudah dibaca.
- Bidang tinta gelap memberi kontras pada huruf warna kertas. Warna tembaga menandai perangkat, dan mint menyorot data.
- Monitor, penyimpanan, dan bingkai visual menggambarkan antarmuka web, sistem informasi, dan multimedia. Ketiganya berada dalam satu ilustrasi, dengan jarak yang menjaga nama tetap dominan.
- Susunan ponsel menempatkan ilustrasi di bawah nama supaya teks dan gambar tetap terbaca. Kartu statistik memakai sudut bertangga dan grafik yang sejajar dengan kisi piksel.
- Opening menampilkan nama per blok, menyalakan layar, lalu mengirim sinyal ke dua perangkat. Gerak pembuka selesai dalam sekitar 2,9 detik.
- Saat idle, kursor di layar dan lampu penyimpanan berkedip pelan dengan tempo berbeda. Gunakan panah di atas banner untuk menyembunyikannya. Preferensi pengurangan gerak menampilkan banner diam.

Buat ulang kedua banner dengan `python3 scripts/render_banner.py`. Panel statistik dirender oleh `scripts/profile_stats.py` saat GitHub Actions mengambil data.

Rujukan [README profil](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme), [kalender GitHub](https://docs.github.com/en/graphql/reference/users), dan [jadwal GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
