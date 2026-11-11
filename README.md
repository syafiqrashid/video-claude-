# Buku Kedai 🧾

Web app ringkas untuk perniagaan kecil: rekod **belian (dengan gambar resit)**, rekod **jualan**, lihat **untung rugi** bulanan & tahunan, dan **muat turun laporan Excel / PDF**.

## Ciri-ciri

| Menu | Fungsi |
|---|---|
| **Utama** | Jumlah jualan, belian dan untung/rugi bulan dipilih + carta 12 bulan + transaksi terkini |
| **Jualan** | Key-in jualan (barang, kuantiti, harga, pelanggan, cara bayaran). Tapis ikut bulan & cari |
| **Belian** | Key-in belian + upload / ambil gambar resit terus dari kamera telefon |
| **Laporan** | Laporan tahunan (pecahan bulan) atau bulanan (pecahan hari), barang paling laris. Muat turun **Excel** (4 sheet: Ringkasan, Jualan, Belian, Barang Laris) atau **PDF** (boleh sertakan gambar resit) |
| **Tetapan** | Nama perniagaan, sandaran (backup) & pulih data, padam semua data |

Lain-lain: harga barang diisi automatik daripada rekod lepas, sesuai untuk telefon (boleh "Add to Home Screen"), mod gelap, boleh dibuka tanpa internet selepas kali pertama.

## Cara guna

Tiada server atau pemasangan diperlukan — hanya fail statik.

- **Cuba di komputer:** jalankan `python3 -m http.server 8000` dalam folder ini, buka http://localhost:8000
- **Guna di telefon (percuma):** aktifkan **GitHub Pages** (Settings → Pages → Deploy from branch → pilih branch & folder `/root`). Buka pautan itu di telefon, kemudian pilih **Add to Home Screen** supaya ia jadi macam app.

## Penting tentang data

Data (termasuk gambar resit) disimpan **dalam pelayar di peranti itu sahaja** (IndexedDB) — tiada siapa lain boleh lihat. Oleh itu:

- Tekan **Tetapan → Muat turun sandaran** secara berkala (contoh: setiap minggu) dan simpan fail itu di Google Drive / WhatsApp sendiri.
- Untuk pindah ke telefon baru, buka app di telefon baru dan **Pulihkan sandaran**.
- Jangan "Clear browsing data" untuk laman ini tanpa sandaran.

## Fail

- `index.html` — struktur halaman
- `style.css` — rekaan (mobile-first, mod gelap)
- `app.js` — logik: storan, borang, laporan, eksport Excel (SheetJS) & PDF (jsPDF)
- `sw.js`, `manifest.json`, `icons/` — supaya boleh dipasang di telefon & dibuka offline
