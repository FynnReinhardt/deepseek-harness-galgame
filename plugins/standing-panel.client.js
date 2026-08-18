return {
  inject: ['timer'],
  apply(ctx) {
    const slots = ctx.get('slots')
    if (slots === undefined) return

    ctx.effect(() => {
      const layout = ctx.get('layout')
      if (layout !== undefined) layout.openDetails()
      return () => {}
    })

    ctx.effect(() => styles.insert(`
      .standing-panel{display:flex;flex-direction:column;height:100%;min-height:0;padding:12px;gap:10px;box-sizing:border-box}
      .standing-header{display:flex;align-items:center;justify-content:space-between;flex:none}
      .standing-title{font-size:15px;font-weight:600;color:var(--dsw-alias-label-primary,#222)}
      .standing-close{background:none;border:none;cursor:pointer;font-size:18px;line-height:1;color:var(--dsw-alias-label-secondary,#888);padding:2px 6px;border-radius:6px}
      .standing-close:hover{background:var(--dsw-alias-interactive-bg-hover,rgba(128,128,128,.12))}
      .standing-body{flex:1;min-height:0;display:flex;flex-direction:column;gap:8px;overflow:auto}
      .standing-main{flex:1;min-height:0;display:flex;flex-direction:column;gap:6px}
      .standing-img{flex:1;min-height:0;width:100%;object-fit:contain;background:var(--dsw-specific-bubble,rgba(128,128,128,.08));border-radius:8px}
      .standing-caption{font-size:11px;color:var(--dsw-alias-label-secondary,#666);word-break:break-all;flex:none}
      .standing-thumbs{display:flex;gap:6px;flex:none;flex-wrap:wrap}
      .standing-thumb{width:64px;height:64px;object-fit:cover;border-radius:6px;border:1px solid var(--dsw-alias-label-caption,rgba(128,128,128,.3));cursor:pointer}
      .standing-empty{color:var(--dsw-alias-label-secondary,#666);font-size:13px;text-align:center;padding:24px 8px}
      .standing-diag{font-size:11px;color:var(--dsw-alias-label-tertiary,#999);word-break:break-all;flex:none}
      .standing-toggle{background:none;border:none;cursor:pointer;font-size:13px;color:var(--dsw-alias-label-primary,#333);padding:2px 8px;border-radius:6px}
      .standing-toggle:hover{background:var(--dsw-alias-interactive-bg-hover,rgba(128,128,128,.12))}
    `))

    slots.inject('conversation.session.header.actions', () => slots.register(
      { name: 'conversation.session.header.actions', id: 'standing-toggle', order: 100 },
      () => React.createElement('button', {
        type: 'button',
        className: 'standing-toggle',
        title: '打开右侧角色立绘面板',
        onClick: () => { const l = ctx.get('layout'); if (l !== undefined) l.openDetails() },
      }, '立绘'),
    ))

    slots.inject('details', () => slots.register(
      { name: 'details' },
      function StandingPanel() {
        const [state, setState] = React.useState({ items: [], error: null, diag: null, busy: false })

        const load = () => {
          setState((s) => ({ ...s, busy: true }))
          host.call('standing/snapshot', { limit: 3 })
            .then((r) => {
              setState((s) => ({
                ...s,
                items: r && Array.isArray(r.items) ? r.items : [],
                error: (r && r.error) ? String(r.error) : null,
                diag: r ? { files: r.files, errors: (r.errors || []).slice(0, 3) } : null,
              }))
            })
            .catch((e) => setState((s) => ({ ...s, error: String(e && e.message || e) })))
            .finally(() => setState((s) => ({ ...s, busy: false })))
        }

        React.useEffect(() => {
          load()
          const dispose = ctx.interval(load, 8000)
          return () => { if (dispose) dispose() }
        }, [])

        const close = () => { const l = ctx.get('layout'); if (l !== undefined) l.closeDetails() }
        const main = state.items[0] || null
        const rest = state.items.slice(1)

        return React.createElement('div', { className: 'standing-panel' },
          React.createElement('div', { className: 'standing-header' },
            React.createElement('div', { className: 'standing-title' }, '角色立绘'),
            React.createElement('button', { type: 'button', className: 'standing-close', onClick: close, title: '关闭' }, '×'),
          ),
          React.createElement('div', { className: 'standing-body' },
            state.error ? React.createElement('div', { className: 'standing-empty' }, '错误：' + state.error)
            : main && main.dataUrl ? React.createElement('div', { className: 'standing-main' },
                React.createElement('img', { src: main.dataUrl, alt: main.name, className: 'standing-img' }),
                React.createElement('div', { className: 'standing-caption' }, main.name),
              )
            : React.createElement('div', { className: 'standing-empty' }, state.busy ? '加载中…' : '暂无立绘（outputs/webui 为空）'),
            rest.length > 0 ? React.createElement('div', { className: 'standing-thumbs' },
              rest.map((it) => React.createElement('img', { key: it.name, src: it.dataUrl, alt: it.name, className: 'standing-thumb' })),
            ) : null,
            state.diag ? React.createElement('div', { className: 'standing-diag' },
              'files=' + (state.diag.files ?? '?') + (state.diag.errors && state.diag.errors.length ? ' | ' + state.diag.errors.join(' | ') : ''),
            ) : null,
          ),
        )
      },
    ))
  },
}
