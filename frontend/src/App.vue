<template>
  <div class="min-h-screen flex flex-col bg-slate-50">
    <NavBar />
    <main class="flex-1">
      <router-view v-slot="{ Component }">
        <transition name="page" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <Footer />
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import NavBar from './components/NavBar.vue'
import Footer from './components/Footer.vue'
import { useAuth } from './composables/useAuth'

const { init } = useAuth()

// 首屏加载时恢复并拉取登录态（无 token 则保持匿名）。
onMounted(() => {
  init()
})
</script>

<style>
.page-enter-active,
.page-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>