import type { AppProps } from 'next/app'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div style={{fontFamily:"Inter, system-ui, sans-serif", padding:24}}>
      <Component {...pageProps} />
      <footer style={{marginTop:32, fontSize:12, color:'#6b7280'}}>
        ⚠️ Solo per scopi informativi. Non è un invito al gioco. 18+
      </footer>
    </div>
  )
}
