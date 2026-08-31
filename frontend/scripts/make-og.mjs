// 生成 1200x630 的 OG 占位图（蓝紫渐变）。零依赖：手写 PNG（zlib 压缩）。
// 运行：node scripts/make-og.mjs。上线后用品牌真实图替换 public/og.png 即可。
import { deflateSync } from 'node:zlib'
import { writeFileSync, mkdirSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const publicDir = resolve(root, 'public')
mkdirSync(publicDir, { recursive: true })

const W = 1200
const H = 630
// 每行 = 1 字节过滤类型(0) + W*3 字节 RGB
const raw = Buffer.alloc((W * 3 + 1) * H)

const c1 = [102, 126, 234] // #667eea
const c2 = [118, 75, 162] // #764ba2

for (let y = 0; y < H; y++) {
  const rowStart = y * (W * 3 + 1)
  raw[rowStart] = 0
  for (let x = 0; x < W; x++) {
    const t = x / (W - 1)
    const o = rowStart + 1 + x * 3
    raw[o] = Math.round(c1[0] + (c2[0] - c1[0]) * t)
    raw[o + 1] = Math.round(c1[1] + (c2[1] - c1[1]) * t)
    raw[o + 2] = Math.round(c1[2] + (c2[2] - c1[2]) * t)
  }
}

// 预计算 CRC 表
const table = new Uint32Array(256)
for (let n = 0; n < 256; n++) {
  let c = n
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1
  table[n] = c >>> 0
}
function crc32(buf) {
  let crc = 0xffffffff
  for (let i = 0; i < buf.length; i++) crc = table[(crc ^ buf[i]) & 0xff] ^ (crc >>> 8)
  return (crc ^ 0xffffffff) >>> 0
}

function chunk(type, data) {
  const len = Buffer.alloc(4)
  len.writeUInt32BE(data.length, 0)
  const t = Buffer.from(type, 'ascii')
  const crc = Buffer.alloc(4)
  crc.writeUInt32BE(crc32(Buffer.concat([t, data])), 0)
  return Buffer.concat([len, t, data, crc])
}

const ihdr = Buffer.alloc(13)
ihdr.writeUInt32BE(W, 0)
ihdr.writeUInt32BE(H, 4)
ihdr[8] = 8 // bit depth
ihdr[9] = 2 // color type: truecolor RGB
ihdr[10] = 0
ihdr[11] = 0
ihdr[12] = 0

const png = Buffer.concat([
  Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
  chunk('IHDR', ihdr),
  chunk('IDAT', deflateSync(raw)),
  chunk('IEND', Buffer.alloc(0)),
])

writeFileSync(resolve(publicDir, 'og.png'), png)
console.log('og.png written', png.length, 'bytes')
