// 服务端渲染入口：供 build 阶段的预渲染脚本在 Node 中调用。
//
// 它会为每个路径创建一个临时的 Vue + router 实例，用 renderToString 产出该
// 路由的静态 HTML。页面内容（标题、副标题、平台列表、功能区块等）都会写进
// HTML 源码，从而对搜索引擎“开箱即读”，使命不是纯客户端渲染的空壳。
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'
import { createRouter, createMemoryHistory } from 'vue-router'
import App from './App.vue'
import router from './router'

// 返回 { html, title, description }：html 是注入到 #app 的静态内容，
// title/description 传给脚本写入 <head>。
export async function render(path) {
  const app = createSSRApp(App)
  const history = createMemoryHistory()
  const instance = createRouter({ history, routes: router.options.routes })
  app.use(instance)

  instance.push(path)
  await instance.isReady()

  // 等待异步组件 / await 解析完成后再渲染，确保 HTML 完整。
  const ctx = {}
  const html = await renderToString(app, ctx)

  const meta = instance.currentRoute.value.meta || {}
  return {
    html,
    title: meta.title || '',
    description: meta.description || '',
  }
}
