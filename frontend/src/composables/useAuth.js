/**
 * 全局登录/会员状态（单例 composable）。
 *
 * - 所有组件通过 useAuth() 拿到同一份响应式状态，避免重复请求。
 * - token 只存 localStorage（浏览器），SSR/预渲染没有 window 时保持不激活。
 * - init() 在 App.vue 挂载时调用一次；各页面可调用 refresh() 拉取最新 me。
 *
 * 状态形状（来自后端 /api/auth/me）：
 *   user = { id, email }
 *   isMember = bool
 *   membership = { plan, status, current_period_end, cancel_at_period_end } | null
 *   quota = { is_member, downloads: {used,limit,unlimited}, ai: {...} }
 */
import { ref, computed } from 'vue'
import {
  login as apiLogin,
  register as apiRegister,
  fetchMe,
  createCheckout,
  mockActivate,
} from '../utils/api'

const TOKEN_KEY = 'vd_token'
const USER_KEY = 'vd_user'

const user = ref(null)
const isMember = ref(false)
const membership = ref(null)
const quota = ref(null)
const ready = ref(false)
const loading = ref(false)

let initPromise = null

// 便捷计算：是否已登录
const isLoggedIn = computed(() => !!user.value)

// 下载/ AI 次数的可视化（免费用户显示剩余，会员显示无限）
const downloads = computed(() => quota.value?.downloads || null)
const ai = computed(() => quota.value?.ai || null)

function applyMe(data) {
  user.value = data.user || null
  isMember.value = !!data.is_member
  membership.value = data.membership || null
  quota.value = data.quota || null
}

function clearAuth() {
  user.value = null
  isMember.value = false
  membership.value = null
  quota.value = null
  if (typeof window !== 'undefined') {
    window.localStorage.removeItem(TOKEN_KEY)
    window.localStorage.removeItem(USER_KEY)
  }
}

async function refresh() {
  const token = typeof window !== 'undefined' ? window.localStorage.getItem(TOKEN_KEY) : null
  if (!token) {
    clearAuth()
    ready.value = true
    return null
  }
  loading.value = true
  try {
    const data = await fetchMe()
    applyMe(data)
    return data
  } catch (e) {
    // 401 已被 api 拦截器清理；这里只需本地重置。
    clearAuth()
    return null
  } finally {
    loading.value = false
    ready.value = true
  }
}

async function init() {
  if (initPromise) return initPromise
  initPromise = refresh()
  return initPromise
}

async function login(credentials) {
  const data = await apiLogin(credentials)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(TOKEN_KEY, data.token)
    window.localStorage.setItem(USER_KEY, JSON.stringify(data.user || {}))
  }
  await refresh()
  return data
}

async function register(credentials) {
  const data = await apiRegister(credentials)
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(TOKEN_KEY, data.token)
    window.localStorage.setItem(USER_KEY, JSON.stringify(data.user || {}))
  }
  await refresh()
  return data
}

function logout() {
  clearAuth()
  ready.value = true
}

/**
 * 发起订阅：先下单，再根据是否 mock 决定「本地模拟付款」还是「跳转 Stripe」。
 * - mock 模式：后端返回 mock:true，我们调用 /dev/mock-activate 授予会员并刷新。
 * - 真实模式：返回 Stripe Checkout URL，跳转过去（回跳后 /membership 会刷新）。
 */
async function subscribe(plan) {
  const res = await createCheckout(plan)
  if (res.mock) {
    const me = await mockActivate(plan)
    applyMe(me)
    return { mock: true }
  }
  if (typeof window !== 'undefined') {
    window.location.href = res.url
  }
  return { redirect: true, url: res.url }
}

export function useAuth() {
  return {
    // state
    user,
    isMember,
    membership,
    quota,
    ready,
    loading,
    isLoggedIn,
    downloads,
    ai,
    // actions
    init,
    refresh,
    login,
    register,
    logout,
    subscribe,
  }
}
