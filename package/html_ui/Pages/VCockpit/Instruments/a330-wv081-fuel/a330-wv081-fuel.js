// Original WV081 centre-fuel controller and indication prototype, CC BY-NC-SA 4.0.
// Import AFTER the installed WasmInstrument.js. Only the exact WV081 aircraft title is affected.
(() => {
    "use strict";

    const TITLE = "A330 WV081 Community - A330-300 (RR) Baseline";
    const SVG_NS = "http://www.w3.org/2000/svg";
    // Native ECAM colours, sampled from the stock fuel-page element sheet.
    const GREEN = "#60cd63";
    const AMBER = "#ff8a50";
    const EDGE = "#cdced0";
    const PUMP_Y = 265.7; // Centre line of the native -200 centre pump squares, in gauge pixels.
    const TRANSFER_Y = 311.2; // Native -200 transfer line under the centre pumps.
    const states = new WeakMap();

    // Measured on the installed A330-200 (package 0.0.53): each centre pump moves about
    // 3,375 US gal/h into its inner tank, and AUTO transfer starts 2,000 kg below inner capacity.
    const PUMP_GALLONS_PER_SECOND = 3375 / 3600;
    const REFILL_BELOW_FULL_KG = 2000;
    const FULL_MARGIN_KG = 50;
    // A330-200 refuel schedule above full wings: trim from 2,400 kg towards capacity, the rest in centre.
    const TRIM_BASE_KG = 2400;
    // TCDS A330-300 3-tank: 83 L of centre fuel is unusable.
    const CENTRE_UNUSABLE_GALLONS = 22;
    // The stock systems overwrite tank changes unless total fuel moves by more than about 50 kg
    // (measured: 15 gal kept stock values, 20 gal was adopted). Every write step must exceed that.
    const ADOPT_GALLONS = 25;
    const DIP_GALLONS = 50;
    const CHUNK_GALLONS = 25;
    const CONTROL_PERIOD_S = 0.25;
    const ADOPT_TIMEOUT_S = 5;
    const MAX_RETRIES = 8;
    const TANKS = ["LEFT MAIN", "RIGHT MAIN", "LEFT AUX", "RIGHT AUX", "EXTERNAL1", "CENTER"];
    // The stock fuel loop checks about twice a second; its own tank weights show what it kept.
    const REPORTED = {
        "LEFT MAIN": "INI_FUEL_WEIGHT_LEFT_INNER", "RIGHT MAIN": "INI_FUEL_WEIGHT_RIGHT_INNER",
        "LEFT AUX": "INI_FUEL_WEIGHT_LEFT_OUTER", "RIGHT AUX": "INI_FUEL_WEIGHT_RIGHT_OUTER",
        "EXTERNAL1": "INI_FUEL_WEIGHT_TRIM", "CENTER": "INI_FUEL_WEIGHT_CENTER",
    };
    const controller = {
        lastTime: NaN, nextTime: -Infinity, remaining: null, targets: null, steps: [], check: null, retries: 0, onDone: null,
        dueLeft: 0, dueRight: 0, activeLeft: false, activeRight: false,
        refuelSequence: NaN, published: {},
    };

    if (typeof WasmInstrument === "undefined" || WasmInstrument.prototype.wv081CentreOverlay) {
        return;
    }

    function read(name, unit = "number") {
        const value = SimVar.GetSimVarValue(name, unit);
        return typeof value === "number" && Number.isFinite(value) ? value : NaN;
    }

    function local(name) {
        return read("L:" + name);
    }

    function quantity(tank) {
        return read("FUEL TANK " + tank + " QUANTITY", "gallons");
    }

    function capacity(tank) {
        return read("FUEL TANK " + tank + " CAPACITY", "gallons");
    }

    function publish(name, value) {
        if (controller.published[name] !== value) {
            controller.published[name] = value;
            SimVar.SetSimVarValue("L:" + name, "number", value);
        }
    }

    // Split tank changes (gallons) into write steps that each change total fuel enough to be adopted.
    function plan(changes) {
        const tanks = Object.keys(changes).filter(tank => Math.abs(changes[tank]) >= 0.05);
        const pick = list => list.reduce((step, tank) => { step[tank] = changes[tank]; return step; }, {});
        const sum = list => list.reduce((total, tank) => total + changes[tank], 0);
        const negative = tanks.filter(tank => changes[tank] < 0);
        const positive = tanks.filter(tank => changes[tank] > 0);
        if (!tanks.length) {
            return [];
        }
        if (Math.abs(sum(tanks)) >= ADOPT_GALLONS) {
            return [pick(tanks)];
        }
        if (-sum(negative) >= ADOPT_GALLONS && sum(positive) >= ADOPT_GALLONS) {
            return [pick(negative), pick(positive)];
        }
        // Small redistribution: lower the fullest tank first so the final write raises the total.
        const reservoir = TANKS.reduce((best, tank) => quantity(tank) > quantity(best) ? tank : best, TANKS[0]);
        const final = pick(tanks);
        final[reservoir] = (final[reservoir] || 0) + DIP_GALLONS;
        return [{ [reservoir]: -DIP_GALLONS }, final];
    }

    // Absolute targets (refuelling) are re-planned from the current split after any rejection, so a
    // stock load landing in between can never be added twice.
    function begin(changes, onDone, targets) {
        controller.remaining = Object.assign({}, changes);
        controller.targets = targets || null;
        controller.steps = plan(changes);
        controller.retries = 0;
        controller.onDone = onDone || null;
    }

    function finishIfDone() {
        if (controller.remaining && !controller.steps.length) {
            const done = controller.onDone;
            controller.remaining = controller.onDone = controller.targets = null;
            if (done) {
                done();
            }
        }
    }

    // Tank quantity as held by the stock fuel loop, which overwrites any value it has not adopted.
    function reported(tank, kilogramsPerGallon) {
        return local(REPORTED[tank]) / kilogramsPerGallon;
    }

    function writeStep(now, kilogramsPerGallon) {
        const step = controller.steps[0];
        const before = {};
        for (const tank of Object.keys(step)) {
            before[tank] = reported(tank, kilogramsPerGallon);
            if (!Number.isFinite(before[tank])) {
                controller.steps = [];
                controller.remaining = controller.onDone = controller.targets = null;
                publish("WV081_CTR_STATUS", 2);
                return;
            }
        }
        controller.check = { step, before, at: now };
        Object.keys(step).forEach(tank => {
            SimVar.SetSimVarValue("FUEL TANK " + tank + " QUANTITY", "gallons", Math.max(0, before[tank] + step[tank]));
        });
    }

    // Book only the changes the stock fuel loop kept; anything it overwrote is planned again.
    function verifyStep(now, kilogramsPerGallon) {
        const { step, before, at } = controller.check;
        const tanks = Object.keys(step);
        const kept = tanks.filter(tank => (reported(tank, kilogramsPerGallon) - before[tank]) / step[tank] > 0.5);
        if (kept.length < tanks.length && now - at < ADOPT_TIMEOUT_S) {
            return;
        }
        const complete = kept.length === tanks.length;
        controller.check = null;
        kept.forEach(tank => {
            controller.remaining[tank] = (controller.remaining[tank] || 0) - step[tank];
        });
        if (complete) {
            controller.steps.shift();
            controller.retries = 0;
            publish("WV081_CTR_STATUS", 0);
        } else {
            controller.steps = plan(controller.targets ? towards(controller.targets, kilogramsPerGallon) : controller.remaining);
            controller.retries += 1;
            if (controller.retries >= MAX_RETRIES) {
                publish("WV081_CTR_STATUS", 1);
            }
        }
        finishIfDone();
    }

    function towards(targets, kilogramsPerGallon) {
        return Object.keys(targets).reduce((changes, tank) => {
            changes[tank] = targets[tank] - reported(tank, kilogramsPerGallon);
            return changes;
        }, {});
    }

    // A330-200 split of a request above full wings: trim from 2,400 kg towards capacity, the rest in centre.
    function refuelTargets(requestKg, kilogramsPerGallon) {
        const wingGallons = ["LEFT MAIN", "RIGHT MAIN", "LEFT AUX", "RIGHT AUX"].map(capacity);
        const trimCapacity = capacity("EXTERNAL1");
        const centreCapacity = capacity("CENTER");
        const wingsKg = wingGallons.reduce((sum, value) => sum + value, 0) * kilogramsPerGallon;
        const lower = wingsKg + TRIM_BASE_KG;
        const upper = wingsKg + (trimCapacity + centreCapacity) * kilogramsPerGallon;
        if (!(requestKg > lower) || !(centreCapacity > 0) || !(upper > lower)) {
            return null;
        }
        const total = Math.min(requestKg, upper);
        const trimKg = TRIM_BASE_KG + (total - lower) / (upper - lower) * (trimCapacity * kilogramsPerGallon - TRIM_BASE_KG);
        const gallons = wingGallons.concat([trimKg / kilogramsPerGallon, (total - wingsKg - trimKg) / kilogramsPerGallon]);
        return TANKS.reduce((result, tank, index) => {
            result[tank] = gallons[index];
            return result;
        }, {});
    }

    // The WV081 EFB hands loads above full wings to this controller instead of the stock loader, which
    // would overfill the trim tank. Each request carries a new sequence value; gradual EFB loads send one
    // per step, and only the latest is placed once the current step completes.
    function handleRefuel(kilogramsPerGallon) {
        const sequence = local("WV081_FUEL_TARGET_SEQ");
        if (!(sequence > 0) || sequence === controller.refuelSequence) {
            return false;
        }
        controller.refuelSequence = sequence;
        const requestKg = local("WV081_FUEL_TARGET_KG");
        const targets = refuelTargets(requestKg, kilogramsPerGallon);
        if (!targets) {
            return false;
        }
        // The stock loader records each load here; keep that record correct for the routed amount.
        SimVar.SetSimVarValue("L:INI_TOTAL_FUEL_WEIGHT", "number", requestKg);
        controller.dueLeft = controller.dueRight = 0;
        begin(towards(targets, kilogramsPerGallon), null, targets);
        return true;
    }

    function updateSide(side, pump, autoAllowed, innerKg, fullKg, centreGallons, dt) {
        const key = side === "LEFT" ? "Left" : "Right";
        let active = controller["active" + key];
        if (!pump || !autoAllowed || !(centreGallons > CENTRE_UNUSABLE_GALLONS)) {
            active = false;
        } else if (!active && innerKg <= fullKg - REFILL_BELOW_FULL_KG) {
            active = true;
        } else if (active && innerKg >= fullKg - FULL_MARGIN_KG) {
            active = false;
        }
        controller["active" + key] = active;
        if (active) {
            controller["due" + key] += PUMP_GALLONS_PER_SECOND * dt;
        }
        publish("WV081_CTR_" + side.charAt(0) + "_PUMP_ON", pump ? 1 : 0);
        publish("WV081_CTR_" + side.charAt(0) + "_FEEDING", active ? 1 : 0);
    }

    function runController() {
        const now = read("E:SIMULATION TIME", "seconds");
        if (!(now >= controller.nextTime)) {
            return;
        }
        controller.nextTime = now + CONTROL_PERIOD_S;
        const kilogramsPerGallon = read("FUEL WEIGHT PER GALLON", "kilograms");
        if (!(kilogramsPerGallon > 0)) {
            return;
        }
        if (controller.check) {
            verifyStep(now, kilogramsPerGallon);
            return;
        }
        if (controller.steps.length) {
            writeStep(now, kilogramsPerGallon);
            return;
        }
        if (handleRefuel(kilogramsPerGallon)) {
            return;
        }
        // Credit pump flow for the whole interval, including ticks spent writing and verifying.
        const dt = Math.min(Math.max(now - controller.lastTime, 0), 5) || 0;
        controller.lastTime = now;
        const centre = quantity("CENTER");
        const usable = Math.max(0, centre - CENTRE_UNUSABLE_GALLONS);
        const phase = local("INI_flight_phase");
        // The stock -200 logic needs the manual XFR selection up to the takeoff phase.
        const autoAllowed = phase > 2 || local("INI_CENTER_TANK_FUEL_XFR") === 1;
        const sides = [["LEFT", "LEFT MAIN", "INI_CENTER_TANK_LEFT", "INI_ELEC_AC_BUS_1_IS_POWERED"],
            ["RIGHT", "RIGHT MAIN", "INI_CENTER_TANK_RIGHT", "INI_ELEC_AC_BUS_2_IS_POWERED"]];
        const room = {};
        for (const [side, tank, button, bus] of sides) {
            const inner = quantity(tank);
            const full = capacity(tank);
            room[side] = Math.max(0, full - FULL_MARGIN_KG / kilogramsPerGallon - inner);
            updateSide(side, local(button) === 1 && local(bus) === 1, autoAllowed,
                inner * kilogramsPerGallon, full * kilogramsPerGallon, centre, dt);
        }
        const left = Math.min(controller.dueLeft, room.LEFT);
        const right = Math.min(controller.dueRight, room.RIGHT);
        // Batch transfers so each verified step clearly exceeds engine burn; flush the rest when flow stops.
        if ((controller.activeLeft || controller.activeRight) && left + right < Math.min(CHUNK_GALLONS, usable)) {
            return;
        }
        controller.dueLeft = controller.dueRight = 0;
        const scale = left + right > usable ? usable / (left + right) : 1;
        const moveLeft = left * scale;
        const moveRight = right * scale;
        if (moveLeft + moveRight > 0.5) {
            begin({ "CENTER": -(moveLeft + moveRight), "LEFT MAIN": moveLeft, "RIGHT MAIN": moveRight });
        }
    }

    function add(parent, tag, attributes, text) {
        const element = document.createElementNS(SVG_NS, tag);
        Object.keys(attributes).forEach(key => element.setAttribute(key, attributes[key]));
        if (text !== undefined) {
            element.textContent = text;
        }
        parent.appendChild(element);
        return element;
    }

    // Original drawing of the -200 centre section, measured against the live stock -200 page in gauge
    // pixels. The native page draws its 768-pixel background about 6 px right of the gauge origin.
    function createLayer(instrument) {
        const frame = instrument.querySelector("#Mainframe");
        if (!frame) {
            return null;
        }
        const svg = add(frame, "svg", {
            viewBox: "0 0 780 780", preserveAspectRatio: "none",
            "aria-label": "Experimental centre fuel indications"
        });
        svg.style.cssText = "position:absolute;left:0;top:0;width:100%;height:100%;"
            + "pointer-events:none;z-index:1;display:none;";
        // The private build copies the installed A330 ECAM font next to this script.
        add(svg, "style", {}, "@font-face{font-family:'WV081 ECAM';"
            + "src:url('/Pages/VCockpit/Instruments/a330-wv081-fuel/inidisplayini-regular.ttf');}");
        add(svg, "line", { x1: 313, y1: 367, x2: 474, y2: 367, stroke: EDGE, "stroke-width": 4 });
        const pumps = [366.3, 413.7].map(centre => {
            const group = add(svg, "g", { fill: "none", "stroke-width": 2 });
            const box = add(group, "rect", { x: centre - 20.5, y: PUMP_Y - 20.5, width: 41, height: 41 });
            const bar = add(group, "line", {});
            return { centre, box, bar };
        });
        const transfer = add(svg, "line", { x1: 348, y1: TRANSFER_Y, x2: 432, y2: TRANSFER_Y, "stroke-width": 2 });
        const quantity = add(svg, "text", {
            x: 388.6, y: 352.6, "font-size": 23, "font-family": "'WV081 ECAM', Roboto, sans-serif",
            "text-anchor": "middle", fill: GREEN, stroke: GREEN, "stroke-width": 0.4 // Native digit weight.
        }, "---");
        return { svg, pumps, transfer, quantity };
    }

    // Selected and powered pumps are green, otherwise amber. While transferring the bar turns in line
    // and runs down to the transfer line, as on the -200 page.
    function showPump(pump, available, transferring) {
        const colour = available ? GREEN : AMBER;
        pump.box.setAttribute("stroke", colour);
        pump.bar.setAttribute("stroke", colour);
        const attributes = transferring
            ? { x1: pump.centre, y1: PUMP_Y - 20.5, x2: pump.centre, y2: TRANSFER_Y }
            : { x1: pump.centre - 14, y1: PUMP_Y, x2: pump.centre + 14, y2: PUMP_Y };
        Object.keys(attributes).forEach(key => pump.bar.setAttribute(key, attributes[key]));
    }

    function isFuelPageVisible(instrument) {
        const canvas = instrument.m_wasmSimCanvas;
        const nativeImage = canvas && canvas.m_imgElement;
        if (!nativeImage || !nativeImage.parentNode || !nativeImage.getAttribute("src")) {
            return false;
        }
        // Normal display configuration only; do not cover video, swaps, failed or unpowered screens.
        return local("INI_IS_200") === 0
            && local("INI_ECAM_ACTIVE_PAGE") === 8
            && local("ECAM_CURRENT_STATUS") > 0
            && local("INI_ECAM_VALID") === 0 // Stock: 0 normal, 1 self-test, 2 invalid data.
            && local("INI_ELEC_AC_BUS_1_IS_POWERED") === 1
            && local("ECAM_BRIGHTNESS_ACT") > 0
            && local("INI_ECAM_DMC_MODE") === 1
            && local("INI_ECAM_ND_NORM_MODE") === 1
            && local("INI_EWD_ECAM_TFR") === 0
            && local("INI_ECAM_OVERRIDE_EWD") === 0
            && local("INI_ECAM_VIDEO_STATE") === 0;
    }

    function updateLayer(instrument) {
        let state = states.get(instrument);
        if (!isFuelPageVisible(instrument)) {
            if (state) {
                state.svg.style.display = "none";
            }
            return;
        }
        if (!state) {
            state = createLayer(instrument);
            if (!state) {
                return;
            }
            states.set(instrument, state);
        }
        const gallons = read("FUEL TANK CENTER QUANTITY", "gallons");
        const kilogramsPerGallon = read("FUEL WEIGHT PER GALLON", "kilograms");
        const metric = local("INI_IS_METRIC");
        const kilograms = gallons * kilogramsPerGallon;
        const validQuantity = Number.isFinite(kilograms) && gallons >= 0 && kilogramsPerGallon > 0;
        const unitKnown = metric === 0 || metric === 1;
        const quantity = metric === 0 ? kilograms * 2.20462 : kilograms;
        const fault = local("WV081_CTR_STATUS") > 0;
        state.quantity.textContent = validQuantity && unitKnown ? String(Math.round(quantity / 10) * 10) : "XX";
        const quantityColour = fault || !(validQuantity && unitKnown) ? AMBER : GREEN;
        state.quantity.setAttribute("fill", quantityColour);
        state.quantity.setAttribute("stroke", quantityColour);
        // Transfer states come from this controller; the stock -300 clears its own centre flags.
        const leftFeeding = local("WV081_CTR_L_FEEDING") === 1;
        const rightFeeding = local("WV081_CTR_R_FEEDING") === 1;
        showPump(state.pumps[0], local("WV081_CTR_L_PUMP_ON") === 1, leftFeeding);
        showPump(state.pumps[1], local("WV081_CTR_R_PUMP_ON") === 1, rightFeeding);
        state.transfer.setAttribute("stroke", leftFeeding || rightFeeding ? GREEN : "none");
        state.svg.style.display = "block";
    }

    function scoped(instrument, gauge) {
        const config = instrument.urlConfig;
        return config && typeof config.wasmModule === "string"
            && config.wasmModule.toLowerCase() === "inibuilds-a330.wasm"
            && String(config.wasmGauge).toLowerCase() === gauge // The simulator lowercases gauge names.
            && SimVar.GetSimVarValue("TITLE", "string") === TITLE;
    }

    const stockUpdate = WasmInstrument.prototype.Update;
    WasmInstrument.prototype.Update = function (...args) {
        const result = stockUpdate.apply(this, args);
        try {
            if (scoped(this, "systems")) {
                runController();
            } else if (scoped(this, "ecam")) {
                updateLayer(this);
            } else {
                const state = states.get(this);
                if (state) {
                    state.svg.style.display = "none";
                }
            }
        } catch (_) {
            const state = states.get(this);
            if (state) {
                state.svg.style.display = "none";
            }
        }
        return result;
    };
    WasmInstrument.prototype.wv081CentreOverlay = true;
})();
