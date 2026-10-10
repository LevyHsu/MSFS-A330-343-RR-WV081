# A330 RR baseline and WV081 prototypes

**Withdrawn:** Two initial-loading crashes occurred with v0.1.1 installed. Both crash reports record the same native `purecall` failure before an aircraft container loaded; neither identifies a specific faulty package file. After this package was moved out of Community, the user confirmed that MSFS reached the main menu. This strongly implicates the prototype, but the exact configuration fault remains unresolved. Do not reinstall this build.

Baseline v0.1.2 has a successful user-reported basic ground check. It appears as a new variant within the existing Microsoft/iniBuilds A330 aircraft group, using the installed A330-300 RR attachments. The v0.2.1 EFB experiment is withdrawn after the cockpit disappeared during its local trial. v0.2.2 recovered the stock cockpit attachment and retained four weight limits. The v0.2.3 trial rendered the cockpit/EFB, but direct ZFW entry still showed 175t instead of the intended 171t. v0.2.5 combined the v0.2.4 compatibility correction with loading checks and clearer status messages, but its in-game trial still showed 175t and no extension message. v0.2.6 added the missing shared HTML override declaration, but the trial still showed 175t and refreshed VFS inspection found the stock loader. v0.2.7 changes the override path to lowercase to match the layout; SDK packaging passed, it is installed, and fresh VFS inspection confirms the modified loader is selected. The user confirmed the 171t direct-entry maximum and successfully applied a load, with the intended amber warning and permissive gross-overweight behavior. Remaining loading paths and stock-aircraft isolation still need checks. Centre-tank activation remains separate work.

The initial development target is MSFS 2024 1.8.16.0 with the downloaded `microsoft-aircraft-a330` package version 0.0.53. Compatibility with other versions or a streamed-only installation has not been established.

## v0.2.2 configuration prototype

The authored `flight_model.cfg` delta adds four `[WEIGHT_AND_BALANCE]` fields, using pounds as required by the SDK:

| Limit | Target | CFG field | Value in lb |
| --- | --- | --- | --- |
| Ramp/taxi | 242,900 kg | `max_gross_weight` | 535502.834847 |
| Takeoff | 242,000 kg | `max_takeoff_weight` | 533518.674487 |
| Landing | 187,000 kg | `max_landing_weight` | 412264.430286 |
| Zero fuel | 171,000 kg | `max_zero_fuel_weight` | 376990.468336 |

The [aircraft specification](../docs/aircraft-specification.md) links the Airbus targets. These separate fields follow the SDK [CFG reference](https://docs.flightsimulator.com/msfs2024/html/5_Content_Configuration/CFG_Files/flight_model_cfg.htm) and [weight-and-balance guidance](https://docs.flightsimulator.com/msfs2024/html/7_Samples_Tutorials/Tutorials/Tuning_The_Flight_Model/Weight_And_Balance.htm). Weight limits do not add fuel capacity or adjust the CG envelope, engine, aerodynamics or performance tables.

The stock EFB payload page reads gross weight for its `Max Weight` display and warning, but uses a separate 175,000 kg direct-entry ZFW limit. Its passenger/cargo loading path also needs an explicit 171t check. Takeoff calculations use bundled performance data and custom aircraft variables; their structural-limit handling and the MCDU/WASM limits are unresolved. Do not treat these CFG values as complete weight enforcement or validated WV081 performance.

## Withdrawn v0.2.1 EFB experiment

The user reported the entire cockpit missing on 2026-10-08. v0.2.1 redirected the preset's interior to `Function_A330-300_Interior_WV081`, containing only an inheritance declaration and EFB panel contribution. The preset still requested `model/A330-300_Interior.xml`, which did not exist in that new attachment. The build passed, but the assumed runtime inheritance did not produce a usable cockpit. The exact simulator resolution failure was not captured.

v0.2.2 uses the pristine stock `attached_objects.cfg`, including the original `Function_A330-300_Interior` root. The custom interior, panel contribution and EFB wrapper are excluded from the active source and SDK package. EFB integration remains unfinished; do not expect the experimental green guard message in this build. A future EFB change must first establish working model and panel resolution.

## v0.2.3 EFB loading guard local trial

The candidate preserves the stock attachment map and panel/model references. Preparation adds an original extension import before the stock JavaScript import in a private copy of the installed EFB HTML loader. The SDK copies that loader to its existing virtual path. This is a shared A330 resource override; the extension selects the exact aircraft title `A330 WV081 Community - A330-300 (RR) Baseline`. Other resolved titles use the stock loading behavior. Unknown titles temporarily block loading until identification becomes available.

The extension uses the stock component plugin callbacks to adapt each payload instance, preserving existing callbacks and the stock EFB registration. It waits for simulator variables to become available according to the [SDK instrument lifecycle](https://docs.flightsimulator.com/msfs2024/html/6_Programming_APIs/JavaScript/BaseInstruments.htm), retries unresolved identity, and checks the title again at each loading request. For WV081 it exposes a 171,000 kg direct-entry limit and rejects excessive planned ZFW at both `applyPlannedLoad` and `loadAircraft`, before fuel/ZFW writes. Passenger/cargo loads, direct ZFW entry and the stock loading modes therefore share the intended guard. Metric and imperial bounds follow the stock calculator's integer conversion. A green `WV081: 171 t zero-fuel-weight loading limit active.` message identifies successful initialization.

Private source preparation, JavaScript syntax checks and SDK build 013 passed on 2026-10-08. The build generated 25 package files and a complete 23-entry payload layout, with no new builder diagnostics. All 13 output CFGs and both EFB loader files match preparation. The stock attachment map is unchanged; no panel, model or stock JavaScript replacement is included.

v0.2.3 was installed into the configured Community folder, replacing v0.2.2. All 25 installed files are present and their payload sizes match the SDK layout; the installed manifest reports 0.2.3. No backup or rollback was performed. The user reported a normal cockpit/EFB, but after selecting direct ZFW entry confirmed the maximum remains 175t; the intended 171t override did not take effect in this trial. The reported fuel maximum of approximately 76.5t matches the unchanged stock 76,551 kg limit. A corrected trial must cover the green message, blocking ZFW above 171t without changing the load, acceptance at/below 171t in both units and all loading modes, and unchanged stock A330 behavior. SimBrief unit interpretation, MCDU limits and takeoff/landing performance remain unverified. Another mod replacing the same EFB HTML loader may conflict with this approach.

## v0.2.4 compatibility correction local trial

The user's v0.2.3 screenshot shows the WV081 gross limit and a normal cockpit/EFB, but no expected guard message; the subsequent direct-entry check still shows 175t. Static inspection found six uses of ES2020 optional chaining in the original extension. Microsoft recommends an [ES2017 target for Coherent GT](https://microsoft.github.io/msfs-avionics-mirror/2024/docs/getting-started/setting-up-your-environment/). The v0.2.3 script fails an ES2017 syntax parse at the first optional chain; v0.2.4 replaces those expressions with explicit checks and passes the same parse. A simulator-side parse error was not captured, so this is a confirmed compatibility correction, not proof of the runtime cause or a working guard.

SDK build 014 passed on 2026-10-08 with no new builder diagnostics. All 13 CFGs and both EFB files match preparation, the stock attachment map remains unchanged, and the complete 23-entry payload layout matches file sizes. v0.2.4 replaced the Community trial package with MSFS closed; all 25 installed files are present and payload sizes match the layout. No backup or rollback was performed. In-game acceptance remains pending: confirm the green guard message and 171,000 kg direct-entry maximum, then check loading behavior described above. Fuel remains at the stock 76,551 kg EFB maximum.

The two Payload layouts are a separate stock EFB preference: **Options → Use ZFW Entry → Yes** selects direct ZFW entry; **No** selects passengers/cargo. The setting is saved per aircraft title, and a new title defaults to passengers/cargo. The **ENTER ZFW** button opens a one-time payload-distribution dialog; it does not change the saved preference. For a like-for-like comparison, use the same option on stock and WV081. Stock's direct-entry maximum is 175,000 kg; the WV081 target remains 171,000 kg.

## v0.2.5 combined local trial

At the user's request, this candidate batches the remaining EFB corrections for one simulator session. v0.2.4 was installed but had no reported in-game check before replacement. v0.2.5 keeps its ES2017 correction and checks both requested ZFW and fuel before either stock loading entry point. Fuel must be finite, nonnegative and within the stock capacity; metric and imperial checks follow the stock integer conversion. ZFW remains capped at 171t. A planned total above 242.9t produces an amber warning when applying/loading, but loading is allowed, preserving the stock behavior reported by the user. This is not takeoff/landing approval or performance validation.

A separate startup monitor reports when the WV081 EFB script loads but cannot capture payload controls. It stops after initialization, stock-aircraft identification, instrument removal or a bounded number of checks after simulator readiness. A one-time console message records the extension version and actual aircraft title; the ready message includes `v0.2.5`. Failed initialization now clears readiness so a later update can retry. Known stock titles retain their original loading behavior.

The stock SimBrief callback copies imported fuel/ZFW numbers into the current EFB units without a response-unit conversion. v0.2.5 adds an amber reminder after import; it does not guess or convert the source units. Set SimBrief and the EFB to matching units and review both values before applying a load. This reminder does not validate the imported flight plan.

ES2017 parsing and SDK build 016 passed on 2026-10-08, with no new builder diagnostics. The final warning-only ramp behavior is included. The 13 CFGs and two EFB files match preparation, stock attachments are unchanged, and all 23 payload entries match their file sizes. With MSFS closed, the 25-file package replaced v0.2.4 in Community; the installed manifest reports `0.2.5`. No backup or rollback was performed. The subsequent in-game check still showed a 175,000 kg ZFW maximum, 76,551 kg fuel maximum and no extension message. Gross weight was white at 242,000 kg and red at 243,000 kg, with a displayed maximum of 242,901 kg. This confirms the gross-weight indication responds while the EFB extension remains inactive. Fuel capacity and centre-tank behavior are unchanged.

## v0.2.6 HTML override declaration local trial

The SDK's [global override rules](https://docs.flightsimulator.com/msfs2024/html/2_DevMode/Project_Editor/The_Project_Inspector.htm) require an explicit declaration for replacing existing files under `html_ui`. v0.2.5 includes the modified EFB HTML file, but both its package definition and installed manifest lack that declaration. Ordinary package priority does not enable this replacement. The v0.2.5 session's package report listed that version as loaded. With VFS Projector enabled, the resolved EFB HTML was 330 bytes and byte-identical to pristine stock, without our extension import. The unique extension file was separately projected at v0.2.5, and the projected WV081 preset retained the expected title. This confirms the shared loader was not replaced despite the mod package being loaded.

v0.2.6 adds one `GloballyOverridenBaseSimFile` entry for `html_ui\Pages\VCockpit\Instruments\ini-efb-a330\ini-efb-a330.html`, using the [SDK XML schema](https://docs.flightsimulator.com/msfs2024/retail/sdk-tools/package-tool/package-tool-xml-properties/). The unique extension JavaScript needs no base-file override entry. Apart from its displayed version, the extension code is unchanged. Stock attachment, model, panel, weight and fuel settings are unchanged. SDK build 017 passed on 2026-10-08 with no new builder diagnostics. Its generated manifest contains exactly the intended loader path in `globally_overriden_base_sim_files`. The 13 CFGs and both EFB files match preparation, stock attachments remain unchanged, and the complete 23-entry payload layout matches file sizes. With MSFS closed, v0.2.6 replaced the Community package; all 25 files, the version and the override declaration were checked after installation. No backup or rollback was performed. The user subsequently reported 175t still accepted with the stock `Payload Applied` message. After restarting VFS Projector, the projected v0.2.6 extension was 13,698 bytes and matched the installed file, but the HTML remained 330-byte pristine stock without the extension import. The session report showed the expected WV081 aircraft title. The earlier projection had retained v0.2.5, so projection freshness must be checked before comparing files.

## v0.2.7 override path candidate

The declaration now uses `html_ui/pages/vcockpit/instruments/ini-efb-a330/ini-efb-a330.html`, matching the layout key exactly in source. SDK build 018 converted its separators to backslashes in the generated manifest while preserving lowercase; case is therefore the actual override-path change from v0.2.6. Fresh VFS inspection now confirms loader selection after this change. This supports using the lowercase path for this package; it does not establish a universal SDK casing requirement. The extension differs only in its displayed version.

Build 018 passed on 2026-10-08 with no new builder diagnostics. All 13 CFGs and both EFB files match preparation, stock attachments remain unchanged, and all 23 payload entries match file sizes. With MSFS closed, v0.2.7 replaced the Community trial package; all 25 files, its version and the lowercase override declaration were checked after installation. No backup or rollback was performed. On 2026-10-08, the refreshed projection contained the 442-byte HTML loader with the original extension import before stock JavaScript, and the 13,698-byte v0.2.7 extension. Both files matched the installed package byte-for-byte; the session report listed v0.2.7 and the expected WV081 aircraft title. Loader selection is confirmed.

The subsequent cockpit screenshot and user report confirm basic extension activation: direct-entry ZFW maximum, input and planned ZFW all show 171,000 kg; fuel maximum and loaded fuel remain 76,551 kg. The stock `Payload Applied` message is visible, live gross weight is 247,551 kg in red, and the original amber WV081 message warns that planned ZFW plus fuel exceeds the 242,900 kg ramp limit while allowing loading. This confirms the metric maximum display, loading at that ZFW and warning-only gross-overweight behavior. The screenshot does not establish rejection above 171t, imperial-unit behavior, all loading modes or stock-aircraft isolation. The displayed gross maximum remains 242,901 kg.

## v0.3.0 fuel-system local trial

Weight-entry policy is now permissive: direct entry allows up to 175,000 kg for SimBrief compatibility, while the original status text states the 171,000 kg WV081 aircraft maximum. A request above 171t produces a red warning and remains loadable through 175t. Gross overweight remains warning-only. The source does not claim to convert SimBrief units; they must still match the EFB. No further input-limit-only trial is planned.

The flight-model delta now includes the installed A330-200 donor centre tank (`Center1=-9.551,0,0,10735,0`). Other tank geometry, A333 identity and the stock fuel controller remain intact. The EFB fuel entry ceiling follows the simulator's total capacity and fuel density when positive centre capacity is available, using the [SDK fuel variables](https://docs.flightsimulator.com/msfs2024/html/6_Programming_APIs/SimVars/Aircraft_SimVars/Aircraft_Fuel_Variables.htm). It still delegates loading to the stock request/events. This does not yet establish that stock distribution, transfer or consumption supports the new capacity.

The batch adds only the three donor centre buttons and their annunciator faces as an additive attachment. The preparation tool extracts their geometry/animations privately and aligns them against shared overhead controls; the installed stock textures remain dependencies. The original ECAM extension adds a centre indication inset on the WV081 fuel page, reading actual tank quantity, pump state and feeding flags. It retains the native gauge beneath it and hides outside its supported powered, normal display configuration. Neither switch selection nor a green label is treated as proof of fuel flow.

The native module also gates centre refuelling and centre-to-inner transfer on -200 identity, while the A333 trim branch requires -300 identity. The private fuel-module preparation adapts only the two centre selections in a uniquely named module. A complete private A330-300 interior/panel references that module for all native gauges, retaining the stock 300 model references, cabin, systems and navigation contributions. This avoids changing shared stock aircraft or globally impersonating a -200. This version-specific native adaptation is experimental; native-module loading, electrical/pump response and the combined fuel behavior remain unverified.

Private preparation, ES2017 parsing of both extensions and SDK build 019 passed on 2026-10-08, with no new builder diagnostics. The package contains 169 files and a complete 167-entry payload layout; all 152 Copy-group files and 13 preset CFGs match preparation. With MSFS closed, v0.3.0 replaced the Community package. Its installed version, file count and payload sizes match the SDK output. No backup, rollback or normal simulator launch was performed. Packaging does not establish that the projected native PE module can load from its new location/name; that remains the first runtime uncertainty.

The user reported that the EFB extension and cockpit render, but selecting ON APU, battery power or ground power does not start the aircraft; all native displays remain dark. The session report lists the WV081 title and v0.3.0 package but no A330 native module. The projected module is a native Windows PE, not portable WebAssembly; copying it into a Community package has no established loading contract. This is the leading explanation, not an explicit captured loader error. The v0.3.0 fuel trial did not establish centre loading, transfer or trim operation.

## v0.3.1 systems-loading correction local trial

The candidate uses the original installed A330-300 interior, panel and native systems module. It retains the additive donor controls, configured centre capacity, original display extension and permissive ZFW policy. The private interior, copied native module and copied module data are excluded from preparation and packaging. The read-only ECAM layer now selects the stock module for the exact WV081 aircraft title and labels the centre indication `CTR NOT ACTIVE`.

Centre refuelling/transfer is not implemented in this correction. The EFB retains its stock fuel-entry ceiling; the previous 90,000 kg loading trial no longer applies. The next check is aircraft power-up, native displays and overhead-control rendering. Implementing a centre controller requires an established interface with the stock quantity owner or a supported loadable systems extension; writing competing tank quantities or setting a global -200 identity is not a completed solution.

SDK build 020 passed with no new builder diagnostics. Its 32 files and 30-entry payload layout preserve all three original attachments, add only the control attachment and contain no replacement panel/native module or module data. All 15 Copy-group files and 13 preset CFGs match preparation. With MSFS closed, the 32 current files were installed and match the SDK output. Subsequent cleanup removed the 137 obsolete v0.3.0 files; the remaining 32 files match the current layout and the active attachment map references the original installed interior. No backup or normal simulator launch was performed. Runtime recovery remains unverified.

## v0.3.2 centre-fuel controller candidate

On 2026-10-08, live tests through the simulator's Coherent debugger (developer mode, port 19999) measured the stock fuel loop on the installed A330-200 and WV081. Results:
- **Stock fuel loop:** it checks about twice a second. It adopts simulator tank quantities only when total fuel changes by more than about 50 kg (15 gal rejected, 20 gal adopted). Smaller changes and pure redistributions are overwritten. Its `INI_FUEL_WEIGHT_*` variables report the kept quantities. Fuel-used counters did not change.
- **A330-200 transfer:** with both centre pumps and MAN transfer selected, it moves about 3,375 US gal/h into each inner tank. AUTO transfer begins 2,000 kg below inner capacity.
- **APU feed:** the APU draws only from the left inner tank.

The original `a330-wv081-fuel.js` now hosts a controller on the stock Systems gauge for the exact WV081 title:
- **Pumps:** a centre pump runs when its pushbutton is selected and AC bus 1 (left) or 2 (right) is powered.
- **Transfer:** the manual XFR selection is required up to the takeoff phase, as in the stock -200 logic. Transfers are written in verified steps that each change total fuel enough to be adopted, so the stock systems never see a pure redistribution. Rejected parts are planned again; no fuel is created or lost. The TCDS 83 L of unusable centre fuel stays in the tank.
- **EFB loading:** the stock -300 loader puts everything above full wings into the trim tank, even beyond its capacity (28,339 kg observed for a 100 t request). The EFB extension therefore caps the stock request at wings plus trim. After loading settles, the controller applies the A330-200 schedule: trim from 2,400 kg towards capacity, the remainder in the centre tank. A 100 t request produced full wings, 4,239 kg trim and 24,099 kg centre.
- **ECAM:** the centre indication now shows quantity, the controller's pump and transfer states and an amber fault label. The earlier overlay never appeared because the simulator lowercases gauge names.

Live injection of this source into the running WV081 on the ground verified conserved transfer at the measured rate, AUTO stopping on the ground, refuel distribution and the visible ECAM inset. Still unverified: flight-phase AUTO transfer, engine supply with centre fuel, trim-to-centre forward transfer and the built package.

The donor buttons sat behind the A333 fuel-panel face, which lies 0.91–0.94 mm in front of their aligned roots and has no centre holes. The preparation tool now lifts the group 2.3 mm along the press axis, so pressed korry faces stay about 0.3 mm in front of the face. No legends exist on the donor face texture in that area, so no faceplate copy is needed. The model also sets `L:WV081_CTR_CONTROLS_LOADED` to confirm at runtime that the attachment and its behaviors loaded.

SDK build 021 passed with no new builder diagnostics. Its 32 files and 30-entry payload layout match preparation. With MSFS closed, v0.3.2 replaced v0.3.1 in Community, and all 32 installed files match the SDK output. The built package has not yet been loaded in the simulator. The build tool starts the simulator through Steam, and the launch fails silently while Steam still reports the game as running.

## v0.3.3 sound, checklist and button-loading correction

The first v0.3.2 trial had no aircraft sound, while the simulator and the stock A330 were normal. VFS inspection showed why:
- The stock RR preset has no sound, AI-sound or checklist files. It inherits common's real files: `sound.xml` (546,673 bytes, with its sound package), `soundai.xml` and the 537,810-byte checklist.
- Every build since v0.1.2 placed empty `AutoMerge` stubs at those preset paths. The stubs replaced the shared files, silencing the aircraft and blanking its checklist.
- The cached "stock" sound file used for the stubs was itself an 81-byte stub.

Preparation no longer generates these files.

The CTR buttons never rendered, and their load heartbeat stayed 0. When the attachment was built through the `ModularSimObject` group, the SDK's glTF validator rejected the model: the added alignment node lacked an `ASOBO_unique_id` while the extension was in use. The node now carries an ID. The Copy group is removed, so the SDK compiles and optimises the attachment model (`ASOBO_asset_optimized`, texture URIs resolved to the stock `.PNG.KTX2` files).

The v0.3.2 trial loaded only 76.5 t from a 109.2 t EFB request. The stock -300 never clears `INI_FUEL_EFB_LOADING`, so the controller kept waiting. It now waits for the EFB's own `INI_EFB_IS_REFUELING` and `INI_EFB_IS_LOADING` flags, the load request and a settled total. That trial also confirmed that the engines draw only from the inner tanks: the centre quantity stayed constant through engine start, takeoff and initial climb.

SDK build 022 failed on the unique-ID validation. Build 023 passed with no new builder diagnostics: 27 payload entries. With MSFS closed, the installed package was replaced completely; all 29 files match the SDK output.

## v0.3.4 refuel race, ECAM drawing and CTR legends

The v0.3.3 trial restored sound, and the CTR buttons rendered and responded (`WV081_CTR_CONTROLS_LOADED` = 1). An in-page recorder sampled every 0.25 s and captured a 141.9 t ZFW / 109.2 t fuel instant load:
1. The EFB drained the tanks to 500 kg.
2. The controller distributed after 5 s of stable total.
3. The capped stock load landed at the same moment, about 6 s after the request, and overrode the write.
4. The controller's retry reapplied its remaining *changes*, calculated from the 500 kg baseline, on top of the new 76.5 t. The result was 185.2 t of fuel and 327 t gross.

Refuelling now keeps absolute per-tank targets and re-plans from the stock-reported split after any rejection. It acts only once the total has reached the capped stock amount and settled for 3 s, and it gives up after 120 s without loading. A live injection of the corrected controller produced the intended sequence: 500 kg, 76,552 kg stock load, then 109,175 kg with every tank full and 251,095 kg gross. A red gross weight above 242,900 kg is the intended ramp-overweight warning.

The ECAM centre indication is redrawn to match the stock A330-200 fuel page:
- **Outline:** a closing tank edge.
- **Pumps:** two pump symbols under the top edge, green and in line while transferring, green cross-line when selected but idle, amber cross-line when off or unpowered.
- **Quantity:** the centre quantity in 10 kg steps.

The native page draws its 768-pixel background unscaled in the 780-pixel gauge, so the layer uses gauge pixels. A magenta test overlay on the live -200 page confirmed the edge, digits and pump positions. Text uses the base simulator's Roboto Mono.

The A333 panel has no CTR legends. The -200's come from its `INT_DECAL_LIGHTS` lettering decals: CTR, TANK, L and R with their flow lines, XFR, and the vertical AUTO — 12 triangles, selected by position around the XFR button. The nearby T TANK MODE/FEED and ISOL decals label controls the A333 already has, so they are excluded. The legends sit 0.9 mm out along the press axis, keeping the donor's 0.65 mm clearance above the higher A333 face, and use the stock overhead-lettering potentiometer for lighting. The stock -200 also shows its centre pumps OFF in the default panel state.

SDK build 024 passed with no new builder diagnostics: 27 payload entries, and the SDK compiled the legend node and lettering textures into the attachment. With MSFS closed, v0.3.4 replaced v0.3.3; all 29 installed files match the SDK output. In-simulator checks of the legends, EFB loading and ECAM drawing are pending.

## v0.3.5 single-step centre refuelling and native ECAM styling

The v0.3.4 trial showed the overhead legends working. Two things still differed:
- **Refuelling:** a dry 90 t instant load still stepped from 121.4 t (the stock drain to 500 kg) to 197.5 t (the capped stock load) and then 211.0 t (the controller top-up).
- **ECAM:** the colours and digits differed from the native page.

The EFB extension now intercepts the load request it raises before each amount. Amounts above full wings plus the 2,400 kg base trim fuel no longer reach the stock loader. Instead it writes `L:WV081_FUEL_TARGET_KG` with a new `L:WV081_FUEL_TARGET_SEQ`, and the controller places the whole A330-200 split in one verified step; gradual EFB modes send one request per step. Smaller amounts, including the stock drain to 500 kg, stay stock. The first live attempt used `Date.now()` as the sequence. The simulator read that back as 0, while values up to 3,000,000,000 survived, so the sequence now stays below 1e9. A live 90 t load then produced full wings, 3,530 kg trim and 14,810 kg centre.

ECAM colours now use the native green (#60CD63) and amber (#FF8A50), sampled from the stock fuel-page element sheet. The native page builds its pump symbols from tinted square and bar primitives, matching the original SVG shapes. The native digits use the installed A330 `data/fonts/inidisplayini-regular.ttf`, which the HTML layer cannot reach at runtime: only `html_ui` is served, and package `data/` and `SimObjects/` URLs return 404. Preparation therefore copies that font from the user's installed aircraft into the private build beside the overlay script, under the same never-redistribute rule as the donor control mesh. The overlay draws it at 21 units, matching the native digit height.

SDK build 025 passed with no new builder diagnostics: 28 payload entries, including the private font. With MSFS closed, v0.3.5 replaced v0.3.4; all 30 installed files match the SDK output.

The v0.3.5 flight trial confirmed sound, the overhead legends and EFB loading:
- **Load:** a 109.2 t load filled every tank, with the centre at 32,609 kg.
- **Takeoff and climb:** the engines drew only from the inner tanks.
- **Automatic transfer:** with both CTR pumps on and XFR in AUTO, the left transfer began climbing through FL297, when its inner tank reached 30,955 kg. The right followed at 30,957 kg. Over the first 52 s the centre fell 229 kg and the inner tanks rose; total fuel fell only by engine burn (124 kg, about 2.4 kg/s), so the transfer conserved fuel.

That trial also found the stock `L:INI_TOTAL_FUEL_WEIGHT` left at 500 kg, from the EFB's drain step, because routed loads bypass the stock loader. The controller now writes the routed total there. The EFB's takeoff-performance SYNC reads the stock `L:FMGS_TAKEOFF_WEIGHT`, which the FMS derives from its INIT B ZFW and block fuel. A 100 t block entry therefore synced 231.7 t while the aircraft weighed about 241 t; the cause was the block entry, not the mod.

At takeoff the engines continue to draw from the inner tanks. AUTO centre transfer begins in flight once an inner tank is about 2,000 kg below full; with full inner tanks that is roughly 10–15 minutes after takeoff thrust.

## v0.3.6 ECAM centre section copied from the A330-200

The v0.3.5 centre section still differed from the stock -200 page in shape and digit weight. It was measured again on the live -200 page with magenta overlays and screenshots of each pump state:
- **Background:** the native page draws its 768-pixel background about 6 px right of the gauge origin and unscaled vertically. The added tank bottom line now spans gauge x 313–474, meeting the native tank sides.
- **Pumps:** 41 × 41 squares with a 2 px stroke, matching the native element-sheet square, centred at gauge x 366.3 and 413.7, y 265.7. The idle cross-line is 28 units long. While transferring, each pump's line runs in line from the top of its square down to a transfer line at y 311.2, spanning x 348–432, as the -200 draws with CTR XFR in MAN.
- **Quantity:** `inidisplayini` at 23 units, centred at x 388.6 on a 352.6 baseline, with a 0.4-unit outline in the same colour. Test strings on the live page matched the native digits' 130 × 34 px size; the native stroke weight lies between plain text and a 0.7-unit outline. Coherent GT ignored `font-weight: bold`, and drew no SVG text that also had opacity attributes.

SDK build 026 passed with no new builder diagnostics: 28 payload entries. With MSFS closed, v0.3.6 replaced v0.3.5; all 30 installed files match the SDK output. The ground check confirmed all three pump states, the digit size and weight, and a continuous tank bottom line. Colours are the stock element-sheet values and are not judged from screenshots, which are HDR captures and read brighter than the display.

## v0.3.7 centre pump FAULT lights and E/WD caution

This version adds the indications the A330-200 gives when a demanded centre transfer does not happen:
- **Overhead:** the upper half of each CTR pump button is the amber FAULT face. The donor -200 never drives it (its behaviour lights only the lower OFF and MAN faces from `INI_CENTER_TANK_*`); the attachment now lights it from `L:WV081_CTR_L_FAULT` and `L:WV081_CTR_R_FAULT`, with the stock annunciator-test and lighting multipliers.
- **Controller:** a pump faults when it is selected on and powered, a transfer is demanded (AUTO with an active demand, or MAN with centre fuel available) and the controller could not apply the transfer after its retries (`WV081_CTR_STATUS` 1). An empty centre tank gives no fault: the real aircraft stops the centre pumps and closes the inner inlet valves when the tank is empty, and the stock -200, checked with a zeroed centre tank, both pumps ON and XFR in MAN, shows no FAULT, no LO and no caution. The real FAULT light signals a transfer that should have taken place but has not, or a failed pump; pump failures are not modelled.
- **Fuel page:** a faulted pump shows an amber square with LO inside instead of its bar, and its transfer line is removed.
- **E/WD:** drawn by an overlay on the E/WD gauge in the native caution format and colours (amber, and the cyan sampled from the stock E/WD background). A failure with CTR XFR in AUTO shows `FUEL CTR TK XFR FAULT` with `-CTR TANK XFR ... MAN`: the A330 fuel description has the FCMCs light the pushbutton FAULT and post an ECAM message requesting manual selection when an automatic transfer fails, the documented trim-tank caution is `FUEL T TK XFR FAULT`, and the stock module carries the `-CTR TANK XFR` action text itself; the centre title follows that naming by analogy. A failure with CTR XFR in MAN shows `FUEL L CTR PUMP LO PR` (R, or L+R) with `-L CTR PUMP ... OFF`, the caution for pumps running without delivery pressure.

The stock caution list cannot be extended. The module carries the -200's `CTR PUMP LO PR` text and `INI_CTR_TANK_L/R_FAILURE` variables, but on the -300 it resets those, the master-caution request and light variables and `INI_MASTER_CAUTION_SOUND` within a frame, and no chime event name is exposed. The overlay caution therefore cannot light the MASTER CAUT buttons, sound the single chime, or be cleared with the ECAM CLR key; it stays while the fault persists. The stock list grows from the top and ordinary memos such as NO SMOKING have no readable flag, so the caution always takes the bottom two of the six rows; only a stock list of five or more lines overlaps it. `INI_EWD_DISPLAYING_STATUS` reads 4 on the normal page and is not a flag, so the visibility gate does not use it.

The caution geometry was measured on the stock -300 E/WD against a native `F/CTL SEC (1) FAULT` caution, with a magenta copy drawn in the empty rows below it: a 28-cell monospace grid of 16.8-px cells from gauge x 18.6, first baseline at y 554.7, 31.2-px row pitch (six rows above the divider's end), `inidisplayini` at 20.3 units, and a title underline 3.4 px thick 4.5 px below the baseline. The message starts one cell after the title; action lines carry dot leaders and a right-aligned setting. The fuel LO PR cautions themselves are inhibited on the ground with the engines off, as on the stock aircraft.

SDK build 027 passed with no new builder diagnostics: 28 payload entries, both FAULT components compiled into the attachment. With MSFS closed, v0.3.7 replaced v0.3.6; all 30 installed files match the SDK output.

The build 027 check, with the controller's failure state injected while both CTR pumps were ON and XFR in MAN, showed amber FAULT on both buttons, amber LO pump squares and an amber centre quantity, but no E/WD caution: the gate tested `INI_EWD_DISPLAYING_STATUS`. A one-off drawing of the caution on the live E/WD then confirmed the geometry against the native SEC 1 caution (row pitch and left margin within a pixel) and showed that an ordinary NO SMOKING memo occupies row 1. Build 028 drops the gate condition and keeps the caution on the bottom two rows; it passed with no new builder diagnostics and replaced build 027 with all 30 files matching. Its check showed the installed overlay drawing the caution on the bottom rows with the fault injected and hiding itself when cleared. Build 029 adds the per-mode wording (transfer fault in AUTO, low pressure in MAN); it passed with no new builder diagnostics and replaced build 028 with all 30 files matching. Its check, with the fault variables set directly, showed `FUEL CTR TK XFR FAULT` with XFR in AUTO and `FUEL L+R CTR PUMP LO PR` after selecting MAN, switching live; clearing the variables hid the caution. A 40 s recording of the manual transfer that followed showed the controller status at 0 throughout while 229 kg moved to the inner tanks.

## v0.3.8 later-production performance, trim transfer and flight data

Four items were taken together. Two are code, two are flight data:
- **Later-production performance (done in source):** the 242t standard's documented improvements are about 1% less cruise drag (re-profiled slat 1, shorter flap-track fairings) and about 1% lower fuel consumption (Trent 700 EP2); see the research notes. The preset delta sets `parasite_drag_scalar` to 1.1385, 1% below the stock -300 exterior's 1.15. The engine figure is not applied: during the logged flight the tanks lost fuel at 6,862 kg/h at FL366 while the simulator's `ENG FUEL FLOW` read 4,346 kg/h for both engines and the module's `INI_FUEL_FLOW*_KG` variables stayed 0, so the stock module burns from its own engine model and an `engines.cfg` `fuel_flow_scalar` would change nothing it reads. The structural reinforcement has no public weight figure and the exterior has no public part-level change, so both stay stock. The size of the drag effect in the simulator is unverified.
- **EFB takeoff performance:** the stock bundle hard-codes only the 175,000 kg ZFW cap and the 76,551 kg fuel maximum, both already overridden; no 233t constant exists and its performance MTOW is computed from `MAX GROSS WEIGHT`. A manual entry of 241.9 t on the TAKEOFF PERF page returned V1 168, VR 173, V2 176 at TOGA with a performance MTOW of 242.8 t, so nothing needed changing.
- **AUTO transfer stop and restart** at full inner tanks and the **stock trim forward transfer** (triggers, rate, destination) are recorded in one logged flight before the forward-transfer re-route to the centre tank is designed. The flight (KSEA–VHHH, 153.0 t ZFW, 90.0 t fuel with 14,808 kg in the centre) showed the start working as designed, both sides at 30,963/30,967 kg inner, exactly 2,000 kg below full, but no stop: the inner tanks sat at 32,880–32,916 kg, just under the full−50 kg test, so the controller trickled centre fuel at burn rate for 84 minutes until the centre reached its unusable 67 kg. The stop now triggers at full−150 kg (`REFILL_STOP_KG`), within one 25-gallon chunk of the top-up target, so the transfer cycles between full and 2,000 kg below full as described for the aircraft. The stock aft transfer filled the trim tank from 3,530 to 4,889 kg between FL255 and FL345. Over 11.8 hours no status or fault flag appeared.

The same flight characterised the stock -300's forward transfer, which it triggers only by inner-tank low level, not by the aircraft's FL245 or 35-minutes-to-go rules: at 3,999 kg per inner tank it moved trim fuel into the inner tanks at about 5.4 kg/s per side until they held 5,000 kg, then repeated at 4,000 kg, three episodes in cruise until the trim tank was empty. Outer-to-inner gravity transfer began at 3,558 kg inner at about 2 kg/s per side. The centre-tank re-route of the forward transfer (trim to centre, then centre pumps to the inner tanks, as on the -200) is therefore reproducible on the ground by setting the inner tanks to about 3,900 kg with trim fuel aboard, and is developed as a separate step. Its effect is mostly indication: the -300 centre tank sits at x −9.551 ft against the inner tanks' −6.5 ft, so a tonne routed through it moves the CG aft by well under 0.1 % MAC.

SDK build 030 (v0.3.8: stop threshold, drag scalar, EFB check) passed with no new builder diagnostics: 28 payload entries, `engines.cfg` byte-identical to stock. With MSFS closed, v0.3.8 replaced v0.3.7; all 30 installed files match the SDK output. The transfer stop and restart cycle is still to be observed in flight.

## Prepare private SDK sources

The workflow prepares the current source candidate from the installed RR preset, donor controls and instrument loaders. The distributed project contains only original preparation tools, configuration deltas, instrument extensions and thumbnails. Stock-derived configuration, model extracts and HTML stay in ignored local build files and must not be redistributed. The installed aircraft retains ownership of its native systems module and data.

With the original A330 available through the active VFS Projector, run from the repository root:

```powershell
python tools/prepare_sdk_sources.py "C:\path\to\VFSProjection"
```

The tool reads all 13 stock RR preset CFG files before publishing `dist/local-sdk-sources`. It preserves the six RR engine entries (including the thrust table), engine geometry, cameras, navigation graphs and merge markers. It merges deltas into `aircraft.cfg`, `flight_model.cfg` and `attached_objects.cfg`; the other 10 CFG files remain byte-identical. The original exterior, RR engine and interior attachments remain selected; a fourth attachment adds the centre buttons. Metadata supplies the title/variation, manufacturer, RR classification, user selectability, disabled AI traffic and empty career specializations. Shared stock aircraft grouping remains inherited.

The three original thumbnails replace the stock preset thumbnails. Empty XML merge declarations are generated at the observed stock sound, AI sound and checklist paths, using their actual root names and attributes. Full cockpit meshes, stock cockpit textures, native panel/modules and sound banks remain installed-aircraft dependencies. Only the small donor-control mesh is extracted privately; there is no replacement interior or panel.

The preset uses the company directory `a330wv081community`. The SDK's native modular file lister omitted the three thumbnails and checklist declaration from this partial preset. Preparation therefore stages those four files separately under `dist/local-sdk-sources/preset-resources`; an SDK `Copy` asset group places them at the same preset paths in the finished package. CFG, navigation and sound files remain in the `ModularSimObject` asset group. Nothing is inserted into the package after the SDK build.

Pristine preset CFG inputs are retained under `dist/local-sdk-sources/reference/rr` for local comparison. The EFB loader is read from `html_ui/Pages/VCockpit/Instruments/ini-efb-a330/ini-efb-a330.html`; preparation requires its stock template and exactly one stock JavaScript import. The WASM instrument loader is also extended at its existing path, with a second explicit global override declaration. The original fuel display selects the exact WV081 title, stock A330 module, ECAM gauge and fuel page. Already-overlaid loaders are rejected; use pristine locally cached inputs or project the stock files without this mod mounted. All inputs are read and staged before the generated source directory is replaced, with no backup or rollback. Missing, empty or unreadable inputs cause preparation to fail before replacing that directory. Keep VFS Projector active until preparation completes; projected file sizes alone do not indicate readable content.

## SDK build boundary

[`A330_WV081_Project.xml`](../A330_WV081_Project.xml) points to the prepared private source tree and places build output under `dist/sdk`. Its `Project Version="2"` and `ModularSimObject` structure were checked against the official SDK 1.7.3 full DA62 sample. The package definition also includes the project license and a local-use notice. `package/manifest.json` records the withdrawn v0.1.1 prototype; the SDK generates its own manifest and layout using the version in `PackageDefinitions/a330-wv081-aircraft-baseline.xml`.

Preparation performs no SDK build, simulator launch, installation or ZIP creation. Once preparation finishes, close the normal simulator session before running the SDK package tool:

```powershell
& "C:\path\to\SDK\Tools\bin\fspackagetool.exe" "$PWD\A330_WV081_Project.xml" -forcesteam -nopause
```

This command is for the observed Steam installation. `fspackagetool.exe` starts `FlightSimulator2024.exe` to compile; it may instead attach to an already running normal session. Output remains under `dist/sdk/Packages/a330-wv081-aircraft-baseline`. This build command does not install into Community.

The v0.1.2 and v0.2.0 native SDK builds completed on 2026-10-08 with no new builder errors and generated complete manifests and layouts. Each package contains the 13 preset CFG files, three XML merge declarations, three original thumbnails, license and local-use notice, plus manifest and layout. Their dependency is `microsoft-aircraft-a330` version `0.0.53`. The SDK uses the dependency XML's `Version` value as the manifest dependency version. All four weight fields are present in the v0.2.0 output; all 13 output CFGs match its prepared source. Only v0.1.2 has completed a manual check.

The withdrawn v0.2.1 build also passed SDK and syntax checks. Its subsequent cockpit failure demonstrates that these checks do not validate runtime attachment inheritance. v0.2.2 completed SDK packaging on 2026-10-08 with no new builder diagnostics, 23 package files and a complete 21-entry payload layout. All 13 output CFGs match preparation; 11 are byte-identical to stock, including `attached_objects.cfg`. The flight-model change adds only the four weight fields. No custom attachment, panel or HTML gauge assets are included.

Do not rely on the launcher exit code or empty `_RPTErrors.xml` alone: earlier attempts returned zero and an empty report despite recording package validation failures in the simulator profile's `BuilderLogError.txt`. Check new builder diagnostics and the generated package contents. Successful packaging does not establish correct merged aircraft behavior, startup, variant selection, cockpit systems or sounds. A controlled simulator check remains required. Keep both prepared sources and SDK output private.

`tools/build_package.py` remains disabled. Do not use the former copy-and-ZIP workflow or install the withdrawn build. Correcting the known configuration omissions does not establish which one caused the two startup crashes.

## Removal

With MSFS closed, move only `a330-wv081-aircraft-baseline` out of the configured Community folder. Moving it elsewhere inside Community does not disable it. Keep the original Microsoft/iniBuilds A330 and all unrelated packages unchanged. Stock files were not replaced by this prototype.

## Manual check status and remaining validation

Candidate v0.1.2 passed packaging checks and was installed locally into Community on 2026-10-08. The user's subsequent screenshot confirms startup reached the configuration screen, `A330-300 (RR) - WV081 Development Baseline` is selectable, and its RR exterior renders with a livery. After being asked to load it at a parking stand and check the cockpit, displays, EFB and sounds, the user reported that everything looked good. This records a successful basic manual ground check, not exhaustive systems testing or proof that every earlier crash condition is resolved.

The baseline screenshot exposed an unresolved manufacturer localization key. The authored metadata now sets `ui_manufacturer="Airbus"`; the label itself has not been visually rechecked. Missing cabin, gear and seat rows are not evidence of missing aircraft components: the SDK's [UI field mapping](https://docs.flightsimulator.com/msfs2024/html/7_Samples_Tutorials/Tutorials/Aircraft_Checklist/Additional_Aircraft_Information.htm) ties those rows to Marketplace ingestion data and career classification. Career specializations remain disabled for this development preset.

Complete weight/fuel comparison and detailed systems behavior remain outstanding. The previously observed stock baseline was approximately 233t maximum takeoff weight, 25,189 US gal total fuel capacity, and zero centre-tank capacity.

Baseline v0.1.2 preserves stock RR physics and fuel configuration. v0.2.2 keeps the four simulator weight limits and the original stock cockpit/EFB. It is built as a forward correction from the last good baseline. v0.2.2 was installed into the configured Community folder on 2026-10-08, replacing withdrawn v0.2.1. After loading it in game, the user reported that everything looked normal. This confirms a successful basic load and apparent cockpit recovery; detailed systems/performance validation remains outstanding.

Two subsequent EFB Payload screenshots show `Max Weight` at 242,901 kg, with `Live Gross Weight` first at 253,348 kg in red and then at 242,627 kg in white. This supports the higher gross-weight display and warning threshold working in game. The 1 kg difference from the configured 242,900 kg ramp limit remains unexplained by static inspection of the EFB display path.

Both screenshots show planned ZFW of 176,797 kg, exceeding the WV081 target by 5,797 kg. In the second screenshot, adding the displayed 65,830 kg of fuel gives the displayed live gross weight of 242,627 kg. A white gross-weight value therefore does not establish compliance with the separate 171,000 kg zero-fuel limit or the 242,000 kg takeoff limit; the latter is exceeded by 627 kg in this parked check.

The v0.2.2 installation contained 23 files with sizes matching the SDK layout and manifest version `0.2.2`. The four obsolete v0.2.1 EFB/interior files were removed. The current v0.2.7 installation is described above; its variant label remains `A330-300 (RR) - WV081 Weight Prototype`.

The next trial prioritizes centre-tank loading and transfer, overhead control response, ECAM indications, engine supply and trim interaction. Weight readback and EFB/MCDU agreement remain secondary outstanding items. The stock EFB Payload page's `Max Weight` field reads the ramp/gross limit, so its target is 242,900 kg rather than the separate 242,000 kg takeoff limit. Detailed camera/navigation operation, checklist operation and flight performance still need validation. The unique aircraft title may give the EFB separate saved options and SimBrief settings.

These declarations follow the SDK's [modular merge rules](https://docs.flightsimulator.com/msfs2024/html/5_Content_Configuration/Modular_SimObjects/Modular_SimObject_Merging.htm) and [preset structure](https://docs.flightsimulator.com/msfs2024/html/5_Content_Configuration/Modular_SimObjects/Modular_SimObject_Project_Structure.htm). Static packaging checks cannot establish successful simulator loading.

## License and disclaimer

Original project contributions are free under CC BY-NC-SA 4.0; see [LICENSE](../LICENSE). Stock Microsoft/iniBuilds assets remain separately licensed and are not distributed here.

**Disclaimer:** This is a community-driven, freeware delta mod. It requires the original Microsoft/iniBuilds A330-300 to work. This project is NOT affiliated with, endorsed by, or sponsored by Microsoft, Asobo Studio, iniBuilds, or Airbus.
