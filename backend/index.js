const express = require('express')
const cors = require('cors')
const fs = require('fs')
const path = require('path')

const app = express()

app.use(cors())
app.use(express.json())

// 部署时，后端服务需要提供前端打包好的静态文件
const frontendDistPath = path.join(__dirname, '../frontend/dist')
app.use(express.static(frontendDistPath))

const RECIPES_PATH = path.join(__dirname, 'recipes_clean.json')

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok' })
})

app.get('/', (req, res) => {
  res.sendFile(path.join(frontendDistPath, 'index.html'))
})

app.get('/api/recipes', (req, res) => {
  try {
    const raw = fs.readFileSync(RECIPES_PATH, 'utf-8')
    const recipes = JSON.parse(raw)
    res.json({ count: recipes.length, recipes })
  } catch (err) {
    res.status(500).json({ error: 'failed_to_load_recipes', message: String(err) })
  }
})

const PORT = process.env.PORT || 4000
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Backend listening on http://0.0.0.0:${PORT}`)
})

