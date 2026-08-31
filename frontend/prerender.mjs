// 构建后预渲染：为每个路由生成带完整内容的静态 HTML，并产出 robots.txt / sitemap.xml。
//
// 为什么用手写脚本而不是 vue 预渲染插件？—— 当前环境 registry.npmjs.org 不可达，
// 无法安装任何新依赖。本项目已有 @vue/server-renderer 与 vue-router，因此用
// Vite 的 SSR 加载能力 + renderToString 实现零依赖的预渲染。
//
// 用法：在 `vite build` 之后运行 `node prerender.mjs`（已并入 `npm run build`）。
// 若某个路由渲染失败，这里会打印错误但不会让构建失败（跳过预渲染，保留 SPA 产出）。
import { createServer } from 'vite'
import { readFileSync, writeFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'
import { SITE_URL, PAGES, OG_IMAGE, siteSchema } from './src/seo.config.js'
import { faq, faqPageSchema } from './src/faq.js'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = __dirname
const dist = resolve(root, 'dist')
const ROUTES = ['/', '/download', '/privacy', '/terms']

// 在 <head> 中替换/插入的一整套页面级 SEO 标签。
function buildSeoBlock(path) {
  const page = PAGES[path] || {}
  const url = SITE_URL + (path === '/' ? '/' : path)
  const title = page.title || '万能视频下载器'
  const desc = escapeAttr(page.description || '')
  return [
    `<title>${escapeAttr(title)}</title>`,
    `<meta name="description" content="${desc}" />`,
    `<link rel="canonical" href="${url}" />`,
    '',
    '<meta property="og:type" content="website" />',
    '<meta property="og:site_name" content="万能视频下载器" />',
    '<meta property="og:locale" content="zh_CN" />',
    `<meta property="og:url" content="${url}" />`,
    `<meta property="og:title" content="${escapeAttr(title)}" />`,
    `<meta property="og:description" content="${desc}" />`,
    `<meta property="og:image" content="${OG_IMAGE}" />`,
    '<meta property="og:image:width" content="1200" />',
    '<meta property="og:image:height" content="630" />',
    '',
    '<meta name="twitter:card" content="summary_large_image" />',
    `<meta name="twitter:title" content="${escapeAttr(title)}" />`,
    `<meta name="twitter:description" content="${desc}" />`,
    `<meta name="twitter:image" content="${OG_IMAGE}" />`,
  ].join('\n    ')
}

function escapeAttr(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

// 每个路由的 JSON-LD：站点级 schema，首页再追加一个 FAQPage（与首页可见 FAQ 区块同源）。
function buildLdJson(path) {
  const graph = [...siteSchema()['@graph'], ...(path === '/' ? [faqPageSchema()] : [])]
  return { '@context': 'https://schema.org', '@graph': graph }
}

// llms.txt：AI 专用的站点摘要（正在成为事实标准），从 SITE_URL 与 FAQ 数据生成，
// 保持域名单一来源。
function buildLlmstxt() {
  const q = (i) => faq[i]
  return [
    '# 万能视频下载器',
    '',
    '> 免费的浏览器视频下载与 AI 视频总结工具，支持 1000+ 平台。',
    '',
    '## 是什么',
    '一个基于浏览器运行的视频下载器：粘贴链接即可解析并下载高清视频；解析后可调用 AI 生成总结、思维导图、AI 问答，并可导出中文字幕。核心解析能力基于开源 yt-dlp。',
    '',
    '## 主要能力',
    '- 下载：YouTube / Bilibili / TikTok / 抖音 / Instagram 等 1000+ 平台',
    '- 清晰度：最高 4K / 8K（视平台与视频原始资源而定）',
    '- AI 总结 / 思维导图 / AI 问答 / 中文字幕导出（SRT / VTT / TXT）',
    '',
    '## 典型问题（更多内容见站点 FAQ）',
    '- 支持哪些平台？' + q(0).a,
    '- 需要注册或付费吗？' + q(2).a,
    '- 下载视频有版权风险吗？' + q(3).a,
    '',
    '## 关键页面',
    '- [首页](' + SITE_URL + '/)',
    '- [视频下载](' + SITE_URL + '/download)',
    '- [常见问题](' + SITE_URL + '/#faq)',
    '- [隐私政策](' + SITE_URL + '/privacy)',
    '- [服务条款](' + SITE_URL + '/terms)',
    '',
    '## 说明',
    '本工具仅供个人学习研究，请遵守版权与各平台服务条款，仅下载你有合法授权或使用权的内容。',
  ].join('\n')
}

const server = await createServer({
  root,
  appType: 'custom',
  server: { middlewareMode: true },
  logLevel: 'error',
})

try {
  const { render } = await server.ssrLoadModule('/src/entry-server.js')

  // vite build 已产出 dist/index.html，其中带有构建后的资源链接。<head> 的
  // 页面级 SEO 标签放在 <!--SEO_BLOCK_START--> 与 <!--SEO_BLOCK_END--> 之间，
  // 我们按路由整块替换掉，正文再注入到 #app 里。
  const baseHtml = readFileSync(resolve(dist, 'index.html'), 'utf-8')

  for (const path of ROUTES) {
    const { html, title, description } = await render(path)
    const seoBlock = buildSeoBlock(path)
    const pageTitle = title || PAGES[path]?.title || '万能视频下载器'
    const pageDesc = description || PAGES[path]?.description || ''

    let out = baseHtml
    out = out.replace(/<!--SEO_BLOCK_START-->[\s\S]*?<!--SEO_BLOCK_END-->/, seoBlock)
    out = out.replace(/<div id="app"><\/div>/, `<div id="app">${html}</div>`)
    // 兜底：万一上面两个占位符之一缺失，仍把 title/description 写到正确位置。
    out = out.replace(/<title>[\s\S]*?<\/title>/, `<title>${escapeAttr(pageTitle)}</title>`)
    out = out.replace(
      /<meta name="description" content="[^"]*"/,
      `<meta name="description" content="${escapeAttr(pageDesc)}"`
    )
    // JSON-LD：站点级 schema + 首页额外 FAQPage。插到 </head> 前（若已存在则先去掉避免重复）。
    out = out.replace(/<script type="application\/ld\+json">[\s\S]*?<\/script>\s*\n?/, '')
    out = out.replace(
      '</head>',
      `  <script type="application/ld+json">${JSON.stringify(buildLdJson(path))}</script>\n  </head>`
    )

    const file = path === '/' ? 'index.html' : path.replace(/^\//, '') + '.html'
    writeFileSync(resolve(dist, file), out)
    console.log(`✓ 预渲染 ${file}（title：${pageTitle}）`)
  }

  // robots.txt
  const robots = `User-agent: *\nAllow: /\n\nSitemap: ${SITE_URL}/sitemap.xml\n`
  writeFileSync(resolve(dist, 'robots.txt'), robots)

  // sitemap.xml（仅 canonical、可索引 URL，含首页与下载页）
  const today = new Date().toISOString().slice(0, 10)
  const urlEntries = ROUTES.map((p) => {
    const priority = p === '/' ? '1.0' : '0.8'
    const changefreq = p === '/' ? 'weekly' : 'monthly'
    return `  <url>\n    <loc>${SITE_URL}${p}</loc>\n    <lastmod>${today}</lastmod>\n    <changefreq>${changefreq}</changefreq>\n    <priority>${priority}</priority>\n  </url>`
  }).join('\n')
  const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urlEntries}\n</urlset>\n`
  writeFileSync(resolve(dist, 'sitemap.xml'), sitemap)

  // llms.txt：AI 站点摘要
  writeFileSync(resolve(dist, 'llms.txt'), buildLlmstxt())

  console.log('✓ 已生成 robots.txt、sitemap.xml 与 llms.txt')
} catch (err) {
  // 预渲染失败不应让构建失败：保留 SPA 产出，仅记录错误。
  console.error('预渲染失败（已跳过，构建仍可用）：', err && err.message ? err.message : err)
} finally {
  await server.close()
}
