// Generates the PWA icons in public/ with no dependencies: a solid square in
// the app's dark background with an "E" mark in the accent colour, drawn from
// rectangles so no font is needed. The mark sits inside the central 60% so the
// same file is safe to declare as `maskable` (safe zone is the central 80%).
//
//   node scripts/gen-icons.mjs
import { writeFileSync } from 'node:fs'
import { deflateSync } from 'node:zlib'

const BG = [0x16, 0x17, 0x1d]
const FG = [0xaa, 0x3b, 0xff]

// "E" in a 10x12 unit grid: [x, y, w, h]
const GLYPH_W = 10
const GLYPH_H = 12
const RECTS = [
  [0, 0, 3, 12], // stem
  [0, 0, 10, 3], // top bar
  [0, 4.5, 8, 3], // middle bar
  [0, 9, 10, 3], // bottom bar
]

function crc32(buf) {
  let c
  let crc = 0xffffffff
  for (let n = 0; n < buf.length; n++) {
    c = (crc ^ buf[n]) & 0xff
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
    crc = (crc >>> 8) ^ c
  }
  return (crc ^ 0xffffffff) >>> 0
}

function chunk(type, data) {
  const len = Buffer.alloc(4)
  len.writeUInt32BE(data.length)
  const td = Buffer.concat([Buffer.from(type, 'ascii'), data])
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(td))
  return Buffer.concat([len, td, crc])
}

function icon(size) {
  const glyphH = size * 0.5
  const unit = glyphH / GLYPH_H
  const ox = (size - GLYPH_W * unit) / 2
  const oy = (size - glyphH) / 2
  const inGlyph = (px, py) =>
    RECTS.some(([x, y, w, h]) => {
      const gx = (px + 0.5 - ox) / unit
      const gy = (py + 0.5 - oy) / unit
      return gx >= x && gx < x + w && gy >= y && gy < y + h
    })

  const raw = Buffer.alloc(size * (size * 3 + 1))
  let i = 0
  for (let y = 0; y < size; y++) {
    raw[i++] = 0 // filter: none
    for (let x = 0; x < size; x++) {
      const [r, g, b] = inGlyph(x, y) ? FG : BG
      raw[i++] = r
      raw[i++] = g
      raw[i++] = b
    }
  }

  const ihdr = Buffer.alloc(13)
  ihdr.writeUInt32BE(size, 0)
  ihdr.writeUInt32BE(size, 4)
  ihdr[8] = 8 // bit depth
  ihdr[9] = 2 // colour type: RGB
  return Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    chunk('IHDR', ihdr),
    chunk('IDAT', deflateSync(raw)),
    chunk('IEND', Buffer.alloc(0)),
  ])
}

const out = new URL('../public/', import.meta.url)
for (const size of [192, 512]) {
  writeFileSync(new URL(`pwa-${size}x${size}.png`, out), icon(size))
}
writeFileSync(new URL('apple-touch-icon.png', out), icon(180))
console.log('wrote pwa-192x192.png, pwa-512x512.png, apple-touch-icon.png')
