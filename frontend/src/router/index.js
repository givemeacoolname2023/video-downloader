import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DownloadView from '../views/DownloadView.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: '万能视频下载 - 支持 1000+ 平台' },
  },
  {
    path: '/download',
    name: 'download',
    component: DownloadView,
    meta: { title: '开始下载 - 万能视频下载' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.beforeEach((to) => {
  document.title = to.meta.title || '万能视频下载'
})

export default router