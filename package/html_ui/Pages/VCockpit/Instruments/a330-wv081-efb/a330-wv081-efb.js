// Original WV081 loading extension, CC BY-NC-SA 4.0. Import before the installed stock EFB.
// Keep this untranspiled script compatible with Coherent GT's ES2017 target.
(() => {
    "use strict";

    const AIRCRAFT_TITLE = "A330 WV081 Community - A330-300 (RR) Baseline";
    const VERSION = "0.3.1";
    const MAX_ZFW_KG = 171000;
    const INPUT_MAX_ZFW_KG = 175000;
    const MAX_RAMP_KG = 242900;
    const POUNDS_PER_KG = 2.20462;
    const states = new WeakMap();
    const adapted = new WeakSet();

    function readTitle(state) {
        if (!state.simReady && !BaseInstrument.allInstrumentsLoaded) {
            return null;
        }
        try {
            const title = SimVar.GetSimVarValue("TITLE", "string");
            return typeof title === "string" && title.trim() ? title.trim() : null;
        } catch (_) {
            return null;
        }
    }

    function status(state, message, level = "error") {
        let element = state.instrument.querySelector(".wv081-load-status");
        if (!element && !message) {
            return;
        }
        if (!element) {
            element = document.createElement("div");
            element.className = "wv081-load-status";
            element.setAttribute("role", "status");
            element.style.cssText = "position:absolute;left:16px;right:16px;bottom:16px;"
                + "z-index:10000;padding:12px 16px;color:#fff;border-radius:6px;font-size:18px;";
            state.instrument.appendChild(element);
        }
        element.textContent = message;
        element.style.background = level === "ready" ? "#123329" : level === "notice" ? "#4a3510" : "#38141d";
        element.style.display = message ? "block" : "none";
    }

    function ready(state) {
        state.ready = state.payloads.length > 0 && state.payloads.every(record => {
            const minimum = minimumWeight(record.payload);
            const units = record.payload.weightUnits ? record.payload.weightUnits.get() : undefined;
            return record.valid && record.rendered && Number.isFinite(record.payload.maxFuelKg)
                && record.payload.maxFuelKg > 0 && Number.isFinite(minimum)
                && minimum > 0 && minimum <= MAX_ZFW_KG && (units === "kg" || units === "lb");
        });
        status(state, state.ready ? `WV081 v${VERSION}: maximum ZFW 171 t; entry to 175 t allowed for SimBrief. Centre transfer is not active.`
            : "WV081 loading unavailable: waiting for aircraft weight data.", state.ready ? "ready" : "error");
    }

    function warnZeroFuelWeight(payload, state) {
        const units = payload.weightUnits ? payload.weightUnits.get() : undefined;
        const factor = units === "lb" ? POUNDS_PER_KG : 1;
        const maximum = Math.floor(MAX_ZFW_KG * factor);
        if (payload.inputZFW && payload.inputZFW.get() > maximum) {
            status(state, `WV081 overweight: ZFW exceeds the ${maximum.toLocaleString("en-US")} ${units} aircraft maximum. Loading is allowed; this does not change the 171 t limit.`);
            return true;
        }
        return false;
    }

    function refresh(state) {
        const previous = state.appliedTitle;
        state.title = readTitle(state);
        if (state.title === previous && (state.title !== AIRCRAFT_TITLE || state.ready)) {
            return;
        }
        state.appliedTitle = state.title;
        if (state.title !== previous
            && (state.title === AIRCRAFT_TITLE || previous === AIRCRAFT_TITLE)) {
            for (const record of state.payloads) {
                if (record.rendered && record.valid) {
                    record.payload.calculatePlannedWeight(true);
                }
            }
        }
        if (state.title === AIRCRAFT_TITLE) {
            if (state.payloads.every(record => record.valid)) {
                const wasReady = state.ready;
                ready(state);
                if (!wasReady && state.ready && state.title === previous) {
                    for (const record of state.payloads) {
                        record.payload.calculatePlannedWeight(true);
                    }
                }
            } else {
                status(state, "WV081 loading unavailable: the stock EFB interface has changed.");
            }
        } else {
            state.ready = false;
            status(state, "");
        }
    }

    function stateFor(instrument) {
        let state = states.get(instrument);
        if (state) {
            return state;
        }
        state = { instrument, payloads: [], title: null, appliedTitle: null, simReady: false, ready: false, nextRefresh: 0 };
        states.set(instrument, state);
        const init = instrument.Init;
        if (typeof init === "function") {
            instrument.Init = function (...args) {
                const result = init.apply(this, args);
                state.simReady = true;
                return result;
            };
        }
        const update = instrument.Update;
        instrument.Update = function (...args) {
            const result = update.apply(this, args);
            if (Date.now() >= state.nextRefresh) {
                state.nextRefresh = Date.now() + 500;
                try {
                    refresh(state);
                } catch (_) {
                    state.ready = false;
                    if (state.title === AIRCRAFT_TITLE) {
                        status(state, "WV081 loading unavailable: the loading limit could not initialize.");
                    }
                }
            }
            return result;
        };
        return state;
    }

    function minimumWeight(payload) {
        if (!Number.isFinite(payload.minZFWKg) || payload.minZFWKg <= 0) {
            try {
                payload.minZFWKg = SimVar.GetSimVarValue("EMPTY WEIGHT", "kilograms");
            } catch (_) {
                return NaN;
            }
        }
        return payload.minZFWKg;
    }

    function canLoad(record, state) {
        state.title = readTitle(state);
        if (state.title === null) {
            status(state, "Loading unavailable: waiting for aircraft identification.");
            return false;
        }
        if (state.title !== AIRCRAFT_TITLE) {
            status(state, "");
            return true;
        }
        const payload = record.payload;
        const units = payload.weightUnits ? payload.weightUnits.get() : undefined;
        const requested = payload.inputZFW ? payload.inputZFW.get() : undefined;
        const fuel = payload.inputFuel ? payload.inputFuel.get() : undefined;
        const minimumKg = minimumWeight(payload);
        if (!record.valid || (units !== "kg" && units !== "lb")
            || !Number.isFinite(requested) || !Number.isFinite(fuel)
            || !Number.isFinite(payload.maxFuelKg) || payload.maxFuelKg <= 0 || !Number.isFinite(minimumKg)
            || minimumKg <= 0 || minimumKg > MAX_ZFW_KG) {
            status(state, "WV081 loading blocked: valid aircraft, zero-fuel-weight and fuel data are required.");
            return false;
        }
        const factor = units === "lb" ? POUNDS_PER_KG : 1;
        // Match the stock calculator's integer limits in both units.
        const minimum = Math.floor(Math.floor(minimumKg) * factor);
        const maximum = Math.floor(INPUT_MAX_ZFW_KG * factor);
        if (requested < minimum || requested > maximum) {
            status(state, `WV081 loading blocked: zero-fuel weight must be between ${minimum.toLocaleString("en-US")} and ${maximum.toLocaleString("en-US")} ${units}.`);
            return false;
        }
        const maximumFuel = Math.floor(Math.floor(payload.maxFuelKg) * factor);
        if (fuel < 0 || fuel > maximumFuel) {
            status(state, `WV081 loading blocked: fuel must be between 0 and ${maximumFuel.toLocaleString("en-US")} ${units}.`);
            return false;
        }
        ready(state);
        if (warnZeroFuelWeight(payload, state)) {
            return true;
        }
        const maximumRamp = Math.floor(MAX_RAMP_KG * factor);
        if (requested + fuel > maximumRamp) {
            status(state, `WV081 overweight: planned ZFW plus fuel exceeds ${maximumRamp.toLocaleString("en-US")} ${units} ramp weight. Loading is allowed.`, "notice");
        }
        return true;
    }

    function adapt(payload, instrument) {
        if (adapted.has(payload)) {
            return;
        }
        adapted.add(payload);
        const state = stateFor(instrument);
        const calculate = payload.calculatePlannedWeight;
        const apply = payload.applyPlannedLoad;
        const load = payload.loadAircraft;
        const afterRender = payload.onAfterRender;
        const simbrief = payload.calculatePlannedWeightFromSimbrief;
        const record = {
            payload, rendered: false,
            valid: [calculate, apply, load, afterRender].every(method => typeof method === "function"),
        };
        state.payloads.push(record);
        let stockMaximum = payload.maxZFWKg;
        Object.defineProperty(payload, "maxZFWKg", {
            configurable: true,
            enumerable: true,
            get: () => state.title === AIRCRAFT_TITLE ? INPUT_MAX_ZFW_KG : stockMaximum,
            set: value => { stockMaximum = value; },
        });
        // Retain the stock fuel-entry maximum until centre loading has a working controller.
        payload.calculatePlannedWeight = function (...args) {
            state.title = readTitle(state);
            if (state.title === AIRCRAFT_TITLE) {
                minimumWeight(this);
            }
            const result = typeof calculate === "function" ? calculate.apply(this, args) : undefined;
            if (state.title === AIRCRAFT_TITLE && record.rendered) {
                ready(state);
                warnZeroFuelWeight(this, state);
            }
            return result;
        };
        payload.applyPlannedLoad = function (...args) {
            if (canLoad(record, state)) {
                return typeof apply === "function" ? apply.apply(this, args) : undefined;
            }
        };
        payload.loadAircraft = function (...args) {
            if (canLoad(record, state)) {
                return typeof load === "function" ? load.apply(this, args) : undefined;
            }
        };
        if (typeof simbrief === "function") {
            payload.calculatePlannedWeightFromSimbrief = function (...args) {
                const result = simbrief.apply(this, args);
                state.title = readTitle(state);
                if (state.title === AIRCRAFT_TITLE) {
                    const units = this.weightUnits ? this.weightUnits.get() : undefined;
                    status(state, `WV081: SimBrief units must match EFB units (${units}). Review ZFW and fuel before applying the load.`, "notice");
                }
                return result;
            };
        }
        payload.onAfterRender = function (...args) {
            const result = typeof afterRender === "function" ? afterRender.apply(this, args) : undefined;
            record.rendered = true;
            state.title = readTitle(state);
            if (state.title === AIRCRAFT_TITLE && record.valid) {
                this.calculatePlannedWeight(true);
                ready(state);
            }
            return result;
        };
    }

    const previousPlugin = window._pluginSystem;
    const owners = new WeakMap();
    const plugin = Object.create(previousPlugin || null);
    function delegate(method, args) {
        return previousPlugin && typeof previousPlugin[method] === "function"
            ? previousPlugin[method].apply(previousPlugin, args) : undefined;
    }
    plugin.onComponentCreating = function (type, props) {
        const replacement = delegate("onComponentCreating", [type, props]);
        if (typeof PayloadViewerComponent === "function" && type === PayloadViewerComponent
            && replacement !== null && typeof replacement === "object") {
            owners.set(replacement, props && props.efb ? props.efb.instrument : undefined);
        }
        return replacement;
    };
    plugin.onComponentCreated = function (instance) {
        const result = delegate("onComponentCreated", [instance]);
        const owner = owners.get(instance);
        if (owner || (typeof PayloadViewerComponent === "function" && instance instanceof PayloadViewerComponent)) {
            const instrument = owner || (instance.props && instance.props.efb ? instance.props.efb.instrument : undefined);
            if (instrument && typeof instrument.Update === "function") {
                adapt(instance, instrument);
            }
        }
        return result;
    };
    plugin.onComponentRendered = function (node) {
        return delegate("onComponentRendered", [node]);
    };
    window._pluginSystem = plugin;

    // Report an unavailable payload hook without relying on that hook to initialize.
    function watchStartup(instrument) {
        let attempts = 0;
        let reportedTitle = false;
        function inspect() {
            if (!document.documentElement.contains(instrument)) {
                return;
            }
            if (typeof BaseInstrument !== "undefined" && BaseInstrument.allInstrumentsLoaded
                && typeof SimVar !== "undefined" && typeof SimVar.IsReady === "function" && SimVar.IsReady()) {
                const title = readTitle({ simReady: true });
                const state = states.get(instrument);
                if (title && !reportedTitle) {
                    console.info(`WV081 v${VERSION}: EFB extension loaded; aircraft title: ${title}`);
                    reportedTitle = true;
                }
                if (title && title !== AIRCRAFT_TITLE) {
                    return;
                }
                if (state && state.ready) {
                    return;
                }
                if (title === AIRCRAFT_TITLE && (!state || !state.payloads.length)) {
                    status({ instrument }, `WV081 v${VERSION}: loading limits unavailable — EFB payload controls were not detected.`);
                }
                if (++attempts >= 120) {
                    return;
                }
            }
            setTimeout(inspect, 1000);
        }
        inspect();
    }
    const startupObserver = new MutationObserver(findInstrument);
    function findInstrument() {
        const instrument = document.querySelector("ini-efb-a330");
        if (instrument) {
            startupObserver.disconnect();
            watchStartup(instrument);
        }
    }
    startupObserver.observe(document.documentElement, { childList: true, subtree: true });
    findInstrument();
})();
