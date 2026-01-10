<template>
  <div class="page">
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
          <span v-if="loading">加载中…</span>
          <span v-else>推荐 {{ results.length }} 道（库内共 {{ count }} 道）</span>
        </div>
      </div>
    </header>

    <main class="content">
      <div v-if="error" class="error">加载失败：{{ error }}</div>

      <div v-else-if="!loading && results.length === 0" class="empty">请输入食材后点击“推荐菜谱”</div>

      <div class="list">
        <button
          v-for="r in results"
          :key="r.source_path || r.name"
          class="card"
          @click="openRecipe(r)"
        >
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
      loading: false,
      error: '',
      count: 0,
      recipes: [],
      ingredientsInput: '',
      results: [],
      selected: null,
      _scrollY: 0,
    }
  },
  methods: {
    async load() {
      this.loading = true
      this.error = ''
      try {
        const resp = await fetch('/recipes_clean.json')
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
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(17, 24, 39, 0.08);
  background: #ffffff;
  color: inherit;
  box-shadow: 0 10px 26px rgba(17, 24, 39, 0.08);
}

.card:active {
  transform: scale(0.99);
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
}

.score {
  font-size: 12px;
  color: rgba(31, 41, 55, 0.75);
}

.card-tags {
  margin-top: 10px;
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
  margin-top: 10px;
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
