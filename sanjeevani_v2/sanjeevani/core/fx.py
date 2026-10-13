"""MedX look and motion: "night in the village".

- A deep teal night background: a flowing "silk" light (WebGL, like React Bits' Silk) over drifting aurora
  light and twinkling stars (the CSS aurora is the fallback on slow phones).
- Smooth scrolling with Lenis on computers.
- Glowing fireflies that drift across the whole app and gently move away from the cursor (canvas).
- Entrance animations: page headers slide in, tiles rise one after another, cards pop in.
- Tap ripples, gently tilting home tiles, numbers that count up.
- A home hero scene: hills, coconut palms, a lit hut and a heartbeat line pulsing across.

Everything switches off with the sidebar "Animations" toggle or the phone's "reduce motion" setting,
and the app works the same without any of it.
"""
import html

import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------------------------
# 1. The night skin: background, readable text on dark, glass surfaces, entrance animations
# ---------------------------------------------------------------------------------------------
SKIN = """
<style>
:root{--mx-bg:#051C19;--mx-text:#E9F6F2;--mx-muted:#A6C6BE;--mx-mint:#3EE0AA;--mx-amber:#F6C25B;
  --mx-glass:rgba(255,255,255,.06);--mx-glass-2:rgba(255,255,255,.10);--mx-line:rgba(255,255,255,.13);}
@property --mx-ang{syntax:"<angle>";inherits:false;initial-value:0deg}

/* ---- background: night sky with drifting aurora + stars (behind everything) ---- */
html{background:var(--mx-bg)!important}
body{background:transparent!important}   /* a body background would cover the sky layers */
body::before{content:"";position:fixed;inset:-25vmax;z-index:-2;pointer-events:none;
  background:
    radial-gradient(38vmax 34vmax at 18% 22%,rgba(46,196,160,.30),transparent 62%),
    radial-gradient(42vmax 36vmax at 82% 12%,rgba(64,110,220,.28),transparent 62%),
    radial-gradient(46vmax 40vmax at 72% 88%,rgba(246,194,91,.13),transparent 62%),
    radial-gradient(30vmax 30vmax at 30% 85%,rgba(161,70,200,.16),transparent 62%),
    linear-gradient(165deg,#041A17 0%,#062429 45%,#0A1C38 100%);
  animation:mxAurora 32s ease-in-out infinite alternate;}
body::after{content:"";position:fixed;inset:0;z-index:-2;pointer-events:none;opacity:.55;
  background-image:
    radial-gradient(1.4px 1.4px at 12% 18%,#fff,transparent),radial-gradient(1px 1px at 27% 8%,#fff,transparent),
    radial-gradient(1.2px 1.2px at 44% 22%,#fff,transparent),radial-gradient(1px 1px at 61% 6%,#fff,transparent),
    radial-gradient(1.5px 1.5px at 78% 16%,#fff,transparent),radial-gradient(1px 1px at 91% 30%,#fff,transparent),
    radial-gradient(1.2px 1.2px at 8% 46%,#fff,transparent),radial-gradient(1px 1px at 53% 38%,#fff,transparent),
    radial-gradient(1.3px 1.3px at 86% 52%,#fff,transparent),radial-gradient(1px 1px at 35% 64%,#fff,transparent);
  animation:mxTwinkle 6s ease-in-out infinite alternate;}
@keyframes mxAurora{0%{transform:translate3d(0,0,0) scale(1)}50%{transform:translate3d(3vmax,-2.5vmax,0) scale(1.06)}
  100%{transform:translate3d(-2.5vmax,2vmax,0) scale(1.02)}}
@keyframes mxTwinkle{from{opacity:.25}to{opacity:.6}}

/* let the sky show through Streamlit's own layers */
.stApp,[data-testid="stAppViewContainer"],[data-testid="stMain"],[data-testid="stHeader"],header[data-testid="stHeader"],
[data-testid="stBottom"],[data-testid="stBottom"]>div,[data-testid="stBottomBlockContainer"]{background:transparent!important}
[data-testid="stDecoration"]{display:none}

/* ---- readable light text on the dark sky (works with either Streamlit theme) ---- */
.stApp{color:var(--mx-text)}
.stApp [data-testid="stMarkdownContainer"],.stApp [data-testid="stWidgetLabel"],.stApp label,
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5{color:var(--mx-text)}
.stApp [data-testid="stCaptionContainer"]{color:var(--mx-muted)!important}
.stApp [data-testid="stAlert"] [data-testid="stMarkdownContainer"],.stApp [data-testid="stAlert"] p{color:var(--mx-text)!important}
.stApp [data-testid="stAlert"]>div{border-radius:16px;backdrop-filter:blur(6px)}

/* ---- glass surfaces ---- */
.stApp [data-testid^="stBaseButton-secondary"],.stApp [data-testid^="stBaseLinkButton-secondary"],
.stApp .stButton>button[kind="secondary"],.stApp .stLinkButton>a[kind="secondary"],
.stApp .stDownloadButton>button[kind="secondary"]{background:var(--mx-glass)!important;color:var(--mx-text)!important;
  backdrop-filter:blur(8px)}
.stApp [data-testid^="stBaseButton-secondary"] *,.stApp [data-testid^="stBaseLinkButton-secondary"] *{color:var(--mx-text)!important}
.stApp [data-testid^="stBaseButton-secondary"]:hover,.stApp [data-testid^="stBaseLinkButton-secondary"]:hover{background:var(--mx-glass-2)!important}
.stApp [data-testid="stFileUploaderDropzone"],.stApp [data-testid="stAudioInput"]>div,.stApp [data-testid="stChatInput"],
.stApp [data-testid="stChatInput"]>div{background:var(--mx-glass)!important;border:1px dashed var(--mx-line)!important;border-radius:18px!important}
.stApp [data-testid="stFileUploaderDropzone"] *,.stApp [data-testid="stChatInput"] textarea{color:var(--mx-text)!important;
  -webkit-text-fill-color:var(--mx-text)}
.stApp [data-testid="stChatInput"] textarea{background:transparent!important}
.stApp [data-testid="stVerticalBlockBorderWrapper"]{border-color:var(--mx-line)!important;background:rgba(255,255,255,.035);
  backdrop-filter:blur(6px)}
.stApp [data-testid="stExpander"] details{background:rgba(255,255,255,.035);border-color:var(--mx-line)!important;backdrop-filter:blur(6px)}
.stApp [data-testid="stExpander"] summary *{color:var(--mx-text)!important}

/* ---- motion: entrance animations ---- */
@keyframes mxRise{from{opacity:0;transform:translateY(22px) scale(.98)}to{opacity:1;transform:none}}
@keyframes mxDrop{from{opacity:0;transform:translateY(-16px)}to{opacity:1;transform:none}}
@keyframes mxPop{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:none}}
@keyframes mxFadeWord{from{opacity:0;transform:translateY(.4em);filter:blur(4px)}to{opacity:1;transform:none;filter:none}}
@keyframes mxSheen{0%,70%{transform:translateX(-120%) skewX(-18deg)}100%{transform:translateX(220%) skewX(-18deg)}}
@keyframes mxBob{0%,100%{transform:translateY(0) rotate(-3deg)}50%{transform:translateY(-10px) rotate(3deg)}}
@keyframes mxSpin{to{--mx-ang:360deg}}
@keyframes mxBeat{0%,40%,100%{transform:scale(1)}10%{transform:scale(1.16)}20%{transform:scale(.97)}30%{transform:scale(1.1)}}
.sj-head{animation:mxDrop .55s cubic-bezier(.2,.8,.2,1) both}
.sj-head::after{content:"";position:absolute;top:0;bottom:0;left:0;width:35%;pointer-events:none;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.16),transparent);animation:mxSheen 6s ease-in-out infinite 1s}
.sj-head-icon{animation:mxBob 6s ease-in-out infinite}
.sj-card{animation:mxPop .4s ease both}
.stApp [data-testid="stChatMessage"]{animation:mxRise .45s ease both}
.mx-word{display:inline-block;animation:mxFadeWord .6s cubic-bezier(.2,.8,.2,1) both}

/* ---- tap ripple (made by the script) ---- */
.mx-ripple{position:fixed;width:16px;height:16px;margin:-8px 0 0 -8px;border-radius:50%;pointer-events:none;z-index:99999;
  border:2px solid var(--mx-ripple,#3EE0AA);opacity:0}
.mx-ripple.go{animation:mxRipple .6s ease-out}
@keyframes mxRipple{0%{opacity:.9;transform:scale(.4)}100%{opacity:0;transform:scale(5.5)}}
#mx-fireflies{position:fixed;inset:0;width:100vw;height:100vh;z-index:-1;pointer-events:none}
#mx-silk{position:fixed;inset:0;width:100vw!important;height:100vh!important;z-index:-2;pointer-events:none;
  filter:blur(6px) saturate(1.1)}

/* ---- button effects: fill from the centre, neon glow, scale, dashed ring ---- */
.stApp .stButton>button,.stApp .stDownloadButton>button,.stApp .stLinkButton>a,.stApp [data-testid="stPageLink"] a{
  position:relative;overflow:hidden;isolation:isolate;
  transition:transform .18s ease,box-shadow .25s ease,border-color .25s ease,background-color .25s ease!important}
.stApp .stButton>button::before,.stApp .stDownloadButton>button::before,.stApp .stLinkButton>a::before,
.stApp [data-testid="stPageLink"] a::before{content:"";position:absolute;left:50%;top:50%;width:150%;aspect-ratio:1;
  border-radius:50%;z-index:-1;pointer-events:none;transform:translate(-50%,-50%) scale(0);
  background:radial-gradient(circle,var(--mx-fill,rgba(62,224,170,.38)) 0%,rgba(62,224,170,.10) 48%,transparent 70%);
  transition:transform .5s cubic-bezier(.2,.8,.2,1)}
.stApp .stButton>button:hover::before,.stApp .stDownloadButton>button:hover::before,.stApp .stLinkButton>a:hover::before,
.stApp [data-testid="stPageLink"] a:hover::before{transform:translate(-50%,-50%) scale(1)}
.stApp .stButton>button:hover,.stApp .stDownloadButton>button:hover,.stApp .stLinkButton>a:hover{
  transform:translateY(-2px) scale(1.02);border-color:rgba(62,224,170,.8)!important;
  box-shadow:0 0 0 1px rgba(62,224,170,.55),0 0 18px rgba(62,224,170,.45),0 0 40px rgba(62,224,170,.18)!important}
.stApp .stButton>button[kind="primary"]:hover,.stApp .stLinkButton>a[kind="primary"]:hover,
.stApp .stDownloadButton>button[kind="primary"]:hover{--mx-fill:rgba(255,255,255,.30);
  box-shadow:0 0 0 1px rgba(255,255,255,.35),0 0 22px var(--sj-a1,#3EE0AA),0 10px 30px rgba(0,0,0,.35)!important}
.stApp .stButton>button:active,.stApp .stLinkButton>a:active,.stApp [data-testid="stPageLink"] a:active{transform:scale(.97)}
div[class*="st-key-tile_"] [data-testid="stPageLink"] a{--mx-fill:rgba(255,255,255,.45)}
div[class*="st-key-tile_"] [data-testid="stPageLink"] a:hover{box-shadow:0 0 0 2px rgba(255,255,255,.55),0 0 24px rgba(255,255,255,.35)}
section[data-testid="stSidebar"] .stButton>button:hover{transform:none}
.sj-t-icon{position:relative}
.sj-t-icon::after{content:"";position:absolute;inset:-8px;border-radius:50%;border:2px dashed rgba(255,255,255,.8);
  opacity:0;transform:scale(.7);transition:opacity .3s ease,transform .3s ease}
div[class*="st-key-tile_"]:hover .sj-t-icon::after{opacity:1;transform:scale(1);animation:mxRingSpin 7s linear infinite}
@keyframes mxRingSpin{to{transform:scale(1) rotate(360deg)}}
.sj-chip{transition:box-shadow .25s ease}.sj-chip:hover{box-shadow:0 0 18px rgba(62,224,170,.45)}

/* ---- calm mode: phone setting or the sidebar toggle ---- */
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
.st-key-mx_fx{position:absolute!important;width:0!important;height:0!important;overflow:hidden!important}
</style>
"""

CALM = """<style>*,*::before,*::after{animation:none!important;transition:none!important}
#mx-fireflies,#mx-silk{display:none!important}</style>"""


# ---------------------------------------------------------------------------------------------
# 2. Script that runs once in the page itself: fireflies, ripples, tile tilt, count-up numbers
# ---------------------------------------------------------------------------------------------
PAGE_JS = r"""
(function () {
  if (window.__mxFx) return;                       // only ever install once
  const D = document, W = window;
  const fx = W.__mxFx = { on: true };
  const reduce = W.matchMedia("(prefers-reduced-motion: reduce)");
  const lowPower = (navigator.hardwareConcurrency || 8) <= 4 || (navigator.deviceMemory || 8) <= 2;
  const fine = W.matchMedia("(hover: hover) and (pointer: fine)");
  const active = () => fx.on && !reduce.matches;

  // ---------- fireflies ----------
  const cv = D.createElement("canvas"); cv.id = "mx-fireflies"; D.body.appendChild(cv);
  const g = cv.getContext("2d");
  const DPR = Math.min(W.devicePixelRatio || 1, 1.5);
  let w = 0, h = 0;
  function size() { w = innerWidth; h = innerHeight; cv.width = w * DPR; cv.height = h * DPR; g.setTransform(DPR, 0, 0, DPR, 0, 0); }
  size(); W.addEventListener("resize", size);
  const sprite = D.createElement("canvas"); sprite.width = sprite.height = 48;
  (function () { const s = sprite.getContext("2d"); const r = s.createRadialGradient(24, 24, 0, 24, 24, 24);
    r.addColorStop(0, "rgba(255,240,180,1)"); r.addColorStop(.18, "rgba(246,194,91,.95)");
    r.addColorStop(.45, "rgba(246,170,60,.28)"); r.addColorStop(1, "rgba(246,170,60,0)"); s.fillStyle = r; s.fillRect(0, 0, 48, 48); })();
  const N = lowPower ? 16 : 34, flies = [];
  for (let i = 0; i < N; i++) flies.push({ x: Math.random() * w, y: h * (.25 + Math.random() * .75),
    a: Math.random() * 6.28, s: .15 + Math.random() * .35, p: Math.random() * 6.28, r: 10 + Math.random() * 14 });
  let mx = -999, my = -999, last = 0;
  W.addEventListener("pointermove", e => { mx = e.clientX; my = e.clientY; }, { passive: true });
  function frame(t) {
    requestAnimationFrame(frame);
    if (D.hidden) return;
    if (!active()) { if (cv.style.display !== "none") { cv.style.display = "none"; } return; }
    cv.style.display = "";
    if (lowPower && t - last < 33) return; last = t;
    g.clearRect(0, 0, w, h);
    for (const f of flies) {
      f.a += (Math.random() - .5) * .15;
      f.x += Math.cos(f.a) * f.s; f.y += Math.sin(f.a) * f.s * .7;
      const dx = f.x - mx, dy = f.y - my, d2 = dx * dx + dy * dy;
      if (d2 < 14000) { const d = Math.sqrt(d2) || 1; f.x += dx / d * 1.6; f.y += dy / d * 1.6; }
      if (f.x < -30) f.x = w + 30; if (f.x > w + 30) f.x = -30; if (f.y < -30) f.y = h + 30; if (f.y > h + 30) f.y = -30;
      const glow = .25 + .75 * Math.pow(Math.max(0, Math.sin(t / 900 + f.p)), 3);
      g.globalAlpha = glow; g.drawImage(sprite, f.x - f.r, f.y - f.r, f.r * 2, f.r * 2);
    }
    g.globalAlpha = 1;
  }
  requestAnimationFrame(frame);

  // ---------- silk background (WebGL, like React Bits "Silk"), low resolution + 30 fps ----------
  (function silk() {
    if (lowPower) return;                                  // CSS aurora stays on slow phones
    const c = D.createElement("canvas"); c.id = "mx-silk";
    const gl = c.getContext("webgl", { antialias: false, alpha: false, powerPreference: "low-power" });
    if (!gl) return;
    D.body.insertBefore(c, D.body.firstChild);
    const VS = "attribute vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";
    const FS = `precision mediump float;uniform vec2 r;uniform float t;
      float h(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float n(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);
        return mix(mix(h(i),h(i+vec2(1.,0.)),f.x),mix(h(i+vec2(0.,1.)),h(i+vec2(1.,1.)),f.x),f.y);}
      void main(){vec2 uv=gl_FragCoord.xy/r;vec2 p=uv*vec2(r.x/r.y,1.)*2.2;float s=t*.05;
        vec2 q=p;q.y+=.35*sin(q.x*1.3+s*2.)+.25*n(q*1.5+s);q.x+=.2*sin(q.y*1.7-s*1.4);
        float f=sin(q.x*2.4+q.y*4.2+s*3.)*.5+.5;f=mix(f,sin(q.y*6.5-q.x*1.7-s*2.2)*.5+.5,.35);
        float sh=pow(f,6.);
        vec3 deep=vec3(.016,.09,.082),teal=vec3(.05,.27,.25),night=vec3(.04,.09,.23);
        vec3 col=mix(deep,mix(teal,night,smoothstep(.15,.95,uv.x)),f*.72);
        col+=sh*.17*vec3(.55,1.,.85);col*=.8+.3*uv.y;
        gl_FragColor=vec4(col,1.);}`;
    function sh(type, src) { const o = gl.createShader(type); gl.shaderSource(o, src); gl.compileShader(o); return o; }
    const pr = gl.createProgram(); gl.attachShader(pr, sh(gl.VERTEX_SHADER, VS)); gl.attachShader(pr, sh(gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(pr);
    if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) { c.remove(); return; }
    gl.useProgram(pr);
    const b = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, b);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(pr, "p"); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
    const uR = gl.getUniformLocation(pr, "r"), uT = gl.getUniformLocation(pr, "t");
    const SCALE = .35;
    function fit() { c.width = Math.max(2, innerWidth * SCALE | 0); c.height = Math.max(2, innerHeight * SCALE | 0);
      gl.viewport(0, 0, c.width, c.height); gl.uniform2f(uR, c.width, c.height); }
    fit(); W.addEventListener("resize", fit);
    let last = 0; const t0 = performance.now();
    (function loop(t) {
      requestAnimationFrame(loop);
      if (D.hidden || t - last < 33) return;
      if (!active()) { c.style.display = "none"; return; }
      c.style.display = ""; last = t;
      gl.uniform1f(uT, (t - t0) / 1000); gl.drawArrays(gl.TRIANGLES, 0, 3);
    })(0);
  })();

  // ---------- smooth scrolling with Lenis (computer mouse only; phones keep their own scrolling) ----------
  (function smooth() {
    if (!fine.matches) return;
    const s = D.createElement("script");
    s.src = "https://cdn.jsdelivr.net/npm/lenis@1.1.13/dist/lenis.min.js";
    s.onload = () => {
      let lenis = null, wrap = null;
      function scroller() {
        for (const el of D.querySelectorAll('[data-testid="stMain"],section.stMain,[data-testid="stAppViewContainer"],section.main')) {
          const o = getComputedStyle(el).overflowY;
          if ((o === "auto" || o === "scroll") && el.scrollHeight > el.clientHeight + 4) return el;
        }
        return null;
      }
      function sync() {
        const want = active() && !D.querySelector('[data-testid="stChatInput"]');   // chat pages scroll themselves
        const el = scroller();
        if (lenis && (!want || el !== wrap || (wrap && !wrap.isConnected))) { lenis.destroy(); lenis = null; wrap = null; }
        if (!lenis && want && el && W.Lenis) {
          try { lenis = new W.Lenis({ wrapper: el, content: el.firstElementChild || el, lerp: .1, smoothWheel: true }); wrap = el; }
          catch (e) { lenis = null; }
        }
      }
      (function raf(t) { requestAnimationFrame(raf); if (lenis) lenis.raf(t); })(0);
      setInterval(sync, 1000); sync();
    };
    D.head.appendChild(s);
  })();

  // ---------- tap ripples (a fixed pool, reused) ----------
  const pool = []; let next = 0;
  for (let i = 0; i < 6; i++) { const r = D.createElement("span"); r.className = "mx-ripple"; D.body.appendChild(r); pool.push(r); }
  D.addEventListener("pointerdown", e => {
    if (!active()) return;
    const r = pool[next++ % pool.length];
    const onTile = e.target.closest && e.target.closest('[class*="st-key-tile_"],[class*="st-key-home_sos"],.sj-hero');
    r.style.setProperty("--mx-ripple", onTile ? "#ffffff" : "#3EE0AA");
    r.style.left = e.clientX + "px"; r.style.top = e.clientY + "px";
    r.classList.remove("go"); void r.offsetWidth; r.classList.add("go");
  }, { passive: true });

  // ---------- gentle 3D tilt on the home tiles (mouse only) ----------
  let tilted = null;
  D.addEventListener("pointermove", e => {
    if (!fine.matches || !active()) return;
    const tile = e.target.closest && e.target.closest('[class*="st-key-tile_"]');
    if (tilted && tilted !== tile) { tilted.style.transform = ""; tilted = null; }
    if (!tile) return;
    const b = tile.getBoundingClientRect();
    const rx = ((e.clientY - b.top) / b.height - .5) * -6, ry = ((e.clientX - b.left) / b.width - .5) * 8;
    tile.style.transform = `perspective(900px) rotateX(${rx.toFixed(2)}deg) rotateY(${ry.toFixed(2)}deg) translateY(-4px)`;
    tilted = tile;
  }, { passive: true });

  // ---------- numbers that count up when they come into view ----------
  const io = new IntersectionObserver(es => es.forEach(en => { if (en.isIntersecting) { io.unobserve(en.target); count(en.target); } }),
    { threshold: .4 });
  function count(el) {
    const to = parseFloat(el.dataset.to), pre = el.dataset.pre || "", suf = el.dataset.suf || "";
    const show = v => pre + Math.round(v).toLocaleString("en-IN") + suf;
    if (!active() || isNaN(to)) { el.textContent = show(to); return; }
    const t0 = performance.now(), dur = 1400;
    (function step(t) { const k = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - k, 3);
      el.textContent = show(to * e); if (k < 1) requestAnimationFrame(step); })(t0);
  }
  let queued = false;
  function scan() { queued = false; D.querySelectorAll(".mx-count:not([data-mx])").forEach(el => { el.dataset.mx = "1"; io.observe(el); }); }
  new MutationObserver(() => { if (!queued) { queued = true; requestAnimationFrame(scan); } })
    .observe(D.body, { childList: true, subtree: true });
  scan();
})();
"""

BRIDGE = """<script>
(function () {{
  var P = window.parent, D = P.document;
  if (!D.getElementById("mx-fx-script")) {{
    var s = D.createElement("script"); s.id = "mx-fx-script"; s.textContent = {code}; D.body.appendChild(s);
  }}
  if (P.__mxFx) P.__mxFx.on = {on};
}})();
</script>"""


def inject():
    """Call once per run from app.py (after the sidebar is drawn)."""
    on = st.session_state.get("fx_on", True)
    st.markdown(SKIN, unsafe_allow_html=True)
    if not on:
        st.markdown(CALM, unsafe_allow_html=True)
    import json
    with st.container(key="mx_fx"):
        try:
            components.html(BRIDGE.format(code=json.dumps(PAGE_JS), on="true" if on else "false"), height=0)
        except Exception:
            pass   # the app works fine without the effects


# ---------------------------------------------------------------------------------------------
# 3. Small helpers used by pages
# ---------------------------------------------------------------------------------------------
def words(text, start=0.15, step=0.07):
    """Text that appears word by word (words, never letters, so Kannada stays intact)."""
    out = []
    for i, w in enumerate(str(text).split()):
        out.append(f'<span class="mx-word" style="animation-delay:{start + i * step:.2f}s">{html.escape(w)}</span>')
    return " ".join(out)


def count(value, to, pre="", suf=""):
    """A number that counts up from 0 when it scrolls into view (shows the final value without the script)."""
    return (f'<span class="mx-count" data-to="{to}" data-pre="{html.escape(pre)}" data-suf="{html.escape(suf)}">'
            f'{html.escape(value)}</span>')


# Night village scene for the home hero: hills, coconut palms, a lit hut, fireflies and a heartbeat line.
def _ecg_path():
    pts, x = [], 0
    while x <= 1240:
        pts += [f"{x},236", f"{x + 70},236", f"{x + 82},228", f"{x + 92},236", f"{x + 104},236", f"{x + 112},248",
                f"{x + 124},166", f"{x + 136},262", f"{x + 146},236", f"{x + 172},236", f"{x + 190},222",
                f"{x + 208},236", f"{x + 260},236"]
        x += 260
    return "M" + " L".join(pts)


def _palm(x, y, scale=1.0):
    s = scale
    trunk = (f'<path d="M{x},{y} C{x + 8 * s},{y - 60 * s} {x - 6 * s},{y - 120 * s} {x + 14 * s},{y - 170 * s}" '
             f'stroke="#03211C" stroke-width="{8 * s:.1f}" fill="none" stroke-linecap="round"/>')
    tx, ty = x + 14 * s, y - 170 * s
    fronds = [(-70, 18), (-52, -12), (-18, -34), (22, -36), (58, -14), (76, 16), (-34, 34), (40, 36)]
    leaves = "".join(
        f'<path d="M{tx:.1f},{ty:.1f} Q{tx + dx * .5 * s:.1f},{ty + (dy - 26) * s:.1f} {tx + dx * s:.1f},{ty + dy * s:.1f}" '
        f'stroke="#03211C" stroke-width="{6 * s:.1f}" fill="none" stroke-linecap="round"/>' for dx, dy in fronds)
    return trunk + leaves


def hero_scene():
    flies = "".join(
        f'<circle class="mx-hf" cx="{cx}" cy="{cy}" r="{r}" style="animation-delay:{d}s,{d * 1.7:.1f}s"/>'
        for cx, cy, r, d in [(860, 150, 3, 0), (930, 205, 2.4, 1.2), (1010, 120, 2.8, 2.1), (1110, 180, 2.2, .6),
                             (760, 200, 2.6, 1.8), (1160, 110, 2.4, 2.6), (690, 150, 2, 3.1), (980, 240, 2.2, .9)])
    stars = "".join(f'<circle class="mx-st" cx="{cx}" cy="{cy}" r="{r}" style="animation-delay:{d}s"/>'
                    for cx, cy, r, d in [(640, 40, 1.4, 0), (720, 70, 1, 1), (820, 30, 1.6, 2), (900, 64, 1.1, .5),
                                         (1150, 40, 1.3, 1.5), (980, 24, 1, 2.5), (560, 80, 1.2, 1.2)])
    return f"""
<svg class="mx-scene" viewBox="0 0 1200 300" preserveAspectRatio="xMaxYMax slice" aria-hidden="true">
  <defs>
    <radialGradient id="mxMoon"><stop offset="0" stop-color="#FFF3C9"/><stop offset=".55" stop-color="#F6DFA0" stop-opacity=".9"/>
      <stop offset="1" stop-color="#F6DFA0" stop-opacity="0"/></radialGradient>
    <radialGradient id="mxWin"><stop offset="0" stop-color="#FFD27A"/><stop offset="1" stop-color="#FFB347" stop-opacity="0"/></radialGradient>
  </defs>
  {stars}
  <circle cx="1112" cy="64" r="60" fill="url(#mxMoon)" opacity=".35"/>
  <circle cx="1112" cy="64" r="24" fill="#FFF0C4"/>
  <circle cx="1122" cy="57" r="21" fill="#0D3B3D"/>
  <path d="M0,250 C160,200 300,214 460,232 C620,250 760,196 900,206 C1040,216 1120,190 1200,200 L1200,300 L0,300Z" fill="#0A3A33" opacity=".75"/>
  <path class="mx-ecg-base" d="{_ecg_path()}"/>
  <path class="mx-ecg" d="{_ecg_path()}"/>
  <path d="M0,276 C200,246 380,262 560,268 C740,274 880,244 1020,250 C1110,254 1160,248 1200,246 L1200,300 L0,300Z" fill="#05261F"/>
  {_palm(965, 264, .85)}{_palm(1070, 260, .62)}
  <g transform="translate(830,226)">
    <circle cx="26" cy="30" r="34" fill="url(#mxWin)" opacity=".55" class="mx-glow"/>
    <polygon points="-6,20 26,-6 58,20" fill="#03211C"/><rect x="2" y="20" width="48" height="30" fill="#03211C"/>
    <rect x="18" y="28" width="14" height="12" rx="2" fill="#FFC861" class="mx-glow"/>
  </g>
  {flies}
</svg>"""


HERO_CSS = """
<style>
.sj-hero{position:relative;overflow:hidden;border-radius:28px;padding:2rem 2.2rem 170px;margin-bottom:1.2rem;
  background:linear-gradient(170deg,#0B2E40 0%,#0C3A3C 45%,#0A4034 100%);border:1px solid rgba(255,255,255,.08);
  box-shadow:0 20px 50px rgba(0,0,0,.35);animation:mxDrop .6s cubic-bezier(.2,.8,.2,1) both}
.sj-hero .mx-scene{position:absolute;left:0;right:0;bottom:0;width:100%;height:240px;overflow:visible;pointer-events:none}
.sj-hero>.sj-hero-in{position:relative;z-index:1}
.sj-greet{color:#F6C25B;font-size:1.25rem;font-weight:700}
.sj-title{font-size:3.4rem;font-weight:800;line-height:1.05;margin:.35rem 0 .5rem;letter-spacing:-.01em;
  background:linear-gradient(90deg,#FFFFFF 0%,#BFF7E2 45%,#3EE0AA 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.sj-tag{color:#D6EDE6;font-size:1.2rem;max-width:620px;line-height:1.5}
.sj-chip{display:inline-flex;gap:.35rem;margin-top:.9rem;background:rgba(255,255,255,.12);color:#fff;border-radius:999px;
  padding:.3rem .9rem;font-weight:600;font-size:.95rem;border:1px solid rgba(255,255,255,.18);backdrop-filter:blur(6px)}
.mx-ecg-base{fill:none;stroke:rgba(62,224,170,.18);stroke-width:2}
.mx-ecg{fill:none;stroke:#3EE0AA;stroke-width:3;stroke-linecap:round;stroke-linejoin:round;stroke-dasharray:180 2400;
  filter:drop-shadow(0 0 6px #3EE0AA);animation:mxEcg 4.2s linear infinite}
@keyframes mxEcg{from{stroke-dashoffset:2580}to{stroke-dashoffset:0}}
.mx-hf{fill:#FFD98A;filter:drop-shadow(0 0 5px #F6C25B);transform-box:fill-box;transform-origin:center;
  animation:mxBlink 3.2s ease-in-out infinite,mxDrift 9s ease-in-out infinite alternate}
@keyframes mxBlink{0%,100%{opacity:.15}50%{opacity:1}}
@keyframes mxDrift{from{transform:translate(0,0)}to{transform:translate(22px,-16px)}}
.mx-st{fill:#fff;animation:mxBlink 4s ease-in-out infinite}
.mx-glow{animation:mxLamp 3.5s ease-in-out infinite}
@keyframes mxLamp{0%,100%{opacity:.75}50%{opacity:1}}
@media (max-width:640px){.sj-title{font-size:2.6rem}.sj-hero{padding:1.5rem 1.3rem 150px}.sj-hero .mx-scene{height:175px}}
</style>
"""
