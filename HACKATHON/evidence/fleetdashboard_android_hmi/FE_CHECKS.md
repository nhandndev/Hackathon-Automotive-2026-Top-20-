# FE Checks

## npm run lint

Exit code: 0

```text

> react-example@0.0.0 lint
> tsc --noEmit


```

## npm run build

Exit code: 0

```text

> react-example@0.0.0 build
> vite build && esbuild server.ts --bundle --platform=node --format=cjs --packages=external --sourcemap --outfile=dist/server.cjs

vite v6.4.3 building for production...
transforming...
✓ 2524 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.40 kB │ gzip:   0.27 kB
dist/assets/index--w2t9nPL.css   58.40 kB │ gzip:  10.16 kB
dist/assets/index-DuChJBA8.js   804.39 kB │ gzip: 232.23 kB

(!) Some chunks are larger than 500 kB after minification. Consider:
- Using dynamic import() to code-split the application
- Use build.rollupOptions.output.manualChunks to improve chunking: https://rollupjs.org/configuration-options/#output-manualchunks
- Adjust chunk size limit for this warning via build.chunkSizeWarningLimit.
✓ built in 2.29s

  dist/server.cjs      45.7kb
  dist/server.cjs.map  75.1kb

⚡ Done in 4ms

```

