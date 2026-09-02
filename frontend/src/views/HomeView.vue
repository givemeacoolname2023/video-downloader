<template>
  <div>
    <!-- Hero Section -->
    <section class="relative overflow-hidden bg-white">
      <!-- Background decoration -->
      <div class="absolute inset-0 overflow-hidden">
        <div class="absolute -top-40 -right-40 w-80 h-80 bg-primary-100 rounded-full opacity-30 blur-3xl"></div>
        <div class="absolute -bottom-40 -left-40 w-96 h-96 bg-accent-100 rounded-full opacity-30 blur-3xl"></div>
      </div>

      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-28">
        <div class="text-center max-w-3xl mx-auto">
          <!-- Badge -->
          <div class="inline-flex items-center gap-2 bg-primary-50 text-primary-600 rounded-full px-4 py-1.5 text-sm font-medium mb-6 animate-fade-in">
            <span class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            已支持 1000+ 视频平台
          </div>

          <!-- Title -->
          <h1 class="text-4xl md:text-5xl lg:text-6xl font-extrabold text-slate-900 leading-tight mb-6 tracking-tight text-balance">
            万能视频下载器<br />
            <span class="gradient-text">一个链接，搞定所有平台</span>
          </h1>

          <!-- Subtitle -->
          <p class="text-lg md:text-xl text-slate-500 mb-10 leading-relaxed text-balance">
            支持 YouTube、Bilibili、TikTok、抖音、Instagram 等主流平台<br />
            高清下载，永久保存，随时随地观看
          </p>

          <!-- Search Bar -->
          <div class="max-w-xl mx-auto mb-8">
            <div class="flex flex-col sm:flex-row gap-3">
              <div class="flex-1 relative">
                <div class="absolute inset-y-0 left-4 flex items-center pointer-events-none">
                  <svg class="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <input
                  v-model="url"
                  type="url"
                  placeholder="粘贴视频链接：https://..."
                  class="w-full pl-12 pr-5 py-4 bg-white border-2 border-slate-200 rounded-xl focus:border-primary-400 focus:ring-4 focus:ring-primary-100 outline-none transition-all duration-300 text-base placeholder:text-slate-400 shadow-sm"
                  @keyup.enter="handleDownload"
                />
              </div>
              <button
                @click="handleDownload"
                class="btn-primary whitespace-nowrap text-lg !py-4 !px-8 flex items-center justify-center gap-2"
              >
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                开始下载
              </button>
            </div>
          </div>

          <!-- Supported platforms -->
          <div class="flex flex-wrap items-center justify-center gap-4 text-slate-400 text-sm">
            <span>支持平台：</span>
            <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 rounded-full text-slate-600 font-medium">
              <svg class="w-4 h-4 text-red-500" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>
              YouTube
            </span>
            <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 rounded-full text-slate-600 font-medium">
              <span class="text-pink-500 font-bold text-xs">B</span> BiliBili
            </span>
            <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 rounded-full text-slate-600 font-medium">
              <svg class="w-4 h-4" viewBox="0 0 24 24" fill="currentColor"><path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/></svg>
              TikTok
            </span>
            <span class="text-slate-400">等 1000+ 平台</span>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section id="features" class="py-20 bg-slate-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-14">
          <h2 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">
            为什么选择 <span class="gradient-text">VideoDown</span>？
          </h2>
          <p class="text-slate-500 text-lg max-w-2xl mx-auto">
            基于 yt-dlp 开源核心，稳定可靠，持续迭代更新
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <!-- Feature 1 -->
          <FeatureCard
            icon="🌍"
            title="1000+ 平台"
            description="覆盖 YouTube、Bilibili、TikTok 等全球主流视频平台，一个工具搞定所有需求"
            color="blue"
          />
          <!-- Feature 2 -->
          <FeatureCard
            icon="⚡"
            title="极速下载"
            description="多线程下载技术，极限带宽利用，大文件也能飞速完成"
            color="purple"
          />
          <!-- Feature 3 -->
          <FeatureCard
            icon="🎬"
            title="高清无压缩"
            description="支持 4K/8K 超高清分辨率，原画质下载，拒绝马赛克"
            color="pink"
          />
          <!-- Feature 4 -->
          <FeatureCard
            icon="📱"
            title="移动优先"
            description="完美适配手机和平板，无需安装 APP，浏览器打开即用"
            color="orange"
          />
        </div>
      </div>
    </section>

    <!-- How It Works -->
    <section class="py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-14">
          <h2 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">三步搞定下载</h2>
          <p class="text-slate-500 text-lg">操作简单，甚至你的奶奶都会用 😎</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <!-- Step 1 -->
          <div class="text-center relative animate-slide-up" style="animation-delay: 0s">
            <div class="w-20 h-20 bg-primary-100 rounded-2xl flex items-center justify-center mx-auto mb-5 rotate-3 hover:rotate-0 transition-transform duration-300 shadow-sm">
              <svg class="w-10 h-10 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-slate-900 mb-3">1. 粘贴链接</h3>
            <p class="text-slate-500">复制你想要下载的视频链接，粘贴到搜索框</p>
            <!-- Arrow for desktop -->
            <div class="hidden md:block absolute top-10 -right-4 text-slate-300">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
          </div>

          <!-- Step 2 -->
          <div class="text-center relative animate-slide-up" style="animation-delay: 0.15s">
            <div class="w-20 h-20 bg-accent-100 rounded-2xl flex items-center justify-center mx-auto mb-5 -rotate-3 hover:rotate-0 transition-transform duration-300 shadow-sm">
              <svg class="w-10 h-10 text-accent-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 15l-2 5L9 9l11 4-5 2zm0 0l5 5M7.188 2.239l.777 2.897M5.136 7.965l-2.898-.777M13.95 4.05l-2.122 2.122m-5.657 5.656l-2.12 2.122" />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-slate-900 mb-3">2. 选择清晰度</h3>
            <p class="text-slate-500">自动解析视频信息，选择你想要的清晰度</p>
            <!-- Arrow for desktop -->
            <div class="hidden md:block absolute top-10 -right-4 text-slate-300">
              <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </div>
          </div>

          <!-- Step 3 -->
          <div class="text-center animate-slide-up" style="animation-delay: 0.3s">
            <div class="w-20 h-20 bg-green-100 rounded-2xl flex items-center justify-center mx-auto mb-5 rotate-3 hover:rotate-0 transition-transform duration-300 shadow-sm">
              <svg class="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-slate-900 mb-3">3. 一键下载</h3>
            <p class="text-slate-500">点击下载，实时查看进度，完成后保存到你的设备</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Pricing Section -->
    <section id="pricing" class="py-20 bg-slate-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-14">
          <h2 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">
            选择适合你的<span class="gradient-text">方案</span>
          </h2>
          <p class="text-slate-500 text-lg">免费可用，付费解锁更多高级功能</p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <!-- Free Plan -->
          <div class="card p-8 flex flex-col">
            <div class="mb-6">
              <h3 class="text-xl font-bold text-slate-900 mb-2">免费版</h3>
              <p class="text-slate-500 text-sm">无需注册，轻量体验</p>
            </div>
            <div class="mb-6">
              <span class="text-4xl font-extrabold text-slate-900">¥0</span>
              <span class="text-slate-500 ml-1">/天</span>
            </div>
            <ul class="space-y-3 mb-8 flex-1">
              <li class="flex items-start gap-2 text-sm text-slate-600">
                <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                每日 3 次下载
              </li>
              <li class="flex items-start gap-2 text-sm text-slate-600">
                <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                每日 3 次 AI 功能
              </li>
              <li class="flex items-start gap-2 text-sm text-slate-600">
                <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                不限清晰度，不降画质
              </li>
            </ul>
            <button @click="$router.push('/download')" class="btn-primary w-full">免费开始</button>
          </div>

          <!-- Member Plan (Highlighted) -->
          <div class="card p-8 flex flex-col relative ring-2 ring-primary-500 shadow-xl shadow-primary-500/10 scale-105">
            <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-cta-gradient text-white text-xs font-bold px-4 py-1 rounded-full">
              🔥 无限畅用
            </div>
            <div class="mb-6">
              <h3 class="text-xl font-bold text-slate-900 mb-2">会员版</h3>
              <p class="text-slate-500 text-sm">下载与 AI 全部无限次使用</p>
            </div>
            <div class="mb-6">
              <span class="text-4xl font-extrabold text-slate-900">¥29</span>
              <span class="text-slate-500 ml-1">/月</span>
              <p class="text-slate-400 text-xs mt-2">年付 ¥199（约 ¥16.6/月）</p>
            </div>
            <ul class="space-y-3 mb-8 flex-1">
              <li class="flex items-start gap-2 text-sm text-slate-600">
                <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                无限次下载
              </li>
              <li class="flex items-start gap-2 text-sm text-slate-600">
                <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                AI 总结 / 思维导图 / 问答无限用
              </li>
              <li class="flex items-start gap-2 text-sm text-slate-600">
                <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                不限清晰度，不降画质
              </li>
              <li class="flex items-start gap-2 text-sm text-slate-600">
                <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                支持月度 / 年度订阅，随时取消
              </li>
            </ul>
            <button @click="$router.push('/membership')" class="btn-cta w-full">立即开通</button>
          </div>
        </div>
      </div>
    </section>

    <!-- FAQ Section -->
    <section id="faq" class="py-20 bg-white">
      <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-4">
            常见<span class="gradient-text">问题</span>
          </h2>
          <p class="text-slate-500 text-lg">关于下载、画质、版权与 AI 功能的解答</p>
        </div>

        <div class="space-y-3">
          <details
            v-for="(item, i) in faq"
            :key="i"
            class="group bg-slate-50 border border-slate-100 rounded-2xl px-5 py-4 open:bg-white open:shadow-sm"
          >
            <summary class="flex items-center justify-between gap-4 cursor-pointer list-none text-base font-semibold text-slate-800 select-none">
              <span>{{ item.q }}</span>
              <span class="shrink-0 text-slate-400 transition-transform duration-200 group-open:rotate-45">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
              </span>
            </summary>
            <p class="mt-3 text-slate-600 text-sm leading-relaxed">{{ item.a }}</p>
          </details>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="py-20 bg-hero-gradient relative overflow-hidden">
      <div class="absolute inset-0 opacity-10">
        <div class="absolute -top-20 -left-20 w-60 h-60 bg-white rounded-full blur-3xl"></div>
        <div class="absolute -bottom-20 -right-20 w-80 h-80 bg-white rounded-full blur-3xl"></div>
      </div>

      <div class="relative max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <h2 class="text-3xl md:text-4xl font-extrabold text-white mb-4">
          准备好开始下载你的第一个视频了吗？
        </h2>
        <p class="text-primary-200 text-lg mb-8 max-w-2xl mx-auto">
          几分钟后，你最喜欢的视频就能永久保存在你的设备上了
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <button @click="$router.push('/download')" class="bg-white text-primary-600 font-bold py-4 px-10 rounded-xl hover:shadow-xl transition-all duration-300 active:scale-95 text-lg">
            免费开始使用
          </button>
          <button class="bg-white/20 text-white border-2 border-white/40 hover:bg-white/30 font-bold py-4 px-10 rounded-xl transition-all duration-300 text-lg backdrop-blur-sm">
            了解详情
          </button>
        </div>
      </div>
    </section>

    <!-- Copyright Notice -->
    <section id="copyright" class="py-8 bg-slate-100">
      <div class="max-w-4xl mx-auto px-4 text-center">
        <p class="text-slate-400 text-xs leading-relaxed">
          ⚠️ 版权声明：本工具基于开源项目 yt-dlp，仅供个人学习和研究使用。请遵守相关平台的服务条款和版权法规，
          仅下载您拥有合法权限的内容。严禁下载和传播受版权保护的视频内容。用户需对使用本工具下载的内容承担全部法律责任。
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import FeatureCard from '../components/FeatureCard.vue'
import { faq } from '../faq'

const router = useRouter()
const url = ref('')

function handleDownload() {
  if (url.value.trim()) {
    router.push({ path: '/download', query: { url: url.value.trim() } })
  } else {
    router.push('/download')
  }
}
</script>