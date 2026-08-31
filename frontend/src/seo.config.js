// 站点 SEO 统一配置：唯一需要维护的“一份”文案/域名。
//
// 上线时只改 SITE_URL 一处，然后重新执行 `npm run build`（脚本会按这里重新
// 生成每个页面的 canonical / OG 标签，并重写 robots.txt 与 sitemap.xml）。
export const SITE_URL = 'https://example.com' // TODO: 上线替换为真实域名

// 分享/预览用的 OG 图（1200x630）。建议上线后换成品牌真实图。
export const OG_IMAGE = SITE_URL + '/og.png'

// 每个路由的 meta。title 用于 <title> 与 og:title / twitter:title，
// description 用于 <meta name="description"> 与 og:description。
export const PAGES = {
  '/': {
    title: '万能视频下载器 - 一键免费下载B站/YouTube/TikTok等1000+平台视频',
    description:
      '免安装免注册，在线下载 1000+ 平台的视频：YouTube、Bilibili、TikTok、抖音、Instagram 等。支持 4K 高清、AI 视频总结、思维导图与中文字幕导出，粘贴链接即可下载。',
  },
  '/download': {
    title: '在线视频下载器 - 粘贴链接免费下载高清视频',
    description:
      '粘贴视频链接，一键解析并下载高清视频。支持清晰度选择、实时下载进度、AI 视频总结、思维导图与字幕导出，随时随地保存你喜欢的视频。',
  },
  '/privacy': {
    title: '隐私政策 - 万能视频下载器',
    description:
      '了解万能视频下载器如何收集、使用与保护你的信息：链接仅用于临时解析下载，不做长期保存、不公开展示。',
  },
  '/terms': {
    title: '服务条款 - 万能视频下载器',
    description:
      '万能视频下载器的服务说明与使用规则：仅供个人学习研究，请遵守版权与平台条款，仅下载你拥有合法授权的内容。',
  },
}

// 站点级 JSON-LD（WebSite + SearchAction / Organization / SoftwareApplication）。
// 在 pre-render 阶段注入到每个页面的 <head>，让搜索引擎理解站点是做什么的。
export function siteSchema() {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'WebSite',
        '@id': SITE_URL + '/#website',
        url: SITE_URL + '/',
        name: '万能视频下载器',
        description: PAGES['/'].description,
        inLanguage: 'zh-CN',
        // 站内搜索动作：把用户搜索词当成要下载的视频链接带过去。
        potentialAction: {
          '@type': 'SearchAction',
          target: SITE_URL + '/download?url={search_term_string}',
          'query-input': 'required name=search_term_string',
        },
      },
      {
        '@type': 'Organization',
        '@id': SITE_URL + '/#organization',
        name: 'VideoDown',
        url: SITE_URL + '/',
        logo: SITE_URL + '/favicon.svg',
      },
      {
        '@type': 'SoftwareApplication',
        name: '万能视频下载器',
        applicationCategory: 'MultimediaApplication',
        operatingSystem: 'Web',
        url: SITE_URL + '/',
        offers: { '@type': 'Offer', price: '0', priceCurrency: 'CNY' },
        inLanguage: 'zh-CN',
        description: PAGES['/'].description,
      },
    ],
  }
}
