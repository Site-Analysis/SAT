import Link from "next/link";
import styles from "./landing.module.css";

const $ = styles as Record<string, string>;

export function LandingPage() {
  return (
    <div className={$["landing"]}>

      {/* ── NAV ── */}
      <nav>
        <a className={$["nav-logo"]} href="#">
          <img src="/qnit-logo.svg" alt="Qnit by GeoKnit" />
        </a>
        <ul className={$["nav-links"]}>
          <li><a href="#problem">The problem</a></li>
          <li><a href="#modules">Modules</a></li>
          <li><a href="#pricing">Pricing</a></li>
          <li><Link href="/login" className={$["btn-nav"]}>Try free →</Link></li>
        </ul>
      </nav>

      {/* ── HERO ── */}
      <section className={$["hero"]}>
        <div>
          <div className={$["hero-eyebrow"]}>
            <span className={$["hero-eyebrow-dot"]}></span>
            Site Intelligence · India · Bengaluru
          </div>
          <h1 className={$["hero-h1"]}>
            Your site knows its flood history,<br />
            wind patterns, and climate zone.<br />
            <em>You just need one place to ask.</em>
          </h1>
          <p className={$["hero-sub"]}>
            Architects use it before the first sketch.
            Builders use it before the land is bought.
            Cited, India-specific site intelligence — flood risk, sun path, wind, rainfall, temperature — on one map, in one session.
          </p>
          <div className={$["hero-actions"]}>
            <Link href="/login" className={$["btn-primary"]}>Try your first site free →</Link>
            <a href="#problem" className={$["btn-ghost"]}>See the problem it solves</a>
          </div>
          <p className={$["hero-fine"]}>No install · NBC 2016 · BBMP / BDA · Bengaluru</p>
        </div>

        <div className={$["hero-app"]}>
          <div className={$["app-bar"]}>
            <div className={$["app-dot"]} style={{ background: "#FF5F57" }}></div>
            <div className={$["app-dot"]} style={{ background: "#FEBC2E" }}></div>
            <div className={$["app-dot"]} style={{ background: "#28C840" }}></div>
            <div className={$["app-bar-addr"]}>
              <div className={$["app-bar-addr-pin"]}></div>
              <div className={$["app-bar-addr-text"]}>Koramangala 4th Block, Bengaluru</div>
            </div>
          </div>
          <div className={$["app-map"]}>
            <div className={$["app-grid"]}></div>
            <div className={$["app-block"]} style={{ width: "64px", height: "44px", top: "16px", left: "24px" }}></div>
            <div className={$["app-block"]} style={{ width: "44px", height: "58px", top: "16px", left: "98px" }}></div>
            <div className={$["app-block"]} style={{ width: "72px", height: "36px", top: "92px", left: "16px" }}></div>
            <div className={$["app-block"]} style={{ width: "50px", height: "50px", top: "88px", right: "36px" }}></div>
            <div className={$["app-block"]} style={{ width: "56px", height: "30px", bottom: "18px", left: "78px" }}></div>
            <div className={$["app-road-h"]} style={{ width: "100%", height: "7px", top: "80px", left: "0" }}></div>
            <div className={$["app-road-v"]} style={{ width: "7px", height: "100%", top: "0", left: "158px" }}></div>
            <div className={$["app-rings"]}>
              <div className={$["app-ring"]} style={{ width: "140px", height: "140px" }}></div>
              <div className={$["app-ring"]} style={{ width: "84px", height: "84px" }}></div>
              <div className={$["app-ring"]} style={{ width: "36px", height: "36px" }}></div>
            </div>
            <div className={$["app-pin"]}>
              <div className={$["app-pin-head"]}></div>
              <div className={$["app-pin-tail"]}></div>
              <div className={$["app-pin-label"]}>Bengaluru · Site Analysis</div>
            </div>
          </div>
          <div className={$["app-modules"]}>
            <div className={$["app-mod"]}>
              <div className={$["app-mod-icon"]}>🌊</div>
              <div className={$["app-mod-name"]}>Flood Risk</div>
              <div className={$["app-mod-bar"]}><div className={$["app-mod-fill"]} style={{ width: "38%", background: "var(--flood)" }}></div></div>
              <div className={$["app-mod-val"]} style={{ color: "var(--flood)" }}>38/100</div>
            </div>
            <div className={$["app-mod"]}>
              <div className={$["app-mod-icon"]}>☀️</div>
              <div className={$["app-mod-name"]}>Sun Path</div>
              <div className={$["app-mod-bar"]}><div className={$["app-mod-fill"]} style={{ width: "84%", background: "var(--sun)" }}></div></div>
              <div className={$["app-mod-val"]} style={{ color: "var(--sun)" }}>84/100</div>
            </div>
            <div className={$["app-mod"]}>
              <div className={$["app-mod-icon"]}>💨</div>
              <div className={$["app-mod-name"]}>Wind</div>
              <div className={$["app-mod-bar"]}><div className={$["app-mod-fill"]} style={{ width: "81%", background: "var(--wind)" }}></div></div>
              <div className={$["app-mod-val"]} style={{ color: "var(--wind)" }}>81/100</div>
            </div>
          </div>
          <div className={$["app-source-strip"]}>JRC · Open-Meteo · IMD · GEE · NBC 2016 · BBMP/BDA</div>
        </div>
      </section>

      {/* ── ANCHOR QUOTE ── */}
      <div className={$["quote-anchor"]}>
        <div className={$["qa-inner"]}>
          <div className={$["qa-label"]}>UX Research · Transcript 01:02:06 · Phase 1</div>
          <div className={$["qa-quote"]}><strong>&ldquo;The main problem is that we don&apos;t get any site analysis data in a one-stop.&rdquo;</strong></div>
          <div className={$["qa-attr"]}><strong>Ranjitha</strong> — Architect · Bengaluru · confirmed beta participant</div>
        </div>
      </div>

      {/* ── PROBLEM — ARCHITECT ── */}
      <section className={$["prob-arch"]} id="problem">
        <div>
          <div className={$["sec-eyebrow"]}>For Architects</div>
          <h2 className={$["sec-title"]}>Your design starts on top of data that was never built for architects.</h2>
          <p className={$["sec-sub"]}>Every Indian architect runs the same hunt before a single line is drawn. Scattered across portals, contacts, and top Google results — none of which you can cite.</p>

          <div className={$["source-list"]}>
            <div className={$["src-row"]}>
              <div className={$["src-info"]}>
                <div className={$["src-name"]}>Google Maps / Google Earth Pro</div>
                <div className={$["src-pain"]}>Base map only. No climate, no regulatory, no flood data.</div>
              </div>
              <div className={`${$["src-badge"]} ${$["ok"]}`}>Partial</div>
            </div>
            <div className={$["src-row"]}>
              <div className={$["src-info"]}>
                <div className={$["src-name"]}>BBMP / BDA municipal portals</div>
                <div className={$["src-pain"]}>Frequently offline. Inconsistent data. No export.</div>
              </div>
              <div className={`${$["src-badge"]} ${$["warn"]}`}>Unreliable</div>
            </div>
            <div className={$["src-row"]}>
              <div className={$["src-info"]}>
                <div className={$["src-name"]}>Top Google results — wind, rainfall</div>
                <div className={$["src-pain"]}>Reliability unknown. Cannot be cited in submissions.</div>
              </div>
              <div className={`${$["src-badge"]} ${$["bad"]}`}>Not citable</div>
            </div>
            <div className={$["src-row"]}>
              <div className={$["src-info"]}>
                <div className={$["src-name"]}>Flood risk — no authoritative Indian source</div>
                <div className={$["src-pain"]}>Fragmented. Nothing site-specific. Nothing that holds up.</div>
              </div>
              <div className={`${$["src-badge"]} ${$["bad"]}`}>Gap</div>
            </div>
            <div className={$["src-row"]}>
              <div className={$["src-info"]}>
                <div className={$["src-name"]}>Regulatory bylaws — firm contact network</div>
                <div className={$["src-pain"]}>Relationship-locked. Not portable. Not documentable.</div>
              </div>
              <div className={`${$["src-badge"]} ${$["warn"]}`}>Manual</div>
            </div>
            <div className={$["src-row"]}>
              <div className={$["src-info"]}>
                <div className={$["src-name"]}>Parametric — Rhino + Grasshopper + Python</div>
                <div className={$["src-pain"]}>Specialist setup. Then a second full effort to represent the output.</div>
              </div>
              <div className={`${$["src-badge"]} ${$["warn"]}`}>Expert only</div>
            </div>
          </div>
        </div>

        <div className={$["arch-right"]}>
          <div className={$["consequence-card"]}>
            <div className={$["cc-label"]}>Real Consequence · Ranjitha · Bengaluru</div>
            <p className={$["cc-text"]}>Galvanised steel was specified for a site in a humid climate microzone. No authoritative rainfall and humidity data existed for that exact location. The material began rusting within two monsoon seasons.</p>
            <div className={$["cc-outcome"]}>→ Client paid double the labour cost to remediate.</div>
          </div>

          <div className={$["workflow-box"]}>
            <div className={$["wf-label"]}>Confirmed workflow · Bengaluru practice</div>
            <div className={$["wf-steps"]}>
              <div className={$["wf-step"]}>
                <div className={$["wf-dot"]}><div className={$["wf-dot-inner"]}></div></div>
                <div className={$["wf-text"]}><strong>Pre-study</strong> — programme, client brief</div>
              </div>
              <div className={$["wf-step"]}>
                <div className={`${$["wf-dot"]} ${$["warn"]}`}><div className={$["wf-dot-inner"]}></div></div>
                <div className={$["wf-text"]}><strong>Site visits</strong> — three temporal windows (morning / noon / evening)</div>
              </div>
              <div className={$["wf-step"]}>
                <div className={`${$["wf-dot"]} ${$["warn"]}`}><div className={$["wf-dot-inner"]}></div></div>
                <div className={$["wf-text"]}><strong>Climate hunting</strong> — cross-referenced manually across sources above</div>
              </div>
              <div className={$["wf-step"]}>
                <div className={`${$["wf-dot"]} ${$["warn"]}`}><div className={$["wf-dot-inner"]}></div></div>
                <div className={$["wf-text"]}><strong>Parametric analysis</strong> — SketchUp + Rhino + AI-generated Python</div>
              </div>
              <div className={$["wf-step"]}>
                <div className={`${$["wf-dot"]} ${$["bad"]}`}><div className={$["wf-dot-inner"]}></div></div>
                <div className={$["wf-text"]}><strong>Regulatory</strong> — contact network, not portal-based</div>
              </div>
              <div className={$["wf-step"]}>
                <div className={`${$["wf-dot"]} ${$["bad"]}`}><div className={$["wf-dot-inner"]}></div></div>
                <div className={$["wf-text"]}><strong>Spec → Presentation</strong> — AutoCAD/Revit → Photoshop/Canva. A full second effort after the analysis.</div>
              </div>
            </div>
            <div className={$["wf-time"]}>1 week (firm, parallelised) · 6–7 weeks (solo)</div>
          </div>
        </div>
      </section>

      <div className={$["divider"]}></div>

      {/* ── PROBLEM — BUILDER ── */}
      <section className={$["prob-builder"]}>
        <div>
          <div className={`${$["sec-eyebrow"]} ${$["amber"]}`}>For Builders &amp; Developers</div>
          <h2 className={$["sec-title"]}>A bad site decision doesn&apos;t cost time. It costs the project.</h2>
          <p className={$["sec-sub"]}>Builder firms evaluate many sites before shortlisting a few. Each one takes weeks of consultant co-ordination. Each one carries the same risk — data gaps that don&apos;t surface until capital is already committed.</p>

          <div className={$["builder-pull"]}>
            <p>&ldquo;Before you spend a rupee on a site, know everything it will cost you.&rdquo;</p>
            <cite>The Qnit principle for builder due diligence</cite>
          </div>
        </div>

        <div>
          <div className={$["ct-table"]}>
            <div className={$["ct-row"]}>
              <div>
                <div className={$["ct-error"]}>Flood zone — undisclosed until bank appraisal</div>
                <div className={$["ct-cause"]}>Land cost committed. Design underway. Financing refused months in.</div>
              </div>
              <div className={$["ct-impact"]}>Crores locked<br />+ months lost</div>
            </div>
            <div className={$["ct-row"]}>
              <div>
                <div className={$["ct-error"]}>Wrong FSI — built area exceeds sanction</div>
                <div className={$["ct-cause"]}>Demolition order or compounding fine. Structure at risk.</div>
              </div>
              <div className={$["ct-impact"]}>Structure loss<br />+ litigation</div>
            </div>
            <div className={$["ct-row"]}>
              <div>
                <div className={$["ct-error"]}>Wrong setback — encroachment on municipality</div>
                <div className={$["ct-cause"]}>Stop-work order. Months of delay. Penalties outstanding.</div>
              </div>
              <div className={$["ct-impact"]}>Stop-work<br />+ penalties</div>
            </div>
            <div className={$["ct-row"]}>
              <div>
                <div className={$["ct-error"]}>Climate misread — material failure post-occupation</div>
                <div className={$["ct-cause"]}>Waterproofing failure, basement flooding, resident complaints.</div>
              </div>
              <div className={$["ct-impact"]}>₹50L–₹5Cr<br />remediation</div>
            </div>
          </div>

          <div className={$["stage-map"]}>
            <div className={$["stage"]} style={{ paddingTop: "0" }}>
              <div className={$["stage-num"]}>01</div>
              <div style={{ flex: 1 }}>
                <div className={$["stage-name"]}>Land Identification</div>
                <div className={$["stage-desc"]}>Title, ownership, site visits, rough feasibility</div>
              </div>
            </div>
            <div className={$["stage"]}>
              <div className={$["stage-num"]}>02</div>
              <div style={{ flex: 1 }}>
                <div className={`${$["stage-name"]} ${$["active"]}`}>Site Due Diligence</div>
                <div className={$["stage-desc"]}>Flood, FSI, setback, climate, drainage, TDR</div>
              </div>
              <div className={`${$["stage-fit"]} ${$["primary"]}`}>Qnit fits here</div>
            </div>
            <div className={$["stage"]}>
              <div className={$["stage-num"]}>03</div>
              <div style={{ flex: 1 }}>
                <div className={$["stage-name"]}>Financial Feasibility</div>
                <div className={$["stage-desc"]}>Buildable area, IRR/NPV, MEP cost estimate</div>
              </div>
              <div className={`${$["stage-fit"]} ${$["secondary"]}`}>Accelerates</div>
            </div>
            <div className={$["stage"]}>
              <div className={$["stage-num"]}>04</div>
              <div style={{ flex: 1 }}>
                <div className={$["stage-name"]}>Architect Brief</div>
                <div className={$["stage-desc"]}>Site constraints, climate, regulatory parameters</div>
              </div>
              <div className={`${$["stage-fit"]} ${$["secondary"]}`}>Accelerates</div>
            </div>
            <div className={$["stage"]}>
              <div className={$["stage-num"]}>05–07</div>
              <div style={{ flex: 1 }}>
                <div className={$["stage-name"]}>Design → Approvals → Construction</div>
                <div className={$["stage-desc"]}>Qnit PDF export supports RERA and bank documentation</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── MODULES ── */}
      <section className={$["modules-sec"]} id="modules">
        <div className={$["modules-header"]}>
          <div>
            <div className={$["sec-eyebrow"]}>Five live analysis modules</div>
            <h2 className={$["sec-title"]}>One map. Everything the site is telling you.</h2>
          </div>
          <p className={$["sec-sub"]}>Not global averages. Actual IMD readings, JRC historical flood extents, and NBC 2016 zone mapping — for your exact site in Bengaluru. Every parameter shows its source and last-updated date.</p>
        </div>
        <div className={$["modules-grid"]}>
          <div className={$["mod-card"]}>
            <div className={$["mod-icon"]} style={{ background: "rgba(37,99,235,0.07)" }}>🌊</div>
            <div className={$["mod-name"]}>Flood Risk</div>
            <div className={$["mod-score"]} style={{ color: "var(--flood)" }}>38<span>/100</span></div>
            <p className={$["mod-desc"]}>JRC 30-year water surface history + DEM elevation + rainfall accumulation + drainage catchment. Composite score per site.</p>
            <div className={$["mod-uses"]}>Bank · RERA · Insurance · Basement risk</div>
            <div className={$["mod-source"]}>JRC · MERIT-DEM · IMD · 2025</div>
          </div>
          <div className={$["mod-card"]}>
            <div className={$["mod-icon"]} style={{ background: "rgba(245,158,11,0.07)" }}>☀️</div>
            <div className={$["mod-name"]}>Sun Path</div>
            <div className={$["mod-score"]} style={{ color: "var(--sun)" }}>84<span>/100</span></div>
            <p className={$["mod-desc"]}>Solar angles, shadow volumes, peak exposure hours, orientation brief for passive solar and ECBC compliance.</p>
            <div className={$["mod-uses"]}>Orientation · ECBC · Solar panels</div>
            <div className={$["mod-source"]}>GEE · MERIT-DEM · 2024</div>
          </div>
          <div className={$["mod-card"]}>
            <div className={$["mod-icon"]} style={{ background: "rgba(6,182,212,0.07)" }}>💨</div>
            <div className={$["mod-name"]}>Wind</div>
            <div className={$["mod-score"]} style={{ color: "var(--wind)" }}>81<span>/100</span></div>
            <p className={$["mod-desc"]}>Prevailing direction, seasonal speeds, IS-875 Part 3 load zone, natural ventilation feasibility.</p>
            <div className={$["mod-uses"]}>Structural loads · Ventilation · Facade</div>
            <div className={$["mod-source"]}>Open-Meteo · IMD · 2025</div>
          </div>
          <div className={$["mod-card"]}>
            <div className={$["mod-icon"]} style={{ background: "rgba(124,58,237,0.07)" }}>🌧</div>
            <div className={$["mod-name"]}>Rainfall</div>
            <div className={$["mod-score"]} style={{ color: "var(--rain)" }}>72<span>/100</span></div>
            <p className={$["mod-desc"]}>Annual total, monsoon peak intensity, NBC 2016 drainage brief, waterproofing grade, construction schedule risk.</p>
            <div className={$["mod-uses"]}>Drainage · Waterproofing · Schedule</div>
            <div className={$["mod-source"]}>Open-Meteo · IMD · 2025</div>
          </div>
          <div className={$["mod-card"]}>
            <div className={$["mod-icon"]} style={{ background: "rgba(239,68,68,0.06)" }}>🌡</div>
            <div className={$["mod-name"]}>Temperature</div>
            <div className={$["mod-score"]} style={{ color: "var(--temp)" }}>66<span>/100</span></div>
            <p className={$["mod-desc"]}>NBC climate zone, degree-days, seasonal highs. ECBC compliance brief and HVAC sizing input.</p>
            <div className={$["mod-uses"]}>HVAC · ECBC · Materials</div>
            <div className={$["mod-source"]}>Open-Meteo · IMD · 2025</div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className={$["how-sec"]}>
        <div className={$["sec-eyebrow"]}>How it works</div>
        <h2 className={$["sec-title"]}>Pin. Analyse. Export.</h2>
        <p className={$["sec-sub"]}>Three steps. One session. No consultant co-ordination, no waiting for siloed reports, no cross-referencing tools that don&apos;t talk to each other.</p>
        <div className={$["steps"]}>
          <div className={$["step"]}>
            <div className={$["step-num"]}>01</div>
            <div className={$["step-title"]}>Drop a pin on your site</div>
            <p className={$["step-desc"]}>Search your site address or click on the map. Bengaluru boundary confirmed — BBMP / BDA regulatory context loads automatically. No install, no GIS software, no file import.</p>
          </div>
          <div className={$["step"]}>
            <div className={$["step-num"]}>02</div>
            <div className={$["step-title"]}>All five layers populate</div>
            <p className={$["step-desc"]}>Flood risk, rainfall, wind, temperature, sun path — sourced from JRC, IMD, GEE, and MERIT-DEM. Each parameter shows its source name and last-updated date. You know exactly what you are trusting and why.</p>
          </div>
          <div className={$["step"]}>
            <div className={$["step-num"]}>03</div>
            <div className={$["step-title"]}>Export and use it</div>
            <p className={$["step-desc"]}>Download a cited PDF. Ready for a client presentation, architect brief, bank due-diligence package, or BBMP regulatory submission. Every number is traceable — by you, your reviewer, and your bank.</p>
          </div>
        </div>
      </section>

      {/* ── DATA TRUST ── */}
      <section className={$["trust-sec"]}>
        <div>
          <h2 className={$["trust-title"]}>Data you can cite.<br />Not data you have to defend.</h2>
          <p className={$["trust-sub"]}>
            The first data layer that looks no better than a Google result — architects close the tab and never come back.
            Every Qnit output includes the source name, dataset version, and last-updated date.
            When your client, reviewer, or bank asks where the flood score came from, you have a traceable answer that holds up.
          </p>
        </div>
        <div className={$["trust-rows"]}>
          <div className={$["trust-row"]}>
            <div className={$["trust-dot"]} style={{ background: "var(--flood)" }}></div>
            <div className={$["trust-name"]}>JRC Global Surface Water</div>
            <div className={$["trust-what"]}>Flood extent · 30-year history</div>
            <div className={$["trust-tag"]}>Flood Risk</div>
          </div>
          <div className={$["trust-row"]}>
            <div className={$["trust-dot"]} style={{ background: "#7B8F83" }}></div>
            <div className={$["trust-name"]}>MERIT-DEM</div>
            <div className={$["trust-what"]}>Elevation · drainage catchment</div>
            <div className={$["trust-tag"]}>Flood · Sun Path</div>
          </div>
          <div className={$["trust-row"]}>
            <div className={$["trust-dot"]} style={{ background: "var(--accent)" }}></div>
            <div className={$["trust-name"]}>IMD / Open-Meteo</div>
            <div className={$["trust-what"]}>India climate · metered · site-specific</div>
            <div className={$["trust-tag"]}>Wind · Rain · Temp</div>
          </div>
          <div className={$["trust-row"]}>
            <div className={$["trust-dot"]} style={{ background: "var(--sun)" }}></div>
            <div className={$["trust-name"]}>Google Earth Engine</div>
            <div className={$["trust-what"]}>Solar · land cover · satellite imagery</div>
            <div className={$["trust-tag"]}>Sun Path</div>
          </div>
          <div className={$["trust-row"]}>
            <div className={$["trust-dot"]} style={{ background: "#7C3AED" }}></div>
            <div className={$["trust-name"]}>NBC 2016 · BBMP · BDA</div>
            <div className={$["trust-what"]}>Regulatory · climate zones · setback references</div>
            <div className={$["trust-tag"]}>All modules</div>
          </div>
        </div>
      </section>

      {/* ── PRICING ── */}
      <section className={$["pricing-sec"]} id="pricing">
        <div className={$["sec-eyebrow"]}>Pricing</div>
        <h2 className={$["sec-title"]}>Less than one consultant report. For a full year.</h2>

        <div className={$["pricing-framing"]}>
          <div className={$["pricing-framing-text"]}>
            A single consultant flood assessment costs <strong>₹20,000–₹50,000 per site</strong>. Qnit replaces the exploratory layer — aggregation, consolidation, and initial interpretation — before statutory reports are commissioned.
            <strong> ₹4,500 / month is not a SaaS subscription. It is a consultant fee replacement.</strong>
          </div>
          <div className={$["pricing-framing-aside"]}>₹20k–₹1.5L per site<br />vs ₹4,500 / month</div>
        </div>

        <div className={$["pricing-grid"]}>
          <div className={$["price-card"]}>
            <div className={$["price-tier"]}>Beta Access</div>
            <div className={$["price-amount"]}>Free</div>
            <div className={$["price-period"]}>During early access · limited analyses</div>
            <div className={$["price-div"]}></div>
            <ul className={$["price-features"]}>
              <li>All five live modules</li>
              <li>Bengaluru</li>
              <li>Map interface</li>
              <li className={$["off"]}>PDF export with source citations</li>
              <li className={$["off"]}>NBC 2016 regulatory references</li>
              <li className={$["off"]}>Per-parameter last-updated date</li>
            </ul>
            <a href="mailto:chiragds0117@gmail.com?subject=Qnit%20beta%20waitlist" className={`${$["price-cta"]} ${$["out"]}`}>Join beta waitlist</a>
          </div>

          <div className={`${$["price-card"]} ${$["featured"]}`}>
            <div className={$["price-badge"]}>Start here</div>
            <div className={$["price-tier"]}>Individual · Architect · Builder</div>
            <div className={$["price-amount"]}>₹4,500<span>/mo</span></div>
            <div className={$["price-period"]}>Per user · billed monthly · cancel anytime</div>
            <div className={$["price-div"]}></div>
            <ul className={$["price-features"]}>
              <li>All five live analysis modules</li>
              <li>Bengaluru · BBMP / BDA regulatory data</li>
              <li>NBC 2016 climate zone mapping</li>
              <li>PDF export with cited sources</li>
              <li>Per-parameter source + last-updated date</li>
              <li>No firm procurement needed</li>
            </ul>
            <Link href="/login" className={`${$["price-cta"]} ${$["fill"]}`}>Start free trial →</Link>
            <div className={$["price-compare"]}>
              <strong>vs. one consultant flood report:</strong> ₹20,000–₹50,000 per site.<br />
              Qnit covers the aggregation layer for all twelve months.
            </div>
          </div>

          <div className={$["price-card"]}>
            <div className={$["price-tier"]}>Firm / Developer Team</div>
            <div className={$["price-amount"]}>₹20k<span>/seat/mo</span></div>
            <div className={$["price-period"]}>Multi-user · multi-city · coming soon</div>
            <div className={$["price-div"]}></div>
            <ul className={$["price-features"]}>
              <li>Everything in Individual</li>
              <li>Multi-city (Chennai, Mumbai, Delhi…)</li>
              <li>Team seats + shared projects</li>
              <li className={$["off"]}>FSI / TDR / zoning overlay — roadmap</li>
              <li className={$["off"]}>Revit / IFC export — roadmap</li>
              <li className={$["off"]}>Enterprise contract — roadmap</li>
            </ul>
            <a href="mailto:chiragds0117@gmail.com?subject=Qnit%20firm%20waitlist" className={`${$["price-cta"]} ${$["out"]}`}>Join firm waitlist</a>
          </div>
        </div>
      </section>

      {/* ── FINAL CTA ── */}
      <section className={$["cta-sec"]}>
        <h2 className={$["cta-title"]}>Your site is already telling you<br />what to build. Start listening.</h2>
        <p className={$["cta-sub"]}>Drop a pin. Get flood risk, sun path, wind, rainfall, and temperature — cited, India-specific, ready to use. One session. No hunting.</p>
        <Link href="/login" className={$["btn-primary"]} style={{ display: "inline-flex", margin: "0 auto" }}>Try your first site free →</Link>
        <p className={$["cta-fine"]}>No install · No GIS expertise · NBC 2016 · BBMP / BDA · Bengaluru</p>
      </section>

      {/* ── FOOTER ── */}
      <footer>
        <a className={$["footer-logo"]} href="#">
          <img src="/qnit-logo.svg" alt="Qnit by GeoKnit" />
        </a>
        <ul className={$["footer-links"]}>
          <li><a href="#">Privacy</a></li>
          <li><a href="#">Terms</a></li>
          <li><a href="mailto:chiragds0117@gmail.com">Contact</a></li>
        </ul>
      </footer>

    </div>
  );
}
