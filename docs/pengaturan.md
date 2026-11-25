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

Tipografi serif membedakan nama dan topik dari angka serta keterangan. Bidang navy memberi kontras pada garis mint yang mengarahkan mata dari nama ke tiga minat. Panel statistik memakai warna kertas agar hierarki peta dan angka terlihat jelas. Peta ponsel memiliki komposisi vertikal dengan teks yang lebih besar. Animasi berlangsung sekitar 2,6 detik, berhenti setelah satu putaran, dan menghormati pengaturan pengurangan gerak.

Rujukan [README profil](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme), [kalender GitHub](https://docs.github.com/en/graphql/reference/users), dan [jadwal GitHub Actions](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
