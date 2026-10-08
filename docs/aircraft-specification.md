# Aircraft specification

Target selected on 2026-10-07. This document defines the intended aircraft; it does not claim that the mod or its simulator integration has been implemented.

## First version

| Item | Target |
| --- | --- |
| Simulator | Microsoft Flight Simulator 2024 |
| Required base aircraft | Default Microsoft/iniBuilds A330-300 (RR), passenger version |
| Real aircraft model | Airbus A330-343, Rolls-Royce-powered |
| Weight variant | WV081, fixed weight limits |
| Maximum ramp/taxi weight (MRW/MTW) | 242,900 kg |
| Maximum takeoff weight (MTOW) | 242,000 kg |
| Maximum landing weight (MLW) | 187,000 kg |
| Maximum zero-fuel weight (MZFW) | 171,000 kg |

The [Airbus weight-variant table, pages 3-4](https://www.aircraft.airbus.com/sites/g/files/jlcbta126/files/2024-06/a330_family_weight_variant.pdf#page=4) confirms these limits and lists WV081 for the A330-343. WV050 is a different 230t variant; the earlier WV050 project designation was incorrect. WV082's variable zero-fuel-weight limits are outside this first version's scope.

MTOW, MLW, and MZFW are separate limits. The [Airbus aircraft characteristics document, December 2025, section 2-1-1 pages 1 and 3-4](https://www.aircraft.airbus.com/sites/g/files/jlcbta126/files/2025-12/AC_A330_20251201.pdf#page=45) identifies the A330-300 WV081 maximum ramp/taxi weight as 242,900 kg, separate from 242,000 kg MTOW. Do not substitute the checklist's unsupported 178,000 kg MZFW.

## Development priorities

The user confirmed on 2026-10-08 that the core work is centre-tank activation, fuel overhead controls, fuel supply and trim-transfer logic, and ECAM integration. Later-production exterior model differences follow. Weight-entry enforcement is secondary: retain input through 175,000 kg for SimBrief compatibility, state the WV081 aircraft maximum of 171,000 kg, and show a red warning above it while allowing the load. Keep the fixed structural limits unchanged. Batch meaningful fuel/model changes before the next simulator trial.

## Intended centre-tank configuration

Centre-tank activation is part of the intended mod. It is a separate configuration choice: [Airbus describes it as an option accompanying the 242t upgrade](https://www.airbus.com/en/newsroom/news/2020-10-the-a330-family-legacy-continues-with-the-1500th-delivery), not something established by the weight-variant label alone.

The [EASA A330 type-certificate data sheet, Issue 69, A330-300 section 7.1, page 41](https://www.easa.europa.eu/en/downloads/7518/en#page=41) provides these reference values for the three-tank configuration:

| Usable fuel | Volume | Mass at 0.8 kg/L |
| --- | --- | --- |
| Wing tanks, combined | 91,300 L | 73,040 kg |
| Centre tank | 41,560 L | 33,248 kg |
| Trim tank | 6,230 L | 4,984 kg |
| Total | 139,090 L | 111,272 kg |

These are usable capacities, not total tank volumes or simulator configuration entries. Aircraft modification applicability, unusable quantities, tank positions, and their mapping to the stock simulator aircraft remain to be established. Fuel mass depends on density; centre capacity is not an extra 41 tonnes of fuel.

VFS inspection of the installed A330 package 0.0.53 found a 10,735 US gal (40,636.40 L) A330-200 centre tank, below the 41,560 L reference. The -200 and -300 share their configured datum and wing-apex reference, but their wing-tank positions differ. The -300 cockpit also lacks the -200 centre-pump/transfer controls and their model nodes. The donor is therefore a source of configuration and control references, not a complete centre-tank implementation. Refuelling distribution, transfer logic, indications and trim interaction remain unverified. Do not transplant the complete -200 flight model or set its aircraft-identity flag: the stock EFB couples that identity to different passenger, fuel and ZFW limits. The v0.3.0 prototype added donor `Center1=-9.551,0,0,10735,0`; v0.3.1 retains that configured capacity and the additive controls. Capacity is not proof of loading, transfer or engine supply. The correction retains the stock EFB fuel-entry ceiling until centre loading has a working controller.

The stock native code separately gates centre refuelling, centre-to-inner transfer and centre ECAM graphics using `INI_IS_200`. Its A333 trim branch requires the opposite identity. A capacity change or a global -200 identity substitution cannot provide the intended combination. The v0.3.0 trial used a private projected native-module adaptation, but aircraft systems did not start and native displays remained dark. The session report contains no loaded A330 module. v0.3.1 removes that deployment route and uses the installed stock interior/panel/module; SDK build 020 and installation passed; runtime recovery remains unverified. A supported centre-controller interface remains unresolved because the stock controller reads and writes the same tank quantities. The original ECAM prototype reads actual centre quantity, pump states and feeding flags and labels this incomplete configuration `CTR NOT ACTIVE`; it does not invent flow or replace other native ECAM pages. Detailed inspection notes and stock-derived experimental output stay private and are not part of the active package.

## Later-production exterior model

Compare the stock exterior against the applicable A330ceo production standard before changing geometry. Airbus describes shortened flap-track fairings and a revised slat 1 profile among its A330 incremental aerodynamic changes ([FAST A330 special edition, October 2015, printed page 08](https://aircraft.airbus.com/sites/g/files/jlcbta126/files/2022-04/Airbus-FAST-special-edition-Oct2015.pdf#page=8)). Applicability to the intended aircraft and the stock model's existing shapes still need comparison; no exterior geometry change has been implemented.

## Base package observed

Read-only local inspection on 2026-10-07 found package `microsoft-aircraft-a330`, version `0.0.53`, and the preset directory `SimObjects/Airplanes/microsoft-a330/presets/inibuilds/a330-300 (rr)`.

This identifies the starting installation, not a verified compatibility range. Read-only checks found live legacy fuel mode, approximately 233t maximum takeoff weight, zero centre-tank capacity, and readable wing/trim state. Exact engine rating, internal fuel logic, and the required cockpit extension points remain unresolved.

## Items requiring evidence before implementation

- Exact engine subtype/rating and the stock engine configuration; no generic thrust or fuel-consumption increase.
- Operating empty weight, payload stations, tank locations, and the applicable CG envelope; no arbitrary weight increase or wider CG limits.
- Centre/wing/trim transfer logic, refuelling distribution, pump and valve behaviour, electrical dependencies, and indications.
- Access to the necessary configuration overrides, FMS/ECAM/EFB interfaces, and cockpit controls without redistributing proprietary assets.
- Performance-data applicability, including speeds, fuel predictions, and takeoff/landing calculations; accepting a weight entry alone is insufficient.
- Any required aerodynamic or braking changes, supported by evidence and comparison with the base aircraft.

Static archive and VFS inspection established the RR preset's attachment map, metadata, engine and geometry contributions, and panel/EFB references. Baseline v0.1.2 passed private SDK packaging checks and a successful reported basic ground check. The v0.2.1 EFB experiment is withdrawn after the cockpit disappeared during its local trial. v0.2.2 retained the four explicit simulator weight fields while using the original stock attachment map and EFB. On 2026-10-08, the user reported that v0.2.2 loaded in game with everything looking normal. Subsequent EFB screenshots show a 242,901 kg gross limit, with 253,348 kg in red and 242,627 kg in white; the 1 kg difference from the configured ramp limit remains unexplained. The stock EFB has a 175t direct-entry zero-fuel limit, and its passenger/cargo path displayed a planned ZFW of 176,797 kg, above the 171t target. Installed v0.2.3 adds a title-scoped EFB loading guard through a shared HTML loader override while preserving stock cockpit attachments. SDK packaging passed, but the user confirmed that direct ZFW entry still shows 175t, so the intended override did not take effect. The reported fuel maximum remains approximately 76.5t, as expected with stock fuel capacity. v0.2.5 combines the JavaScript compatibility correction with stock fuel-capacity checks, startup diagnostics and a SimBrief unit reminder. It warns on planned ramp overweight while allowing the load, matching the reported stock behavior; the 171t ZFW guard remains. SDK packaging passed, but the v0.2.5 in-game check still showed 175t and no extension message. Screenshots show 242t gross weight in white and 243t in red. VFS inspection confirmed that the shared EFB loader was still pristine stock. v0.2.6 added the missing SDK override declaration, but its trial still accepted 175t. Refreshed VFS inspection found the current extension file and expected aircraft title while the shared HTML remained stock. v0.2.7 changes the override path to lowercase to match the layout; the SDK normalizes its separators to backslashes. Build 018 passed and the candidate is installed. Fresh VFS inspection confirms the modified HTML loader and v0.2.7 extension match the installed files, establishing loader selection for this package. The subsequent user ground check confirms extension activation, a 171,000 kg direct-entry maximum and successful loading at that ZFW with 76,551 kg fuel. The resulting 247,551 kg gross weight is red and the original amber WV081 warning allows the overweight load as intended. That 171t entry cap is superseded in v0.3.0 source by the user-requested warning-only policy, with entry through 175t. Its in-game behavior remains unverified. A universal SDK casing requirement has not been established. Other limit readbacks, EFB/FMS agreement and performance remain unverified. No writable FMS structural-limit interface has been established. Centre-tank, overhead, fuel supply/trim and ECAM integration are the current priority.
