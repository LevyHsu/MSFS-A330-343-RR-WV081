# A330 RR development baseline

**Withdrawn:** Two initial-loading crashes occurred with v0.1.1 installed. Both crash reports record the same native `purecall` failure before an aircraft container loaded; neither identifies a specific faulty package file. After this package was moved out of Community, the user confirmed that MSFS reached the main menu. This strongly implicates the prototype, but the exact configuration fault remains unresolved. Do not reinstall this build.

This is a development Community preset for the A330-343 WV081 project, with a successful user-reported basic ground check. It appears as a new variant within the existing Microsoft/iniBuilds A330 aircraft group, using the installed A330-300 RR attachments. It does not implement the 242t upgrade or centre-tank activation.

The initial development target is MSFS 2024 1.8.16.0 with the downloaded `microsoft-aircraft-a330` package version 0.0.53. Compatibility with other versions or a streamed-only installation has not been established.

## Prepare private SDK sources

The new workflow prepares candidate v0.1.2 from each user's installed RR preset. The distributed project contains the preparation tool, original metadata changes and original thumbnails. Stock-derived configuration exists only in ignored local build files and must not be redistributed.

With the original A330 available through the active VFS Projector, run from the repository root:

```powershell
python tools/prepare_sdk_sources.py "C:\path\to\VFSProjection"
```

The tool reads all 13 stock RR preset CFG files before publishing `dist/local-sdk-sources`. It preserves the attachment map, six RR engine entries (including the thrust table), two engine-geometry sections, camera configuration, navigation graphs and merge markers. Only `aircraft.cfg` receives the project's metadata changes: unique title/variation, RR classification, user selectability, disabled AI traffic and empty career specializations. Shared stock aircraft grouping remains inherited.

The three original thumbnails replace the stock preset thumbnails. Empty XML merge declarations are generated at the observed stock sound, AI sound and checklist paths, using their actual root names and attributes. No unsupported `panel.xml` is added; the cockpit uses the stock attachment's `panel.cfg`. Common configuration, attachments, models, textures, sound banks and WASM modules remain dependencies and are not bundled by preparation.

The preset uses the company directory `a330wv081community`. The SDK's native modular file lister omitted the three thumbnails and checklist declaration from this partial preset. Preparation therefore stages those four files separately under `dist/local-sdk-sources/preset-resources`; an SDK `Copy` asset group places them at the same preset paths in the finished package. CFG, navigation and sound files remain in the `ModularSimObject` asset group. Nothing is inserted into the package after the SDK build.

Pristine preset CFG inputs are retained under `dist/local-sdk-sources/reference/rr` for local comparison. A successful subsequent preparation moves the previous tree to another ignored `dist` directory. Missing, empty or unreadable projected inputs cause preparation to fail before publishing a replacement. Keep VFS Projector active until preparation completes; projected file sizes alone do not indicate readable content.

## SDK build boundary

[`A330_WV081_Project.xml`](../A330_WV081_Project.xml) points to the prepared private source tree and places build output under `dist/sdk`. Its `Project Version="2"` and `ModularSimObject` structure were checked against the official SDK 1.7.3 full DA62 sample. The package definition also includes the project license and a local-use notice. `package/manifest.json` records the withdrawn v0.1.1 prototype; the SDK generates its own v0.1.2 manifest and layout.

Preparation performs no SDK build, simulator launch, installation or ZIP creation. Once preparation finishes, close the normal simulator session before running the SDK package tool:

```powershell
& "C:\path\to\SDK\Tools\bin\fspackagetool.exe" "$PWD\A330_WV081_Project.xml" -forcesteam -nopause
```

This command is for the observed Steam installation. `fspackagetool.exe` starts `FlightSimulator2024.exe` to compile; it may instead attach to an already running normal session. Output remains under `dist/sdk/Packages/a330-wv081-aircraft-baseline`. This project does not install into Community.

The native SDK build completed on 2026-10-08 with no new builder errors and generated the complete manifest and layout. The package contains the 13 preset CFG files, three XML merge declarations, three original thumbnails, license and local-use notice, plus the manifest and layout. Its dependency is `microsoft-aircraft-a330` version `0.0.53`. The SDK uses the dependency XML's `Version` value as the manifest dependency version.

Do not rely on the launcher exit code or empty `_RPTErrors.xml` alone: earlier attempts returned zero and an empty report despite recording package validation failures in the simulator profile's `BuilderLogError.txt`. Check new builder diagnostics and the generated package contents. Successful packaging does not establish correct merged aircraft behavior, startup, variant selection, cockpit systems or sounds. A controlled simulator check remains required. Keep both prepared sources and SDK output private.

`tools/build_package.py` remains disabled. Do not use the former copy-and-ZIP workflow or install the withdrawn build. Correcting the known configuration omissions does not establish which one caused the two startup crashes.

## Removal

With MSFS closed, move only `a330-wv081-aircraft-baseline` out of the configured Community folder. Moving it elsewhere inside Community does not disable it. Keep the original Microsoft/iniBuilds A330 and all unrelated packages unchanged. Stock files were not replaced by this prototype.

## Manual check status and remaining validation

Candidate v0.1.2 passed packaging checks and was installed locally into Community on 2026-10-08. The user's subsequent screenshot confirms startup reached the configuration screen, `A330-300 (RR) - WV081 Development Baseline` is selectable, and its RR exterior renders with a livery. After being asked to load it at a parking stand and check the cockpit, displays, EFB and sounds, the user reported that everything looked good. This records a successful basic manual ground check, not exhaustive systems testing or proof that every earlier crash condition is resolved.

The screenshot exposes an unresolved manufacturer localization key. The authored metadata now sets `ui_manufacturer="Airbus"`; this source correction has not yet been rebuilt or installed. Missing cabin, gear and seat rows are not evidence of missing aircraft components: the SDK's [UI field mapping](https://docs.flightsimulator.com/msfs2024/html/7_Samples_Tutorials/Tutorials/Aircraft_Checklist/Additional_Aircraft_Information.htm) ties those rows to Marketplace ingestion data and career classification. Career specializations remain disabled for this development preset.

Measured weight/fuel comparison and detailed systems behavior remain outstanding. The previously observed stock baseline was approximately 233t maximum takeoff weight, 25,189 US gal total fuel capacity, and zero centre-tank capacity. The user's general confirmation did not provide new numerical readings or flight-performance results.

The prepared preset preserves stock RR physics and fuel configuration without introducing WV081 limits or centre-tank changes. Detailed engine behavior, camera/navigation operation, checklist operation and flight performance still need validation in the new preset. The unique aircraft title may give the EFB separate saved options and SimBrief settings.

These declarations follow the SDK's [modular merge rules](https://docs.flightsimulator.com/msfs2024/html/5_Content_Configuration/Modular_SimObjects/Modular_SimObject_Merging.htm) and [preset structure](https://docs.flightsimulator.com/msfs2024/html/5_Content_Configuration/Modular_SimObjects/Modular_SimObject_Project_Structure.htm). Static packaging checks cannot establish successful simulator loading.

## License and disclaimer

Original project contributions are free under CC BY-NC-SA 4.0; see [LICENSE](../LICENSE). Stock Microsoft/iniBuilds assets remain separately licensed and are not distributed here.

**Disclaimer:** This is a community-driven, freeware delta mod. It requires the original Microsoft/iniBuilds A330-300 to work. This project is NOT affiliated with, endorsed by, or sponsored by Microsoft, Asobo Studio, iniBuilds, or Airbus.
