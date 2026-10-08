# Stock MSFS A330-300 (RR) vs A330-343 WV081: collected data

Collected 2026-10-08. These are research notes, not implementation status. Only facts and short paraphrases are recorded; no Airbus, EASA or iniBuilds files are stored here. Confidence is marked where a source is unofficial.

## Your checklist

| Question | Verdict | Evidence |
| --- | --- | --- |
| The default MSFS A330-300 is WV052 (233t MTOW, 175t MZFW) | **Plausible, not provable.** WV022 has identical limits (233.9 / 233 / 187 / 175 t) and both are certified for the A330-343. MSFS does not name a weight variant. WV052 is a reasonable label. | Airbus WV table pp. 3–4; AC doc 2-1-1 pp. 1–2; stock config below |
| The target WV081 is 242 / 187 / 171 t | **Confirmed.** Maximum ramp weight is 242.9t. | Airbus WV table p. 4; AC doc 2-1-1 p. 3 |
| The centre tank is different (enabled?) | **Yes, but it is an option, not part of the WV label.** The -300 always had the centre-tank structure, but it was left dry. Activation is MOD 204025, offered with the 242t standard. It brings a mandatory nitrogen inerting system (FRS, MOD 58723). | AC doc 2-1-1 p. 6 note; EASA TCDS pp. 41, 46; Aviation Week 2012 |
| Fuel supply, trim and ECAM are all different | **Partly.** The engines still feed from the wing tanks. The centre tank adds a centre-to-inner transfer, its own overhead pushbuttons, a different refuel split, a different trim forward-transfer destination and a centre display on the ECAM FUEL page. | See "Fuel system with a centre tank" |
| Fuel efficiency is about 1% better | **About 1% from aerodynamics; Airbus quotes "up to 2%" overall.** A re-profiled slat 1 and shorter flap-track fairings cut cruise drag by about 1%. Airbus split its 2% fuel-burn figure half aerodynamics, half engines (RR Trent 700 EP2, about 1%). These are production-standard improvements, not properties of the WV081 label. | FAST Oct 2015 p. 08; Aviation Week 2012; AIN 2013 |

## Side-by-side numbers

| Item | Stock MSFS A330-300 (RR), package 0.0.53 | Real WV052 | Real WV081 |
| --- | --- | --- | --- |
| Max ramp/taxi weight | `max_gross_weight` 513,676 lb = 233.0 t | 233.9 t | 242.9 t |
| MTOW | no CFG field | 233 t | 242 t |
| MLW | no CFG field | 187 t | 187 t |
| MZFW | EFB direct-entry cap 175,000 kg | 175 t | **171 t** (4 t lower) |
| Usable fuel | 25,189 US gal (95,351 L); EFB maximum 76,551 kg | 97,530 L (2-tank) | 97,530 L, or **139,090 L** with the centre-tank option |
| Centre tank | 0 (the -200 has 10,735 US gal = 40,636 L) | none (dry) | 41,560 L if MOD 204025 is fitted |
| Engine take-off thrust | `static_thrust` 71,100 lbf | Trent 772B-60 / 772C-60, 71,100 lbf | same engines and rating |
| Main gear tyre pressure | not simulated | 14.5 bar (210 psi) | 14.9 bar (216 psi) |
| Nose gear tyre pressure | not simulated | 11.6 bar (168 psi) | 11.6 bar (168 psi) |
| Advertised range | `ui_max_range` 6,350 nm (already the 242t brochure figure) | — | 6,350 nm (Airbus product page) |

For every A330-300 weight variant, maximum ramp/taxi weight is MTOW + 0.9 t (AC doc 2-1-1). The full table is in [a330-300-weight-variants.csv](a330-300-weight-variants.csv).

**Payload consequence:** with the same operating empty weight, WV081's maximum structural payload is 4 t lower than WV052's. WV082 offers a dynamic 171–175 t MZFW that trades against actual takeoff weight.

## Other differences found

1. **Structure:** partial wing and fuselage reinforcement, and use of the existing load-alleviation function (Aviation Week, 2012). No public part-level detail was found.
2. **Tyres:** main gear pressure rises from 14.5 to 14.9 bar. The WV080–083 rows list only the 1400x530R23 radial main tyre; earlier variants also list a bias-ply alternative (AC doc 7-2-0 p. 9).
3. **Certification additions for WV080s with the centre tank:**
   - JAR 25.733(c)(1) (tyres), JAR 25.963(g) (centre fuel tank) and JAR 25.979 (pressure fuelling);
   - Special Condition P-27 (flammability reduction system) and P-32 (fuel tank safety).

   Source: EASA TCDS pp. 30 and 34.
4. **Unusable fuel** is higher for the 3-tank aircraft: 437 L basic, or 279 L with MOD 205749. The 2-tank figures are 354 L and 196 L (TCDS pp. 40–41).
5. **Production and conversion:** an A330-343 at WV030s/050s/060s can be changed to WV080 by MOD 205273, from MSN 1627 onwards (TCDS p. 46). EASA certified the first 242t A330-300 in April 2015 after about 100 flight-test hours. MSN 871 tested the aerodynamic changes and MSN 1628 the centre tank. That first aircraft had GE CF6-80E1 engines and went to Delta on 28 May 2015. Rolls-Royce and Pratt & Whitney certification followed; no date was found.
6. **Range:** about +500 nm over the 235t A330-300 at full passenger payload (Airbus, 2012). The 2012 projection was 6,100 nm; today's Airbus page says 6,350 nm.
7. **Payload-range, RR Trent 700, 242t MTOW / 175t MZFW, ISA** (AC doc 3-2-1 p. 8, read from the chart, ±100 nm):
   - maximum structural payload is about 45 t (100,000 lb) out to about 4,250 nm;
   - both configurations follow the same line until about 5,450 nm at about 34.5 t;
   - **without** a centre tank, payload reaches zero at about 6,600 nm;
   - **with** a centre tank, payload is about 22.5 t at 6,500 nm and reaches zero at about 8,850 nm;
   - at WV081's 171t MZFW, the structural-payload plateau would be about 4 t lower.
8. **No evidence of change:** engine thrust ratings, flight-control laws, VMO/MMO (these are in the AFM, which is not public) and the 41,450 ft ceiling (TCDS p. 41).

## Fuel system with a centre tank

> **Unofficial sources.** This section comes from study flashcards and training copies, not a current FCOM. Use it as a behaviour outline and verify before treating it as exact.

- **Engine feed:** the engines are still fed from the inner (wing) tanks. Centre fuel is not fed to the engines directly. Two centre-tank pumps transfer it into the left and right inner tanks, under control of the fuel control and monitoring computer (FCMC).
- **Overhead controls:** CTR TK L and CTR TK R pump pushbuttons, plus a CTR XFR pushbutton (AUTO/MAN, with a FAULT light). The stock -300 cockpit has none of these; the -200 has all three.
- **AUTO transfer:**
  - the centre pumps run while the centre tank contains fuel;
  - the inner-tank inlet valves let each inner tank fall about 2,000 kg below full before refilling it;
  - when the centre tank is empty, the pumps stop and the valves close.
- **MAN transfer:** opens the inner-tank valves and transfers centre fuel. Use it only when the inner tanks can take all of the centre fuel; below about 17,000 kg per inner tank there is no overflow risk.
- **FAULT:** both CTR pushbuttons show FAULT when automatic transfer has failed and both inner tanks hold more than 17,000 kg.
- **Trim tank:**
  - forward transfer goes to the **centre tank** on variants that have one, and to the **inner tanks** on variants that do not;
  - automatic forward transfer starts descending through FL245, or when less than 35 minutes remain to destination; neither trigger is specific to the centre tank.
- **Outer to inner:** outer-tank fuel moves inward by gravity, holding each inner tank at about 3,500–4,000 kg.
- **ECAM:**
  - the FUEL page adds the centre-tank quantity, pumps and transfer indications;
  - the TRIM TK XFR and T TK XFRD memos exist on all variants.

  No centre-specific ECAM caution list was confirmed publicly.

**Stock iniBuilds native module.** From this repo's private static research of 2026-10-08, in `dist/research/`:
- centre refuel allocation above 74,058 kg is gated on `INI_IS_200 == 1`;
- the centre-to-inner transfer block (with a 30,970 kg inner-tank threshold) has the same gate;
- the ECAM centre background, pump and flow graphics, and centre quantity have the same gate;
- the A333 CG/trim block requires `INI_IS_200 == 0`.

So the stock code already models the -200 version of this behaviour, but cannot run it on the -300 identity.

## What this means for the mod

- **Weights:** the four `flight_model.cfg` limits already match WV081. The 171t MZFW reduces maximum payload by 4 t compared with stock.
- **Fuel:** the centre tank plus its transfer logic is the real gap. The behaviour outline above is the specification an original controller would need to meet.
- **Efficiency:** optional. About 1% cruise drag (aerodynamics) and about 1% fuel consumption (engine) apply only if the mod represents the later production standard. How large the effect is in the simulator is unverified.
- **Tyres, inerting and certification items:** not simulated. Recorded for completeness.

## Sources

Primary:
1. Airbus, *ATA03 – Available A330 Family Weight Variants*, May 2024, pp. 3–4 (A330-300). <https://www.aircraft.airbus.com/sites/g/files/jlcbta126/files/2024-06/a330_family_weight_variant.pdf>
2. Airbus, *A330 Aircraft Characteristics – Airport and Maintenance Planning*, Dec 01/25. Sections used: 2-1-1 pp. 1–7 (weights, fuel capacity, centre tank as a WV08X option), 3-2-1 p. 8 (RR payload-range) and 7-2-0 pp. 8–9 (tyres). <https://www.aircraft.airbus.com/sites/g/files/jlcbta126/files/2025-12/AC_A330_20251201.pdf>. A local private copy is at `dist/reference/AC_A330_20251201.pdf`.
3. EASA, *TCDS EASA.A.004 Airbus A330*, Issue 69, 19 Dec 2025. Pages used: 30 and 34 (certification basis for WV080s with the centre tank), 39 (engine thrust), 40–41 (2-tank and 3-tank fuel), 42 (maximum mass) and 46 (MOD 205273 and FRS MOD 58723). <https://www.easa.europa.eu/en/downloads/7518/en>
4. Airbus, *FAST special edition: A330 Incremental Development*, Oct 2015, printed p. 08 (1% drag saving) and p. 10 (centre tank added to the -200 in 1998). <https://aircraft.airbus.com/sites/g/files/jlcbta126/files/2022-04/Airbus-FAST-special-edition-Oct2015.pdf>
5. Airbus A330-300 product page (6,350 nm, 139,090 L). <https://www.aircraft.airbus.com/en/aircraft/a330/a330-300>

Press (Airbus releases and trade reporting):

6. Aviation Week, *Airbus boosts A330 range and MTOW for 2015 target*, 2012: 2% fuel burn split half aerodynamics, half engines; reinforcement; load alleviation. <https://aviationweek.com/aerospace/emerging-technologies/airbus-boosts-a330-range-motw-2015-target>
7. AviTrader, 29 Nov 2012, Airbus release: 242t; +500 nm over the 235t -300; first centre-tank activation on the -300. <https://avitrader.com/2012/11/29/airbus-offers-new-242-tonne-a330-takeoff-weight-capability-to-extend-market-coverage>
8. Airbus release on EASA certification, April 2015, reposted: up to 2% lower fuel consumption; MSN 871 and 1628 flight test. <https://skiesmag.com/press-releases/easacertifiesthelatestandmostcapable242tonnea330version/>
9. First 242t A330-300 delivered to Delta, May 2015. <https://aviationnews.eu/news/2015/05/first-242-tonne-a330-300-is-delivered-to-delta-air-lines/>
10. AIN, *Rolls-Royce continues to improve whole Trent engine family*, 15 Nov 2013 (Trent 700 EP2, about 1%). <https://ainonline.com/aviation-news/air-transport/2013-11-15/rolls-royce-continues-improve-whole-trent-engine-family>

Unofficial (fuel-system behaviour only):

11. <https://quizlet.com/49172316/a330-fuel-flash-cards/>
12. <https://www.brainscape.com/flashcards/ch12-a330-fuel-11270654/packs/19847683>
13. <https://www.smartcockpit.com/wp_quiz/airbus-a330-fuel/>

Simulator values come from cached stock files under `dist/cached-stock-inputs/` (package 0.0.53): `Function_A330-300_Exterior/config/flight_model.cfg`, the RR preset's `aircraft.cfg` and `engines.cfg`, and the stock EFB limits recorded in `docs/stock-aircraft-audit.md`.
