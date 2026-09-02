<template>
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
    <div class="text-center mb-10">
      <h1 class="text-3xl md:text-4xl font-extrabold text-slate-900 mb-3">
        会员<span class="gradient-text">中心</span>
      </h1>
      <p class="text-slate-500">开通会员，下载与 AI 功能无限次数使用</p>
    </div>

    <!-- Return-from-Stripe banners -->
    <div v-if="justSuccess" class="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl text-green-700 text-sm">
      ✅ 支付成功，会员已生效！现在可以无限次下载和使用 AI 功能了。
    </div>
    <div v-if="justCanceled" class="mb-6 p-4 bg-slate-100 border border-slate-200 rounded-xl text-slate-600 text-sm">
      已取消支付，未产生任何费用。
    </div>
    <div v-if="error" class="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
      {{ error }}
    </div>

    <!-- 未登录 -->
    <div v-if="!isLoggedIn && authReady" class="card p-8 text-center">
      <p class="text-slate-600 mb-6">开通会员前需要先登录账号。</p>
      <div class="flex justify-center gap-3">
        <router-link :to="{ path: '/login', query: { redirect: '/membership' } }" class="btn-primary !py-3 !px-8">去登录</router-link>
        <router-link :to="{ path: '/register', query: { redirect: '/membership' } }" class="btn-ghost !py-3 !px-8">免费注册</router-link>
      </div>
    </div>

    <!-- 已是会员 -->
    <div v-else-if="isMember" class="card p-8">
      <div class="flex items-center gap-3 mb-6">
        <span class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-cta-gradient text-white text-sm font-bold">✦ 会员</span>
        <span class="text-slate-500 text-sm">无限下载 / 无限 AI</span>
      </div>
      <dl class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
        <div class="rounded-xl bg-slate-50 p-4">
          <dt class="text-slate-400 text-xs">当前方案</dt>
          <dd class="font-bold text-slate-800 mt-1">{{ planLabel }}</dd>
        </div>
        <div class="rounded-xl bg-slate-50 p-4">
          <dt class="text-slate-400 text-xs">状态</dt>
          <dd class="font-bold text-slate-800 mt-1">{{ statusLabel }}</dd>
        </div>
        <div class="rounded-xl bg-slate-50 p-4" v-if="membership?.current_period_end">
          <dt class="text-slate-400 text-xs">到期时间</dt>
          <dd class="font-bold text-slate-800 mt-1">{{ formatDate(membership.current_period_end) }}</dd>
        </div>
        <div class="rounded-xl bg-slate-50 p-4" v-if="membership">
          <dt class="text-slate-400 text-xs">自动续费</dt>
          <dd class="font-bold text-slate-800 mt-1">{{ membership.cancel_at_period_end ? '到期后取消' : '已开启' }}</dd>
        </div>
      </dl>
      <p class="text-xs text-slate-400 mt-6">
        管理 / 取消订阅请在 Stripe 账户中操作；到期前不会重复扣费。
      </p>
    </div>

    <!-- 免费用户：订阅 -->
    <div v-else class="space-y-8">
      <!-- Free / member comparison strip -->
      <div class="grid grid-cols-2 gap-4 text-sm">
        <div class="rounded-2xl border border-slate-200 p-5">
          <h3 class="font-bold text-slate-700 mb-3">免费版</h3>
          <ul class="space-y-1.5 text-slate-500">
            <li>每日 3 次下载</li>
            <li>每日 3 次 AI 功能</li>
            <li>不限清晰度</li>
          </ul>
        </div>
        <div class="rounded-2xl border-2 border-primary-500 bg-primary-50/40 p-5">
          <h3 class="font-bold text-primary-600 mb-3">会员版</h3>
          <ul class="space-y-1.5 text-slate-600">
            <li>♾️ 无限次下载</li>
            <li>♾️ 无限次 AI 功能</li>
            <li>不限清晰度，不降画质</li>
          </ul>
        </div>
      </div>

      <!-- Plan selection -->
      <div>
        <h3 class="text-lg font-bold text-slate-800 mb-4">选择订阅方案</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <button
            v-for="plan in plans"
            :key="plan.key"
            @click="selectedPlan = plan.key"
            :class="[
              'relative text-left rounded-2xl border-2 p-6 transition-all duration-200',
              selectedPlan === plan.key
                ? 'border-primary-500 bg-primary-50/40 shadow-md shadow-primary-500/10'
                : 'border-slate-200 bg-white hover:border-primary-300',
            ]"
          >
            <span v-if="plan.badge" class="absolute -top-2.5 right-4 bg-cta-gradient text-white text-xs font-bold px-2.5 py-0.5 rounded-full">
              {{ plan.badge }}
            </span>
            <div class="flex items-baseline gap-1 mb-1">
              <span class="text-3xl font-extrabold text-slate-900">¥{{ plan.price }}</span>
              <span class="text-slate-400 text-sm">{{ plan.unit }}</span>
            </div>
            <p class="text-slate-500 text-sm">{{ plan.note }}</p>
            <div v-if="selectedPlan === plan.key" class="mt-3 text-primary-500 text-sm font-semibold">✓ 已选择</div>
          </button>
        </div>
      </div>

      <!-- Subscribe CTA -->
      <button
        @click="handleSubscribe"
        :disabled="subscribing"
        class="btn-cta w-full !py-4 !text-lg flex items-center justify-center gap-2"
      >
        <LoadingSpinner v-if="subscribing" :size="18" inline />
        <template v-else>
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
          立即开通（{{ selectedPlanLabel }}）
        </template>
      </button>
      <p class="text-center text-xs text-slate-400">
        支付由 Stripe 处理，支持主流卡；支持月付 / 年付，可随时取消。
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import LoadingSpinner from '../components/LoadingSpinner.vue'

const route = useRoute()
const auth = useAuth()

const plans = [
  { key: 'monthly', price: 29, unit: '/ 月', note: '按月付费，灵活随时取消', badge: '' },
  { key: 'yearly', price: 199, unit: '/ 年', note: '约 ¥16.6/月，年付更划算', badge: '省 ¥149' },
]

const selectedPlan = ref('monthly')
const subscribing = ref(false)
const error = ref('')

const isLoggedIn = computed(() => auth.isLoggedIn.value)
const isMember = computed(() => auth.isMember.value)
const membership = computed(() => auth.membership.value)
const authReady = computed(() => auth.ready.value)

const justSuccess = computed(() => route.query.success === '1')
const justCanceled = computed(() => route.query.canceled === '1')

const selectedPlanLabel = computed(() =>
  selectedPlan.value === 'yearly' ? '年付 ¥199' : '月付 ¥29'
)

const planLabel = computed(() =>
  membership.value?.plan === 'yearly' ? '年付会员' : '月付会员'
)
const statusLabel = computed(() => {
  const s = membership.value?.status
  const map = { active: '生效中', past_due: '扣费失败', unpaid: '未支付', canceled: '已取消' }
  return map[s] || s || '—'
})

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

async function handleSubscribe() {
  error.value = ''
  subscribing.value = true
  try {
    const res = await auth.subscribe(selectedPlan.value)
    // mock：后端直接授予会员并返回 me；真实：window.location 已跳转 Stripe。
    if (res.mock) {
      await auth.refresh()
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '订阅失败，请稍后重试。'
  } finally {
    subscribing.value = false
  }
}

onMounted(() => {
  auth.refresh()
})
</script>