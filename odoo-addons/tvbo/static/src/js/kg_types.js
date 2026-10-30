/**
 * The Knowledge Graph's types in one place: each type's label, icon and colours, where it opens in the Experiment Builder, and what its card shows.
 *
 * A card is the title, then the type's byline, the description, its facts and its links, all read from the item the KG API serves. Each fact is one line below, built by a helper: `value` reads a field, `count`, `names` and `copied` read a link (`item.related`), `usedBy` reads the records that link to this one (`item.used_by`). A helper returns nothing when the item lacks what it reads, so a card shows only what its record has; the detail view lists every field regardless.
 */
(function () {
    const filled = v => v !== undefined && v !== null && v !== '' && v !== false && !(Array.isArray(v) && !v.length);
    const lines = v => String(v).split('\n').map(s => s.trim()).filter(Boolean);
    const words = v => String(v).replace(/_/g, ' ');
    /** A time in the item's own unit, to four significant digits; zero means unset and hides the fact. */
    const time = (v, item) => (Number(v) ? `${+Number(v).toPrecision(4)} ${item.related?.time_scale?.names?.[0] || ''}`.trim() : null);
    const listed = (names, count) => names.join(', ') + (count > names.length ? ` +${count - names.length}` : '');

    /** A fact from the field *key*, shown as *label* and the value *format* makes of it; *format* may return nothing to hide the fact. */
    const value = (key, label, format = v => v) => item => {
        const shown = filled(item[key]) ? format(item[key], item) : null;
        return filled(shown) ? { label, value: String(shown) } : null;
    };
    /** A fact that only names *label*, shown when the boolean field *key* is true. */
    const flag = (key, label) => item => (item[key] === true ? { value: label } : null);
    /** A fact from a multi-line text field, each line one entry. */
    const list = (key, label) => value(key, label, v => lines(v).join(', '));
    /** How many records the link *field* holds, as "3 state variables". */
    const count = (field, singular, plural = `${singular}s`) => item => {
        const n = item.related?.[field]?.count;
        return n ? { value: `${n} ${n === 1 ? singular : plural}` } : null;
    };
    /** The names of the records the link *field* holds, each as *format* writes it. */
    const names = (field, label, format = n => n) => item => {
        const linked = item.related?.[field];
        return linked?.names?.length ? { label, value: listed(linked.names.map(format), linked.count) } : null;
    };
    /** A value an experiment's copy changes, as a card writes it: a number to four significant digits, a per-node array by its length. */
    const setting = v => {
        if (typeof v === 'number') return String(+v.toPrecision(4));
        if (typeof v === 'boolean') return v ? 'yes' : 'no';
        if (Array.isArray(v)) return `${v.length} values`;
        return v === null || v === undefined ? 'unset' : String(v);
    };
    /** What an experiment's copy of the record a link *summary* names changes from the library record, as ", with a 0.065 (library 0.1), mu 0.15 (library 0.22)", or an empty string. */
    const changes = summary => (summary?.changes?.length ? `, with ${summary.changes.map(([name, v, library]) => `${name} ${setting(v)} (library ${setting(library)})`).join(', ')}` : '');
    /** The record the link *field* holds, followed by what the experiment's copy of it changes. */
    const copied = (field, label) => item => {
        const fact = names(field, label)(item);
        return fact && { label, value: fact.value + changes(item.related?.[field]) };
    };
    /** The names of the records of KG type *type* that link to this one. */
    const usedBy = (type, label) => item => {
        const linked = item.used_by?.[type];
        return linked?.names?.length ? { label, value: listed(linked.names, linked.count) } : null;
    };
    /** A link from the field *key* to the address *href* makes of it; *href* may return nothing to hide the link. */
    const link = (key, label, href = v => v) => item => {
        const url = filled(item[key]) ? href(item[key]) : null;
        return url ? { label, href: url } : null;
    };

    const doiUrl = doi => (String(doi).startsWith('http') ? doi : `https://doi.org/${doi}`);
    const pubmedUrl = pmid => `https://pubmed.ncbi.nlm.nih.gov/${pmid}/`;
    const isUrl = v => /^https?:\/\//.test(String(v));
    /** "Jansen & Rit (1995)": the authors' family names as a citation gives them (one, two, or the first "et al."), and the year. */
    const citation = item => {
        const family = lines(item.authors || '').map(a => a.split(',')[0].trim());
        const who = family.length > 2 || family.includes('others') ? `${family[0]} et al.` : family.join(' & ');
        const year = item.year > 0 ? String(item.year) : '';
        return who ? who + (year && ` (${year})`) : year || null;
    };

    /** One type's entry: *colors* are the accent and the end of its gradient. */
    const kgType = (label, icon, colors, card = {}) => ({
        label, icon, colors, color: colors[0], gradient: `linear-gradient(135deg, ${colors[0]} 0%, ${colors[1]} 100%)`,
        byline: () => null, facts: [], links: [], equation: false, builder: null, ...card,
    });

    const types = {
        dynamics: kgType('Dynamics', 'fa-solid fa-wave-square', ['#667eea', '#764ba2'], {
            builder: 'dynamics',
            facts: [
                count('state_variables', 'state variable'),
                count('parameters', 'parameter'),
                names('model_type', 'Type', words),
                names('system_type', 'System', words),
                list('references', 'Cites'),
                usedBy('experiment', 'In experiment'),
                value('source', 'Source', v => (isUrl(v) ? null : v)),
            ],
            links: [link('source', 'Source', v => (isUrl(v) ? v : null))],
        }),
        network: kgType('Network', 'fa-solid fa-diagram-project', ['#43e97b', '#38f9d7'], {
            builder: 'network',
            facts: [
                value('number_of_nodes', null, n => `${n} nodes`),
                names('edges', 'Layers'),
                names('parcellation', 'Atlas'),
                names('tractogram', 'Tractogram'),
                value('descriptor', 'Descriptor'),
                usedBy('experiment', 'In experiment'),
            ],
        }),
        coupling: kgType('Coupling', 'fa-solid fa-arrow-right-arrow-left', ['#a18cd1', '#fbc2eb'], {
            builder: 'coupling',
            equation: true,
            facts: [count('parameters', 'parameter'), flag('delayed', 'Delayed'), flag('sparse', 'Sparse'), names('incoming_states', 'Reads'), usedBy('network', 'In network'), usedBy('experiment', 'In experiment')],
        }),
        integrator: kgType('Integrator', 'fa-solid fa-gears', ['#4facfe', '#00f2fe'], {
            builder: 'integration',
            facts: [
                value('step_size', 'Step', time),
                value('number_of_stages', 'Stages'),
                value('duration', 'Duration', time),
                flag('delayed', 'Delays'),
                names('noise', 'Noise'),
                usedBy('experiment', 'In experiment'),
            ],
        }),
        experiment: kgType('Simulation experiment', 'fa-solid fa-flask', ['#fa709a', '#fee140'], {
            builder: 'experiment',
            facts: [
                copied('dynamics', 'Model'),
                copied('network', 'Network'),
                copied('integration', 'Integrator'),
                copied('coupling', 'Coupling'),
                count('observations', 'observation'),
                count('explorations', 'exploration'),
                count('optimizations', 'fit'),
                count('inferences', 'inference'),
                count('continuations', 'continuation'),
            ],
        }),
        study: kgType('Study', 'fa-solid fa-book-open', ['#f7971e', '#ffd200'], {
            byline: citation,
            facts: [
                value('venue', null),
                value('volume', 'Vol.', (v, item) => (item.number ? `${v} (${item.number})` : v)),
                value('pages', 'pp.'),
                value('kind', 'Type'),
                usedBy('dynamics', 'Cited by'),
            ],
            links: [link('doi', 'DOI', doiUrl), link('pmid', 'PubMed', pubmedUrl), link('url', 'Web')],
        }),
        graph_generator: kgType('Graph generator', 'fa-solid fa-circle-nodes', ['#30cfd0', '#330867'], {
            facts: [value('kind', 'Family'), flag('directed', 'Directed'), names('parameters', 'Parameters'), names('bindings', 'Bindings'), value('seed', 'Seed')],
        }),
        continuation: kgType('Continuation', 'fa-solid fa-route', ['#5ee7df', '#b490ca'], {
            facts: [names('dynamics', 'Model'), names('algorithm', 'Algorithm'), names('free_parameters', 'Free parameter'), names('branches', 'Branches'), names('software', 'Software'), usedBy('experiment', 'In experiment')],
        }),
        observation: kgType('Observation', 'fa-solid fa-binoculars', ['#11998e', '#38ef7d'], {
            builder: 'observation',
            equation: true,
            facts: [
                names('imaging_modality', 'Modality', words),
                value('period', 'Period', time),
                names('pipeline', 'Pipeline'),
                names('parameters', 'Parameters'),
                usedBy('experiment', 'In experiment'),
            ],
        }),
        atlas: kgType('Brain atlas', 'fa-solid fa-location-dot', ['#f5576c', '#f093fb'], {
            facts: [value('abbreviation', 'Abbreviation'), names('coordinateSpace', 'Space'), value('versionIdentifier', 'Version'), usedBy('network', 'In network')],
        }),
        software: kgType('Simulation tool', 'fa-solid fa-desktop', ['#6a85b6', '#bac8e0'], {
            byline: item => lines(item.author || item.maintainer || '').slice(0, 2).join(', ') || null,
            facts: [
                value('application_category', 'Category', words),
                names('programming_language', 'Language', words),
                names('tool_role', 'Role', words),
                names('scale', 'Scale', words),
                names('development_status', 'Status', words),
                value('license', 'License'),
                names('interoperates_with', 'Works with'),
            ],
            links: [link('homepage', 'Homepage'), link('repository', 'Code'), link('doi', 'DOI', doiUrl)],
        }),
        ontology: kgType('Ontology term', 'fa-solid fa-graduation-cap', ['#c471f5', '#fa71cd'], {
            facts: [value('is_a', 'Is a', v => [...new Set(v)].join(', ')), value('requires', 'Requires', v => [...new Set(v)].join(', '))],
        }),
    };
    const fallback = kgType('Item', 'fa-solid fa-tag', ['#a0aec0', '#718096']);

    /** Field labels the detail view writes differently from the field's name. */
    const fieldLabels = { kind: 'Type', doi: 'DOI', pmid: 'PMID', url: 'URL', issn: 'ISSN', isbn: 'ISBN', iri: 'IRI', number: 'Issue', venue: 'Published in', voi: 'Variables of interest' };
    /** How the detail view writes a field that needs more than its value: the text, `{ href, text }` for a link, or nothing to leave it out. */
    const fieldFormats = {
        year: v => (v > 0 ? String(v) : null),
        doi: v => ({ href: doiUrl(v), text: v }),
        pmid: v => ({ href: pubmedUrl(v), text: v }),
    };
    const plain = v => {
        if (typeof v === 'boolean') return v ? 'Yes' : 'No';
        if (Array.isArray(v)) return [...new Set(v)].join(', ');
        return isUrl(v) ? { href: v, text: v } : lines(v).join('; ');
    };

    window.KGTypes = {
        types,
        /** The entry for *typeName*, or a neutral one for a type this file does not list. */
        get: typeName => types[String(typeName || '').toLowerCase()] || fallback,
        /** Whether *v* holds something worth showing. */
        filled,
        /** What an experiment's copy changes, as the text that follows the copy's name. */
        changes,
        /** The detail view's label for the field *key*: "number_of_nodes" reads "Number of nodes". */
        label: key => fieldLabels[key] || key.replace(/_/g, ' ').replace(/([a-z])([A-Z])/g, '$1 $2').toLowerCase().replace(/^./, c => c.toUpperCase()),
        /** The detail view's rendering of the field *key* holding *v*: text, `{ href, text }`, or nothing. */
        format: (key, v) => (fieldFormats[key] || plain)(v),
    };
})();
