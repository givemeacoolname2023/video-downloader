import { createRouter, createWebHistory, createMemoryHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DownloadView from '../views/DownloadView.vue'
import PrivacyView from '../views/PrivacyView.vue'
import TermsView from '../views/TermsView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: {
      title: '万能视频下载器 - 一键免费下载B站/YouTube/TikTok等1000+平台视频',
      description:
        '免安装免注册，在线下载 1000+ 平台的视频：YouTube、Bilibili、TikTok、抖音、Instagram 等。支持 4K 高清、AI 视频总结、思维导图与中文字幕导出，粘贴链接即可下载。',
    },
  },
  {
    path: '/download',
    name: 'download',
    component: DownloadView,
    meta: {
      title: '在线视频下载器 - 粘贴链接免费下载高清视频',
      description:
        '粘贴视频链接，一键解析并下载高清视频。支持清晰度选择、实时下载进度、AI 视频总结、思维导图与字幕导出，随时随地保存你喜欢的视频。',
    },
  },
  {
    path: '/privacy',
    name: 'privacy',
    component: PrivacyView,
    meta: {
      title: '隐私政策 - 万能视频下载器',
      description:
        '了解万能视频下载器如何收集、使用与保护你的信息：链接仅用于临时解析下载，不做长期保存、不公开展示。',
    },
  },
  {
    path: '/terms',
    name: 'terms',
    component: TermsView,
    meta: {
      title: '服务条款 - 万能视频下载器',
      description:
        '万能视频下载器的服务说明与使用规则：仅供个人学习研究，请遵守版权与平台条款，仅下载你拥有合法授权的内容。',
    },
  },
]

// 浏览器里用 web history；Node（预渲染/SSR）没有 window，改用内存 history。
// 这样同一个路由模块既能被客户端加载，也能被预渲染脚本在 Node 中复用。
const history =
  typeof window !== 'undefined' ? createWebHistory() : createMemoryHistory()

const router = createRouter({
  history,
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  if (typeof document !== 'undefined') {
    document.title = to.meta.title || '万能视频下载器'
  }
})

export default router
