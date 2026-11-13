import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

/**
 * Country dropdown of a country question on the attendee page.
 *
 * The survey form reads a single-choice answer from the checked radio of its question, so the dropdown writes its choice into one hidden radio and fires the radio's change event; submission, validation and the live-session auto-submit stay Odoo's own. Its keys stay inside it, so Enter or an arrow key while choosing never reaches the form's keyboard navigation.
 */
export class SurveyCountrySelect extends Interaction {
    static selector = ".o_tvbo_country_select";
    dynamicContent = {
        _root: { "t-on-change": this.onChange, "t-on-keydown": (ev) => ev.stopPropagation() },
    };

    onChange() {
        const radio = this.el.parentElement.querySelector("input[type=radio]");
        radio.value = this.el.value;
        radio.checked = Boolean(this.el.value);
        radio.dispatchEvent(new Event("change", { bubbles: true }));
    }
}

registry.category("public.interactions").add("tvbo.survey_country_select", SurveyCountrySelect);
