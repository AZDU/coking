<template>
  <div class="page">
    <div v-if="loading" class="loading-overlay" role="status" aria-live="polite">
      <div class="loading-card">
        <div class="spinner-large" aria-hidden="true">
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
          <div class="spinner-ring"></div>
        </div>
        <div class="loading-title">正在加载菜谱</div>
        <div class="loading-subtitle">首次加载可能需要几秒钟，请稍候…</div>
        <div class="loading-hint">数据量较大，正在处理中</div>
      </div>
    </div>

    <header class="header">
      <div class="title">做菜推荐</div>
      <div class="subtitle">输入你手头的食材，推荐能做的菜</div>

      <div class="inputs">
        <label class="label">食材（用逗号分隔）</label>
        <input
          v-model.trim="ingredientsInput"
          class="text-input"
          type="text"
          placeholder="例如：西红柿, 鸡蛋, 葱"
          autocomplete="off"
        />

        <div class="row">
          <button class="primary" @click="recommend">推荐菜谱</button>
          <button class="ghost" @click="reset">清空</button>
        </div>

        <div class="hint">输入后点击“推荐菜谱”，系统会根据菜谱里的食材匹配度排序。</div>

        <div class="meta">
          <span v-if="loadingInitial">加载中…</span>
          <span v-else>推荐 {{ results.length }} 道（库内共 {{ count }} 道）</span>
        </div>
      </div>
    </header>

    <main class="content">
      <div v-if="error" class="error">加载失败：{{ error }}</div>

      <div v-else-if="!loadingInitial && results.length === 0" class="empty">请输入食材后点击“推荐菜谱”</div>

      <div class="list">
        <button
          v-for="r in results"
          :key="r.source_path || r.name"
          class="card"
          @click="openRecipe(r)"
        >
          <div class="thumb" aria-hidden="true">
            <img
              v-if="getCoverUrl(r)"
              class="thumb-img"
              :src="getCoverUrl(r)"
              :alt="r.name"
              loading="lazy"
            />
            <div v-else class="thumb-fallback">{{ (r.name || '').slice(0, 1) }}</div>
          </div>

          <div class="card-body">
            <div class="card-top">
              <div class="card-title">{{ r.name }}</div>
              <div v-if="r._match" class="score">匹配 {{ r._match.matchedCount }}/{{ r._match.inputCount }}</div>
            </div>

            <div class="card-tags">
              <span v-if="r.category" class="tag">{{ r.category }}</span>
              <span v-if="r.difficulty" class="tag">难度 {{ r.difficulty }}</span>
              <span v-for="t in (r.taste || []).slice(0, 4)" :key="t" class="tag">{{ t }}</span>
            </div>

            <div v-if="r._match && r._match.matchedNames.length" class="matched">
              命中：{{ r._match.matchedNames.join('、') }}
            </div>
          </div>
        </button>
      </div>
    </main>

    <div v-if="selected" class="modal" @click.self="closeRecipe">
      <div class="modal-panel" role="dialog" aria-modal="true">
        <div class="modal-header">
          <button class="back" @click="closeRecipe">返回</button>
          <div class="modal-title">{{ selected.name }}</div>
          <div class="spacer"></div>
        </div>

        <div v-if="getCoverUrl(selected)" class="hero">
          <img class="hero-img" :src="getCoverUrl(selected)" :alt="selected.name" />
        </div>

        <div class="section">
          <div class="section-title">食材</div>
          <div class="kv" v-for="(ing, idx) in selected.ingredients" :key="idx">
            <div class="k">{{ ing.name }}</div>
            <div class="v">{{ ing.quantity || '' }}</div>
          </div>
        </div>

        <div class="section">
          <div class="section-title">步骤</div>
          <ol class="steps">
            <li v-for="(s, idx) in selected.steps" :key="idx">{{ s }}</li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
function normalizeText(s) {
  return String(s || '')
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '')
}

function parseIngredientTokens(input) {
  const raw = String(input || '')
  return raw
    .split(/[,，、\n]/)
    .map((x) => x.trim())
    .filter(Boolean)
    .map(normalizeText)
}

function recipeIngredientText(recipe) {
  const arr = Array.isArray(recipe.ingredients) ? recipe.ingredients : []
  return arr.map((i) => normalizeText(i.name)).filter(Boolean)
}

export default {
  data() {
    return {
      loading: true, // 初始默认为加载中
      error: '',
      count: 0,
      recipes: [],
      ingredientsInput: '',
      results: [],
      selected: null,
      _scrollY: 0,
    }
  },
  computed: {
    loadingInitial() {
      return this.loading && this.recipes.length === 0
    },
  },
  methods: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const resp = await fetch('./recipes_clean.json')
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
        const recipes = await resp.json()
        this.recipes = Array.isArray(recipes) ? recipes : []
        this.count = this.recipes.length
      } catch (e) {
        this.error = e && e.message ? e.message : String(e)
      } finally {
        this.loading = false
      }
    },

    getCoverUrl(r) {
      if (!r) return ''
      const name = String(r.name || '').trim()
      if (!name) return ''
      return `./images/recipes/${encodeURIComponent(name)}.jpg`
    },

    recommend() {
      const inputTokens = parseIngredientTokens(this.ingredientsInput)
      const inputSet = new Set(inputTokens)

      if (inputTokens.length === 0) {
        this.results = []
        return
      }

      const scored = this.recipes
        .map((r) => {
          const names = recipeIngredientText(r)
          let matchedCount = 0
          const matchedNames = []

          for (const t of inputSet) {
            if (!t) continue
            const hit = names.find((n) => n && (n.includes(t) || t.includes(n)))
            if (hit) {
              matchedCount += 1
              matchedNames.push(t)
            }
          }

          const inputCount = inputSet.size

          return {
            ...r,
            _match: {
              matchedCount,
              inputCount,
              matchedNames,
            },
          }
        })
        .filter((r) => r._match.matchedCount > 0)
        .sort((a, b) => {
          if (b._match.matchedCount !== a._match.matchedCount) {
            return b._match.matchedCount - a._match.matchedCount
          }
          return (a.difficulty || 0) - (b.difficulty || 0)
        })

      this.results = scored
    },

    reset() {
      this.ingredientsInput = ''
      this.results = []
      this.closeRecipe()
    },

    lockBodyScroll() {
      this._scrollY = window.scrollY || 0
      document.body.style.position = 'fixed'
      document.body.style.top = `-${this._scrollY}px`
      document.body.style.left = '0'
      document.body.style.right = '0'
      document.body.style.width = '100%'
      document.body.style.overflow = 'hidden'
    },

    unlockBodyScroll() {
      const y = this._scrollY || 0
      document.body.style.position = ''
      document.body.style.top = ''
      document.body.style.left = ''
      document.body.style.right = ''
      document.body.style.width = ''
      document.body.style.overflow = ''
      window.scrollTo(0, y)
    },

    openRecipe(r) {
      this.selected = r
      this.lockBodyScroll()
    },

    closeRecipe() {
      if (this.selected) {
        this.selected = null
        this.unlockBodyScroll()
      }
    },
  },
  mounted() {
    this.load()
  },
}
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fff7ed 0%, #ffffff 40%, #fff 100%);
  color: #1f2937;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, "PingFang SC",
    "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
}

.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(255, 247, 237, 0.98) 0%, rgba(255, 255, 255, 0.98) 100%);
  backdrop-filter: blur(12px);
  animation: fadeIn 0.3s ease-in;
}

.loading-card {
  width: min(380px, calc(100vw - 48px));
  padding: 48px 32px;
  border-radius: 24px;
  background: #ffffff;
  border: 2px solid rgba(249, 115, 22, 0.15);
  box-shadow: 0 24px 60px rgba(17, 24, 39, 0.2), 0 0 0 1px rgba(249, 115, 22, 0.05);
  text-align: center;
  animation: slideUp 0.4s ease-out;
}

.spinner-large {
  width: 80px;
  height: 80px;
  margin: 0 auto 24px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 4px solid transparent;
  border-top-color: rgba(249, 115, 22, 0.9);
  animation: spin 1.2s linear infinite;
}

.spinner-ring:nth-child(1) {
  width: 80px;
  height: 80px;
  border-width: 4px;
  animation-duration: 1.2s;
}

.spinner-ring:nth-child(2) {
  width: 60px;
  height: 60px;
  border-width: 3px;
  border-top-color: rgba(249, 115, 22, 0.6);
  animation-duration: 1s;
  animation-direction: reverse;
}

.spinner-ring:nth-child(3) {
  width: 40px;
  height: 40px;
  border-width: 2px;
  border-top-color: rgba(249, 115, 22, 0.4);
  animation-duration: 0.8s;
}

.loading-title {
  font-size: 22px;
  font-weight: 900;
  color: #111827;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.loading-subtitle {
  font-size: 14px;
  color: rgba(31, 41, 55, 0.75);
  margin-bottom: 4px;
}

.loading-hint {
  margin-top: 12px;
  font-size: 12px;
  color: rgba(249, 115, 22, 0.85);
  font-weight: 600;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header {
  position: sticky;
  top: 0;
  z-index: 10;
  padding: 16px;
  background: rgba(255, 247, 237, 0.92);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(17, 24, 39, 0.08);
}

.title {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.2px;
}

.subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(31, 41, 55, 0.70);
}

.inputs {
  margin-top: 12px;
}

.label {
  display: block;
  font-size: 12px;
  color: rgba(31, 41, 55, 0.80);
  margin-bottom: 6px;
}

.text-input {
  width: 100%;
  padding: 12px 12px;
  font-size: 16px;
  border-radius: 14px;
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: #ffffff;
  color: #111827;
  outline: none;
  box-shadow: 0 6px 18px rgba(255, 119, 66, 0.08);
}

.text-input:focus {
  border-color: rgba(249, 115, 22, 0.7);
  box-shadow: 0 8px 22px rgba(249, 115, 22, 0.18);
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 10px;
}

.primary {
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(249, 115, 22, 0.35);
  background: linear-gradient(180deg, rgba(249, 115, 22, 0.22), rgba(249, 115, 22, 0.14));
  color: #7c2d12;
  font-weight: 800;
}

.ghost {
  padding: 12px;
  border-radius: 14px;
  border: 1px solid rgba(17, 24, 39, 0.14);
  background: rgba(255, 255, 255, 0.9);
  color: #111827;
  font-weight: 800;
}

.hint {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(31, 41, 55, 0.65);
}

.meta {
  margin-top: 10px;
  font-size: 12px;
  color: rgba(31, 41, 55, 0.70);
}

.content {
  padding: 12px 12px 24px;
}

.error {
  padding: 12px;
  border-radius: 14px;
  background: rgba(239, 68, 68, 0.10);
  border: 1px solid rgba(239, 68, 68, 0.22);
  color: #991b1b;
}

.empty {
  padding: 24px 12px;
  text-align: center;
  color: rgba(31, 41, 55, 0.70);
}

.list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.card {
  text-align: left;
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: #ffffff;
  color: inherit;
  box-shadow: 0 10px 26px rgba(17, 24, 39, 0.08);
  display: grid;
  grid-template-columns: 64px 1fr;
  gap: 12px;
  align-items: center;
}

.card:active {
  transform: scale(0.99);
}

.thumb {
  width: 64px;
  height: 64px;
  border-radius: 14px;
  overflow: hidden;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: rgba(249, 115, 22, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.thumb-fallback {
  font-weight: 900;
  color: rgba(124, 45, 18, 0.8);
  font-size: 22px;
}

.card-body {
  min-width: 0;
}

.card-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}

.card-title {
  font-weight: 900;
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.score {
  font-size: 12px;
  color: rgba(31, 41, 55, 0.75);
  white-space: nowrap;
}

.card-tags {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tag {
  font-size: 12px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(249, 115, 22, 0.10);
  border: 1px solid rgba(249, 115, 22, 0.18);
  color: #9a3412;
}

.matched {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(31, 41, 55, 0.70);
}

.modal {
  position: fixed;
  inset: 0;
  background: rgba(17, 24, 39, 0.35);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 12px;
  z-index: 50;
  touch-action: none;
}

.modal-panel {
  width: 100%;
  max-width: 680px;
  max-height: 88vh;
  overflow: auto;
  border-radius: 18px;
  background: #ffffff;
  border: 1px solid rgba(17, 24, 39, 0.08);
  box-shadow: 0 18px 40px rgba(17, 24, 39, 0.18);
  -webkit-overflow-scrolling: touch;
}

.modal-header {
  position: sticky;
  top: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(8px);
  padding: 12px;
  border-bottom: 1px solid rgba(17, 24, 39, 0.08);
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 10px;
}

.back {
  border: 1px solid rgba(17, 24, 39, 0.12);
  background: rgba(255, 255, 255, 0.9);
  color: #111827;
  padding: 8px 10px;
  border-radius: 12px;
  font-weight: 800;
}

.modal-title {
  font-size: 16px;
  font-weight: 900;
  text-align: center;
}

.spacer {
  width: 52px;
}

.hero {
  width: 100%;
  height: 180px;
  background: rgba(249, 115, 22, 0.08);
  border-bottom: 1px solid rgba(17, 24, 39, 0.08);
}

.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.section {
  padding: 12px;
}

.section-title {
  font-weight: 900;
  margin-bottom: 8px;
}

.kv {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(17, 24, 39, 0.06);
}

.k {
  color: #111827;
}

.v {
  color: rgba(31, 41, 55, 0.70);
  text-align: right;
  white-space: nowrap;
}

.steps {
  margin: 0;
  padding-left: 18px;
}

.steps li {
  margin: 10px 0;
  line-height: 1.55;
  color: rgba(17, 24, 39, 0.92);
}
</style>
