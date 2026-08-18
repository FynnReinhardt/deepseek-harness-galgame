return {
  apply(ctx) {
    const fs = ctx.get('fs')
    const sp = ctx.get('systemPrompt')
    if (fs === undefined || sp === undefined) return

    // 部署时由 DSH 把 __WORKSPACE__ 替换为当前工作区绝对路径（如 E:\xxx\deepseek-harness-galgame）
    const WORKSPACE = '__WORKSPACE__'

    // 从 <工作区>/config.json 读 char_dir；失败回退 <工作区>/characters
    async function resolveCharPath(charName) {
      let dir = WORKSPACE + '\\characters'
      try {
        const cfgFile = await fs.resolve(WORKSPACE + '\\config.json')
        const cfg = JSON.parse(await fs.readText(cfgFile))
        if (cfg && cfg.char_dir) {
          const p = String(cfg.char_dir)
          dir = (/^[a-zA-Z]:[\\/]/.test(p) || p.startsWith('/')) ? p : WORKSPACE + '\\' + p.replace(/\//g, '\\')
        }
      } catch (e) { /* config.json 缺失时用默认 */ }
      return fs.resolve(dir.replace(/[\\/]+$/, '') + '\\' + charName + '.md')
    }

    let currentDisposer = null
    let currentChar = ''
    let currentSectionName = ''

    function parseCard(text) {
      const data = { name: '', charTag: '', body: '', face: '', outfits: {}, personality: '' }
      let key = null
      for (const raw of text.split(/\r?\n/)) {
        const line = raw.trim()
        if (!line || line.startsWith('#')) continue
        const m = /^(角色(名字|tag|体形|面部|衣服|性格))[:：](.*)$/.exec(line)
        if (m) {
          key = m[1]
          const val = m[3].trim()
          if (key === '角色衣服') data.outfits = {}
          else if (key === '角色名字') data.name = val
          else if (key === '角色tag') data.charTag = val
          else if (key === '角色体形') data.body = val
          else if (key === '角色面部') data.face = val
          else if (key === '角色性格') data.personality = val
          continue
        }
        if (key === '角色衣服' && line.startsWith('- ')) {
          const item = line.slice(2).trim()
          const idx = item.indexOf(':')
          if (idx > 0) data.outfits[item.slice(0, idx).trim()] = item.slice(idx + 1).trim()
          continue
        }
        if (key === '角色性格') data.personality += '\n' + line
        else if (key === '角色tag') data.charTag = data.charTag ? data.charTag + ', ' + line : line
        else if (key === '角色体形') data.body = data.body ? data.body + ', ' + line : line
        else if (key === '角色面部') data.face = data.face ? data.face + ', ' + line : line
      }
      return data
    }

    function buildPersona(card) {
      const identity = [card.charTag, card.body, card.face].filter(Boolean).join(', ')
      const lines = []
      lines.push('# 当前扮演人格')
      lines.push('你正在扮演角色：' + (card.name || '未命名'))
      if (identity) lines.push('外貌：' + identity)
      if (card.personality) lines.push('性格：\n' + card.personality)
      lines.push('')
      lines.push('【扮演指令】')
      lines.push('- 你现在就是这个角色，言行严格贴合上述性格，不要跳出角色')
      lines.push('- 设定细节以向量检索到的设定集/冒险历史为准，不得凭空发明矛盾事实')
      lines.push('- 你不是 AI 助手，不要提及你是 AI、模型或 DSH')
      return lines.join('\n')
    }

    function registerSection(text) {
      try {
        const d = sp.section({ name: 'deployment:persona', order: 0, text })
        currentSectionName = 'deployment:persona'
        return d
      } catch (err) {
        const d = sp.section({ name: 'rp:persona', order: 0, text })
        currentSectionName = 'rp:persona'
        return d
      }
    }

    async function setPersona(charName) {
      if (currentDisposer) { currentDisposer(); currentDisposer = null }
      const file = await resolveCharPath(charName)
      const text = await fs.readText(file)
      const card = parseCard(text)
      if (!card.name && !card.personality) throw new Error('角色卡解析失败: ' + charName)
      const personaText = buildPersona(card)
      currentDisposer = registerSection(personaText)
      currentChar = charName
      return { char: charName, section: currentSectionName, persona: personaText }
    }

    function clearPersona() {
      if (currentDisposer) { currentDisposer(); currentDisposer = null }
      currentChar = ''
      currentSectionName = ''
      return { char: '', section: '', persona: '' }
    }

    const tool = harness.defineTool({
      name: 'set_persona',
      description: '根据角色卡（characters/<名字>.md）把 DSH 自身人格切换为指定角色：action=set 用该角色的性格+外貌替换当前人格，action=clear 恢复默认。RP 开始时调用 set，RP 结束调用 clear。',
      parameters: {
        type: 'object',
        properties: {
          char: { type: 'string', description: '角色名（characters/<名字>.md，如 龙娘/羽织/DS娘）' },
          action: { type: 'string', enum: ['set', 'clear'], description: 'set=扮演该角色；clear=恢复默认人格' },
        },
        required: ['action'],
      },
      output: {
        schema: {
          type: 'object',
          properties: {
            char: { type: 'string' },
            section: { type: 'string' },
            persona: { type: 'string' },
          },
          additionalProperties: false,
        },
        render: (args, value) => [{ type: 'text', text: JSON.stringify(value) }],
      },
      async execute(args) {
        const action = (args && args.action) || 'set'
        if (action === 'clear') return clearPersona()
        const charName = String((args && args.char) || '').trim()
        if (!charName) throw new Error('action=set 需要 char 角色名')
        return setPersona(charName)
      },
    })

    ctx.effect(() => harness.registerTool(ctx, tool))
  },
}
