# Lunar Landing Mission: Data Package for Phases 1–5
 
**As of:** 2026-10-30
**Reference vehicle:** Apollo Lunar Module (LM), descent stage and landing gear
**Validation case:** Apollo 11 powered descent and touchdown (20 July 1969)
**Companion to:** *Lunar Landing Mission: Documentation and Roadmap*
 
This package collects public data for the five roadmap phases. Every value carries a source and a provenance tag. A value that was not found is marked **unknown** and is **not** filled in, so the readiness report can keep blocking on it.
 
> **Read this first.** The LM flew from lunar orbit to the surface and back. It supports Phases 1, 4 and 5 directly. Phases 2 and 3 (Earth departure, transfer, lunar arrival) need Saturn V and lunar-environment data, and only a thin slice of that was retrieved. Section 6 lists conflicts between sources and values that look wrong; read it before entering anything.
 
---
 
## 0. Conventions
 
### Provenance tags
 
| Tag | Meaning | Map to roadmap schema |
| --- | --- | --- |
| `published` | Stated in a primary NASA or contractor document that was opened and read | `published` |
| `published-secondary` | Stated in an encyclopedia page, press-kit copy or other summary | `estimated` until checked against a primary source |
| `measured` | Read from flight photography or telemetry (with stated uncertainty) | `measured` |
| `derived` | Computed here from other listed values (arithmetic shown) | `estimated` |
| `estimated` | Tuned or inferred, e.g. a simulation parameter fitted to Apollo 11 | `estimated` |
| `illustrative` | Placeholder for code testing, not flight data | `illustrative` |
| `unknown` | Not found in any source reviewed | leave empty; keep blocking |
 
### Units
 
SI is used. Original US units are kept alongside where the source used them. Conversions: 1 lbf = 4.44822 N, 1 lb = 0.453592 kg, 1 ft = 0.3048 m, 1 nmi = 1.852 km, 1 psi = 6.89476 kPa.
 
### What was and was not opened
 
Opened and read: S1–S5 below, plus the PDS GRGM1200A label and the NSSDC fact sheet. **Only the first ~100,000 characters of the LM Familiarization Manual (S5) were read, and its extraction missed the weight, CG, inertia and tank-capacity tables.** Several documents listed under "Pointers" were located but not opened.
 
---
 
## 1. Phase 1: Vehicle definition (Apollo LM)
 
### 1.1 Mass and propellant
 
| Parameter | Value | Source | Tag |
| --- | --- | --- | --- |
| LM separation weight, design trajectory (Dec 1967 weights) | 33,055 lb = 14,993 kg | S4 §Mission design changes | `published` |
| DPS requirement, early design | 26,000 lb separation weight, ~6,000 ft/s ΔV | S2 §Mission requirements | `published` |
| DPS requirement, later design | ~33,000 lb separation weight, ~7,000 ft/s ΔV for landing | S2 §Mission requirements | `published` |
| Descent propellant required, nominal, total | 16,082 lb = 7,295 kg | S4 Table II | `published` |
| Descent propellant by phase: braking / final approach / landing / vertical descent | 13,666 / 1,556 / 703 / 155 lb (6,199 / 706 / 319 / 70 kg) | S4 Table II | `published` |
| Touchdown total mass, "nominal" case | 7,063.5 kg | S1 Table 1 | `published-secondary` |
| Touchdown total mass, "Apollo 11" case | 4,932 kg | S1 Table 1 | `published-secondary`, **suspect (see §6)** |
| Apollo 11 propellant remaining at landing | Ox tank 1: 5.7 %; ox tank 2: 2.7 %; fuel tank 1: 3.9 %; fuel tank 2: 3.9 % | S2 §Apollo 11 | `published` |
| Apollo 11 hover time remaining at landing, based on minimum-usable quantity | 63.5 s | S2 §Apollo 11 | `published` |
| Propellant low-level warning threshold | 5.6 % of tank in any tank | S2 §Propellant storage | `published` |
| Tank layout | 4 tanks (2 oxidizer, 2 fuel), fed in parallel with balance lines, for CG control | S2 §Propellant storage | `published` |
| Mixture ratio (oxidizer : fuel by weight) | 1.6 | S5 §3-4.1; S12 | `published` |
| Propellants | N₂O₄ oxidizer; 50 % UDMH / 50 % hydrazine fuel (Aerozine 50) | S2 | `published` |
| Pressurization | Supercritical helium tank; regulated to 246 psia (1.70 MPa), changed from 210 psia | S2 | `published` |
| Landing-gear thermal insulation mass: Apollo 11 / Apollo 12 / Apollo 13 and later | 31.03 kg (68.4 lb) / 29.44 kg (64.9 lb) / 17.10 kg (37.7 lb) | S3 Table II | `published` |
| Descent stage dry mass | not retrieved | | `unknown` |
| Ascent stage dry and loaded mass | not retrieved | | `unknown` |
| Tank capacities (volume or mass) and unusable residuals | not retrieved | | `unknown` |
| RCS propellant load | not retrieved | | `unknown` |
 
**Modelling note.** On Apollo 11 the oxidizer quantities in the two oxidizer tanks diverged by ~3.4 % by 360 s into the burn, because the CG offset tilted the vehicle and propellant crossed the balance line (S2). A point-mass tank model will not reproduce this; CG shift during the burn matters.
 
### 1.2 Descent engine (LMDE / DPS)
 
| Parameter | Value | Source | Tag |
| --- | --- | --- | --- |
| Maximum rated thrust | 10,500 lbf = 46.7 kN | S2 §Descent engine | `published` |
| Throttle ratio | 10 : 1 | S2 | `published` |
| Minimum throttle | 10 % of rated = 1,050 lbf = 4.67 kN | S2 | `published` |
| Fixed throttle point (FTP) | 92.5 % of rated = 9,712.5 lbf = 43.2 kN | S2 (92.5 % stated; thrust is arithmetic) | `published` + `derived` |
| Non-operating thrust region | 65 % to 92.5 % (6,825 to 9,712.5 lbf; 30.4 to 43.2 kN). The engine can be throttled there physically but it is not used | S2 | `published` |
| Upper limit of the throttleable region | Raised from 60 % to 65 % of rated thrust; throttle recovery point raised from 52 % to 57 % | S4 §Mission design changes | `published` |
| Why the FTP exists | "Excessive problems with mixture-ratio control and throat erosion" near maximum thrust | S2 | `published` |
| Specific impulse requirement (end of duty cycle) | 305 lbf·s/lbm | S2 §Descent engine | `published` |
| Vacuum Isp, full thrust / 10 % thrust | 311 s / 285 s | S12 | `published-secondary` |
| Isp change in descent design | Predicted effective Isp raised by 3 s from engine test data; Isp higher at 57 % than at 52 % thrust (no numbers given) | S4 | `published` |
| Chamber pressure, 100 % / 10 % thrust | 110 psi (760 kPa) / 11 psi (76 kPa) | S12 | `published-secondary` |
| Sea-level Isp and ambient-pressure dependence | not published in sources reviewed. The engine uses a 47.5:1 skirt and was built for vacuum operation (inference) | | `unknown`; likely N/A |
| Ablative chamber / nozzle extension | Ablatively cooled to 16:1 area ratio; columbium skirt from 16:1 to 47.5:1 (radiation cooled) | S2 | `published` |
| Nozzle area ratio, later vehicles | 53.6:1 (Apollo 15 and later); engine length 100 in vs 85 in | S12 | `published-secondary` |
| Exit diameter (engine outer diameter) | 59.0 in (1.499 m) up to Apollo 14; 63.0 in (1.600 m) Apollo 15 and later | S12 | `published-secondary` |
| Exit area | 1.764 m² (59 in) and 2.011 m² (63 in) | circular area from the diameters above | `derived` |
| Throat area | 0.0371 m² (47.5:1) and 0.0375 m² (53.6:1); throat diameter ≈ 0.217 to 0.219 m | exit area ÷ area ratio | `derived` |
| Duty-cycle life | 1,000 s (design); burn time listed as 1,030 s | S2; S12 | `published` / `published-secondary` |
| Restarts | Designed for 2 restarts; tested to 4 on Apollo 9 | S12 | `published-secondary` |
| Gimbal | ±6° in Y and Z; actuator travel 2 in from mid-position | S2; S5 §3-4.3.1 | `published` |
| Gimbal rate and trim-system dynamics | not retrieved. The DPS gimbal is a *trim* system (NTRS 19700025390), so attitude control comes mainly from RCS | | `unknown` |
| Throttle actuator | Triple-redundant, electrically driven; response time not retrieved | S2 | `published` / `unknown` |
| Start transient | Injector sized for an oxidizer lead during start; ullage of 7.5 s listed in the descent timeline | S2; S4 Table I (garbled) | `published` |
| Minimum impulse bit | not retrieved | | `unknown` |
| Tail-off thrust after shutdown | Reconstructed curve exists for Apollo 11 touchdown (Fig. 2) but numeric values not in text | S1 Fig. 2 | `unknown` (digitize) |
| Design assumption for thrust decay | ~0.5 s assumed in design; actual descent-engine data showed "several seconds" | S3 §Statistical landing performance | `published` |
| Dry mass of engine | 394 lb (179 kg) | S12 | `published-secondary` |
 
**Operating-region anomalies to model or avoid** (all `published`, S2): rough combustion near 27 % thrust on Apollo 9, traced to helium ingestion; 500 Hz oxidizer-manifold oscillation near 40 % thrust (harmless, up to 300 psi peak-to-peak in the transducer line); 100 Hz chamber-pressure oscillation near 25 % thrust (~10 psi peak-to-peak). On Apollo 11 the last ~140 s of descent held an average throttle near 26 % with ~15 % peak-to-peak oscillation, driven by a false vertical-acceleration reading from IMU accelerometers high above the CG during rapid pitch changes.
 
### 1.3 Other propulsion
 
| Parameter | Value | Source | Tag |
| --- | --- | --- | --- |
| Ascent engine thrust | 3,500 lbf = 15.6 kN, fixed | S5 §3-4 | `published` |
| Ascent engine Isp and propellant | not retrieved | | `unknown` |
| RCS thrusters | 16 | S5 §3-2 | `published` |
| RCS thrust per thruster, Isp, minimum impulse bit, attitude deadband | not retrieved | | `unknown` |
 
### 1.4 Geometry, CG and inertia
 
| Parameter | Value | Source | Tag |
| --- | --- | --- | --- |
| CG height above footpad bottom | 3.62 m (both mass cases) | S1 Table 1 | `published-secondary`; verify, see §6 |
| Roll / pitch / yaw moment of inertia, "nominal" | 16,492 / 17,409 / 20,800 kg·m² | S1 Table 1 | `published-secondary` |
| Roll / pitch / yaw moment of inertia, "Apollo 11" | 7,953 / 6,332 / 5,879 kg·m² | S1 Table 1 | `published-secondary`, suspect (§6) |
| Body frame | +X up through the vehicle; yaw about +X, pitch about +Y, roll about +Z | S1 §Apollo Lunar Module | `published` |
| Inertia and CG at other propellant states | only the two points above | | `unknown` |
| Overall vehicle height and width | not recovered (Fig. 2-2 of S5 not legible in extraction) | | `unknown` |
| Engine skirt ground clearance | not retrieved. Design allows the skirt to crush on surface contact | S3 Table I | `unknown` |
 
### 1.5 Landing gear
 
Four legs, symmetric about the yaw axis, cantilever truss: one primary strut and two secondary struts per leg, crushable aluminium honeycomb in each (S1, S3).
 
**Geometry** (S1 Table 2; measured from NASA's public CAD model and spot-checked by the authors against schematics, tag `estimated`):
 
| Parameter | Value |
| --- | --- |
| Footprint radius | 4.242 m |
| Truss radius, upper / lower | 3.061 m / 2.996 m |
| Truss height, upper / lower | 2.874 m / 1.19 m |
| Footpad height (base to ball joint) | 0.10 m |
| Secondary truss width | 2.239 m |
| Primary-secondary connection length | 1.157 m |
 
**Footpad and probes** (S3, `published`): footpad ~0.91 m (3 ft) diameter, convex and crescent-shaped on a ball joint; designed to support the LM on a surface of 0.69 N/cm² (1 lb/in²) bearing strength; a 1.73 m (68 in) lunar-surface sensing probe on three of the four footpads. Probe mode (engine shutdown commanded on probe contact) is the primary landing procedure; pad mode (shutdown after footpad contact) is the backup. The manual states descent-engine cutoff at about 3 ft above the surface (S5 §1-3).
 
**Honeycomb strut properties** (S1 Table 3, `published-secondary`; modelled values from NASA reconstruction work):
 
| Item | Value |
| --- | --- |
| Primary compression stroke limit | 0.812 m (stage 1: 0.254 m at 20,017 N; stage 2: 0.558 m at 42,358 N) |
| Secondary compression stroke limit | 0.305 m at 20,017 N |
| Secondary tension stroke limit | 0.407 m (stage 1: 0.102 m at 2,224 N; stage 2: 0.305 m at 22,241 N) |
| Bearing coefficient of friction | 0.23 (S1) |
| Effective friction, primary strut bearing | 0.05 on a flat surface to ~0.21 based on footpad side load; bearing friction is 10–20 % of strut force (S3, `published`) |
| Strut masses | primary 43.1 kg; primary inner piston 13.6 kg; secondary 5.12 kg; footpad 11 kg (S1 Table 1) |
 
The S3 figure labels a primary-strut load of 42,256 N (9,500 lb), consistent with S1's 42,358 N stage-2 value.
 
### 1.6 Touchdown envelope and attitude limits (design)
 
| Parameter | Value | Source | Tag |
| --- | --- | --- | --- |
| Design (specification) touchdown velocity envelope | Vertical axis marked 3.05 m/s (10 ft/s), 2.13 m/s (7 ft/s), 1.22 m/s (4 ft/s); horizontal axis marked 0 to 1.22 m/s (4 ft/s). The envelope polygon itself must be read from S3 Fig. 6/8 | S3 | `published`; polygon `unknown` |
| Certification slope ("Doghouse") | 12° | S1 §Bounding performance | `published-secondary` |
| Certification boundaries (must lie outside the Doghouse) | toppling stability; primary strut stroke; secondary compression stroke; secondary tension stroke | S1 | `published-secondary` |
| Statistical certification result | P(no strut fully strokes) = 0.999; P(stable landing, slope ≤ 12°) = 0.998; P(stable landing anywhere in the site) = 0.967 | S3 Fig. 6 | `published` |
| Allowable tilt at touchdown | not found. S3 Table I lists a requirement to "maintain tilt angle within specified limits for ascent-stage lift-off" but gives no number | S3 | `unknown` |
| Allowable angular rates at touchdown | not found. S3 says flight rates were "low" | S3 | `unknown` |
 
**This is the biggest open item for the success definition** (roadmap requirement 4). The tilt and rate limits must stay blocking until found. Best leads are Zupp, NASA/SP-2013-605 and Rogers, NASA TN D-6850 (see §8 Pointers).
 
---
 
## 2. Phase 2: Earth departure and lunar transfer
 
The LM did not fly this phase, and no Apollo launch vehicle dataset was retrieved. Apollo 11 timeline anchors are included so a reference case exists.
 
### 2.1 Apollo 11 launch and transfer anchors
 
| Event | Value | Source | Tag |
| --- | --- | --- | --- |
| Liftoff | 16 July 1969, 13:32:00 UTC, Launch Complex 39A | S11 | `published-secondary` |
| S-IC burnout and separation | T+2 min 42.30 s (13:34:42.30 UTC); 4,700,000 lb (2,131,884 kg) propellant burned | S11 | `published-secondary` |
| Earth orbit insertion | GET 00:11:50; listed velocity 25,567 ft/s (7,793 m/s); 100 nmi (185.2 km) circular parking orbit | S11 (press-kit table; column label not visible, value consistent with orbital velocity) | `published-secondary` |
| Translunar injection (S-IVB re-ignition) | GET 02:44:15 to 02:44:16.2; 16:16:16 UTC; after about 1.5 parking orbits | S11 | `published-secondary` |
| TLI burn ΔV | 9,965 ft/s (3,037 m/s) listed against the TLI event | S11 (column label unclear) | `published-secondary` |
| Translunar trajectory type | Free-return, 60 nmi (111.1 km) pericynthion | S11 | `published-secondary` |
| Lunar orbit insertion (LOI-1) | GET 75:54:28; ΔV 2,924 ft/s (891 m/s); into a 60 × 170 nmi (111 × 315 km) elliptical lunar orbit | S11 | `published-secondary` |
| Descent orbit | 50,000 ft (15.24 km) × 60 nmi, formed by a burn from a 60 nmi circular lunar orbit | S2 §Mission requirements; S4 | `published` |
 
### 2.2 What is still needed
 
| Item | Status | Where to look |
| --- | --- | --- |
| Saturn V stage masses, propellant loads, thrust, Isp, burn times (S-IC, S-II, S-IVB) | `unknown` | Boeing D5-15481 (AS-504 reference trajectory); Apollo 11 Mission Operation Report M-932-69-11 |
| Actual Apollo 11 launch azimuth and parking-orbit inclination | `unknown`. The AS-504 reference trajectory tabulates azimuths from 72° to 108° across a launch window; the Apollo 11 value was not retrieved | Apollo 11 Mission Report; AS-506 postflight trajectory (not found) |
| TLI burn duration, targeting parameters, S-IVB residuals | `unknown` | NTRS 19700025320 (Hyle, *Translunar Injection Maneuver*, located, not opened) |
| Atmosphere, wind, aerodynamic coefficients, gravity-loss data | `unknown`. Not researched this session | |
| Earth-fixed frame and rotation model | Handled by SPICE kernels, not vehicle data | NAIF (roadmap link) |
| Dispersions: launch timing, thrust, mass, navigation, maneuver errors | `unknown` for Apollo; keep any placeholders `illustrative` | |
 
---
 
## 3. Phase 3: Lunar arrival and landing-site model
 
### 3.1 Landing site: Apollo 11, Tranquility Base
 
| Parameter | Value | Source | Tag |
| --- | --- | --- | --- |
| **Recommended default:** Lunar Module position, planetocentric, Mean Earth/Polar Axis frame, DE421, from LRO images | 0.67416° N, 23.47314° E | S6 (NSSDC, Wagner et al. 2017) | `published` |
| Same, earlier solution (IAU Mean Earth Polar Axis; Davies & Colvin 2000) | 0.67408° N, 23.47297° E | S6 archive copy | `published` |
| ALSJ listing | 0.67409° N, 23.47298° E | S7 | `published` |
| LROC listing | 0.6742° N, 23.4731° E | S7 | `published` |
| Apollo-era figure (superseded) | 0.6875° N, 23.4333° E; about 1.2 km east–west and 0.4 km north–south from the LRO values | S7 secondary pages | `published-secondary` |
| Planned landing point | 0.75° N, 23.62° E; actual touchdown about 6.4 km west of it, near the south-west edge of the Site 2 landing ellipse | S7 (LROC) | `published` |
| Landing ellipse dimensions and target region | not retrieved | | `unknown` |
| Surface elevation at site | one secondary page lists −2,600 m relative to mean radius; not verified | S7 secondary | `unknown`; derive from LOLA |
| Slope at touchdown | 4.2° to 4.5° (tuned by trial and error in the reconstructions, not measured directly) | S1 Table 5 | `estimated` |
| Regolith at landing | Footpad penetrations 2.0 to 7.62 cm and skids up to 7.62 cm, from mission photography | S1 | `measured` |
 
> **Frame trap.** Site coordinates above are in the Mean Earth/Polar Axis frame. The GRGM1200A gravity coefficients are in the lunar principal-axes frame defined by DE430 (S8). Transform between them and document it; the two frames differ by a rotation of a fraction of a degree.
 
### 3.2 Gravity: GRAIL
 
| Parameter | Value | Source | Tag |
| --- | --- | --- | --- |
| Model | GRGM1200A, degree and order 1200, resolution <5 km; uses all GRAIL mission data and no other data | S8 | `published` |
| GM | 4902.80011526323 km³/s² | S8 PDS label | `published` |
| Reference radius for gravity | 1738.0 km | S8 | `published` |
| Reference frame | Lunar body-fixed principal axes, defined by planetary ephemeris DE430 | S8 | `published` |
| Lower-degree alternatives | GRGM600PRIM1, GRGM900C2 | S8 | `published` |
| Mission design resolution goal | 30 km (degree and order ~180). Bouguer gravity is globally accurate to about degree 600 | S8 | `published` |
| Covariance archive | Truncated to degree 50 (26 MB) and 180 (4 GB). The full degree-1200 matrix (~8 TB) was not archived | S8 | `published` |
| Gravity used in the Apollo 11 touchdown reconstruction | 1.63 m/s² | S1 | `published-secondary` |
 
### 3.3 Terrain: LRO LOLA
 
| Parameter | Value | Source | Tag |
| --- | --- | --- | --- |
| Product | SLDEM2015 (LOLA + SELENE/Kaguya Terrain Camera), ±60° latitude, ~59 m per pixel (512 pixels/degree) | S9 | `published` |
| Accuracy | LOLA vertical precision ~10 cm, accuracy ~1 m; SLDEM2015 typical vertical accuracy ~3 to 4 m | S9 | `published` |
| Topography reference radius | 1737.4 km (differs from the 1738.0 km gravity radius) | S8; S9 | `published` |
| Companion products | SLDEM2015 slope and azimuth maps; 5 m/pixel LOLA DEMs near the south pole | S9 | `published` |
| Hazard-scale terrain (rocks, craters at meter scale) | Not resolved by SLDEM2015 (~60 m). LROC NAC imagery and DTMs are needed for hazard constraints | | `unknown` |
 
Apollo 11 at 0.67° N lies inside the ±60° SLDEM2015 coverage.
 
### 3.4 Lunar constants (NSSDC Moon Fact Sheet, S10, `published`)
 
| Parameter | Value |
| --- | --- |
| Mass | 0.07346 × 10²⁴ kg |
| Equatorial / polar / volumetric mean radius | 1738.1 km / 1736.0 km / 1737.4 km |
| Mean density | 3344 kg/m³ |
| Surface gravity | 1.62 m/s² |
| Escape velocity | 2.38 km/s |
| GM | 0.00490 × 10⁶ km³/s² (rounded; use the GRGM1200A GM for dynamics) |
| Sidereal rotation period | 655.720 h |
| Obliquity to orbit | 6.68° |
| Semimajor axis / eccentricity / inclination to ecliptic | 0.3844 × 10⁶ km / 0.0549 / 5.145° |
| Orbital period / mean orbital velocity | 27.3217 d / 1.022 km/s |
 
### 3.5 Ephemeris and orientation
 
| Item | Status |
| --- | --- |
| DE440/DE441, NAIF SPK, PCK, LSK kernels | Linked in the roadmap. Coverage of July 1969 was **not verified** here; check before use |
| Apollo 11 mission-specific SPICE kernels | `unknown`. One secondary page notes Horizons does not include the CSM-LM Moon trajectory |
| Lunar orientation model (libration, principal-axis frame) | Use the PCK matching the gravity model's ephemeris (DE430) or document the mismatch |
 
---
 
## 4. Phase 4: Powered descent and touchdown dynamics
 
### 4.1 Descent profile (Apollo, design)
 
| Item | Value | Source | Tag |
| --- | --- | --- | --- |
| Start | Near pericynthion of the 50,000 ft × 60 nmi descent orbit | S4 | `published` |
| Braking phase | Ends at 9,000 ft (2,743 m) altitude, "high gate" | S4 | `published` |
| Final approach | High gate to "low gate" at about 500 ft (152 m) | S4 | `published` |
| Landing phase | Low gate to touchdown; includes slow vertical descent at about 3 ft/s (0.91 m/s) from about 65 ft (19.8 m) | S4 | `published` |
| Hover phase | Last 1,000 ft (305 m) of descent | S2 | `published` |
| Manual's description | Braking begins at about 50,000 ft; vehicle pitches to vertical near 200 ft | S5 §3-3.1 | `published`; conflicts in detail with S4 (§6) |
| High-gate target pitch attitude | 69° (changed from 65°); guidance time-to-go to high gate 180 s at 25,000 ft (was 145 s) | S4 | `published` |
| Guidance | Quadratic acceleration guidance; linear acceleration in the last 20 s of braking and last 10 s of final approach; velocity-nulling for a constant-rate vertical descent | S4 | `published` |
| Landing-radar update | Longer updating during braking phase; velocity data valid to 25,000 ft, altitude to 38,000 ft; zero-Doppler dropouts between 350 and 135 ft; hover antenna position commanded at 8,000 to 9,000 ft | S4; S5 Table 3-3.1 | `published` |
 
### 4.2 ΔV and propellant by phase (S4 Table II, `published`)
 
Based on the 33,055 lb separation weight.
 
| Phase | ΔV (ft/s) | ΔV (m/s) | Propellant (lb) | Propellant (kg) |
| --- | --- | --- | --- | --- |
| Braking | 5,237 | 1,596 | 13,666 | 6,199 |
| Final approach | 863 | 263 | 1,556 | 706 |
| Landing | 387 | 118 | 703 | 319 |
| Vertical descent | 88 | 27 | 155 | 70 |
| **Total** | **6,575** | **2,004** | **16,082** | **7,295** |
 
The phase propellant figures sum to 16,080 lb against the printed total of 16,082 lb; treat as rounding.
 
### 4.3 Terminal outcomes and the data that supports each
 
| Outcome (roadmap Phase 4) | Threshold data available | Tag |
| --- | --- | --- |
| Safe touchdown | Inside the design velocity envelope (vertical ≤ 3.05 m/s, horizontal ≤ 1.22 m/s, per axis marks only), slope ≤ 12°, all struts within stroke | `published`; tilt and rate limits `unknown` |
| Hard landing / strut overstroke | Primary compression > 0.812 m; secondary compression > 0.305 m; secondary tension > 0.407 m | `published-secondary` |
| Tip-over | Stability boundary of the Doghouse at 12° slope; footpad sliding ignored in the certification analysis (conservative) | `published` |
| Terrain collision | Vehicle/gear envelope against local terrain; skirt may crush on contact | `published`; clearance `unknown` |
| Fuel exhaustion | Low-level warning at 5.6 % in any tank; minimum-usable quantity definition not retrieved | `published`; usable `unknown` |
| Missed site | Needs a landing ellipse | `unknown` |
 
### 4.4 Proposed touchdown-limit defaults for review
 
The roadmap says defaults must be documented and reviewed before they are treated as meaningful. These are `illustrative` placeholders taken from the Apollo design envelope, not validated mission requirements.
 
| Limit | Placeholder | Basis | Tag |
| --- | --- | --- | --- |
| Vertical speed | 3.05 m/s | Maximum marked on the S3 envelope axis | `illustrative` |
| Horizontal speed | 1.22 m/s | Maximum marked on the S3 envelope axis | `illustrative` |
| Surface slope | 12° | S1 Doghouse | `illustrative` |
| Tilt | **no value**: blocking | not found | `unknown` |
| Angular rate | **no value**: blocking | not found | `unknown` |
| Gear stroke | Per §1.5 limits | S1 | `illustrative` |
 
---
 
## 5. Phase 5: Verification and validation data
 
### 5.1 Apollo 11 touchdown reconstruction (S1)
 
Two published reconstructions exist with different assumptions. Run both and keep them separate.
 
| Parameter | "Zupp-like" | "Adams-like" | Unit |
| --- | --- | --- | --- |
| Mass set | Nominal (7,063.5 kg) | Apollo 11 (4,932 kg) | |
| Axial velocity (body) | 0.5730 | 0.5740 | m/s |
| Lateral velocity (body) | −0.6147 | −0.6481 | m/s |
| Forward velocity (body) | −0.2130 | −0.0447 | m/s |
| Horizontal speed (derived) | 0.651 | 0.650 | m/s |
| Pitch / roll / yaw Euler angle (321 rotation) | 0.9430 / 2.5450 / 15.09 | 1.4827 / 2.2937 / 0.0 | ° |
| Pitch / roll / yaw rate (body) | 0.0 / −2.8648 / −0.6188 | 0.0 / −2.8648 / −0.6188 | °/s |
| Ground slope | 4.5 | 4.2 | ° |
| Ground slope approach azimuth | 0.0 | −12.0 | ° |
| Footpad–surface friction coefficient | 0.33 | 0.36 | |
| Bearing strength coefficient Kn | 350,254 | 150,000 | N/mᵖ |
| Compaction exponent p | 1.0 | 1.5 | |
| Damping coefficient Cn | 0.0 | 150,000 | N·s/m |
| Plowing coefficient Kp | 1,454 | 1,454 | N/m |
 
Tag: `estimated`. These are tuned to match Apollo 11, valid only near its conditions (S1), and the two velocity sets carry the same kinetic energy in different frames. Engine tail-off during touchdown is part of the case (S1 Fig. 2, to be digitized).
 
### 5.2 Apollo 11 outcomes to match
 
| Item | Value | Tag |
| --- | --- | --- |
| Footpad penetration | 2.0 to 7.62 cm (photos) | `measured` |
| Skid distance | up to 7.62 cm (photos) | `measured` |
| Soil energy absorption | ~60 % of touchdown energy through footpad penetration and sliding; secondary-strut tension stroking ~10 cm | `published` (S3) |
| Vehicle settling | all motion stopped about 1.6 s after chamber pressure began decaying (Apollo 14 report; use the Apollo 11 equivalent when retrieved) | `published` |
 
**Strut crush levels (cm)**, photo estimates with ~0.635 cm uncertainty per measurement; secondary struts (left/right) are tension stroke (S1 Table 6):
 
| Strut | Photo average | Rogers sim | Zupp sim | GLASS (Zupp-like) | Adams sim | GLASS (Adams-like) |
| --- | --- | --- | --- | --- | --- | --- |
| +Z primary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| +Z right | n/a | 0.51 | 0.00 | 0.00 | 0.00 | 0.00 |
| +Z left | 10.16 | 9.14 | 4.57 | 7.01 | 6.10 | 4.20 |
| −Z primary | 0.00 | 0.00 | 0.00 | 1.52 | 0.00 | 0.00 |
| −Z right | 6.35 | 8.13 | 3.81 | 10.15 | 9.40 | 6.00 |
| −Z left | 11.43 | 0.51 | 0.00 | 0.57 | 0.00 | 0.00 |
| +Y primary | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| +Y right | 7.11 | 8.64 | 4.57 | 10.15 | 9.14 | 5.84 |
| +Y left | 1.27 | 2.54 | 1.78 | 1.66 | 2.29 | 1.40 |
| −Y primary | 0.00 | 0.00 | 0.00 | 1.52 | 0.00 | 0.16 |
| −Y right | 8.13 | 3.56 | 2.54 | 5.89 | 2.29 | 1.43 |
| −Y left | 0.00 | 3.56 | 3.05 | 2.55 | 0.25 | 0.59 |
| Cumulative difference | n/a | 25.16 | 31.25 | 29.07 | 27.68 | 26.59 |
 
The −Z left photo estimate (11.43 cm) disagrees with every simulation; the paper flags it as the least certain row.
 
### 5.3 Regression and Monte Carlo inputs
 
| Item | Value | Source | Tag |
| --- | --- | --- | --- |
| Certification statistics (benchmark for a Monte Carlo run) | P(no strut fully strokes) 0.999; P(stable, slope ≤ 12°) 0.998; P(stable, any slope in site) 0.967 | S3 | `published` |
| Surface model used in certification | Statistical slopes and protuberances from Lunar Orbiter photography; most severe of seven original Apollo sites | S3 | `published` |
| Input dispersion distributions (velocities, attitudes, rates, thrust decay) | not retrieved | | `unknown` |
| Flight time histories (attitude, rates) for Apollo 11 touchdown | Digitized from the Apollo Experience Report (NASA TN D-6850) in S1 | S1 | pointer; data `unknown` here |
 
### 5.4 Reproducibility record (fields to store with every result)
 
Software version; SPICE kernel names and dates; gravity model (e.g., GRGM1200A, degree and order used); terrain model (e.g., SLDEM2015); frame definitions (Mean Earth/Polar Axis versus principal axes, DE421 versus DE430 versus DE440); vehicle data revision and the tag of every value used; contact-model parameter set (Zupp-like or Adams-like); solver and tolerances; configuration hash.
 
---
 
## 6. Conflicts and red flags
 
| # | Issue | Detail | Action |
| --- | --- | --- | --- |
| 1 | **Apollo 11 touchdown mass looks too low** | S1 gives 4,932 kg for Apollo 11 and 7,063.5 kg nominal. From memory (not verified here), the ascent stage alone is about 4.5 to 4.7 t loaded and the descent stage dry mass about 2 t, which would put an Apollo 11 touchdown near 7 t or more. The paper also says Apollo 11 landed with ~20 s of propellant remaining while S2 says 63.5 s of hover time remained | Do not enter 4,932 kg or its inertias without checking the Apollo 11 Mission Report and the LM weight-and-balance tables |
| 2 | **Maximum thrust disagrees across sources** | S2: FTP 9,712.5 lbf (92.5 % of 10,500). S5: "about 9,870 lb" at full throttle, "almost 10,000 pounds". S12: 10,125 lbf upper throttle value (96.4 % of 10,500) | Different vehicles or revisions are likely (S5 covers LM-10 to LM-14, Apollo 15 onward). Pick one vehicle and cite its source |
| 3 | **Throttle ceiling disagrees** | S2 and S4: top of throttleable region is 65 % (6,825 lbf). S5: throttle range 1,050 to 6,300 lb (60 % of 10,500) | S4 says the limit was raised from 60 to 65 %. The 60 % figure likely reflects the earlier configuration |
| 4 | **Isp figures are not comparable** | S2: 305 s is a requirement at end of duty cycle. S12: 311 s vacuum at full thrust and 285 s at 10 % | Treat 311 and 285 as unverified until checked against TRW characteristics document 01827-6119-T000 |
| 5 | **Descent-phase altitudes differ by source** | S4: vertical descent from ~65 ft. S5: pitches to vertical near 200 ft. S2: hover phase is the last 1,000 ft | These likely describe different events (pitchover versus vertical descent versus hover). Define each phase boundary explicitly |
| 6 | **Gravity and topography reference radii differ** | 1738.0 km versus 1737.4 km | Use the correct radius for each model |
| 7 | **Site coordinate versions differ by about 1 km** | Apollo-era 0.6875° N, 23.4333° E versus LRO-based 0.67416° N, 23.47314° E | Use the LRO-based value |
| 8 | **OCR damage** | S4 Table I (guidance targets) and parts of S2 are garbled; one S2 line on pitch rates reads "15 at 10"/ec" | Re-extract from the page scans before use |
| 9 | **Wikipedia-derived engine numbers** | Chamber pressure, Isp pair, restarts, engine mass and area ratio for Apollo 15+ are `published-secondary` | Verify against S2 and the TRW documents |
| 10 | **CG height 3.62 m** | Same in both mass cases, though the vehicle's mass distribution differs | Verify against the CAD model or weight-and-balance tables |
| 11 | **Design vs flight vehicles** | S4 uses design-phase 1968 weights; S1 uses reconstruction masses; S3 covers all landings | Keep a vehicle revision field; do not mix sources across revisions |
 
---
 
## 7. Data gap register
 
| ID | Gap | Blocks | Where to look next |
| --- | --- | --- | --- |
| G1 | Allowable touchdown tilt and angular rate | Success definition (req. 4) | Zupp NASA/SP-2013-605; Rogers NASA TN D-6850; LM Operations Handbook Vol. I and II |
| G2 | Descent and ascent stage dry masses, tank capacities, residuals, RCS propellant | Phase 1 | LM Familiarization Manual (later pages); LM Operations Handbook Vol. I (S3 pointers); Apollo 11 Mission Report |
| G3 | Resolve Apollo 11 touchdown mass (§6 #1) | Phase 5 validation | Apollo 11 Mission Report (MSC-00171); Zupp SP-2013-605 |
| G4 | Thrust, chamber pressure, Isp and mass flow as functions of throttle | Phase 1 engine model | TRW *Characteristics of the LMDE* 01827-6119-T000; NASA TN D-7143 figures; LM Operations Handbook |
| G5 | Sea-level and ambient-pressure behaviour | Phase 1 | Probably N/A for a vacuum engine; confirm in the TRW document |
| G6 | Measured throat and exit areas | Phase 1 | TRW document; Mechanical Design of the LMDE (cited by S12). Current values are `derived` |
| G7 | Gimbal rate, throttle actuator response, minimum impulse bit, start and shutdown transients, numeric tail-off curve | Phase 4 | S1 Fig. 2 (digitize); Stengel AIAA 69-892; LM Operations Handbook |
| G8 | RCS thrust, Isp, minimum impulse, attitude deadbands | Phase 4 | LM Familiarization Manual; Stengel AIAA 69-892 |
| G9 | Inertia and CG at intermediate propellant states | Phase 4 | Weight-and-balance data; compute from tank and structure masses |
| G10 | Numeric design velocity envelope polygon | Phase 4 | S3 Fig. 6 and 8 (read from scan); Rogers TN D-6850 |
| G11 | Vehicle height, width, engine skirt clearance, footpad span as built | Phase 1 | LM Familiarization Manual Fig. 2-2; Rogers TN D-6850 |
| G12 | Saturn V stage data, Apollo 11 launch azimuth, parking-orbit inclination, TLI burn data | Phase 2 | Boeing D5-15481; M-932-69-11; NTRS 19700025320 |
| G13 | Atmosphere, winds, aerodynamics, gravity losses | Phase 2 | Not researched this session |
| G14 | Landing ellipse and target region definition | Phase 3, outcome "missed site" | Apollo 11 Mission Report; LROC |
| G15 | Meter-scale terrain and hazards at Tranquility Base | Phase 3, 4 | LROC NAC DTMs |
| G16 | Apollo 11 SPICE kernels and DE440 coverage check | Phase 3, 5 | NAIF data page |
| G17 | Navigation and sensor error models; landing-radar performance | Phase 4 | Apollo GN&C documents; S5 radar table |
| G18 | Propellant slosh model | Phase 4 | S2 notes slosh drove an early low-level warning 36 s early on Apollo 11; baffles added from Apollo 14 |
| G19 | Dispersion distributions for Monte Carlo | Phase 5 | Zupp SP-2013-605; Walton, Herr and Leonard, *J. Spacecraft* 1964 |
| G20 | Apollo 11 flight time histories for validation | Phase 5 | Digitize from Rogers TN D-6850 (as S1 did) |
 
---
 
## 8. Sources
 
### Opened and used
 
- **S1** Ali, Slagle, Mordasiewicz, Orphee, McDonough. *Apollo 11 Lunar Module Touchdown Dynamics Reconstruction Verification and Validation for Human Landing Systems*, AAS-26-167. [NTRS 20260001760](https://ntrs.nasa.gov/api/citations/20260001760/downloads/Apollo%2011%20LM%20Touchdown%20Dynamics%20VnV%20HLS.pdf)
- **S2** Hammock, Currie, Fisher. *Apollo Experience Report: Descent Propulsion System*, NASA TN D-7143, March 1973. [PDF](https://www.sierrafoot.org/x-15/NASA_TN_D-7143.pdf)
- **S3** Rogers. *Apollo Lunar Module Landing Gear*, 7th Aerospace Mechanisms Symposium, Nov 1972. [ALSJ PDF](https://www.nasa.gov/wp-content/uploads/static/history/alsj/LM_Landing%20Gear1973010151.pdf)
- **S4** Alphin, Taylor, Kirkland. *LM Powered Descent Trajectory for the Apollo Lunar Landing Mission*, MSC Internal Note 68-FM-78, 29 March 1968. [PDF](https://ibiblio.org/apollo/Documents/19740072761.pdf)
- **S5** Grumman. *Lunar Module LM 10 through LM 14 Vehicle Familiarization Manual*, LMA790-2 (partial read). [ALSJ PDF](https://www.nasa.gov/wp-content/uploads/static/history/alsj/a14/a14-43939523-LM10-LM14-Fam-Manual.pdf)
- **S6** NSSDC. [Apollo Landing Site Coordinates](https://nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html) (LRO-based; Wagner et al., Icarus 283, 2017) and an [archived earlier version](https://webarchive.library.unt.edu/eot2008/20080916013832/http:/nssdc.gsfc.nasa.gov/planetary/lunar/lunar_sites.html)
- **S7** [Apollo Lunar Surface Journal, Apollo 11 overview](https://www.nasa.gov/wp-content/uploads/static/history/alsj/a11/a11ov.html); [LROC post on Apollo 11 landing site](https://www.lroc.asu.edu/posts/1122)
- **S8** GRGM1200A: [PGDA product page](https://pgda.gsfc.nasa.gov/products/50); [PDS label](https://pds-geosciences.wustl.edu/grail/grail-l-lgrs-5-rdr-v1/grail_1001/shbdr/gggrx_1200a_shb_l50.xml); [AGU abstract](https://agu.confex.com/agu/fm14/webprogram/Paper8961.html)
- **S9** SLDEM2015: [PGDA](https://pgda.gsfc.nasa.gov/products/54); [PDS ODE](https://ode.rsl.wustl.edu/moon/pagehelp/Content/Missions_Instruments/LRO/LOLA/SLDEM.htm); [USGS Astrogeology](https://astrogeology.usgs.gov/search/map/moon_lro_lola_selene_kaguya_tc_dem_merge_60n60s_59m)
- **S10** [NASA NSSDC Moon Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html)
- **S11** Apollo 11 launch and TLI anchors: [Apollo 11 press kit copy](https://www.scribd.com/document/596513412/a11-Press-Kit1); [Apollo Flight Journal, Earth orbit and TLI](https://www.nasa.gov/history/afj/ap11fj/02earth-orbit-tli.html); [This Day in Aviation timeline](https://www.thisdayinaviation.com/page/354/?lang=ar) (secondary)
- **S12** [Descent propulsion system (Wikipedia)](https://en.wikipedia.org/wiki/Descent_propulsion_system) (secondary)
### Pointers: located, not opened
 
- NASA TN D-6850, Rogers, *Apollo Experience Report: Lunar Module Landing Gear Subsystem*
- NASA/SP-2013-605, Zupp, *An Analysis and a Historical Review of the Apollo Program Lunar Module Touchdown Dynamics*
- NASA TN D-5029, Blanchard, full-scale landing-gear impact tests; NASA TN D-4711, vertical-impact tests of an LM-type gear ([NTRS](https://ntrs.nasa.gov/api/citations/19680021033/downloads/19680021033.pdf))
- [Apollo Operations Handbook, LM 10 and Subsequent, Vol. I](https://nasa.gov/wp-content/uploads/static/history/alsj/lm10handbookvol1.pdf) (weights, subsystem data)
- [LM Operations Handbook Vol. II and the ALSJ LM document index](https://www.nasa.gov/wp-content/uploads/static/history/alsj/alsj-LMdocs.html)
- [Apollo 11 Mission Operation Report M-932-69-11](https://webarchive.library.unt.edu/eot2008/20090109180457/http:/www.hq.nasa.gov/alsj/a11/A11_MissionOpReport.pdf)
- [Hyle, *Translunar Injection Maneuver*, NTRS 19700025320](https://ntrs.nasa.gov/api/citations/19700025320/downloads/19700025320.pdf)
- [Boeing D5-15481, Saturn V AS-504 reference trajectory](https://ibiblio.org/apollo/Documents/BOEING-D5-15481-1%20-%20Saturn%20V%20AS-504%20-%20Launch%20Vehicle%20Reference%20Trajectory%20-%20Volume%202%20of%202%20-%20Book%203.pdf)
- [Apollo Lunar-Descent Guidance, Klumpp](https://webarchive.library.unt.edu/eot2008/20090120005921/http:/www.hq.nasa.gov/alsj/ApolloDescentGuidnce.pdf)
- [NTRS 19700025390, DPS gimbal trim system failure controllability](https://ntrs.nasa.gov/api/citations/19700025390/downloads/19700025390.pdf)
- TRW, *Characteristics of the TRW Lunar Module Descent Engine*, 01827-6119-T000, 31 Jan 1969 (cited by S2, not located online)
- Stengel, *Manual Attitude Control of the Lunar Module*, AIAA 69-892 (cited by S1)
 