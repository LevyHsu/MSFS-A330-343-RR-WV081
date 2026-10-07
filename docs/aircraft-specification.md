# Aircraft specification

Target selected on 2026-10-07. This document defines the intended aircraft; it does not claim that the mod or its simulator integration has been implemented.

## First version

| Item | Target |
| --- | --- |
| Simulator | Microsoft Flight Simulator 2024 |
| Required base aircraft | Default Microsoft/iniBuilds A330-300 (RR), passenger version |
| Real aircraft model | Airbus A330-343, Rolls-Royce-powered |
| Weight variant | WV081, fixed weight limits |
| Maximum takeoff weight (MTOW) | 242,000 kg |
| Maximum landing weight (MLW) | 187,000 kg |
| Maximum zero-fuel weight (MZFW) | 171,000 kg |

The [Airbus weight-variant table, pages 3-4](https://www.aircraft.airbus.com/sites/g/files/jlcbta126/files/2024-06/a330_family_weight_variant.pdf#page=4) confirms these limits and lists WV081 for the A330-343. WV050 is a different 230t variant; the earlier WV050 project designation was incorrect. WV082's variable zero-fuel-weight limits are outside this first version's scope.

MTOW, MLW, and MZFW are separate limits. Maximum ramp/taxi weight remains unresolved and must not be assumed equal to MTOW. Do not substitute the checklist's unsupported 178,000 kg MZFW.

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

Static archive and VFS inspection established the RR preset's attachment map, metadata, engine and geometry contributions, and panel/EFB references. Candidate v0.1.2 preserves those stock preset contributions and has passed private SDK packaging checks. User evidence confirms variant selection and exterior rendering, followed by a successful reported basic ground check. Numerical weight/fuel comparison, detailed systems behavior, flight performance and modification interfaces remain unresolved. The next development step is mapping the fixed WV081 weight limits through simulator configuration and EFB/FMS handling; centre-tank integration remains separate work.
