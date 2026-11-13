import { SurveySessionChart } from "@survey/interactions/survey_session_chart";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { Interaction } from "@web/public/interaction";

const MAP_URL = "/tvbo/static/src/img/world_map.svg";
let mapSvg;

/** The world map's SVG text, fetched once per page. */
function loadMap() {
    mapSvg ??= fetch(MAP_URL).then((response) => {
        if (!response.ok) {
            throw new Error(`World map not loaded: ${response.status} ${MAP_URL}`);
        }
        return response.text();
    });
    return mapSvg;
}

/** Reads a TVB-O design token from survey_live.css. */
const token = (el, name) => getComputedStyle(el).getPropertyValue(`--tvbo-${name}`).trim();

patch(SurveySessionChart, { selector: ".o_survey_session_chart:not(.o_tvbo_session_map)" });
patch(SurveySessionChart.prototype, {
    /**
     * Horizontal bars in the TVB-O accent, so every answer reads as one flat line beside its bar on a shared screen; Odoo's label wrapping for upright bars is dropped, its counts, colours and animations are kept.
     */
    buildChartConfiguration() {
        const config = super.buildChartConfiguration();
        const ink = token(this.el, "ink");
        this.accentRgb = token(this.el, "accent-rgb");
        config.plugins = config.plugins.filter((plugin) => plugin.id); // keeps datalabels, drops the anonymous label wrapper
        config.data.datasets[0].borderRadius = 6;
        config.data.datasets[0].maxBarThickness = 56;
        Object.assign(config.options, {
            indexAxis: "y",
            layout: { padding: { right: 72 } },
            scales: {
                x: { display: false, beginAtZero: true },
                y: {
                    grid: { display: false },
                    border: { display: false },
                    ticks: { color: ink, autoSkip: false, padding: 16, font: { family: token(this.el, "text"), size: 28 } },
                },
            },
        });
        Object.assign(config.options.plugins.datalabels, {
            anchor: "end",
            align: "right",
            font: { family: token(this.el, "display"), size: 36, weight: 700 },
        });
        return config;
    },

    /** A wrong answer of a scored question stays faded, as in Odoo. */
    getBackgroundColor(metaData) {
        const faded = this.showAnswers && this.hasCorrectAnswers && !this.isValidAnswer(metaData.dataIndex);
        return `rgba(${this.accentRgb},${faded ? 0.2 : 1})`;
    },
});

/**
 * World map that stands in for the bar chart of a country question on the host screen of a live session.
 *
 * It takes the place of the native chart interaction: the session manager dispatches the same ``updateState`` events (``showInputs`` and the latest ``questionStatistics``) to it and waits for the same start signal. Each answered country is filled and carries a bubble whose area grows with its count, and the ranking beside the map gives every answered country its number, including the territories Natural Earth draws as part of another country; ``data-country-codes`` lists the ISO codes in answer order, the order of the statistics.
 */
export class SurveySessionMap extends Interaction {
    static selector = ".o_tvbo_session_map";
    dynamicContent = {
        _root: {
            "t-on-updateState": this.updateState,
            "t-att-class": () => ({ chart_is_ready: this.mapReady }),
        },
    };

    setup() {
        this.mapReady = false;
        this.showInputs = false;
        this.codes = JSON.parse(this.el.dataset.countryCodes);
        this.points = JSON.parse(this.el.closest(".o_survey_session_manage").dataset.questionStatistics);
    }

    async willStart() {
        this.svgText = await loadMap();
    }

    start() {
        this.el.innerHTML = `${this.svgText}<ol class="o_tvbo_country_ranking"></ol>`;
        this.mapReady = true;
        this.env.bus.trigger("SURVEY:CHART_INTERACTION_STARTED");
    }

    updateState(ev) {
        if ("showInputs" in ev.detail) {
            this.showInputs = ev.detail.showInputs;
        }
        if (ev.detail.questionStatistics) {
            this.points = ev.detail.questionStatistics;
        }
        this.draw();
    }

    draw() {
        const answered = this.showInputs
            ? this.points
                  .map((point, index) => ({ ...point, code: this.codes[index] }))
                  .filter((point) => point.code && point.count)
                  .sort((a, b) => b.count - a.count || a.text.localeCompare(b.text))
            : [];
        const byCode = Object.fromEntries(answered.map((point) => [point.code, point.count]));
        const maxCount = Math.max(1, ...answered.map((point) => point.count));
        for (const path of this.el.querySelectorAll(".o_tvbo_world_land path")) {
            path.classList.toggle("o_tvbo_answered", Boolean(byCode[path.dataset.code]));
        }
        const anchors = this.el.querySelector(".o_tvbo_world_anchors");
        for (const anchor of anchors.querySelectorAll("circle")) {
            const count = byCode[anchor.dataset.code];
            anchor.setAttribute("r", count ? 6 + 18 * Math.sqrt(count / maxCount) : 0);
        }
        for (const point of answered) {
            const anchor = anchors.querySelector(`circle[data-code="${point.code}"]`);
            if (anchor) {
                anchors.append(anchor); // smaller bubbles paint over larger neighbours
            }
        }
        this.el.querySelector(".o_tvbo_country_ranking").replaceChildren(
            ...answered.map((point) => {
                const item = document.createElement("li");
                const name = document.createElement("span");
                const count = document.createElement("strong");
                name.textContent = point.text;
                count.textContent = point.count;
                item.append(name, count);
                return item;
            })
        );
    }
}

registry.category("public.interactions").add("tvbo.survey_session_map", SurveySessionMap);
