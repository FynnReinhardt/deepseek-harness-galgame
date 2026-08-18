return {
  apply(ctx) {
    const fs = ctx.get('fs')
    if (fs === undefined) return

    // 从 config.json（工作区根）读 output_dir；失败回退 'outputs/webui'
    async function resolveOutputDir() {
      try {
        const sp = ctx.get('sandboxPolicy')
        const root = sp && sp.workspaceRoot ? String(sp.workspaceRoot).replace(/[\\/]+$/, '') : ''
        const cfgFile = await fs.resolve((root ? root + '\\' : '') + 'config.json')
        const cfg = JSON.parse(await fs.readText(cfgFile))
        if (cfg && cfg.output_dir) {
          const p = String(cfg.output_dir)
          if (/^[a-zA-Z]:[\\/]/.test(p) || p.startsWith('/')) return p
          return root ? root + '\\' + p.replace(/\//g, '\\') : p
        }
      } catch (e) { /* config.json 缺失时用默认 */ }
      return 'outputs/webui'
    }

    const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
    function b64FromBytes(bytes) {
      let out = ''
      for (let i = 0; i < bytes.length; i += 3) {
        const b0 = bytes[i]
        const b1 = i + 1 < bytes.length ? bytes[i + 1] : -1
        const b2 = i + 2 < bytes.length ? bytes[i + 2] : -1
        out += B64[b0 >> 2]
        out += B64[((b0 & 3) << 4) | (b1 >= 0 ? b1 >> 4 : 0)]
        out += b1 >= 0 ? B64[((b1 & 15) << 2) | (b2 >= 0 ? b2 >> 6 : 0)] : '='
        out += b2 >= 0 ? B64[b2 & 63] : '='
      }
      return out
    }

    ctx.effect(() => harness.handle('standing/snapshot', async (args) => {
      const result = { items: [], errors: [], dir: '', files: 0 }
      try {
        const OUTPUT_DIR = await resolveOutputDir()
        result.dir = OUTPUT_DIR
        const limit = Math.min(Math.max(Number(args && args.limit) || 3, 1), 6)
        const dir = await fs.resolve(OUTPUT_DIR)
        const st = await fs.stat(dir)
        result.dirExists = !!(st && st.type)
        const entries = await fs.listDir(dir)
        const pngs = (entries || [])
          .filter((e) => e.type === 'file' && typeof e.name === 'string' && e.name.toLowerCase().endsWith('.png'))
          .sort((a, b) => (a.name < b.name ? 1 : -1))
        result.files = pngs.length
        for (const e of pngs.slice(0, limit)) {
          try {
            const bytes = await fs.readBytes(e.target, undefined, 4 * 1024 * 1024)
            result.items.push({
              name: e.name,
              size: bytes ? bytes.length : 0,
              dataUrl: bytes ? 'data:image/png;base64,' + b64FromBytes(bytes) : null,
            })
          } catch (err) {
            result.errors.push(e.name + ': ' + String(err && err.message || err))
          }
        }
      } catch (err) {
        result.error = String(err && err.message || err)
      }
      return result
    }))
  },
}
