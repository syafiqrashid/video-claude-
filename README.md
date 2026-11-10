# video-claude-

Projek video menggunakan Claude Code dan plugin HyperFrames.

## Cara pasang plugin HyperFrames

### 1. Pasang prasyarat (kalau belum ada)

- **Node.js 22 atau lebih baru** — muat turun dari [nodejs.org](https://nodejs.org)
- **FFmpeg** — untuk Windows, buka PowerShell dan taip:

  ```powershell
  winget install Gyan.FFmpeg
  ```

Semak pemasangan:

```bash
node --version
ffmpeg -version
```

### 2. Pasang Claude Code

Ikut panduan pemasangan rasmi di <https://docs.claude.com> (cari bahagian "Claude Code").
Claude Code boleh digunakan di terminal atau dalam app desktop Claude.

### 3. Buka Claude Code

Buka terminal, pergi ke folder projek anda, kemudian taip:

```bash
claude
```

### 4. Pasang plugin HyperFrames

Dalam Claude Code, tambah marketplace rasmi dahulu (langkau kalau sudah ada), kemudian pasang plugin:

```
/plugin marketplace add anthropics/claude-plugins-official
```

```
/plugin install hyperframes@claude-plugins-official
```

Selepas pasang, mulakan semula Claude Code (keluar dan taip `claude` semula) supaya plugin dimuatkan.

Selepas pemasangan, taip `/plugin` untuk memastikan HyperFrames tersenarai dan aktif.
