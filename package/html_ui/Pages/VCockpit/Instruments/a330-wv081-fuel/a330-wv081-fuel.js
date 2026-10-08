// Original WV081 centre indication prototype, CC BY-NC-SA 4.0.
// Import AFTER the installed WasmInstrument.js. This layer only reads simulator state.
(() => {
    "use strict";

    const TITLE = "A330 WV081 Community - A330-300 (RR) Baseline";
    const SVG_NS = "http://www.w3.org/2000/svg";
    const WHITE = "#d2dddd";
    const GREEN = "#00ff00";
    const states = new WeakMap();

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

    function add(parent, tag, attributes, text) {
        const element = document.createElementNS(SVG_NS, tag);
        Object.keys(attributes).forEach(key => element.setAttribute(key, attributes[key]));
        if (text !== undefined) {
            element.textContent = text;
        }
        parent.appendChild(element);
        return element;
    }

    function createLayer(instrument) {
        const frame = instrument.querySelector("#Mainframe");
        if (!frame) {
            return null;
        }
        const svg = add(frame, "svg", {
            viewBox: "0 0 768 768", preserveAspectRatio: "none",
            "aria-label": "Experimental centre fuel indications"
        });
        svg.style.cssText = "position:absolute;left:0;top:0;width:100%;height:100%;"
            + "pointer-events:none;z-index:1;display:none;";
        // This small original inset occupies the unused centre of the stock -300 fuel diagram.
        const group = add(svg, "g", {
            "font-family": "monospace", "text-anchor": "middle", fill: WHITE
        });
        add(group, "rect", { x: 319, y: 240, width: 130, height: 111, fill: "black", stroke: WHITE, "stroke-width": 1.5 });
        add(group, "text", { x: 384, y: 256, "font-size": 12 }, "CTR NOT ACTIVE");
        const quantity = add(group, "text", { x: 384, y: 281, "font-size": 21, fill: GREEN }, "---");
        const units = add(group, "text", { x: 384, y: 298, "font-size": 12 }, "KG");
        const leftPump = add(group, "text", { x: 352, y: 320, "font-size": 13 }, "L:---");
        const rightPump = add(group, "text", { x: 416, y: 320, "font-size": 13 }, "R:---");
        const leftFeed = add(group, "text", { x: 352, y: 340, "font-size": 11 }, "---");
        const rightFeed = add(group, "text", { x: 416, y: 340, "font-size": 11 }, "---");
        return { svg, quantity, units, leftPump, rightPump, leftFeed, rightFeed };
    }

    function showState(element, prefix, value, onText, offText) {
        element.textContent = prefix + (value === 1 ? onText : value === 0 ? offText : "---");
        element.setAttribute("fill", value === 1 ? GREEN : WHITE);
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
            && local("INI_ECAM_VALID") === 1
            && local("INI_ELEC_AC_BUS_1_IS_POWERED") === 1
            && local("ECAM_BRIGHTNESS_ACT") > 0
            && local("INI_ECAM_DMC_MODE") === 1
            && local("INI_ECAM_ND_NORM_MODE") === 1
            && local("INI_EWD_ECAM_TFR") === 0
            && local("INI_ECAM_OVERRIDE_EWD") === 0
            && local("INI_ECAM_VIDEO_STATE") === 0
            && local("INI_CKPT_DOOR_VIDEO") === 0;
    }

    function updateLayer(instrument) {
        let state = states.get(instrument);
        const config = instrument.urlConfig;
        const scoped = config && typeof config.wasmModule === "string"
            && config.wasmModule.toLowerCase() === "inibuilds-a330.wasm"
            && config.wasmGauge === "ECAM"
            && SimVar.GetSimVarValue("TITLE", "string") === TITLE;
        if (!scoped || !isFuelPageVisible(instrument)) {
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
        state.quantity.textContent = validQuantity && unitKnown ? String(Math.round(quantity)) : "---";
        state.units.textContent = metric === 1 ? "KG" : metric === 0 ? "LB" : "---";
        showState(state.leftPump, "L:", local("INI_CENTER_TANK_LEFT_PUMP_ON"), "ON", "OFF");
        showState(state.rightPump, "R:", local("INI_CENTER_TANK_RIGHT_PUMP_ON"), "ON", "OFF");
        // Feed indications reflect the stock state; pump selection alone must never imply transfer.
        showState(state.leftFeed, "", local("INI_CENTER_TANK_LEFT_FEEDING"), "FEED", "NO FEED");
        showState(state.rightFeed, "", local("INI_CENTER_TANK_RIGHT_FEEDING"), "FEED", "NO FEED");
        state.svg.style.display = "block";
    }

    const stockUpdate = WasmInstrument.prototype.Update;
    WasmInstrument.prototype.Update = function (...args) {
        const result = stockUpdate.apply(this, args);
        try {
            updateLayer(this);
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
