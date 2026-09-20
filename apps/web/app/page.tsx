"use client";
import {useEffect,useState} from "react";

const symbols=["NIFTY 50","BANKNIFTY","RELIANCE","TCS","INFY","HDFCBANK"];
const timeframes=["1m","5m","15m","1h","1D"];
const instrumentKeys:Record<string,string>={
 "NIFTY 50":"NSE_INDEX|Nifty 50",
 "BANKNIFTY":"NSE_INDEX|Nifty Bank",
};

export default function Home(){
 const [symbol,setSymbol]=useState("NIFTY 50"),[live,setLive]=useState(false),[connected,setConnected]=useState(false),[last,setLast]=useState<number|null>(null),[analysis,setAnalysis]=useState<any>(null),[fusion,setFusion]=useState<any>(null),[selectedTf,setSelectedTf]=useState("5m"),[intel,setIntel]=useState<any>(null),[intelStatus,setIntelStatus]=useState("not-requested");

 useEffect(()=>{
  const key=instrumentKeys[symbol];
  if(!key){setIntel(null);setIntelStatus("not-supported");return;}
  const base=process.env.NEXT_PUBLIC_QUANTPULSE_API_URL||"http://localhost:8000/api/v1";
  setIntelStatus("loading");
  fetch(base+"/quantpulse/market-intelligence/"+encodeURIComponent(key)+"?expiry=current_week")
   .then(async r=>{if(!r.ok)throw new Error("provider unavailable");return r.json();})
   .then(data=>{setIntel(data);setIntelStatus(data.status||"provider-fed");})
   .catch(()=>{setIntel(null);setIntelStatus("unavailable");});
 },[symbol]);

 useEffect(()=>{
  if(!live)return;
  const base=process.env.NEXT_PUBLIC_QUANTPULSE_WS_URL;
  if(!base)return;
  const ws=new WebSocket(base);
  ws.onopen=()=>{setConnected(true);ws.send(JSON.stringify({type:"subscribe",symbol,timeframe:selectedTf}));};
  ws.onclose=()=>setConnected(false);
  ws.onerror=()=>setConnected(false);
  ws.onmessage=e=>{try{const p=JSON.parse(e.data);if(p.type==="candle"&&p.symbol===symbol){setLast(Number(p.close));if(p.analysis)setAnalysis(p.analysis);if(p.fusion)setFusion(p.fusion);}}catch{}};
  return()=>{try{ws.send(JSON.stringify({type:"unsubscribe",symbol,timeframe:selectedTf}))}catch{}ws.close();setConnected(false);setAnalysis(null);setFusion(null);};
 },[live,symbol,selectedTf]);

 const tf=fusion?.timeframes?.[selectedTf];
 const factors=analysis?.factor_contributions;

 return <main>
  <header><div><b>⚡ QuantPulse</b><span> Market Intelligence Terminal</span></div><div className="status">{connected?"LIVE STREAM CONNECTED":live?"LIVE GATE ARMED":"PAPER MODE"}</div></header>
  <section className="hero"><div><p className="eyebrow">QUANTPULSE TERMINAL</p><h1>Multi-timeframe market intelligence in one terminal.</h1><p className="muted">Provider-fed OHLCV, technical structure, volatility, volume, derivatives context and multi-timeframe fusion. Paper trading remains the default.</p></div><div className="gate"><button onClick={()=>setLive(!live)}>{live?"Disable live stream":"Connect live stream"}</button><small>Market-data streaming and real-money execution are separate controls.</small></div></section>
  <nav>{symbols.map(s=><button className={s===symbol?"active":""} onClick={()=>setSymbol(s)} key={s}>{s}</button>)}</nav>

  <section className="grid"><article className="chart"><div className="cardhead"><div><strong>{symbol}</strong><div className="muted">{selectedTf} • provider-fed market structure</div></div><div className="liveDot">{connected?"● LIVE":"○ DISCONNECTED"}</div></div>
   <div className="tfbar">{timeframes.map(t=><button className={t===selectedTf?"active":""} onClick={()=>setSelectedTf(t)} key={t}>{t}</button>)}</div>
   <div className="chartbox"><div className="price">{last?last.toFixed(2):"—"}</div><div className="empty">{connected?"Waiting for validated OHLCV candles…":"Connect an authorized market-data provider to stream live candles."}</div></div>
  </article>

  <aside><div className="signal"><p>MTF FUSION SIGNAL</p><h2>{fusion?.signal??"WAITING"}</h2><div className="confidence">{fusion?fusion.confidence+"%":"—"}</div><span>Model agreement strength, not profit probability.</span></div>
   <div className="risk"><p>RISK ENGINE</p><div>Entry <b>{last?.toFixed(2)??"—"}</b></div><div>Stop loss <b>{analysis?.stop_loss??"—"}</b></div><div>Target <b>{analysis?.target??"—"}</b></div><div>R:R <b>{analysis?.risk_reward??"—"}</b></div></div>
  </aside></section>

  <section className="cards">
   <div><b>{selectedTf} Structure</b><span>{tf?tf.trend+" • "+(tf.signal??"—")+" • "+tf.confidence+"%":"Waiting for timeframe data"}</span></div>
   <div><b>Market Regime</b><span>{analysis?.market_regime??"Waiting for analysis"}</span></div>
   <div><b>Structure</b><span>{analysis?.structure??"Waiting for candles"}</span></div>
   <div><b>Volume</b><span>{analysis?.volume_regime??"Waiting for candles"}</span></div>
  </section>

  <section className="cards">
   <div><b>Trend</b><span>{factors?factors.trend:"—"}</span></div>
   <div><b>Momentum</b><span>{factors?factors.momentum+" • RSI "+analysis.rsi:"—"}</span></div>
   <div><b>Pattern</b><span>{factors?factors.pattern+" • "+analysis.pattern:"—"}</span></div>
   <div><b>Structure</b><span>{factors?factors.structure+" • "+analysis.structure_score:"—"}</span></div>
  </section>

  <section className="cards">
   <div><b>PCR</b><span>{intel?.pcr??"—"} {intelStatus==="provider-fed"?"• live provider snapshot":intelStatus==="partial"?"• partial":"• unavailable"}</span></div>
   <div><b>Put / Call OI</b><span>{intel?.total_put_oi??"—"} / {intel?.total_call_oi??"—"}</span></div>
   <div><b>Change OI</b><span>{intel?.put_change_oi??"—"} / {intel?.call_change_oi??"—"}</span></div>
   <div><b>Max Pain / VIX</b><span>{intel?.max_pain??"—"} / {intel?.india_vix??"—"}</span></div>
  </section>

  <section className="cards">
   <div><b>Derivatives Bias</b><span>{intel?.derivatives_bias??"—"} {intel?.status==="provider-fed"?"• provider-fed":"• neutral until validated"}</span></div>
   <div><b>1m</b><span>{fusion?.timeframes?.["1m"]?.signal??"—"}</span></div><div><b>5m</b><span>{fusion?.timeframes?.["5m"]?.signal??"—"}</span></div><div><b>15m / 1h / 1D</b><span>{fusion?((fusion.timeframes["15m"]?.signal??"—")+" / "+(fusion.timeframes["1h"]?.signal??"—")+" / "+(fusion.timeframes["1D"]?.signal??"—")):"—"}</span></div>
  </section>

  <footer>QuantPulse is analytical software. Signals are not guaranteed returns or profit probabilities. News and derivatives inputs remain neutral when a validated provider is unavailable. Real-money execution remains locked until broker authorization, security controls and risk validation are independently verified.</footer>
 </main>
}
