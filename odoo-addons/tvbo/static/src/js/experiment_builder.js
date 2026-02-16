// ============================================================================
// TVBO Experiment Builder for Odoo Platform
// ============================================================================
// Comprehensive interactive builder for SimulationExperiment specifications
// Aligned with TVBO schema: https://w3id.org/tvbo
// ============================================================================

(function () {
  const STATE = {
    dataLoaded: false,
    data: [],
    lastFullModelSpec: null,
    previewEnabled: false,
    functions: {}, // Reusable function definitions
    observations: {}, // Observation specifications
    derivedObservations: {}, // Derived observations
    algorithms: {}, // Iterative tuning algorithms (FIC, EIB, etc.)
    optimizations: [], // Optimization stages
    explorations: [], // Parameter exploration specs
    execution: {} // Execution configuration
  };

  const DEBUG = true;
  const log = (...args) => { if (DEBUG && console && console.log) console.log('[ExperimentBuilder]', ...args); };

  // Global error handler to help debug issues
  window.addEventListener('error', function(event) {
    console.error('[ExperimentBuilder] Global error caught:', event.message, 'at', event.filename, ':', event.lineno);
  });

  function initializeBuilder() {
    try {
      // Load data
      STATE.data = window.searchData || [];
      STATE.dataLoaded = true;
      log('Initializing builder with data:', { count: STATE.data.length });

      const content = document.getElementById('builderContent');
      if (content) {
        renderBuilder(content);
      }
    } catch (err) {
      console.error('[ModelBuilder] Error in initializeBuilder:', err);
    }
  }

  // Expose to global scope
  window.initializeBuilder = initializeBuilder;

  function renderBuilder(root) {
    const data = STATE.data || [];
    log('Rendering builder with data count:', data.length);
    const models = data;
    log('Models available:', models.length);

    // Initialize dynamics list in STATE
    STATE.dynamicsModels = STATE.dynamicsModels || [];

    root.innerHTML = `
      <h5 class="mb-3" style="color: #1f2937;">Local Dynamics</h5>
      
      <!-- Dynamics Models List -->
      <div id="dynamicsModelsList"></div>
      
      <!-- Add Model Button -->
      <div class="mb-3">
        <button class="btn btn-outline-primary" id="addDynamicsModel">+ Add Dynamics Model</button>
      </div>
      
      <!-- Model Editor (shown when editing a model) -->
      <div id="modelEditor" style="display: none;">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <span id="editorTitle">Edit Model</span>
            <div>
              <span id="editorLoading" class="spinner-border spinner-border-sm text-primary me-2" role="status" style="display: none;"></span>
              <button class="btn btn-sm btn-outline-secondary" id="closeEditor">✕ Close</button>
            </div>
          </div>
          <div class="card-body">
            <!-- Model Source Selection -->
            <div class="mb-3">
              <label class="form-label fw-bold">Base Model</label>
              <select id="editorBaseModel" class="form-select">
                <option value="">— Start from scratch —</option>
                ${models.map(m => `<option value="${m.id}" data-name="${escapeAttr(m.name || '')}">${escapeHtml(m.label || m.name)}</option>`).join('')}
              </select>
              <small class="text-muted">Select a base model to customize, or start from scratch.</small>
            </div>
            
            <!-- Basic Info -->
            <div class="row mb-3">
              <div class="col-md-4">
                <label class="form-label">Name <span class="text-danger">*</span></label>
                <input type="text" id="editorModelName" class="form-control" placeholder="e.g., ReducedWongWang"/>
              </div>
              <div class="col-md-4">
                <label class="form-label">Label</label>
                <input type="text" id="editorModelLabel" class="form-control" placeholder="Display label"/>
              </div>
              <div class="col-md-4">
                <label class="form-label">System Type</label>
                <select id="editorSystemType" class="form-select">
                  <option value="continuous">Continuous (ODE/SDE)</option>
                  <option value="discrete">Discrete (Maps)</option>
                </select>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label">Description</label>
              <textarea id="editorDescription" class="form-control" rows="2" placeholder="Model description..."></textarea>
            </div>
            <div class="mb-3">
              <label class="form-label">References</label>
              <input type="text" id="editorReferences" class="form-control" placeholder="DOI or publication references"/>
            </div>
            
            <!-- Accordion for sections -->
            <div class="accordion" id="dynamicsAccordion">
              <!-- Parameters Section -->
              <div class="accordion-item">
                <h2 class="accordion-header">
                  <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#paramsSection">
                    Parameters <span class="badge bg-secondary ms-2" id="paramsCount">0</span>
                  </button>
                </h2>
                <div id="paramsSection" class="accordion-collapse collapse show">
                  <div class="accordion-body">
                    <div class="row g-2 mb-1 small text-muted fw-bold">
                      <div class="col-2">Name</div>
                      <div class="col-1">Symbol</div>
                      <div class="col-2">Value</div>
                      <div class="col-1">Unit</div>
                      <div class="col-1">Min</div>
                      <div class="col-1">Max</div>
                      <div class="col-3">Description</div>
                      <div class="col-1"></div>
                    </div>
                    <div id="editorParamsContainer"></div>
                    <button class="btn btn-sm btn-outline-secondary mt-2" id="addEditorParam">+ Add Parameter</button>
                  </div>
                </div>
              </div>
              
              <!-- State Variables Section -->
              <div class="accordion-item">
                <h2 class="accordion-header">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#stateVarsSection">
                    State Variables <span class="badge bg-secondary ms-2" id="stateVarsCount">0</span>
                  </button>
                </h2>
                <div id="stateVarsSection" class="accordion-collapse collapse">
                  <div class="accordion-body">
                    <div class="row g-2 mb-1 small text-muted fw-bold">
                      <div class="col-2">Name</div>
                      <div class="col-4">Equation (dX/dt = ...)</div>
                      <div class="col-1">Initial</div>
                      <div class="col-1">Unit</div>
                      <div class="col-3">Options</div>
                      <div class="col-1"></div>
                    </div>
                    <div id="editorStateVarsContainer"></div>
                    <button class="btn btn-sm btn-outline-secondary mt-2" id="addEditorStateVar">+ Add State Variable</button>
                  </div>
                </div>
              </div>
              
              <!-- Derived Parameters Section -->
              <div class="accordion-item">
                <h2 class="accordion-header">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#derivedParamsSection">
                    Derived Parameters <span class="badge bg-secondary ms-2" id="derivedParamsCount">0</span>
                  </button>
                </h2>
                <div id="derivedParamsSection" class="accordion-collapse collapse">
                  <div class="accordion-body">
                    <div class="row g-2 mb-1 small text-muted fw-bold">
                      <div class="col-2">Name</div>
                      <div class="col-6">Expression</div>
                      <div class="col-1">Unit</div>
                      <div class="col-2">Description</div>
                      <div class="col-1"></div>
                    </div>
                    <div id="editorDerivedParamsContainer"></div>
                    <button class="btn btn-sm btn-outline-secondary mt-2" id="addEditorDerivedParam">+ Add Derived Parameter</button>
                  </div>
                </div>
              </div>
              
              <!-- Derived Variables Section -->
              <div class="accordion-item">
                <h2 class="accordion-header">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#derivedVarsSection">
                    Derived Variables <span class="badge bg-secondary ms-2" id="derivedVarsCount">0</span>
                  </button>
                </h2>
                <div id="derivedVarsSection" class="accordion-collapse collapse">
                  <div class="accordion-body">
                    <div class="row g-2 mb-1 small text-muted fw-bold">
                      <div class="col-2">Name</div>
                      <div class="col-6">Expression</div>
                      <div class="col-1">Unit</div>
                      <div class="col-2">Description</div>
                      <div class="col-1"></div>
                    </div>
                    <div id="editorDerivedVarsContainer"></div>
                    <button class="btn btn-sm btn-outline-secondary mt-2" id="addEditorDerivedVar">+ Add Derived Variable</button>
                  </div>
                </div>
              </div>
              
              <!-- Functions Section -->
              <div class="accordion-item">
                <h2 class="accordion-header">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#functionsSection">
                    Functions <span class="badge bg-secondary ms-2" id="functionsCount">0</span>
                  </button>
                </h2>
                <div id="functionsSection" class="accordion-collapse collapse">
                  <div class="accordion-body">
                    <div class="row g-2 mb-1 small text-muted fw-bold">
                      <div class="col-2">Name</div>
                      <div class="col-6">Expression</div>
                      <div class="col-3">Description</div>
                      <div class="col-1"></div>
                    </div>
                    <div id="editorFunctionsContainer"></div>
                    <button class="btn btn-sm btn-outline-secondary mt-2" id="addEditorFunction">+ Add Function</button>
                  </div>
                </div>
              </div>
              
              <!-- Coupling Inputs Section -->
              <div class="accordion-item">
                <h2 class="accordion-header">
                  <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#couplingInputsSection">
                    Coupling Inputs <span class="badge bg-secondary ms-2" id="couplingInputsCount">0</span>
                  </button>
                </h2>
                <div id="couplingInputsSection" class="accordion-collapse collapse">
                  <div class="accordion-body">
                    <div class="row g-2 mb-1 small text-muted fw-bold">
                      <div class="col-3">Name</div>
                      <div class="col-2">Dimension</div>
                      <div class="col-3">Keys</div>
                      <div class="col-3">Description</div>
                      <div class="col-1"></div>
                    </div>
                    <div id="editorCouplingInputsContainer"></div>
                    <button class="btn btn-sm btn-outline-secondary mt-2" id="addEditorCouplingInput">+ Add Coupling Input</button>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Save Button -->
            <div class="d-flex gap-2 mt-3">
              <button class="btn btn-primary" id="saveEditorModel">Save Model</button>
              <button class="btn btn-outline-secondary" id="cancelEditorModel">Cancel</button>
            </div>
          </div>
        </div>
      </div>
    `;

    const modelsList = root.querySelector('#dynamicsModelsList');
    const modelEditor = root.querySelector('#modelEditor');
    const editorLoading = root.querySelector('#editorLoading');
    let currentEditIndex = null;

    // Update counts
    function updateCounts() {
      root.querySelector('#paramsCount').textContent = root.querySelectorAll('#editorParamsContainer .param-row').length;
      root.querySelector('#stateVarsCount').textContent = root.querySelectorAll('#editorStateVarsContainer .sv-row').length;
      root.querySelector('#derivedParamsCount').textContent = root.querySelectorAll('#editorDerivedParamsContainer .dp-row').length;
      root.querySelector('#derivedVarsCount').textContent = root.querySelectorAll('#editorDerivedVarsContainer .dv-row').length;
      root.querySelector('#functionsCount').textContent = root.querySelectorAll('#editorFunctionsContainer .fn-row').length;
      root.querySelector('#couplingInputsCount').textContent = root.querySelectorAll('#editorCouplingInputsContainer .ci-row').length;
    }

    // Render the models list
    function renderModelsList() {
      if (STATE.dynamicsModels.length === 0) {
        modelsList.innerHTML = '<div class="text-muted text-center py-3 mb-3 border rounded">No dynamics models added yet. Click "Add Dynamics Model" to get started.</div>';
        return;
      }

      modelsList.innerHTML = STATE.dynamicsModels.map((m, idx) => `
        <div class="card mb-2">
          <div class="card-body py-2">
            <div class="d-flex justify-content-between align-items-center">
              <div>
                <strong>${escapeHtml(m.name || 'Unnamed Model')}</strong>
                ${m.label ? `<span class="text-muted ms-2">(${escapeHtml(m.label)})</span>` : ''}
                ${m.basedOn ? `<span class="badge bg-info ms-2">Based on ID: ${escapeHtml(m.basedOn)}</span>` : ''}
              </div>
              <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary edit-model-btn" data-idx="${idx}">Edit</button>
                <button class="btn btn-outline-danger remove-model-btn" data-idx="${idx}">✕</button>
              </div>
            </div>
            <div class="small text-muted mt-1">
              ${m.parameters?.length ? `<span class="me-3">📊 ${m.parameters.length} params</span>` : ''}
              ${m.state_variables?.length ? `<span class="me-3">📈 ${m.state_variables.length} state vars</span>` : ''}
              ${m.derived_variables?.length ? `<span class="me-3">🔢 ${m.derived_variables.length} derived vars</span>` : ''}
              ${m.functions?.length ? `<span>ƒ ${m.functions.length} functions</span>` : ''}
            </div>
          </div>
        </div>
      `).join('');

      // Attach event listeners
      modelsList.querySelectorAll('.edit-model-btn').forEach(btn => {
        btn.addEventListener('click', () => openEditor(parseInt(btn.dataset.idx)));
      });
      modelsList.querySelectorAll('.remove-model-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          STATE.dynamicsModels.splice(parseInt(btn.dataset.idx), 1);
          renderModelsList();
        });
      });
    }

    // Row creators - comprehensive versions aligned with schema
    function createParamRow(p = {}) {
      const div = document.createElement('div');
      div.className = 'row g-1 mb-2 param-row align-items-center';
      const domainLo = p.domain?.lo ?? (p.domain && Array.isArray(p.domain) ? p.domain[0] : '');
      const domainHi = p.domain?.hi ?? (p.domain && Array.isArray(p.domain) ? p.domain[1] : '');
      div.innerHTML = `
        <div class="col-2"><input type="text" class="form-control form-control-sm p-name" placeholder="name" value="${escapeAttr(p.name || '')}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm p-symbol" placeholder="σ" value="${escapeAttr(p.symbol || '')}"/></div>
        <div class="col-2"><input type="text" class="form-control form-control-sm p-value" placeholder="1.0" value="${escapeAttr(p.value ?? '')}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm p-unit" placeholder="mV" value="${escapeAttr(p.unit || '')}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm p-lo" placeholder="-∞" value="${escapeAttr(domainLo)}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm p-hi" placeholder="∞" value="${escapeAttr(domainHi)}"/></div>
        <div class="col-3"><input type="text" class="form-control form-control-sm p-desc" placeholder="description" value="${escapeAttr(p.description || '')}"/></div>
        <div class="col-1"><button class="btn btn-sm btn-outline-danger remove-row">✕</button></div>
      `;
      div.querySelector('.remove-row').addEventListener('click', () => { div.remove(); updateCounts(); });
      return div;
    }

    function createStateVarRow(sv = {}) {
      const div = document.createElement('div');
      div.className = 'row g-1 mb-2 sv-row align-items-center';
      const eqRhs = sv.equation?.rhs || sv.equation?.righthandside || '';
      div.innerHTML = `
        <div class="col-2"><input type="text" class="form-control form-control-sm sv-name" placeholder="S" value="${escapeAttr(sv.name || '')}"/></div>
        <div class="col-4"><input type="text" class="form-control form-control-sm sv-expr font-monospace" placeholder="(1 - S) / tau_s - gamma * S" value="${escapeAttr(eqRhs)}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm sv-initial" placeholder="0.1" value="${escapeAttr(sv.initial_value ?? 0)}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm sv-unit" placeholder="" value="${escapeAttr(sv.unit || '')}"/></div>
        <div class="col-3">
          <div class="form-check form-check-inline"><input type="checkbox" class="form-check-input sv-voi" ${sv.variable_of_interest ? 'checked' : ''}/><label class="form-check-label small">VOI</label></div>
          <div class="form-check form-check-inline"><input type="checkbox" class="form-check-input sv-coupling" ${sv.coupling_variable ? 'checked' : ''}/><label class="form-check-label small">Coupling</label></div>
          <div class="form-check form-check-inline"><input type="checkbox" class="form-check-input sv-stim" ${sv.stimulation_variable ? 'checked' : ''}/><label class="form-check-label small">Stim</label></div>
        </div>
        <div class="col-1"><button class="btn btn-sm btn-outline-danger remove-row">✕</button></div>
      `;
      div.querySelector('.remove-row').addEventListener('click', () => { div.remove(); updateCounts(); });
      return div;
    }

    function createDerivedParamRow(dp = {}) {
      const div = document.createElement('div');
      div.className = 'row g-1 mb-2 dp-row align-items-center';
      const eqRhs = dp.equation?.rhs || dp.equation?.righthandside || '';
      div.innerHTML = `
        <div class="col-2"><input type="text" class="form-control form-control-sm dp-name" placeholder="name" value="${escapeAttr(dp.name || '')}"/></div>
        <div class="col-6"><input type="text" class="form-control form-control-sm dp-expr font-monospace" placeholder="a * b + c" value="${escapeAttr(eqRhs)}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm dp-unit" placeholder="unit" value="${escapeAttr(dp.unit || '')}"/></div>
        <div class="col-2"><input type="text" class="form-control form-control-sm dp-desc" placeholder="description" value="${escapeAttr(dp.description || '')}"/></div>
        <div class="col-1"><button class="btn btn-sm btn-outline-danger remove-row">✕</button></div>
      `;
      div.querySelector('.remove-row').addEventListener('click', () => { div.remove(); updateCounts(); });
      return div;
    }

    function createDerivedVarRow(dv = {}) {
      const div = document.createElement('div');
      div.className = 'row g-1 mb-2 dv-row align-items-center';
      const eqRhs = dv.equation?.rhs || dv.equation?.righthandside || '';
      div.innerHTML = `
        <div class="col-2"><input type="text" class="form-control form-control-sm dv-name" placeholder="name" value="${escapeAttr(dv.name || '')}"/></div>
        <div class="col-6"><input type="text" class="form-control form-control-sm dv-expr font-monospace" placeholder="x + y" value="${escapeAttr(eqRhs)}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm dv-unit" placeholder="unit" value="${escapeAttr(dv.unit || '')}"/></div>
        <div class="col-2"><input type="text" class="form-control form-control-sm dv-desc" placeholder="description" value="${escapeAttr(dv.description || '')}"/></div>
        <div class="col-1"><button class="btn btn-sm btn-outline-danger remove-row">✕</button></div>
      `;
      div.querySelector('.remove-row').addEventListener('click', () => { div.remove(); updateCounts(); });
      return div;
    }

    function createFunctionRow(fn = {}) {
      const div = document.createElement('div');
      div.className = 'row g-1 mb-2 fn-row align-items-center';
      const eqRhs = fn.equation?.rhs || fn.equation?.righthandside || '';
      div.innerHTML = `
        <div class="col-2"><input type="text" class="form-control form-control-sm fn-name" placeholder="name" value="${escapeAttr(fn.name || '')}"/></div>
        <div class="col-6"><input type="text" class="form-control form-control-sm fn-expr font-monospace" placeholder="1 / (1 + exp(-x))" value="${escapeAttr(eqRhs)}"/></div>
        <div class="col-3"><input type="text" class="form-control form-control-sm fn-desc" placeholder="description" value="${escapeAttr(fn.description || '')}"/></div>
        <div class="col-1"><button class="btn btn-sm btn-outline-danger remove-row">✕</button></div>
      `;
      div.querySelector('.remove-row').addEventListener('click', () => { div.remove(); updateCounts(); });
      return div;
    }

    function createCouplingInputRow(ci = {}) {
      const div = document.createElement('div');
      div.className = 'row g-1 mb-2 ci-row align-items-center';
      const keysStr = Array.isArray(ci.keys) ? ci.keys.join(', ') : (ci.keys || '');
      div.innerHTML = `
        <div class="col-3"><input type="text" class="form-control form-control-sm ci-name" placeholder="name" value="${escapeAttr(ci.name || '')}"/></div>
        <div class="col-2"><input type="number" class="form-control form-control-sm ci-dim" placeholder="1" value="${escapeAttr(ci.dimension ?? 1)}"/></div>
        <div class="col-3"><input type="text" class="form-control form-control-sm ci-keys" placeholder="lre, ffi" value="${escapeAttr(keysStr)}"/></div>
        <div class="col-3"><input type="text" class="form-control form-control-sm ci-desc" placeholder="description" value="${escapeAttr(ci.description || '')}"/></div>
        <div class="col-1"><button class="btn btn-sm btn-outline-danger remove-row">✕</button></div>
      `;
      div.querySelector('.remove-row').addEventListener('click', () => { div.remove(); updateCounts(); });
      return div;
    }

    function renderEditorSections(model) {
      // Parameters
      const paramsContainer = root.querySelector('#editorParamsContainer');
      paramsContainer.innerHTML = '';
      (model.parameters || []).forEach(p => paramsContainer.appendChild(createParamRow(p)));

      // State Variables
      const svContainer = root.querySelector('#editorStateVarsContainer');
      svContainer.innerHTML = '';
      (model.state_variables || []).forEach(sv => svContainer.appendChild(createStateVarRow(sv)));

      // Derived Parameters
      const dpContainer = root.querySelector('#editorDerivedParamsContainer');
      dpContainer.innerHTML = '';
      (model.derived_parameters || []).forEach(dp => dpContainer.appendChild(createDerivedParamRow(dp)));

      // Derived Variables
      const dvContainer = root.querySelector('#editorDerivedVarsContainer');
      dvContainer.innerHTML = '';
      (model.derived_variables || []).forEach(dv => dvContainer.appendChild(createDerivedVarRow(dv)));

      // Functions
      const fnContainer = root.querySelector('#editorFunctionsContainer');
      fnContainer.innerHTML = '';
      (model.functions || []).forEach(fn => fnContainer.appendChild(createFunctionRow(fn)));

      // Coupling Inputs
      const ciContainer = root.querySelector('#editorCouplingInputsContainer');
      ciContainer.innerHTML = '';
      (model.coupling_inputs || []).forEach(ci => ciContainer.appendChild(createCouplingInputRow(ci)));

      updateCounts();
    }

    // Open the model editor
    function openEditor(index = null) {
      currentEditIndex = index;
      modelEditor.style.display = 'block';

      const model = index !== null ? STATE.dynamicsModels[index] : {};
      root.querySelector('#editorTitle').textContent = index !== null ? 'Edit Model' : 'Add New Model';
      root.querySelector('#editorBaseModel').value = model.basedOn || '';
      root.querySelector('#editorModelName').value = model.name || '';
      root.querySelector('#editorModelLabel').value = model.label || '';
      root.querySelector('#editorSystemType').value = model.system_type || 'continuous';
      root.querySelector('#editorDescription').value = model.description || '';
      root.querySelector('#editorReferences').value = model.references || '';

      renderEditorSections(model);
    }

    function closeEditor() {
      modelEditor.style.display = 'none';
      currentEditIndex = null;
    }

    // Collect model data from editor
    function collectEditorModel() {
      const params = Array.from(root.querySelectorAll('#editorParamsContainer .param-row')).map(row => {
        const lo = row.querySelector('.p-lo').value.trim();
        const hi = row.querySelector('.p-hi').value.trim();
        return {
          name: row.querySelector('.p-name').value.trim(),
          symbol: row.querySelector('.p-symbol').value.trim() || undefined,
          value: parseMaybeNumber(row.querySelector('.p-value').value.trim()),
          unit: row.querySelector('.p-unit').value.trim() || undefined,
          domain: (lo || hi) ? { lo: parseMaybeNumber(lo), hi: parseMaybeNumber(hi) } : undefined,
          description: row.querySelector('.p-desc').value.trim() || undefined,
        };
      }).filter(p => p.name);

      const stateVars = Array.from(root.querySelectorAll('#editorStateVarsContainer .sv-row')).map(row => ({
        name: row.querySelector('.sv-name').value.trim(),
        equation: { rhs: row.querySelector('.sv-expr').value.trim() },
        initial_value: parseMaybeNumber(row.querySelector('.sv-initial').value.trim()),
        unit: row.querySelector('.sv-unit').value.trim() || undefined,
        variable_of_interest: row.querySelector('.sv-voi').checked,
        coupling_variable: row.querySelector('.sv-coupling').checked,
        stimulation_variable: row.querySelector('.sv-stim').checked,
      })).filter(sv => sv.name);

      const derivedParams = Array.from(root.querySelectorAll('#editorDerivedParamsContainer .dp-row')).map(row => ({
        name: row.querySelector('.dp-name').value.trim(),
        equation: { rhs: row.querySelector('.dp-expr').value.trim() },
        unit: row.querySelector('.dp-unit').value.trim() || undefined,
        description: row.querySelector('.dp-desc').value.trim() || undefined,
      })).filter(dp => dp.name);

      const derivedVars = Array.from(root.querySelectorAll('#editorDerivedVarsContainer .dv-row')).map(row => ({
        name: row.querySelector('.dv-name').value.trim(),
        equation: { rhs: row.querySelector('.dv-expr').value.trim() },
        unit: row.querySelector('.dv-unit').value.trim() || undefined,
        description: row.querySelector('.dv-desc').value.trim() || undefined,
      })).filter(dv => dv.name);

      const functions = Array.from(root.querySelectorAll('#editorFunctionsContainer .fn-row')).map(row => ({
        name: row.querySelector('.fn-name').value.trim(),
        equation: { rhs: row.querySelector('.fn-expr').value.trim() },
        description: row.querySelector('.fn-desc').value.trim() || undefined,
      })).filter(fn => fn.name);

      const couplingInputs = Array.from(root.querySelectorAll('#editorCouplingInputsContainer .ci-row')).map(row => {
        const keysStr = row.querySelector('.ci-keys').value.trim();
        return {
          name: row.querySelector('.ci-name').value.trim(),
          dimension: parseInt(row.querySelector('.ci-dim').value) || 1,
          keys: keysStr ? keysStr.split(',').map(k => k.trim()) : undefined,
          description: row.querySelector('.ci-desc').value.trim() || undefined,
        };
      }).filter(ci => ci.name);

      return {
        basedOn: root.querySelector('#editorBaseModel').value || undefined,
        name: root.querySelector('#editorModelName').value.trim(),
        label: root.querySelector('#editorModelLabel').value.trim() || undefined,
        system_type: root.querySelector('#editorSystemType').value,
        description: root.querySelector('#editorDescription').value.trim() || undefined,
        references: root.querySelector('#editorReferences').value.trim() || undefined,
        parameters: params.length ? params : undefined,
        state_variables: stateVars.length ? stateVars : undefined,
        derived_parameters: derivedParams.length ? derivedParams : undefined,
        derived_variables: derivedVars.length ? derivedVars : undefined,
        functions: functions.length ? functions : undefined,
        coupling_inputs: couplingInputs.length ? couplingInputs : undefined,
      };
    }

    // Load base model into editor - fetch full details from API
    async function loadBaseModel(modelId) {
      log('Loading base model:', modelId);
      editorLoading.style.display = 'inline-block';

      try {
        const response = await fetch(`/tvbo/api/configurator/dynamics/${modelId}`);
        const result = await response.json();

        if (!result.success || !result.data) {
          console.error('Failed to load model details:', result.error);
          alert('Error loading model: ' + (result.error || 'Unknown error'));
          return;
        }

        const model = result.data;
        log('Loaded model details:', model);

        // Fill basic fields
        root.querySelector('#editorModelName').value = model.name || '';
        root.querySelector('#editorModelLabel').value = model.label || '';
        root.querySelector('#editorDescription').value = model.description || '';
        root.querySelector('#editorReferences').value = model.references || '';

        // System type is a Many2one in Odoo, returns [id, name]
        if (model.system_type) {
          const stName = Array.isArray(model.system_type) ? model.system_type[1] : model.system_type;
          root.querySelector('#editorSystemType').value = String(stName).toLowerCase().includes('discrete') ? 'discrete' : 'continuous';
        }

        // Transform the data to our internal format
        const transformedModel = {
          parameters: (model.parameters || []).map(p => ({
            name: p.name,
            symbol: p.symbol,
            value: p.value,
            unit: p.unit,
            description: p.description,
            domain: p.domain ? { lo: p.domain.lo, hi: p.domain.hi } : undefined,
          })),
          state_variables: (model.state_variables || []).map(sv => ({
            name: sv.name,
            equation: sv.equation && typeof sv.equation === 'object'
              ? { rhs: sv.equation.righthandside || '' }
              : { rhs: '' },
            initial_value: sv.initial_value,
            unit: sv.unit,
            variable_of_interest: sv.variable_of_interest,
            coupling_variable: sv.coupling_variable,
            stimulation_variable: sv.stimulation_variable,
          })),
          derived_parameters: (model.derived_parameters || []).map(dp => ({
            name: dp.name,
            equation: dp.equation && typeof dp.equation === 'object'
              ? { rhs: dp.equation.righthandside || '' }
              : { rhs: '' },
            unit: dp.unit,
            description: dp.description,
          })),
          derived_variables: (model.derived_variables || []).map(dv => ({
            name: dv.name,
            equation: dv.equation && typeof dv.equation === 'object'
              ? { rhs: dv.equation.righthandside || '' }
              : { rhs: '' },
            unit: dv.unit,
            description: dv.description,
          })),
          functions: (model.functions || []).map(fn => ({
            name: fn.name,
            equation: fn.equation && typeof fn.equation === 'object'
              ? { rhs: fn.equation.righthandside || '' }
              : { rhs: '' },
            description: fn.description,
          })),
          coupling_inputs: (model.coupling_inputs || []).map(ci => ({
            name: ci.name,
            dimension: ci.dimension,
            keys: ci.keys,
            description: ci.description,
          })),
        };

        renderEditorSections(transformedModel);

      } catch (err) {
        console.error('Error loading base model:', err);
        alert('Error loading model: ' + err.message);
      } finally {
        editorLoading.style.display = 'none';
      }
    }

    // Event listeners
    root.querySelector('#addDynamicsModel').addEventListener('click', () => openEditor(null));
    root.querySelector('#closeEditor').addEventListener('click', closeEditor);
    root.querySelector('#cancelEditorModel').addEventListener('click', closeEditor);

    root.querySelector('#saveEditorModel').addEventListener('click', () => {
      const model = collectEditorModel();
      if (!model.name) {
        alert('Please enter a model name');
        return;
      }
      if (currentEditIndex !== null) {
        STATE.dynamicsModels[currentEditIndex] = model;
      } else {
        STATE.dynamicsModels.push(model);
      }
      closeEditor();
      renderModelsList();
    });

    root.querySelector('#addEditorParam').addEventListener('click', () => {
      root.querySelector('#editorParamsContainer').appendChild(createParamRow());
      updateCounts();
    });
    root.querySelector('#addEditorStateVar').addEventListener('click', () => {
      root.querySelector('#editorStateVarsContainer').appendChild(createStateVarRow());
      updateCounts();
    });
    root.querySelector('#addEditorDerivedParam').addEventListener('click', () => {
      root.querySelector('#editorDerivedParamsContainer').appendChild(createDerivedParamRow());
      updateCounts();
    });
    root.querySelector('#addEditorDerivedVar').addEventListener('click', () => {
      root.querySelector('#editorDerivedVarsContainer').appendChild(createDerivedVarRow());
      updateCounts();
    });
    root.querySelector('#addEditorFunction').addEventListener('click', () => {
      root.querySelector('#editorFunctionsContainer').appendChild(createFunctionRow());
      updateCounts();
    });
    root.querySelector('#addEditorCouplingInput').addEventListener('click', () => {
      root.querySelector('#editorCouplingInputsContainer').appendChild(createCouplingInputRow());
      updateCounts();
    });

    root.querySelector('#editorBaseModel').addEventListener('change', (e) => {
      if (e.target.value) {
        loadBaseModel(e.target.value);
      }
    });

    // Initial render
    renderModelsList();
  }

  function updateEquationPreview(row) {
    // Determine the type of row and get appropriate inputs
    let name, expr;

    if (row.querySelector('.sv-name')) {
      // State variable row
      name = row.querySelector('.sv-name')?.value?.trim();
      expr = row.querySelector('.sv-expr')?.value?.trim();
    } else if (row.querySelector('.dp-name')) {
      // Derived parameter row
      name = row.querySelector('.dp-name')?.value?.trim();
      expr = row.querySelector('.dp-expr')?.value?.trim();
    } else if (row.querySelector('.dv-name')) {
      // Derived variable row
      name = row.querySelector('.dv-name')?.value?.trim();
      expr = row.querySelector('.dv-expr')?.value?.trim();
    } else if (row.querySelector('.ot-name')) {
      // Output transform row
      name = row.querySelector('.ot-name')?.value?.trim();
      expr = row.querySelector('.ot-expr')?.value?.trim();
    } else if (row.querySelector('.fn-name')) {
      // Function row
      name = row.querySelector('.fn-name')?.value?.trim();
      expr = row.querySelector('.fn-expr')?.value?.trim();
    } else {
      // Fallback to old names
      name = row.querySelector('.eq-name')?.value?.trim();
      expr = row.querySelector('.eq-expr')?.value?.trim();
    }

    const preview = row.querySelector('.eq-preview');
    if (!preview) return;
    if (!STATE.previewEnabled) {
      preview.style.display = 'none';
      preview.innerHTML = '';
      return;
    }
    preview.style.display = 'block';
    if (!name && !expr) { preview.innerHTML = ''; return; }
    const tex = toTex(name, expr);
    preview.innerHTML = tex ? `$${tex}$` : '';
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise([preview]).catch(() => {
        preview.textContent = tex;
        preview.style.fontFamily = 'monospace';
      });
    }
  }

  function collectSpec(section, lists) {
    const name = section.querySelector('#builderSpecName')?.value?.trim() || 'MyCustomModel';
    const description = section.querySelector('#builderNotes')?.value?.trim() || '';
    const systemType = section.querySelector('#builderSystemType')?.value || 'continuous';

    const modelParams = Array.from(section.querySelectorAll('#modelParamsRows .builder-row')).map(row => {
      const domain_lo = parseMaybeNumber(row.querySelector('.p-domain-lo')?.value?.trim());
      const domain_hi = parseMaybeNumber(row.querySelector('.p-domain-hi')?.value?.trim());
      const domain = (domain_lo !== undefined || domain_hi !== undefined) ? { lo: domain_lo, hi: domain_hi } : undefined;

      return {
        name: row.querySelector('.p-name')?.value?.trim() || '',
        value: parseMaybeNumber(row.querySelector('.p-value')?.value?.trim()),
        unit: row.querySelector('.p-unit')?.value?.trim() || undefined,
        symbol: row.querySelector('.p-symbol')?.value?.trim() || undefined,
        domain: domain
      };
    }).filter(p => p.name);

    const derivedParams = Array.from(section.querySelectorAll('#derivedParamsRows .builder-row')).map(row => ({
      name: row.querySelector('.dp-name')?.value?.trim() || '',
      unit: row.querySelector('.dp-unit')?.value?.trim() || undefined,
      equation: {
        rhs: row.querySelector('.dp-expr')?.value?.trim() || undefined
      }
    })).filter(p => p.name);

    const stateVars = Array.from(section.querySelectorAll('#stateEqRows .builder-row')).map(row => ({
      name: row.querySelector('.sv-name')?.value?.trim() || '',
      symbol: row.querySelector('.sv-symbol')?.value?.trim() || undefined,
      unit: row.querySelector('.sv-unit')?.value?.trim() || undefined,
      initial_value: parseMaybeNumber(row.querySelector('.sv-initial')?.value?.trim()),
      variable_of_interest: row.querySelector('.sv-voi')?.checked || false,
      coupling_variable: row.querySelector('.sv-coupling')?.checked || false,
      equation: {
        rhs: row.querySelector('.sv-expr')?.value?.trim() || undefined
      }
    })).filter(e => e.name);

    const derivedVars = Array.from(section.querySelectorAll('#derivedVarsRows .builder-row')).map(row => ({
      name: row.querySelector('.dv-name')?.value?.trim() || '',
      unit: row.querySelector('.dv-unit')?.value?.trim() || undefined,
      equation: {
        rhs: row.querySelector('.dv-expr')?.value?.trim() || undefined
      }
    })).filter(e => e.name);

    const outputTransforms = Array.from(section.querySelectorAll('#outputTransformsRows .builder-row')).map(row => ({
      name: row.querySelector('.ot-name')?.value?.trim() || '',
      unit: row.querySelector('.ot-unit')?.value?.trim() || undefined,
      equation: {
        rhs: row.querySelector('.ot-expr')?.value?.trim() || undefined
      }
    })).filter(e => e.name);

    const functions = Array.from(section.querySelectorAll('#functionsRows .builder-row')).map(row => ({
      name: row.querySelector('.fn-name')?.value?.trim() || '',
      equation: {
        rhs: row.querySelector('.fn-expr')?.value?.trim() || undefined
      }
    })).filter(f => f.name);

    const couplingTerms = Array.from(section.querySelectorAll('#couplingTermsRows .builder-row')).map(row => ({
      name: row.querySelector('.ct-name')?.value?.trim() || '',
      value: parseMaybeNumber(row.querySelector('.ct-value')?.value?.trim())
    })).filter(c => c.name);

    return {
      model: prune({
        name: name,
        label: name,
        description: description || undefined,
        system_type: systemType,
        parameters: modelParams.length ? modelParams : undefined,
        derived_parameters: derivedParams.length ? derivedParams : undefined,
        state_variables: stateVars.length ? stateVars : undefined,
        derived_variables: derivedVars.length ? derivedVars : undefined,
        output: outputTransforms.length ? outputTransforms : undefined,
        functions: functions.length ? functions : undefined,
        coupling_terms: couplingTerms.length ? couplingTerms : undefined,
      })
    };
  }

  function copyPythonCode() {
    const section = document.getElementById('builderContent');
    if (!section) {
      alert('Please configure a model first');
      return;
    }

    const spec = collectSpec(section, { models: STATE.data || [] });
    const pythonCode = generatePythonCode(spec);

    navigator.clipboard.writeText(pythonCode).then(() => {
      alert('Python code copied to clipboard!');
    }).catch(err => {
      alert('Failed to copy: ' + err.message);
    });
  }

  function downloadYaml() {
    // Check if we have a loaded experiment - use server-side Pydantic serialization
    const loadSelect = document.getElementById('loadExistingExperiment');
    const experimentId = loadSelect ? loadSelect.value : null;

    if (experimentId) {
      // Fetch YAML from server using Pydantic SimulationExperiment
      window.location.href = `/tvbo/api/configurator/experiment/${experimentId}/yaml`;
      return;
    }

    // Fallback: generate from form (for new experiments not yet saved)
    const section = document.getElementById('builderContent');
    if (!section) {
      alert('Please configure a model first');
      return;
    }

    const spec = collectSpec(section, { models: STATE.data || [] });
    const yamlContent = generateYamlContent(spec);
    const modelName = spec.model.name || 'CustomModel';

    const blob = new Blob([yamlContent], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${modelName}.yaml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  function generatePythonCode(spec) {
    const model = spec.model;
    const name = model.name || 'CustomModel';

    let code = `# Generated Neural Mass Model: ${name}\n`;
    code += `from tvbo import Dynamics\n\n`;
    code += `# Define model\n`;
    code += `model_dict = {\n`;
    code += `    'name': '${name}',\n`;
    if (model.description) {
      code += `    'description': '${model.description}',\n`;
    }
    if (model.system_type && model.system_type !== 'continuous') {
      code += `    'system_type': '${model.system_type}',\n`;
    }

    if (model.parameters && model.parameters.length > 0) {
      code += `    'parameters': [\n`;
      model.parameters.forEach(p => {
        code += `        {\n`;
        code += `            'name': '${p.name}',\n`;
        code += `            'value': ${p.value},\n`;
        if (p.unit) code += `            'unit': '${p.unit}',\n`;
        if (p.symbol) code += `            'symbol': '${p.symbol}',\n`;
        if (p.domain) {
          code += `            'domain': {\n`;
          if (p.domain.lo !== undefined) code += `                'lo': ${p.domain.lo},\n`;
          if (p.domain.hi !== undefined) code += `                'hi': ${p.domain.hi},\n`;
          code += `            },\n`;
        }
        code += `        },\n`;
      });
      code += `    ],\n`;
    }

    if (model.derived_parameters && model.derived_parameters.length > 0) {
      code += `    'derived_parameters': [\n`;
      model.derived_parameters.forEach(dp => {
        code += `        {\n`;
        code += `            'name': '${dp.name}',\n`;
        if (dp.unit) code += `            'unit': '${dp.unit}',\n`;
        if (dp.equation && dp.equation.rhs) {
          code += `            'equation': {'rhs': '${dp.equation.rhs}'},\n`;
        }
        code += `        },\n`;
      });
      code += `    ],\n`;
    }

    if (model.state_variables && model.state_variables.length > 0) {
      code += `    'state_variables': [\n`;
      model.state_variables.forEach(sv => {
        code += `        {\n`;
        code += `            'name': '${sv.name}',\n`;
        if (sv.symbol) code += `            'symbol': '${sv.symbol}',\n`;
        if (sv.unit) code += `            'unit': '${sv.unit}',\n`;
        if (sv.initial_value !== undefined) code += `            'initial_value': ${sv.initial_value},\n`;
        if (sv.variable_of_interest !== undefined) code += `            'variable_of_interest': ${sv.variable_of_interest},\n`;
        if (sv.coupling_variable) code += `            'coupling_variable': ${sv.coupling_variable},\n`;
        if (sv.equation && sv.equation.rhs) {
          code += `            'equation': {'rhs': '${sv.equation.rhs}'},\n`;
        }
        code += `        },\n`;
      });
      code += `    ],\n`;
    }

    if (model.derived_variables && model.derived_variables.length > 0) {
      code += `    'derived_variables': [\n`;
      model.derived_variables.forEach(dv => {
        code += `        {\n`;
        code += `            'name': '${dv.name}',\n`;
        if (dv.unit) code += `            'unit': '${dv.unit}',\n`;
        if (dv.equation && dv.equation.rhs) {
          code += `            'equation': {'rhs': '${dv.equation.rhs}'},\n`;
        }
        code += `        },\n`;
      });
      code += `    ],\n`;
    }

    if (model.output && model.output.length > 0) {
      code += `    'output': [\n`;
      model.output.forEach(ot => {
        code += `        {\n`;
        code += `            'name': '${ot.name}',\n`;
        if (ot.unit) code += `            'unit': '${ot.unit}',\n`;
        if (ot.equation && ot.equation.rhs) {
          code += `            'equation': {'rhs': '${ot.equation.rhs}'},\n`;
        }
        code += `        },\n`;
      });
      code += `    ],\n`;
    }

    if (model.functions && model.functions.length > 0) {
      code += `    'functions': [\n`;
      model.functions.forEach(fn => {
        code += `        {\n`;
        code += `            'name': '${fn.name}',\n`;
        if (fn.equation && fn.equation.rhs) {
          code += `            'equation': {'rhs': '${fn.equation.rhs}'},\n`;
        }
        code += `        },\n`;
      });
      code += `    ],\n`;
    }

    if (model.coupling_terms && model.coupling_terms.length > 0) {
      code += `    'coupling_terms': [\n`;
      model.coupling_terms.forEach(ct => {
        code += `        {\n`;
        code += `            'name': '${ct.name}',\n`;
        code += `            'value': ${ct.value},\n`;
        code += `        },\n`;
      });
      code += `    ],\n`;
    }

    code += `}\n\n`;
    code += `# Create Dynamics instance\n`;
    code += `model = Dynamics(**model_dict)\n\n`;
    code += `# Run simulation\n`;
    code += `results = model.run(duration=1000)\n`;
    code += `results.plot()\n`;
    return code;
  }

  function generateYamlContent(spec) {
    const model = spec.model;
    let yaml = `# Neural Mass Model: ${model.name}\n`;
    yaml += `name: ${model.name}\n`;
    yaml += `label: ${model.label || model.name}\n`;
    if (model.description) {
      yaml += `description: "${model.description}"\n`;
    }
    if (model.system_type && model.system_type !== 'continuous') {
      yaml += `system_type: ${model.system_type}\n`;
    }

    if (model.parameters && model.parameters.length > 0) {
      yaml += `\nparameters:\n`;
      model.parameters.forEach(p => {
        yaml += `  - name: ${p.name}\n`;
        yaml += `    value: ${p.value}\n`;
        if (p.unit) yaml += `    unit: ${p.unit}\n`;
        if (p.symbol) yaml += `    symbol: ${p.symbol}\n`;
        if (p.domain) {
          yaml += `    domain:\n`;
          if (p.domain.lo !== undefined) yaml += `      lo: ${p.domain.lo}\n`;
          if (p.domain.hi !== undefined) yaml += `      hi: ${p.domain.hi}\n`;
        }
      });
    }

    if (model.derived_parameters && model.derived_parameters.length > 0) {
      yaml += `\nderived_parameters:\n`;
      model.derived_parameters.forEach(dp => {
        yaml += `  - name: ${dp.name}\n`;
        if (dp.unit) yaml += `    unit: ${dp.unit}\n`;
        if (dp.equation && dp.equation.rhs) {
          yaml += `    equation:\n`;
          yaml += `      rhs: "${dp.equation.rhs}"\n`;
        }
      });
    }

    if (model.state_variables && model.state_variables.length > 0) {
      yaml += `\nstate_variables:\n`;
      model.state_variables.forEach(sv => {
        yaml += `  - name: ${sv.name}\n`;
        if (sv.symbol) yaml += `    symbol: ${sv.symbol}\n`;
        if (sv.unit) yaml += `    unit: ${sv.unit}\n`;
        if (sv.initial_value !== undefined) yaml += `    initial_value: ${sv.initial_value}\n`;
        if (sv.variable_of_interest !== undefined) yaml += `    variable_of_interest: ${sv.variable_of_interest}\n`;
        if (sv.coupling_variable) yaml += `    coupling_variable: ${sv.coupling_variable}\n`;
        if (sv.equation && sv.equation.rhs) {
          yaml += `    equation:\n`;
          yaml += `      rhs: "${sv.equation.rhs}"\n`;
        }
      });
    }

    if (model.derived_variables && model.derived_variables.length > 0) {
      yaml += `\nderived_variables:\n`;
      model.derived_variables.forEach(dv => {
        yaml += `  - name: ${dv.name}\n`;
        if (dv.unit) yaml += `    unit: ${dv.unit}\n`;
        if (dv.equation && dv.equation.rhs) {
          yaml += `    equation:\n`;
          yaml += `      rhs: "${dv.equation.rhs}"\n`;
        }
      });
    }

    if (model.output && model.output.length > 0) {
      yaml += `\noutput:\n`;
      model.output.forEach(ot => {
        yaml += `  - name: ${ot.name}\n`;
        if (ot.unit) yaml += `    unit: ${ot.unit}\n`;
        if (ot.equation && ot.equation.rhs) {
          yaml += `    equation:\n`;
          yaml += `      rhs: "${ot.equation.rhs}"\n`;
        }
      });
    }

    if (model.functions && model.functions.length > 0) {
      yaml += `\nfunctions:\n`;
      model.functions.forEach(fn => {
        yaml += `  - name: ${fn.name}\n`;
        if (fn.equation && fn.equation.rhs) {
          yaml += `    equation:\n`;
          yaml += `      rhs: "${fn.equation.rhs}"\n`;
        }
      });
    }

    if (model.coupling_terms && model.coupling_terms.length > 0) {
      yaml += `\ncoupling_terms:\n`;
      model.coupling_terms.forEach(ct => {
        yaml += `  - name: ${ct.name}\n`;
        yaml += `    value: ${ct.value}\n`;
      });
    }

    return yaml;
  }

  function prune(obj) {
    if (Array.isArray(obj)) {
      return obj.map(prune).filter(v => v !== undefined);
    }
    if (obj && typeof obj === 'object') {
      const out = {};
      for (const k of Object.keys(obj)) {
        const v = prune(obj[k]);
        if (v !== undefined && !(Array.isArray(v) && v.length === 0)) out[k] = v;
      }
      return Object.keys(out).length ? out : undefined;
    }
    return obj === '' ? undefined : obj;
  }

  function toTex(lhs, rhs) {
    let L = lhs || '';
    let R = rhs || '';
    if (!L && !R) return '';
    R = R.replace(/\*\*/g, '^');
    R = R.replace(/\bexp\s*\(([^()]*)\)/g, (m, a) => `e^{${a}}`);
    R = R.replace(/\bsqrt\s*\(([^()]*)\)/g, (m, a) => `\\sqrt{${a}}`);
    R = R.replace(/\b(sin|cos|tan|tanh|log)\b/g, (m, fn) => `\\${fn}`);
    try {
      R = R.replace(/(?<=\b[\w)\}])\*(?=[\w(\{\\])/g, ' \\cdot ');
    } catch {
      R = R.replace(/([0-9A-Za-z_\)\}])\*([0-9A-Za-z_\\\(\{])/g, '$1 \\cdot $2');
    }
    return L && R ? `${L} = ${R}` : (L || R);
  }

  function parseMaybeNumber(v) {
    if (v === '') return undefined;
    const n = Number(v);
    return Number.isFinite(n) ? n : v;
  }

  function valueToStr(v) {
    if (v === undefined || v === null) return '';
    return typeof v === 'number' ? String(v) : v;
  }

  function escapeHtml(s) {
    return String(s || '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  function escapeAttr(s) {
    return String(s || '').replace(/"/g, '&quot;');
  }

  // Expose functions globally
  window.initializeBuilder = initializeBuilder;
  window.collectSpec = collectSpec;
  window.copyPythonCode = copyPythonCode;
  window.downloadYaml = downloadYaml;

  // Expose helper functions for experiment loading
  window.addFunctionRow = addFunctionRow;
  window.addObservationRow = addObservationRow;
  window.addAlgorithmRow = addAlgorithmRow;
  window.addDerivedObservationRow = addDerivedObservationRow;
  window.addOptimizationRow = addOptimizationRow;
  window.addExplorationRow = addExplorationRow;

  // ========================================================================
  // SCHEMA-DRIVEN PREFILL ENGINE
  // ========================================================================
  // Instead of hardcoding field-to-element mappings, we use data-field
  // attributes on form elements and data-section on containers.
  // The API response drives the prefill — if a field exists in the API,
  // it gets mapped to the matching [data-field] element automatically.
  // Adding/removing schema fields requires ZERO loader code changes.
  // ========================================================================

  /**
   * Resolve a raw API value to a displayable scalar.
   * Handles Odoo conventions: false → '', [id, name] → name, {rhs/righthandside} → string, etc.
   */
  function resolveValue(val) {
    if (val === false || val === null || val === undefined) return '';
    if (Array.isArray(val)) {
      // Odoo Many2one: [id, display_name] or list of scalars
      if (val.length === 2 && typeof val[0] === 'number' && typeof val[1] === 'string') return val[1];
      // List of objects with .name → comma-join
      if (val.length > 0 && typeof val[0] === 'object' && val[0] !== null) {
        return val.map(v => v.name || v.display_name || '').filter(Boolean).join(', ');
      }
      return val.join(', ');
    }
    if (typeof val === 'object' && val !== null) {
      // Equation-like: {righthandside, rhs}
      if ('righthandside' in val) return val.righthandside || '';
      if ('rhs' in val) return val.rhs || '';
      // Scalar-like: {value}
      if ('value' in val) return val.value;
      // Fallback: name
      return val.name || val.display_name || val.label || JSON.stringify(val);
    }
    return val;
  }

  /**
   * Prefill all [data-field] elements within a section container.
   * @param {string} sectionName - matches data-section attribute on container
   * @param {object} data - flat API response object for this section
   */
  function prefillSection(sectionName, data) {
    if (!data || typeof data !== 'object') return;
    const container = document.querySelector(`[data-section="${sectionName}"]`);
    if (!container) {
      console.warn(`[Prefill] No container found for section: ${sectionName}`);
      return;
    }
    const fields = container.querySelectorAll('[data-field]');
    const fieldNames = new Set();
    fields.forEach(el => {
      const fieldName = el.dataset.field;
      fieldNames.add(fieldName);
      const rawVal = data[fieldName];
      if (rawVal === undefined) return; // field not in API response
      const val = resolveValue(rawVal);
      if (el.type === 'checkbox') {
        el.checked = !!rawVal && rawVal !== false;
      } else {
        el.value = val;
      }
    });
    // Log unmapped API fields for debugging (helps discover new fields)
    const SKIP = new Set(['id', 'display_name', 'create_uid', 'create_date', 'write_uid', 'write_date']);
    const unmapped = Object.keys(data).filter(k => !fieldNames.has(k) && !SKIP.has(k) && data[k] !== false && data[k] !== null);
    if (unmapped.length > 0) {
      console.info(`[Prefill] Section "${sectionName}": unmapped API fields:`, unmapped);
    }
  }

  /**
   * Array section handlers: define how to create rows from API array items.
   * Each handler: { container: element ID, clear: bool, handler: (item) => void }
   */
  const ARRAY_HANDLERS = {
    functions: {
      containerId: 'functionsRows',
      handler: (func) => {
        const name = func.name || '';
        const equation = func.equation ? resolveValue(func.equation) : (func.source_code || '');
        const description = func.description || '';
        const module = func.callable?.module || '';
        const callable = func.callable?.name || '';
        addFunctionRow(name, description, equation, module, callable);
      }
    },
    observations: {
      containerId: 'observationsRows',
      handler: (obs) => {
        const name = obs.name || '';
        const source = obs.voi || obs.source || '';
        const type = obs.imaging_modality ? 'monitor' : (obs.data_source ? 'external' : 'metric');
        const period = obs.period || obs.downsample_period || '';
        addObservationRow(name, source, type, String(period));
      }
    },
    derived_observations: {
      containerId: 'derivedObservationsRows',
      handler: (obs) => {
        const name = obs.name || '';
        const sources = obs.source_observations ? resolveValue(obs.source_observations) : '';
        const pipeline = obs.pipeline ? resolveValue(obs.pipeline) : '';
        addDerivedObservationRow(name, sources, pipeline);
      }
    },
    algorithms: {
      containerId: 'algorithmsRows',
      handler: (alg) => {
        const name = alg.name || '';
        const type = alg.type || 'fic';
        const nIter = alg.n_iterations || '10';
        const eta = alg.learning_rate || '0.01';
        addAlgorithmRow(name, type, String(nIter), String(eta));
      }
    },
    optimization: {
      containerId: 'optimizationRows',
      handler: (opt) => {
        const name = opt.name || '';
        const optimizer = opt.optimizer || opt.algorithm || 'adam';
        const nIter = opt.n_iterations || opt.max_iterations || '100';
        const lr = opt.learning_rate || '0.01';
        addOptimizationRow(name, optimizer, String(nIter), String(lr));
      }
    },
    explorations: {
      containerId: 'explorationsRows',
      handler: (expl) => {
        const name = expl.name || '';
        const mode = expl.mode || 'product';
        let params = '';
        if (expl.parameters && Array.isArray(expl.parameters)) {
          params = expl.parameters.map(p => {
            if (typeof p === 'object') {
              const pName = p.name || '';
              const lo = p.domain?.lo ?? '';
              const hi = p.domain?.hi ?? '';
              const n = p.domain?.n ?? '';
              return `${pName}:${lo}:${hi}:${n}`;
            }
            return '';
          }).filter(Boolean).join(', ');
        }
        addExplorationRow(name, params, mode);
      }
    }
  };

  /**
   * Master prefill: schema-driven experiment loading.
   * Maps API response sections → DOM sections using data-section/data-field attributes.
   * Arrays use registered ARRAY_HANDLERS.
   * NO hardcoded field names. Adding new fields = add data-field attribute to HTML.
   */
  function prefillExperiment(exp) {
    if (!exp) return;
    console.log('[Prefill] Loading experiment:', exp.display_name || exp.label);

    // 1. General tab (data-section="general" on the general panel)
    prefillSection('general', {
      name: exp.name || exp.display_name,
      label: exp.label,
      description: exp.description,
      references: exp.references
    });

    // 2. Object sections: auto-prefill using data-section containers
    const OBJECT_SECTIONS = {
      integration: exp.integration,
      execution: exp.execution,
      stimulation: exp.stimulation || exp.stimulus
    };
    for (const [section, data] of Object.entries(OBJECT_SECTIONS)) {
      if (data && typeof data === 'object' && !Array.isArray(data)) {
        prefillSection(section, data);
      }
    }

    // 3. Network section: has nested coupling
    const net = exp.network || exp.brain_network;
    if (net && typeof net === 'object') {
      prefillSection('network', net);
      // Coupling is nested inside network
      if (net.coupling && Array.isArray(net.coupling) && net.coupling.length > 0) {
        const coupling = net.coupling[0];
        if (typeof coupling === 'object') {
          prefillCoupling(coupling);
        }
      }
    }

    // 4. Top-level coupling (legacy field on experiment)
    if (exp.coupling && typeof exp.coupling === 'object' && !Array.isArray(exp.coupling)) {
      prefillCoupling(exp.coupling);
    }

    // 5. Dynamics: load first dynamics model into the editor
    const dynamics = Array.isArray(exp.dynamics) ? exp.dynamics : (exp.model ? [exp.model] : []);
    if (dynamics.length > 0 && window.initializeBuilder) {
      const dyn = dynamics[0];
      const baseModelSelect = document.getElementById('editorBaseModel');
      if (baseModelSelect) {
        for (const opt of baseModelSelect.options) {
          if (opt.dataset.name === dyn.name || opt.textContent.trim() === dyn.name) {
            baseModelSelect.value = opt.value;
            baseModelSelect.dispatchEvent(new Event('change'));
            break;
          }
        }
      }
    }

    // 6. Array sections: iterate API arrays, create rows via handlers
    for (const [key, config] of Object.entries(ARRAY_HANDLERS)) {
      const items = exp[key];
      if (!items || !Array.isArray(items) || items.length === 0) continue;
      // Clear existing rows
      const container = document.getElementById(config.containerId);
      if (container) container.innerHTML = '';
      // Create rows from data
      items.forEach(item => {
        if (typeof item === 'object') {
          config.handler(item);
        }
      });
    }

    // 7. Update YAML preview
    setTimeout(() => {
      if (window.initializePreviewTab) window.initializePreviewTab();
      if (window.updateLiveYaml) window.updateLiveYaml();
    }, 300);

    console.log('[Prefill] Experiment loaded successfully');
  }

  window.prefillExperiment = prefillExperiment;
  window.prefillSection = prefillSection;
  window.collectSection = collectSection;

  // Initialize tab content renderers
  function initializeIntegratorTab() {
    const content = document.getElementById('integratorContent');
    if (!content) return;
    // Don't re-initialize if already populated (preserves prefilled values)
    if (content.dataset.initialized === 'true') return;
    content.dataset.initialized = 'true';

    const integrators = window.integratorsData || [];
    content.dataset.section = 'integration';
    content.innerHTML = `
      <div class="builder-field">
        <label>Load Existing Integrator</label>
        <select id="integratorSelect" class="builder-select">
          <option value="">— Create new or select existing —</option>
          ${integrators.map(i => `<option value="${i.id}">${escapeHtml(i.name || i.method)}</option>`).join('')}
        </select>
      </div>
      <div class="row g-3">
        <div class="col-md-4">
          <label class="form-label fw-bold">Method</label>
          <select id="integratorMethod" class="form-select" data-field="method">
            <option value="">— Select —</option>
            <option value="Euler">Euler</option>
            <option value="Heun">Heun</option>
            <option value="RungeKutta4">Runge-Kutta 4</option>
            <option value="Dopri5">Dormand-Prince 5</option>
            <option value="Dopri853">Dormand-Prince 853</option>
            <option value="EulerStochastic">Euler Stochastic</option>
            <option value="HeunStochastic">Heun Stochastic</option>
          </select>
        </div>
        <div class="col-md-4">
          <label class="form-label fw-bold">Step Size (dt)</label>
          <input id="integratorStepSize" type="number" step="0.001" class="form-control" placeholder="0.0122" data-field="step_size" />
        </div>
        <div class="col-md-4">
          <label class="form-label fw-bold">Duration (ms)</label>
          <input id="integratorDuration" type="number" class="form-control" placeholder="1000" data-field="duration" />
        </div>
      </div>
      <div class="row g-3 mt-2">
        <div class="col-md-4">
          <label class="form-label">Transient Time (ms)</label>
          <input id="integratorTransientTime" type="number" class="form-control" placeholder="0" data-field="transient_time" />
          <small class="text-muted">Warmup time to discard before recording</small>
        </div>
        <div class="col-md-4">
          <label class="form-label">Noise Seed</label>
          <input id="integratorNoiseSeed" type="number" class="form-control" placeholder="0" data-field="noise_seed" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Number of Stages</label>
          <input id="integratorNStages" type="number" class="form-control" placeholder="1" min="1" data-field="number_of_stages" />
        </div>
      </div>
      <div class="row g-3 mt-2">
        <div class="col-md-4">
          <label class="form-label">Time Scale</label>
          <input id="integratorTimeScale" type="text" class="form-control" placeholder="ms" data-field="time_scale" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Time Unit</label>
          <input id="integratorTimeUnit" type="text" class="form-control" placeholder="ms" data-field="unit" />
        </div>
        <div class="col-md-4 d-flex align-items-end">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" id="integratorDelayAware" data-field="delayed" />
            <label class="form-check-label" for="integratorDelayAware">Delay-Aware</label>
          </div>
        </div>
      </div>
      <div class="mt-3">
        <label class="form-label">Description</label>
        <textarea id="integratorDescription" class="form-control" rows="2" placeholder="Integrator description..." data-field="description"></textarea>
      </div>
    `;

    // Handle loading existing integrator
    const select = content.querySelector('#integratorSelect');
    select?.addEventListener('change', async (e) => {
      if (!e.target.value) return;
      try {
        const resp = await fetch(`/tvbo/api/configurator/integrators`);
        const result = await resp.json();
        if (result.success) {
          const integrator = result.data.find(i => i.id == e.target.value);
          if (integrator) prefillIntegrator(integrator);
        }
      } catch (err) { console.error('Error loading integrator:', err); }
    });
  }

  function prefillIntegrator(data) {
    if (!data) return;
    prefillSection('integration', data);
  }

  function initializeCouplingTab() {
    const content = document.getElementById('couplingContent');
    if (!content) return;
    if (content.dataset.initialized === 'true') return;
    content.dataset.initialized = 'true';

    const couplings = window.couplingsData || [];
    content.dataset.section = 'coupling';
    content.innerHTML = `
      <div class="builder-field">
        <label>Load Existing Coupling Function</label>
        <select id="couplingSelect" class="form-select">
          <option value="">— Create new or select existing —</option>
          ${couplings.map(c => `<option value="${c.id}">${escapeHtml(c.label || c.name)}</option>`).join('')}
        </select>
      </div>
      <div class="row g-3 mt-2">
        <div class="col-md-6">
          <label class="form-label fw-bold">Coupling Name</label>
          <input id="couplingName" class="form-control" placeholder="Linear" data-field="name" />
        </div>
        <div class="col-md-3">
          <label class="form-label fw-bold">Label</label>
          <input id="couplingLabel" class="form-control" placeholder="Linear Coupling" data-field="label" />
        </div>
        <div class="col-md-3 d-flex align-items-end">
          <div class="form-check">
            <input class="form-check-input" type="checkbox" id="couplingDelayed" data-field="delayed" />
            <label class="form-check-label" for="couplingDelayed">Delayed (transmission delays)</label>
          </div>
        </div>
      </div>
      <div class="mt-3">
        <label class="form-label">Description</label>
        <textarea id="couplingDescription" class="form-control" rows="2" placeholder="Coupling function description..." data-field="description"></textarea>
      </div>
      <div class="row g-3 mt-2">
        <div class="col-md-6">
          <label class="form-label fw-bold">Pre-Expression (before matrix multiply)</label>
          <input id="couplingPreExpr" class="form-control font-monospace" placeholder="e.g., local_states" data-field="pre_expression" />
          <small class="text-muted">Applied to state before matrix multiplication</small>
        </div>
        <div class="col-md-6">
          <label class="form-label fw-bold">Post-Expression (after matrix multiply)</label>
          <input id="couplingPostExpr" class="form-control font-monospace" placeholder="e.g., G * gx" data-field="post_expression" />
          <small class="text-muted">Applied after matrix multiplication</small>
        </div>
      </div>
      <div class="row g-3 mt-2">
        <div class="col-md-4">
          <label class="form-label">Source Variables (comma-sep)</label>
          <input id="couplingSourceVars" class="form-control" placeholder="S_e" data-field="source_variables" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Target Variables (comma-sep)</label>
          <input id="couplingTargetVars" class="form-control" placeholder="S_e, S_i" data-field="target_variables" />
        </div>
        <div class="col-md-4">
          <label class="form-label">Aggregation</label>
          <select id="couplingAggregation" class="form-select" data-field="aggregation_method">
            <option value="">Default</option>
            <option value="sum">Sum</option>
            <option value="mean">Mean</option>
            <option value="max">Max</option>
          </select>
        </div>
      </div>

      <h6 class="mt-4">Coupling Parameters</h6>
      <div class="row g-2 mb-1 small text-muted fw-bold">
        <div class="col-2">Name</div>
        <div class="col-2">Value</div>
        <div class="col-1">Unit</div>
        <div class="col-1">Min</div>
        <div class="col-1">Max</div>
        <div class="col-1">Free</div>
        <div class="col-3">Description</div>
        <div class="col-1"></div>
      </div>
      <div id="couplingParamsContainer"></div>
      <button class="btn btn-sm btn-outline-secondary mt-2" id="addCouplingParam">+ Add Parameter</button>
    `;

    // Add coupling parameter row
    function createCouplingParamRow(p = {}) {
      const div = document.createElement('div');
      div.className = 'row g-1 mb-2 cp-row align-items-center';
      const lo = p.domain?.lo ?? '';
      const hi = p.domain?.hi ?? '';
      div.innerHTML = `
        <div class="col-2"><input type="text" class="form-control form-control-sm cp-name" placeholder="G" value="${escapeAttr(p.name || '')}"/></div>
        <div class="col-2"><input type="text" class="form-control form-control-sm cp-value" placeholder="1.0" value="${escapeAttr(p.value ?? '')}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm cp-unit" placeholder="" value="${escapeAttr(p.unit || '')}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm cp-lo" placeholder="-∞" value="${escapeAttr(lo)}"/></div>
        <div class="col-1"><input type="text" class="form-control form-control-sm cp-hi" placeholder="∞" value="${escapeAttr(hi)}"/></div>
        <div class="col-1"><input type="checkbox" class="form-check-input cp-free" ${p.free ? 'checked' : ''}/></div>
        <div class="col-3"><input type="text" class="form-control form-control-sm cp-desc" placeholder="description" value="${escapeAttr(p.description || p.label || '')}"/></div>
        <div class="col-1"><button class="btn btn-sm btn-outline-danger remove-row">✕</button></div>
      `;
      div.querySelector('.remove-row').addEventListener('click', () => div.remove());
      return div;
    }
    // Expose for prefill
    window._createCouplingParamRow = createCouplingParamRow;

    content.querySelector('#addCouplingParam')?.addEventListener('click', () => {
      content.querySelector('#couplingParamsContainer').appendChild(createCouplingParamRow());
    });

    // Handle loading existing coupling
    const select = content.querySelector('#couplingSelect');
    select?.addEventListener('change', async (e) => {
      if (!e.target.value) return;
      try {
        const couplings = window.couplingsData || [];
        const coupling = couplings.find(c => c.id == e.target.value);
        if (coupling) prefillCoupling(coupling);
      } catch (err) { console.error('Error loading coupling:', err); }
    });
  }

  function prefillCoupling(data) {
    if (!data) return;
    prefillSection('coupling', data);
    // Coupling parameters (array sub-section)
    const container = document.getElementById('couplingParamsContainer');
    if (container && data.parameters) {
      container.innerHTML = '';
      const params = Array.isArray(data.parameters) ? data.parameters : [];
      params.forEach(p => {
        const param = typeof p === 'object' ? p : { name: p };
        container.appendChild(window._createCouplingParamRow(param));
      });
    }
  }

  function initializeMonitorsTab() {
    const content = document.getElementById('monitorsContent');
    if (!content) return;

    const monitors = window.monitorsData || [];
    content.innerHTML = `
      <div class="builder-field">
        <label>Available Monitors</label>
        <div id="monitorsList">
          ${monitors.map(m => `
            <div class="form-check">
              <input class="form-check-input" type="checkbox" id="monitor_${m.id}" value="${m.id}">
              <label class="form-check-label" for="monitor_${m.id}">
                ${escapeHtml(m.label || m.name)} (period: ${m.period || 'default'})
              </label>
            </div>
          `).join('')}
        </div>
      </div>
      <div class="builder-field">
        <h5>Add New Monitor</h5>
        <label>Monitor Name</label>
        <input id="newMonitorName" class="builder-input" placeholder="Raw" />
      </div>
      <div class="builder-field">
        <label>Sampling Period</label>
        <input id="newMonitorPeriod" type="number" step="0.1" class="builder-input" placeholder="0.9765625" />
      </div>
      <div class="builder-actions">
        <button class="btn btn-sm btn-secondary" id="addMonitor">Add Monitor</button>
      </div>
    `;
  }

  function initializeObservationModelsTab() {
    const content = document.getElementById('observationModelsList');
    if (!content) return;

    const monitors = window.monitorsData || [];

    // Container for active observation models in the pipeline
    content.innerHTML = `
      <div id="observationPipeline" class="observation-pipeline" style="
        display: flex;
        flex-direction: row;
        gap: 15px;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 8px;
        min-height: 120px;
        overflow-x: auto;
        align-items: center;
      ">
        <div class="pipeline-placeholder" style="color: #6c757d; font-style: italic;">
          No observation models added yet. Click "Add Observation Model" below.
        </div>
      </div>
    `;

    // Setup add button handler
    const addButton = document.getElementById('addObservationModel');
    if (addButton) {
      addButton.onclick = function() {
        showObservationModelSelector(monitors);
      };
    }
  }

  // Dynamic form builder using Pydantic schema
  async function fetchModelSchema(modelName) {
    try {
      const response = await fetch('/tvbo/api/schema/model/' + modelName, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          params: {}
        })
      });
      const data = await response.json();
      return data.result;
    } catch (error) {
      console.error('Error fetching schema:', error);
      return null;
    }
  }

  function createFormField(fieldDef, idPrefix) {
    const fieldId = idPrefix + '_' + fieldDef.name;
    let inputHtml = '';

    if (fieldDef.enum_values) {
      // Enum field - dropdown
      inputHtml = `
        <select id="${fieldId}" class="builder-select" style="width: 100%;" ${fieldDef.required ? 'required' : ''}>
          <option value="">— Select ${fieldDef.name} —</option>
          ${fieldDef.enum_values.map(ev => `<option value="${ev.value}">${ev.label}</option>`).join('')}
        </select>
      `;
    } else if (fieldDef.type === 'boolean') {
      inputHtml = `
        <input type="checkbox" id="${fieldId}" class="builder-checkbox" />
      `;
    } else if (fieldDef.type === 'integer') {
      inputHtml = `
        <input type="number" id="${fieldId}" class="builder-input" step="1"
               placeholder="${fieldDef.default || ''}" style="width: 100%;"
               ${fieldDef.required ? 'required' : ''} />
      `;
    } else if (fieldDef.type === 'float') {
      inputHtml = `
        <input type="number" id="${fieldId}" class="builder-input" step="0.01"
               placeholder="${fieldDef.default || ''}" style="width: 100%;"
               ${fieldDef.required ? 'required' : ''} />
      `;
    } else if (fieldDef.type === 'string') {
      if (fieldDef.description && fieldDef.description.length > 100) {
        // Long description - textarea
        inputHtml = `
          <textarea id="${fieldId}" class="builder-input" rows="2"
                    placeholder="${fieldDef.default || ''}" style="width: 100%;"
                    ${fieldDef.required ? 'required' : ''}></textarea>
        `;
      } else {
        inputHtml = `
          <input type="text" id="${fieldId}" class="builder-input"
                 placeholder="${fieldDef.default || ''}" style="width: 100%;"
                 ${fieldDef.required ? 'required' : ''} />
        `;
      }
    } else if (fieldDef.type === 'object') {
      // Nested object - show as placeholder for now
      inputHtml = `
        <input type="text" id="${fieldId}" class="builder-input"
               placeholder="Configure ${fieldDef.name}..." style="width: 100%;" readonly />
        <small class="text-muted">Complex object (not yet editable)</small>
      `;
    } else if (fieldDef.is_list) {
      // List field - show as placeholder
      inputHtml = `
        <input type="text" id="${fieldId}" class="builder-input"
               placeholder="Add ${fieldDef.name}..." style="width: 100%;" readonly />
        <small class="text-muted">List field (configure after creation)</small>
      `;
    } else {
      // Fallback
      inputHtml = `
        <input type="text" id="${fieldId}" class="builder-input"
               placeholder="${fieldDef.default || ''}" style="width: 100%;" />
      `;
    }

    const requiredMarker = fieldDef.required ? '<span style="color: red;">*</span>' : '';
    const descriptionHtml = fieldDef.description
      ? `<small class="text-muted">${escapeHtml(fieldDef.description)}</small>`
      : '';

    return `
      <div class="builder-field" style="margin-bottom: 12px;">
        <label style="font-size: 0.9em; font-weight: 600;">
          ${fieldDef.name} ${requiredMarker}
        </label>
        ${inputHtml}
        ${descriptionHtml}
      </div>
    `;
  }

  function collectFormData(fieldDefs, idPrefix) {
    const data = {};
    fieldDefs.forEach(fieldDef => {
      const fieldId = idPrefix + '_' + fieldDef.name;
      const element = document.getElementById(fieldId);
      if (!element) return;

      if (fieldDef.type === 'boolean') {
        data[fieldDef.name] = element.checked;
      } else if (fieldDef.type === 'integer') {
        const val = parseInt(element.value);
        if (!isNaN(val)) data[fieldDef.name] = val;
      } else if (fieldDef.type === 'float') {
        const val = parseFloat(element.value);
        if (!isNaN(val)) data[fieldDef.name] = val;
      } else {
        const val = element.value.trim();
        if (val) data[fieldDef.name] = val;
      }
    });
    return data;
  }

  async function showObservationModelSelector(monitors) {
    // Create inline form instead of modal
    const pipeline = document.getElementById('observationPipeline');
    if (!pipeline) return;

    // Check if form already exists
    if (document.getElementById('observationModelForm')) return;

    // Remove placeholder if exists
    const placeholder = pipeline.querySelector('.pipeline-placeholder');
    if (placeholder) placeholder.remove();

    // Fetch Monitor schema dynamically
    const schema = await fetchModelSchema('Monitor');
    if (!schema) {
      alert('Could not load Monitor schema');
      return;
    }

    // Filter fields to show (skip complex nested objects for now)
    const simpleFields = schema.fields.filter(f =>
      !['parameters', 'environment', 'transformation', 'pipeline',
        'data_injections', 'argument_mappings', 'derivatives', 'equation'].includes(f.name)
    );

    // Generate form HTML dynamically
    const formFieldsHtml = simpleFields.map(field => createFormField(field, 'modal')).join('');

    // Create inline form
    const formCard = document.createElement('div');
    formCard.id = 'observationModelForm';
    formCard.style.cssText = `
      background: #fff3cd;
      border: 2px dashed #ffc107;
      border-radius: 8px;
      padding: 20px;
      min-width: 400px;
      max-width: 600px;
    `;

    formCard.innerHTML = `
      <div style="font-weight: bold; margin-bottom: 15px; font-size: 1.1em;">Configure Monitor / Observation Model</div>
      <div style="font-size: 0.85em; margin-bottom: 12px; color: #666;">
        <strong>Schema:</strong> ${schema.name} <br>
        <em>${schema.doc || 'Observation model for monitoring simulation output'}</em>
      </div>

      ${formFieldsHtml}

      <div style="display: flex; gap: 8px; margin-top: 15px;">
        <button class="btn btn-sm btn-primary" id="confirmAddModel">Add Model</button>
        <button class="btn btn-sm btn-secondary" id="cancelAddModel">Cancel</button>
      </div>

      <div style="margin-top: 10px; padding: 10px; background: #e7f3ff; border-left: 3px solid #0066cc; font-size: 0.85em;">
        <strong>Note:</strong> After adding, you can configure the processing pipeline and complex attributes on the model card.
      </div>
    `;

    pipeline.appendChild(formCard);

    // Setup confirm button
    document.getElementById('confirmAddModel').onclick = function() {
      const formData = collectFormData(simpleFields, 'modal');

      // Validate required fields
      const missingRequired = simpleFields
        .filter(f => f.required && !formData[f.name])
        .map(f => f.name);

      if (missingRequired.length > 0) {
        alert(`Please fill in required fields: ${missingRequired.join(', ')}`);
        return;
      }

      // Add observation model with collected data
      addObservationModelToPipeline({
        id: Date.now(),
        ...formData,
        // Initialize schema-aligned structures
        transformation: null,
        pipeline: [],
        dataInjections: [],
        argumentMappings: [],
        derivatives: [],
        parameters: []
      });

      formCard.remove();
    };

    // Setup cancel button
    document.getElementById('cancelAddModel').onclick = function() {
      formCard.remove();
      // Restore placeholder if pipeline is empty
      if (pipeline.children.length === 0) {
        pipeline.innerHTML = '<div class="pipeline-placeholder" style="color: #6c757d; font-style: italic;">No observation models added yet. Click "Add Observation Model" below.</div>';
      }
    };
  }

  function addObservationModelToPipeline(modelData) {
    const pipeline = document.getElementById('observationPipeline');
    if (!pipeline) return;

    // Remove placeholder if exists
    const placeholder = pipeline.querySelector('.pipeline-placeholder');
    if (placeholder) placeholder.remove();

    // Initialize schema-aligned structures if not exist
    if (!modelData.pipeline) modelData.pipeline = [];
    if (!modelData.dataInjections) modelData.dataInjections = [];
    if (!modelData.argumentMappings) modelData.argumentMappings = [];
    if (!modelData.derivatives) modelData.derivatives = [];

    // Create model card
    const modelCard = document.createElement('div');
    modelCard.className = 'observation-model-card';
    modelCard.dataset.modelId = modelData.id;
    modelCard.style.cssText = `
      background: white;
      border: 2px solid #0d6efd;
      border-radius: 8px;
      padding: 15px;
      min-width: 300px;
      max-width: 400px;
      position: relative;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    `;

    // Build pipeline steps HTML
    const pipelineHtml = modelData.pipeline.length > 0
      ? modelData.pipeline.map((step, idx) => `
          <div style="font-size: 0.8em; padding: 4px 6px; background: #f8f9fa; margin-top: 4px; border-radius: 3px; display: flex; justify-content: space-between; align-items: center;">
            <span><strong>${step.order}.</strong> ${escapeHtml(step.operation_type || 'transform')}</span>
            <button class="btn btn-sm" style="padding: 0 4px; font-size: 0.8em;" onclick="removeProcessingStep(${modelData.id}, ${idx})">×</button>
          </div>
        `).join('')
      : '<div style="font-size: 0.8em; color: #6c757d; font-style: italic; margin-top: 4px;">No pipeline steps</div>';

    // Build basic info section
    let infoLines = [];
    if (modelData.label) infoLines.push(`Label: ${escapeHtml(modelData.label)}`);
    if (modelData.acronym) infoLines.push(`Acronym: ${escapeHtml(modelData.acronym)}`);
    if (modelData.description) infoLines.push(`Desc: ${escapeHtml(modelData.description)}`);
    if (modelData.imaging_modality) infoLines.push(`Modality: ${modelData.imaging_modality}`);
    if (modelData.time_scale) infoLines.push(`Time: ${modelData.time_scale}`);

    const infoHtml = infoLines.length > 0
      ? `<div style="font-size: 0.75em; color: #666; margin-top: 6px;">${infoLines.join(' • ')}</div>`
      : '';

    // Handle name field
    const displayName = modelData.name || modelData.instanceName || 'Unnamed';
    const displayType = modelData.monitorLabel || 'Monitor';
    const displayPeriod = modelData.period || modelData.samplingPeriod || 'N/A';

    modelCard.innerHTML = `
      <button class="btn btn-sm btn-danger" style="position: absolute; top: 5px; right: 5px; padding: 2px 6px;"
              onclick="removeObservationModel(${modelData.id})">×</button>

      <div style="font-weight: bold; margin-bottom: 3px; font-size: 1.05em;">${escapeHtml(displayName)}</div>
      <div style="font-size: 0.85em; color: #6c757d; margin-bottom: 2px;">${escapeHtml(displayType)}</div>
      ${infoHtml}

      <div style="font-size: 0.8em; margin-top: 8px;">
        <span style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">
          Period: ${displayPeriod}
        </span>
      </div>

      <hr style="margin: 10px 0;">

      <div style="font-size: 0.85em; font-weight: bold; margin-bottom: 4px;">Processing Pipeline:</div>
      <div class="processing-steps-list" id="steps-${modelData.id}">
        ${pipelineHtml}
      </div>
      <button class="btn btn-sm btn-outline-primary" style="width: 100%; margin-top: 8px; font-size: 0.85em;"
              onclick="addProcessingStepToModel(${modelData.id})">+ Add Pipeline Step</button>

      <hr style="margin: 10px 0;">

      <div style="font-size: 0.8em; color: #666;">
        <div>Data Injections: ${modelData.dataInjections ? modelData.dataInjections.length : 0}</div>
        <div>Argument Mappings: ${modelData.argumentMappings ? modelData.argumentMappings.length : 0}</div>
        <div>Derivatives: ${modelData.derivatives ? modelData.derivatives.length : 0}</div>
      </div>
    `;

    // Add arrow between models if not first
    if (pipeline.children.length > 0) {
      const arrow = document.createElement('div');
      arrow.innerHTML = '→';
      arrow.style.cssText = 'font-size: 24px; color: #6c757d;';
      pipeline.appendChild(arrow);
    }

    pipeline.appendChild(modelCard);

    // Store model data globally for later access
    if (!window.observationModelsData) {
      window.observationModelsData = {};
    }
    window.observationModelsData[modelData.id] = modelData;
  }

  // Global functions for managing observation models and steps
  window.removeObservationModel = function(modelId) {
    const card = document.querySelector(`.observation-model-card[data-model-id="${modelId}"]`);
    if (card) {
      // Remove arrow before this card if it exists
      const prevSibling = card.previousElementSibling;
      if (prevSibling && prevSibling.innerHTML === '→') {
        prevSibling.remove();
      }
      // Or remove arrow after if this is first card
      const nextSibling = card.nextElementSibling;
      if (nextSibling && nextSibling.innerHTML === '→') {
        nextSibling.remove();
      }
      card.remove();
    }

    // Remove from data store
    if (window.observationModelsData) {
      delete window.observationModelsData[modelId];
    }

    // Restore placeholder if pipeline is empty
    const pipeline = document.getElementById('observationPipeline');
    if (pipeline && pipeline.children.length === 0) {
      pipeline.innerHTML = '<div class="pipeline-placeholder" style="color: #6c757d; font-style: italic;">No observation models added yet. Click "Add Observation Model" below.</div>';
    }
  };

  window.addProcessingStepToModel = function(modelId) {
    const modelData = window.observationModelsData?.[modelId];
    if (!modelData) return;

    // Create inline form for adding processing step
    const stepsList = document.getElementById(`steps-${modelId}`);
    if (!stepsList) return;

    // Check if form already exists
    if (document.getElementById(`step-form-${modelId}`)) return;

    const formHtml = `
      <div id="step-form-${modelId}" style="background: #fff3cd; padding: 8px; margin-top: 8px; border-radius: 4px; border: 1px dashed #ffc107;">
        <div style="font-size: 0.85em; margin-bottom: 6px;">
          <label style="display: block; margin-bottom: 2px;">Operation Type</label>
          <select id="stepOpType-${modelId}" class="builder-select" style="width: 100%; font-size: 0.85em;">
            <option value="subsample">Subsample</option>
            <option value="temporal_average">Temporal Average</option>
            <option value="projection">Projection</option>
            <option value="convolution">Convolution</option>
            <option value="select">Select</option>
            <option value="custom_transform">Custom Transform</option>
          </select>
        </div>
        <div style="font-size: 0.85em; margin-bottom: 6px;">
          <label style="display: block; margin-bottom: 2px;">Function/Transform</label>
          <input id="stepFunction-${modelId}" class="builder-input" placeholder="e.g., downsample" style="width: 100%; font-size: 0.85em;" />
        </div>
        <div style="display: flex; gap: 4px; margin-top: 6px;">
          <button class="btn btn-sm btn-success" style="font-size: 0.8em;" onclick="confirmAddProcessingStep(${modelId})">Add</button>
          <button class="btn btn-sm btn-secondary" style="font-size: 0.8em;" onclick="cancelAddProcessingStep(${modelId})">Cancel</button>
        </div>
      </div>
    `;

    stepsList.insertAdjacentHTML('beforeend', formHtml);
  };

  window.confirmAddProcessingStep = function(modelId) {
    const modelData = window.observationModelsData?.[modelId];
    if (!modelData) return;

    const opType = document.getElementById(`stepOpType-${modelId}`)?.value;
    const func = document.getElementById(`stepFunction-${modelId}`)?.value;

    if (!opType) {
      alert('Please select an operation type');
      return;
    }

    const newStep = {
      order: modelData.pipeline.length + 1,
      operation_type: opType,
      function: func || opType,
      input_mapping: [],
      output_alias: null,
      apply_on_dimension: null,
      ensure_shape: null,
      variables_of_interest: []
    };

    modelData.pipeline.push(newStep);

    // Remove form
    document.getElementById(`step-form-${modelId}`)?.remove();

    // Refresh the model card
    refreshObservationModelCard(modelId);
  };

  window.cancelAddProcessingStep = function(modelId) {
    document.getElementById(`step-form-${modelId}`)?.remove();
  };

  window.removeProcessingStep = function(modelId, stepIndex) {
    const modelData = window.observationModelsData?.[modelId];
    if (!modelData) return;

    modelData.pipeline.splice(stepIndex, 1);

    // Re-order remaining steps
    modelData.pipeline.forEach((step, idx) => {
      step.order = idx + 1;
    });

    refreshObservationModelCard(modelId);
  };

  function refreshObservationModelCard(modelId) {
    const modelData = window.observationModelsData?.[modelId];
    if (!modelData) return;

    const stepsList = document.getElementById(`steps-${modelId}`);
    if (!stepsList) return;

    const stepsHtml = modelData.pipeline.length > 0
      ? modelData.pipeline.map((step, idx) => `
          <div style="font-size: 0.8em; padding: 4px 6px; background: #f8f9fa; margin-top: 4px; border-radius: 3px; display: flex; justify-content: space-between; align-items: center;">
            <span><strong>${step.order}.</strong> ${escapeHtml(step.operation_type || 'transform')} ${step.function ? '(' + escapeHtml(step.function) + ')' : ''}</span>
            <button class="btn btn-sm" style="padding: 0 4px; font-size: 0.8em;" onclick="removeProcessingStep(${modelId}, ${idx})">×</button>
          </div>
        `).join('')
      : '<div style="font-size: 0.8em; color: #6c757d; font-style: italic; margin-top: 4px;">No pipeline steps</div>';

    stepsList.innerHTML = stepsHtml;
  }

  function initializeNetworkTab() {
    // Handle mode switching between Custom and Brain Network
    const customPanel = document.getElementById('customNetworkPanel');
    const brainPanel = document.getElementById('brainNetworkPanel');
    const modeRadios = document.querySelectorAll('input[name="networkMode"]');

    if (!customPanel || !brainPanel) return;

    // Mode switching
    modeRadios.forEach(radio => {
      radio.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
          customPanel.style.display = 'block';
          brainPanel.style.display = 'none';
        } else if (e.target.value === 'brain') {
          customPanel.style.display = 'none';
          brainPanel.style.display = 'block';
        }
      });
    });

    // Populate tractogram dropdown from database
    const tractogramSelect = document.getElementById('brainTractogram');
    if (tractogramSelect && window.tractogramsData) {
      // Clear existing options except the first placeholder
      while (tractogramSelect.options.length > 1) {
        tractogramSelect.remove(1);
      }
      window.tractogramsData.forEach(tractogram => {
        const option = document.createElement('option');
        option.value = tractogram;
        option.textContent = tractogram;
        tractogramSelect.appendChild(option);
      });
      // Add custom option at the end
      const customOption = document.createElement('option');
      customOption.value = 'custom';
      customOption.textContent = 'Custom (upload below)';
      tractogramSelect.appendChild(customOption);
    }

    // Populate parcellation dropdown from database
    const parcellationSelect = document.getElementById('brainParcellation');
    if (parcellationSelect && window.parcellationsData) {
      // Clear existing options except the first placeholder
      while (parcellationSelect.options.length > 1) {
        parcellationSelect.remove(1);
      }
      window.parcellationsData.forEach(parc => {
        const option = document.createElement('option');
        option.value = parc.id;
        option.textContent = parc.label;
        parcellationSelect.appendChild(option);
      });
      // Add custom option at the end
      const customOption = document.createElement('option');
      customOption.value = 'custom';
      customOption.textContent = 'Custom (upload below)';
      parcellationSelect.appendChild(customOption);
    }

    // Initialize Custom Network node/edge builders
    initializeCustomNetworkBuilder();

    // Initialize file upload handlers
    initializeNetworkFileUploads();
  }

  function initializeCustomNetworkBuilder() {
    const nodesContainer = document.getElementById('customNetworkNodes');
    const edgesContainer = document.getElementById('customNetworkEdges');
    const addNodeBtn = document.getElementById('addCustomNode');
    const addEdgeBtn = document.getElementById('addCustomEdge');

    if (!nodesContainer || !edgesContainer) return;

    // Prevent multiple initializations
    if (addNodeBtn?.dataset.initialized === 'true') return;
    if (addNodeBtn) addNodeBtn.dataset.initialized = 'true';
    if (addEdgeBtn) addEdgeBtn.dataset.initialized = 'true';

    // Helper to get current nodes for edge dropdowns
    function getCurrentNodes() {
      const nodes = [];
      nodesContainer.querySelectorAll('.builder-row').forEach(row => {
        const id = row.dataset.nodeId || row.querySelector('.node-id')?.value || '';
        const label = row.querySelector('.node-label')?.value || '';
        nodes.push({ id, label: label || `Node ${id}` });
      });
      return nodes;
    }

    // Update all edge source/target dropdowns when nodes change
    function updateEdgeNodeOptions() {
      const nodes = getCurrentNodes();
      edgesContainer.querySelectorAll('.edge-source-select, .edge-target-select').forEach(select => {
        const currentValue = select.value;
        // Clear all but first option
        while (select.options.length > 1) {
          select.remove(1);
        }
        // Add node options
        nodes.forEach(node => {
          const option = document.createElement('option');
          option.value = node.id;
          option.textContent = `${node.id}: ${node.label}`;
          select.appendChild(option);
        });
        // Restore value if still valid
        select.value = currentValue;
      });
    }

    function createNodeRow(id = 0, label = '', x = '', y = '', z = '', dynamics = '') {
      // Get available models for the dropdown
      const allModels = window.searchData || [
        {name: 'Generic2dOscillator'}, {name: 'JansenRit'}, {name: 'WilsonCowan'}, {name: 'Epileptor'}
      ];

      const row = document.createElement('div');
      row.className = 'builder-row mb-2 p-2 border rounded bg-light d-flex align-items-center gap-2';
      row.dataset.nodeId = id;
      row.innerHTML = `
        <span class="badge bg-secondary py-2 px-3 flex-shrink-0">Node ${id}</span>
        <input type="hidden" class="node-id" value="${id}"/>
        <input class="form-control form-control-sm node-label" style="width: 120px;" value="${escapeAttr(label)}" placeholder="Label"/>
        <select class="form-select form-select-sm node-dynamics" style="width: 150px;">
          <option value="">Use configured model</option>
          ${allModels.map(m => {
            const name = m.name || m.label || m;
            return `<option value="${escapeAttr(name)}" ${dynamics === name ? 'selected' : ''}>${escapeHtml(name)}</option>`;
          }).join('')}
        </select>
        <input type="number" step="0.1" class="form-control form-control-sm node-x" style="width: 70px;" value="${x}" placeholder="X"/>
        <input type="number" step="0.1" class="form-control form-control-sm node-y" style="width: 70px;" value="${y}" placeholder="Y"/>
        <input type="number" step="0.1" class="form-control form-control-sm node-z" style="width: 70px;" value="${z}" placeholder="Z"/>
        <button class="btn btn-sm btn-outline-danger flex-shrink-0" title="Remove">×</button>
      `;
      row.querySelector('button').addEventListener('click', () => {
        row.remove();
        renumberNodes();
        updateEdgeNodeOptions();
        updateGraph3D();
      });
      row.querySelector('.node-label').addEventListener('input', updateEdgeNodeOptions);
      // Update 3D graph when coordinates change
      ['node-x', 'node-y', 'node-z'].forEach(cls => {
        row.querySelector('.' + cls)?.addEventListener('input', updateGraph3D);
      });
      return row;
    }

    // Update 3D visualization
    function updateGraph3D() {
      if (window.NetworkGraph3D && window.NetworkGraph3D.update) {
        window.NetworkGraph3D.update();
      }
    }

    // Renumber nodes after deletion to keep IDs sequential
    function renumberNodes() {
      const rows = nodesContainer.querySelectorAll('.builder-row');
      rows.forEach((row, idx) => {
        row.dataset.nodeId = idx;
        row.querySelector('.node-id').value = idx;
        row.querySelector('.badge').textContent = `Node ${idx}`;
      });
    }

    // Get configured coupling from the Network tab
    function getConfiguredCoupling() {
      const couplingSelect = document.querySelector('#couplingContent select');
      return couplingSelect?.value || 'Linear';
    }

    function createEdgeRow(source = '', target = '', weight = '', delay = '', couplingType = '') {
      const nodes = getCurrentNodes();
      const configuredCoupling = getConfiguredCoupling();
      const selectedCoupling = couplingType || '';

      const allCouplings = window.couplingsData || [
        {name: 'Linear'}, {name: 'Sigmoidal'}, {name: 'Difference'}, {name: 'Kuramoto'}
      ];

      const row = document.createElement('div');
      row.className = 'builder-row mb-2 p-2 border rounded bg-light d-flex align-items-center gap-2';
      row.innerHTML = `
        <select class="form-select form-select-sm edge-source-select" style="width: 150px;">
          <option value="">Source...</option>
          ${nodes.map(n => `<option value="${escapeAttr(n.id)}" ${source == n.id ? 'selected' : ''}>${n.id}: ${escapeHtml(n.label)}</option>`).join('')}
        </select>
        <span class="text-muted">→</span>
        <select class="form-select form-select-sm edge-target-select" style="width: 150px;">
          <option value="">Target...</option>
          ${nodes.map(n => `<option value="${escapeAttr(n.id)}" ${target == n.id ? 'selected' : ''}>${n.id}: ${escapeHtml(n.label)}</option>`).join('')}
        </select>
        <input type="number" step="0.01" class="form-control form-control-sm edge-weight" style="width: 80px;" value="${weight}" placeholder="Weight"/>
        <input type="number" step="0.1" class="form-control form-control-sm edge-delay" style="width: 80px;" value="${delay}" placeholder="Delay"/>
        <select class="form-select form-select-sm edge-coupling flex-grow-1">
          <option value="">Use configured (${escapeHtml(configuredCoupling)})</option>
          ${allCouplings.map(c => {
            const name = c.name || c.label || c;
            return `<option value="${escapeAttr(name)}" ${selectedCoupling === name ? 'selected' : ''}>${escapeHtml(name)}</option>`;
          }).join('')}
        </select>
        <button class="btn btn-sm btn-outline-danger flex-shrink-0" title="Remove">×</button>
      `;
      row.querySelector('button').addEventListener('click', () => row.remove());
      return row;
    }

    // Add initial node if empty
    if (nodesContainer.children.length === 0) {
      nodesContainer.appendChild(createNodeRow(0, '', '', '', '', ''));
    }

    // No default edges - user adds when they have multiple nodes
    if (edgesContainer.children.length === 0) {
      // Empty by default
    }

    addNodeBtn?.addEventListener('click', () => {
      const nodes = nodesContainer.querySelectorAll('.builder-row');
      const nextId = nodes.length;
      nodesContainer.appendChild(createNodeRow(nextId, '', '', '', '', ''));
      updateEdgeNodeOptions();
    });

    addEdgeBtn?.addEventListener('click', () => {
      edgesContainer.appendChild(createEdgeRow('', '', '', '', ''));
    });

    // Random network generator
    const generateRandomBtn = document.getElementById('generateRandomNetwork');
    const randomNodeCountInput = document.getElementById('randomNodeCount');

    // Actual surface vertices extracted from mni152_2009.obj
    // These are EXACT coordinates from the brain mesh file
    const brainSurfaceCoords = [
      [-65.5, -4.5, 16.5], [-63.9, -2.5, -5.5], [-62.0, -5.5, 6.6], [-60.0, -26.4, 48.5],
      [-57.7, -58.0, -22.5], [-55.0, -66.0, -16.7], [-53.6, 9.5, 42.0], [-52.8, -59.5, 20.0],
      [-51.1, -62.5, 7.5], [-49.5, -78.5, 32.0], [-48.5, -45.8, -27.0], [-47.0, 14.9, -40.0],
      [-46.0, -49.5, -44.5], [-45.0, -46.1, -41.0], [-44.0, -49.0, -11.3], [-43.0, -26.9, -28.5],
      [-42.5, 53.5, 19.1], [-41.0, 31.0, -17.5], [-39.5, 16.5, 28.0], [-38.0, -25.5, -11.5],
      [-36.5, -17.2, 41.0], [-35.0, 22.2, -7.5], [-33.1, -6.5, 57.0], [-32.5, 55.6, 7.0],
      [-30.5, -54.5, 44.0], [-29.5, 31.3, 49.0], [-28.8, 29.0, 54.5], [-28.0, 34.5, 49.0],
      [-26.6, -13.5, -23.5], [-24.0, -55.5, -19.5], [-23.3, -46.0, -19.5], [-22.0, -29.3, 77.0],
      [-21.0, -64.4, 70.0], [-18.5, -35.7, 5.5], [-18.0, 2.5, 68.8], [-16.5, -89.9, 29.5],
      [-15.0, 14.5, -18.0], [-14.0, 12.5, 21.5], [-13.0, -35.5, 12.0], [-12.0, 65.0, -12.9],
      [-11.3, -42.0, -29.0], [-10.0, -62.5, -40.1], [-9.5, 46.0, 8.3], [-8.0, 6.9, 12.5],
      [-7.0, -2.5, -15.6], [-5.5, 7.0, 28.7], [-4.5, -52.5, 30.6], [-4.0, 62.0, -5.0],
      [-3.0, 51.0, 11.8], [-2.5, -43.9, 48.5], [-2.0, 63.0, 19.5], [-1.0, -47.7, -6.5],
      [-0.4, 31.5, -19.5], [0.5, -60.0, 6.4], [1.5, 57.0, 34.5], [2.0, 21.2, 6.5],
      [2.5, -47.5, 38.5], [3.0, -17.9, -43.5], [3.4, 63.5, -23.0], [4.5, -89.8, 2.5],
      [5.5, -74.5, -27.6], [6.0, -74.7, -17.0], [7.5, 31.5, 25.1], [8.6, 73.0, 8.5],
      [9.5, -85.0, 44.3], [10.5, -30.5, -2.0], [12.5, -7.2, 75.0], [14.0, -98.0, 20.5],
      [15.5, 66.5, -0.7], [17.0, -33.8, -3.0], [18.2, -45.0, -17.0], [19.5, -62.5, 70.4],
      [20.5, 16.9, -26.0], [22.0, 32.0, -17.9], [23.5, 27.0, 61.5], [25.2, -36.5, -17.0],
      [26.0, -96.8, 19.5], [27.0, -43.0, -56.7], [29.1, -1.5, -37.5], [30.8, -77.0, 30.5],
      [33.0, 65.5, -12.5], [37.3, 31.0, 34.0], [39.3, -12.5, 3.5], [40.2, 0.5, 60.5],
      [41.0, -12.5, -38.6], [42.0, 41.8, 31.0], [43.5, -81.0, -35.9], [45.8, -45.5, -44.5],
      [47.5, -80.6, 12.5], [49.0, 49.0, 5.3], [49.5, -3.5, 55.6], [51.0, -31.5, 28.7],
      [52.3, 10.0, 5.5], [53.0, -22.5, 42.5], [54.5, -64.0, 13.5], [56.0, 37.9, 5.0],
      [58.9, -13.5, -38.0], [61.0, -56.5, 37.9], [62.0, -29.0, 40.5], [71.7, -35.5, -2.5],
    ];

    generateRandomBtn?.addEventListener('click', () => {
      const count = parseInt(randomNodeCountInput?.value) || 5;
      const nodeCount = Math.max(2, Math.min(count, brainSurfaceCoords.length)); // Clamp to available coords

      console.log('[ModelBuilder] Generating uniform network with', nodeCount, 'nodes using farthest-point sampling');

      // Clear existing nodes and edges
      nodesContainer.innerHTML = '';
      edgesContainer.innerHTML = '';

      // Farthest-point sampling for uniform distribution across cortex
      // Start with a random point, then iteratively pick the point farthest from all selected points
      const selectedIndices = [];
      const selectedCoords = [];

      // Helper: Euclidean distance squared
      const distSq = (a, b) => (a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2;

      // Start with a random first point
      const firstIdx = Math.floor(Math.random() * brainSurfaceCoords.length);
      selectedIndices.push(firstIdx);
      selectedCoords.push(brainSurfaceCoords[firstIdx]);

      // Iteratively select the point farthest from all already-selected points
      while (selectedCoords.length < nodeCount) {
        let maxMinDist = -1;
        let bestIdx = -1;

        for (let i = 0; i < brainSurfaceCoords.length; i++) {
          if (selectedIndices.includes(i)) continue;

          // Find minimum distance to any selected point
          let minDist = Infinity;
          for (const sel of selectedCoords) {
            const d = distSq(brainSurfaceCoords[i], sel);
            if (d < minDist) minDist = d;
          }

          // Track the point with the maximum minimum distance
          if (minDist > maxMinDist) {
            maxMinDist = minDist;
            bestIdx = i;
          }
        }

        if (bestIdx >= 0) {
          selectedIndices.push(bestIdx);
          selectedCoords.push(brainSurfaceCoords[bestIdx]);
        }
      }

      // Generate nodes at uniformly distributed brain surface positions
      const nodes = [];
      for (let i = 0; i < nodeCount; i++) {
        const [x, y, z] = selectedCoords[i];
        const label = `Region ${i + 1}`;
        nodes.push({ id: i, x, y, z, label });
        nodesContainer.appendChild(createNodeRow(i, label, x.toString(), y.toString(), z.toString(), ''));
      }

      // Generate random edges (small-world-ish: each node connects to ~2-4 others)
      const edgeSet = new Set();
      for (let i = 0; i < nodeCount; i++) {
        const numConnections = 2 + Math.floor(Math.random() * 3); // 2-4 connections
        for (let c = 0; c < numConnections; c++) {
          const target = Math.floor(Math.random() * nodeCount);
          if (target !== i) {
            const edgeKey = i < target ? `${i}-${target}` : `${target}-${i}`;
            if (!edgeSet.has(edgeKey)) {
              edgeSet.add(edgeKey);
              const weight = (0.5 + Math.random() * 0.5).toFixed(2);
              const delay = (1 + Math.random() * 5).toFixed(1);
              edgesContainer.appendChild(createEdgeRow(i.toString(), target.toString(), weight, delay, ''));
            }
          }
        }
      }

      console.log('[ModelBuilder] Generated', nodeCount, 'nodes and', edgeSet.size, 'edges');

      // Update edge dropdowns and 3D visualization
      updateEdgeNodeOptions();
      updateGraph3D();
    });
  }

  function initializeNetworkFileUploads() {
    // YAML upload for custom network
    const yamlUpload = document.getElementById('networkYamlUpload');
    yamlUpload?.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
          // Store the YAML content
          window.customNetworkYaml = event.target.result;
          alert('Network YAML loaded successfully!');
        };
        reader.readAsText(file);
      }
    });

    // Brain network file uploads
    const tractogramUpload = document.getElementById('brainTractogramUpload');
    tractogramUpload?.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        window.brainTractogramFile = file;
        alert(`Tractogram file loaded: ${file.name}`);
      }
    });

    const parcellationUpload = document.getElementById('brainParcellationUpload');
    parcellationUpload?.addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        window.brainParcellationFile = file;
        alert(`Parcellation file loaded: ${file.name}`);
      }
    });
  }

  function initializeStimulusTab() {
    const content = document.getElementById('stimulusContent');
    if (!content) return;

    content.dataset.section = 'stimulation';
    content.innerHTML = `
      <div class="builder-field">
        <label>Stimulus Type</label>
        <select id="stimulusType" class="builder-select" data-field="type">
          <option value="">None</option>
          <option value="PulseTrain">Pulse Train</option>
          <option value="DC">DC (Constant)</option>
          <option value="Sine">Sinusoidal</option>
        </select>
      </div>
      <div class="builder-field">
        <label>Amplitude</label>
        <input id="stimulusAmplitude" type="number" step="0.01" class="builder-input" placeholder="1.0" data-field="amplitude" />
      </div>
      <div class="builder-field">
        <label>Target Regions (comma-separated indices)</label>
        <input id="stimulusRegions" class="builder-input" placeholder="0,1,2" data-field="target_regions" />
      </div>
    `;
  }

  // ========================================================================
  // TAB INITIALIZERS: Functions, Observations, Algorithms, Optimization
  // ========================================================================

  function initializeFunctionsTab() {
    const content = document.getElementById('functionsContent');
    if (!content) return;

    content.innerHTML = `
      <div class="builder-field">
        <div class="builder-subtitle">Reusable Functions</div>
        <p class="text-muted" style="font-size: 0.9em;">
          Define functions once, reference by name in observations and algorithms. 
          Supports equation (symbolic), callable (Python function), or source_code.
        </p>
        <div id="functionsRows" class="builder-rows"></div>
        <div class="builder-actions">
          <button class="btn btn-sm btn-secondary" id="addFunction">Add Function</button>
        </div>
      </div>
    `;

    // Setup add button
    document.getElementById('addFunction')?.addEventListener('click', function() {
      addFunctionRow();
    });
  }

  function addFunctionRow(name = '', description = '', equation = '', module = '', callable = '') {
    const container = document.getElementById('functionsRows');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'builder-row';
    div.style.gridTemplateColumns = '1fr 2fr 1fr 1fr auto';
    div.innerHTML = `
      <input class="builder-input fn-name" placeholder="function_name" value="${escapeAttr(name)}" />
      <input class="builder-input fn-equation" placeholder="x + y" value="${escapeAttr(equation)}" />
      <input class="builder-input fn-module" placeholder="jax.numpy (optional)" value="${escapeAttr(module)}" />
      <input class="builder-input fn-callable" placeholder="mean (optional)" value="${escapeAttr(callable)}" />
      <button class="btn btn-sm btn-danger fn-del" title="Remove">✕</button>
    `;
    div.querySelector('.fn-del').addEventListener('click', () => div.remove());
    container.appendChild(div);
  }

  function initializeObservationsTab() {
    const content = document.getElementById('observationsContent');
    if (!content) return;

    content.innerHTML = `
      <div class="builder-field">
        <div class="builder-subtitle">Observations</div>
        <p class="text-muted" style="font-size: 0.9em;">
          Define what to observe from simulations: monitors (BOLD, EEG), metrics, or empirical data.
        </p>
        <div id="observationsRows" class="builder-rows"></div>
        <div class="builder-actions">
          <button class="btn btn-sm btn-secondary" id="addObservation">Add Observation</button>
        </div>
      </div>
    `;

    document.getElementById('addObservation')?.addEventListener('click', function() {
      addObservationRow();
    });
  }

  function addObservationRow(name = '', source = '', type = 'monitor', period = '') {
    const container = document.getElementById('observationsRows');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'builder-row';
    div.style.gridTemplateColumns = '1fr 1fr 1fr 1fr auto auto';
    div.innerHTML = `
      <input class="builder-input obs-name" placeholder="bold" value="${escapeAttr(name)}" />
      <select class="builder-select obs-type">
        <option value="monitor" ${type === 'monitor' ? 'selected' : ''}>Monitor</option>
        <option value="metric" ${type === 'metric' ? 'selected' : ''}>Metric</option>
        <option value="external" ${type === 'external' ? 'selected' : ''}>External Data</option>
      </select>
      <input class="builder-input obs-source" placeholder="state variable (e.g., S)" value="${escapeAttr(source)}" />
      <input class="builder-input obs-period" type="number" placeholder="period (ms)" value="${escapeAttr(period)}" />
      <button class="btn btn-sm btn-info obs-pipeline" title="Configure Pipeline">⚙️</button>
      <button class="btn btn-sm btn-danger obs-del" title="Remove">✕</button>
    `;
    div.querySelector('.obs-del').addEventListener('click', () => div.remove());
    div.querySelector('.obs-pipeline').addEventListener('click', () => {
      alert('Pipeline configuration UI - TBD');
    });
    container.appendChild(div);
  }

  function initializeDerivedObservationsTab() {
    const content = document.getElementById('derivedObservationsContent');
    if (!content) return;

    content.innerHTML = `
      <div class="builder-field">
        <div class="builder-subtitle">Derived Observations</div>
        <p class="text-muted" style="font-size: 0.9em;">
          Compute observations from other observations (e.g., FC from BOLD, loss from FC vs empirical).
        </p>
        <div id="derivedObservationsRows" class="builder-rows"></div>
        <div class="builder-actions">
          <button class="btn btn-sm btn-secondary" id="addDerivedObservation">Add Derived Observation</button>
        </div>
      </div>
    `;

    document.getElementById('addDerivedObservation')?.addEventListener('click', function() {
      addDerivedObservationRow();
    });
  }

  function addDerivedObservationRow(name = '', sources = '', pipeline = '') {
    const container = document.getElementById('derivedObservationsRows');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'builder-row';
    div.style.gridTemplateColumns = '1fr 2fr 2fr auto';
    div.innerHTML = `
      <input class="builder-input dobs-name" placeholder="fc" value="${escapeAttr(name)}" />
      <input class="builder-input dobs-sources" placeholder="source observations (comma-sep)" value="${escapeAttr(sources)}" />
      <input class="builder-input dobs-pipeline" placeholder="pipeline functions (comma-sep)" value="${escapeAttr(pipeline)}" />
      <button class="btn btn-sm btn-danger dobs-del" title="Remove">✕</button>
    `;
    div.querySelector('.dobs-del').addEventListener('click', () => div.remove());
    container.appendChild(div);
  }

  function initializeAlgorithmsTab() {
    const content = document.getElementById('algorithmsContent');
    if (!content) return;

    content.innerHTML = `
      <div class="builder-field">
        <div class="builder-subtitle">Iterative Tuning Algorithms</div>
        <p class="text-muted" style="font-size: 0.9em;">
          FIC, EIB, and custom iterative parameter tuning algorithms.
        </p>
        <div id="algorithmsRows" class="builder-rows"></div>
        <div class="builder-actions">
          <button class="btn btn-sm btn-secondary" id="addAlgorithm">Add Algorithm</button>
        </div>
      </div>
    `;

    document.getElementById('addAlgorithm')?.addEventListener('click', function() {
      addAlgorithmRow();
    });
  }

  function addAlgorithmRow(name = '', type = 'fic', nIter = '10', eta = '0.01') {
    const container = document.getElementById('algorithmsRows');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'builder-row';
    div.style.gridTemplateColumns = '1fr 1fr 0.8fr 0.8fr auto auto';
    div.innerHTML = `
      <input class="builder-input alg-name" placeholder="fic_tuning" value="${escapeAttr(name)}" />
      <select class="builder-select alg-type">
        <option value="fic" ${type === 'fic' ? 'selected' : ''}>FIC (Activity Target)</option>
        <option value="eib" ${type === 'eib' ? 'selected' : ''}>EIB (FC Matching)</option>
        <option value="custom" ${type === 'custom' ? 'selected' : ''}>Custom</option>
      </select>
      <input class="builder-input alg-niter" type="number" placeholder="iterations" value="${escapeAttr(nIter)}" />
      <input class="builder-input alg-eta" type="number" step="0.001" placeholder="learn rate" value="${escapeAttr(eta)}" />
      <button class="btn btn-sm btn-info alg-config" title="Configure Details">⚙️</button>
      <button class="btn btn-sm btn-danger alg-del" title="Remove">✕</button>
    `;
    div.querySelector('.alg-del').addEventListener('click', () => div.remove());
    div.querySelector('.alg-config').addEventListener('click', () => {
      alert('Algorithm configuration dialog - TBD');
    });
    container.appendChild(div);
  }

  function initializeOptimizationTab() {
    const content = document.getElementById('optimizationContent');
    if (!content) return;

    content.innerHTML = `
      <div class="builder-field">
        <div class="builder-subtitle">Optimization Configuration</div>
        <p class="text-muted" style="font-size: 0.9em;">
          Gradient-based parameter optimization (single or multi-stage).
        </p>
        <div id="optimizationRows" class="builder-rows"></div>
        <div class="builder-actions">
          <button class="btn btn-sm btn-secondary" id="addOptimization">Add Optimization Stage</button>
        </div>
      </div>
    `;

    document.getElementById('addOptimization')?.addEventListener('click', function() {
      addOptimizationRow();
    });
  }

  function addOptimizationRow(name = '', optimizer = 'adam', nIter = '100', lr = '0.01') {
    const container = document.getElementById('optimizationRows');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'builder-row';
    div.style.gridTemplateColumns = '1fr 1fr 0.8fr 0.8fr 2fr auto';
    div.innerHTML = `
      <input class="builder-input opt-name" placeholder="stage_name" value="${escapeAttr(name)}" />
      <select class="builder-select opt-optimizer">
        <option value="adam" ${optimizer === 'adam' ? 'selected' : ''}>Adam</option>
        <option value="sgd" ${optimizer === 'sgd' ? 'selected' : ''}>SGD</option>
        <option value="lbfgs" ${optimizer === 'lbfgs' ? 'selected' : ''}>L-BFGS</option>
      </select>
      <input class="builder-input opt-niter" type="number" placeholder="iterations" value="${escapeAttr(nIter)}" />
      <input class="builder-input opt-lr" type="number" step="0.001" placeholder="learn rate" value="${escapeAttr(lr)}" />
      <input class="builder-input opt-params" placeholder="target params (comma-sep)" />
      <button class="btn btn-sm btn-danger opt-del" title="Remove">✕</button>
    `;
    div.querySelector('.opt-del').addEventListener('click', () => div.remove());
    container.appendChild(div);
  }

  function initializeExplorationsTab() {
    const content = document.getElementById('explorationsContent');
    if (!content) return;

    content.innerHTML = `
      <div class="builder-field">
        <div class="builder-subtitle">Parameter Explorations</div>
        <p class="text-muted" style="font-size: 0.9em;">
          Grid search or parameter sweeps over defined ranges.
        </p>
        <div id="explorationsRows" class="builder-rows"></div>
        <div class="builder-actions">
          <button class="btn btn-sm btn-secondary" id="addExploration">Add Exploration</button>
        </div>
      </div>
    `;

    document.getElementById('addExploration')?.addEventListener('click', function() {
      addExplorationRow();
    });
  }

  function addExplorationRow(name = '', params = '', mode = 'product') {
    const container = document.getElementById('explorationsRows');
    if (!container) return;

    const div = document.createElement('div');
    div.className = 'builder-row';
    div.style.gridTemplateColumns = '1fr 2fr 1fr auto';
    div.innerHTML = `
      <input class="builder-input exp-name" placeholder="exploration_name" value="${escapeAttr(name)}" />
      <input class="builder-input exp-params" placeholder="params (e.g., a:0:1:10, b:0:1:10)" value="${escapeAttr(params)}" />
      <select class="builder-select exp-mode">
        <option value="product" ${mode === 'product' ? 'selected' : ''}>Grid (product)</option>
        <option value="zip" ${mode === 'zip' ? 'selected' : ''}>Paired (zip)</option>
      </select>
      <button class="btn btn-sm btn-danger exp-del" title="Remove">✕</button>
    `;
    div.querySelector('.exp-del').addEventListener('click', () => div.remove());
    container.appendChild(div);
  }

  function initializeExecutionTab() {
    const content = document.getElementById('executionContent');
    if (!content) return;

    content.dataset.section = 'execution';
    content.innerHTML = `
      <div class="builder-field">
        <div class="builder-subtitle">Execution Configuration</div>
        <p class="text-muted" style="font-size: 0.9em;">
          Configure parallelization, precision, and hardware settings.
        </p>
      </div>
      <div class="builder-field">
        <label>Number of Workers</label>
        <input id="execNWorkers" type="number" class="builder-input" placeholder="1" value="1" data-field="n_workers" />
      </div>
      <div class="builder-field">
        <label>Number of Threads</label>
        <input id="execNThreads" type="number" class="builder-input" placeholder="-1" value="-1" data-field="n_threads" />
      </div>
      <div class="builder-field">
        <label>Precision</label>
        <select id="execPrecision" class="builder-select" data-field="precision">
          <option value="float32">float32</option>
          <option value="float64" selected>float64</option>
        </select>
      </div>
      <div class="builder-field">
        <label>Accelerator</label>
        <select id="execAccelerator" class="builder-select" data-field="accelerator">
          <option value="cpu" selected>CPU</option>
          <option value="gpu">GPU</option>
          <option value="tpu">TPU</option>
        </select>
      </div>
      <div class="builder-field">
        <label>Batch Size</label>
        <input id="execBatchSize" type="number" class="builder-input" placeholder="0" value="0" data-field="batch_size" />
      </div>
      <div class="builder-field">
        <label>Random Seed</label>
        <input id="execRandomSeed" type="number" class="builder-input" placeholder="42" value="42" data-field="random_seed" />
      </div>
    `;
  }

  function initializePreviewTab() {
    const previewElement = document.getElementById('previewYaml');
    if (!previewElement) return;

    // Collect general fields using data-section/data-field
    const general = collectSection('general') || {};

    // Collect configuration from all tabs
    const config = {
      simulation_experiment: {
        name: general.name || 'Simulation Experiment',
        label: general.label || undefined,
        description: general.description || undefined,
        references: general.references || undefined,
        dynamics: collectDynamicsConfig(),
        network: collectNetworkConfig(),
        integration: collectIntegrationConfig(),
        observation_models: collectObservationModelsConfig(),
        stimulus: collectStimulusConfig(),
        functions: collectFunctionsConfig(),
        observations: collectObservationsConfig(),
        derived_observations: collectDerivedObservationsConfig(),
        algorithms: collectAlgorithmsConfig(),
        optimization: collectOptimizationConfig(),
        explorations: collectExplorationsConfig(),
        execution: collectExecutionConfig()
      }
    };

    // Convert to YAML-like format
    const yamlText = generateYamlPreview(config);
    previewElement.textContent = yamlText;
  }

  function collectDynamicsConfig() {
    // Try both possible element IDs for model selection
    const modelSelect = document.getElementById('modelSelect') || document.getElementById('builderModel');
    const modelName = modelSelect?.value;
    const specName = document.getElementById('builderSpecName')?.value?.trim();

    // Start with basic config
    const config = {};
    if (modelName) config.model = modelName;
    if (specName) config.name = specName;

    // Collect parameters from the model builder UI
    // Classes: p-name, p-value, p-unit, p-symbol, p-domain-lo, p-domain-hi
    const paramRows = document.querySelectorAll('#modelParamsRows .builder-row');
    if (paramRows.length > 0) {
      config.parameters = [];
      paramRows.forEach(row => {
        const name = row.querySelector('.p-name')?.value;
        const value = row.querySelector('.p-value')?.value;
        const unit = row.querySelector('.p-unit')?.value;
        const symbol = row.querySelector('.p-symbol')?.value;
        const domainLo = row.querySelector('.p-domain-lo')?.value;
        const domainHi = row.querySelector('.p-domain-hi')?.value;
        if (name) {
          const param = { name: name };
          if (value) param.value = parseFloat(value);
          if (unit) param.unit = unit;
          if (symbol) param.symbol = symbol;
          if (domainLo || domainHi) {
            param.domain = {};
            if (domainLo) param.domain.lo = parseFloat(domainLo);
            if (domainHi) param.domain.hi = parseFloat(domainHi);
          }
          config.parameters.push(param);
        }
      });
    }

    // Collect state variables from the model builder UI
    // Classes: sv-name, sv-expr, sv-symbol, sv-unit, sv-initial, sv-voi, sv-coupling
    const svRows = document.querySelectorAll('#stateEqRows .builder-row');
    if (svRows.length > 0) {
      config.state_variables = [];
      svRows.forEach(row => {
        const name = row.querySelector('.sv-name')?.value;
        const expr = row.querySelector('.sv-expr')?.value;
        const symbol = row.querySelector('.sv-symbol')?.value;
        const unit = row.querySelector('.sv-unit')?.value;
        const initial = row.querySelector('.sv-initial')?.value;
        const voi = row.querySelector('.sv-voi')?.checked;
        const coupling = row.querySelector('.sv-coupling')?.checked;
        if (name) {
          const sv = { name: name };
          if (expr) sv.equation = { rhs: expr };
          if (symbol) sv.symbol = symbol;
          if (unit) sv.unit = unit;
          if (initial) sv.initial_value = parseFloat(initial);
          if (voi !== undefined) sv.variable_of_interest = voi;
          if (coupling !== undefined) sv.coupling_variable = coupling;
          config.state_variables.push(sv);
        }
      });
    }

    // Collect derived parameters
    // Classes: dp-name, dp-expr, dp-unit
    const dpRows = document.querySelectorAll('#derivedParamsRows .builder-row');
    if (dpRows.length > 0) {
      config.derived_parameters = [];
      dpRows.forEach(row => {
        const name = row.querySelector('.dp-name')?.value;
        const expr = row.querySelector('.dp-expr')?.value;
        const unit = row.querySelector('.dp-unit')?.value;
        if (name) {
          const dp = { name: name };
          if (expr) dp.equation = { rhs: expr };
          if (unit) dp.unit = unit;
          config.derived_parameters.push(dp);
        }
      });
    }

    // Collect derived variables
    // Classes: dv-name, dv-expr, dv-unit
    const dvRows = document.querySelectorAll('#derivedVarsRows .builder-row');
    if (dvRows.length > 0) {
      config.derived_variables = [];
      dvRows.forEach(row => {
        const name = row.querySelector('.dv-name')?.value;
        const expr = row.querySelector('.dv-expr')?.value;
        const unit = row.querySelector('.dv-unit')?.value;
        if (name) {
          const dv = { name: name };
          if (expr) dv.equation = { rhs: expr };
          if (unit) dv.unit = unit;
          config.derived_variables.push(dv);
        }
      });
    }

    // Collect functions
    // Classes: fn-name, fn-expr
    const fnRows = document.querySelectorAll('#functionsRows .builder-row');
    if (fnRows.length > 0) {
      config.functions = [];
      fnRows.forEach(row => {
        const name = row.querySelector('.fn-name')?.value;
        const expr = row.querySelector('.fn-expr')?.value;
        if (name) {
          const fn = { name: name };
          if (expr) fn.equation = { rhs: expr };
          config.functions.push(fn);
        }
      });
    }

    return config;
  }

  function collectNetworkConfig() {
    // Check which mode is selected via radio buttons
    const customRadio = document.getElementById('networkModeCustom');
    const brainRadio = document.getElementById('networkModeBrain');

    // Determine mode from radio buttons, fallback to old select for backwards compat
    let networkMode = 'custom';
    if (brainRadio?.checked) {
      networkMode = 'brain';
    } else if (customRadio?.checked) {
      networkMode = 'custom';
    } else {
      // Fallback to old select element
      networkMode = document.getElementById('networkMode')?.value || 'custom';
    }

    if (networkMode === 'brain') {
      const tractogram = document.getElementById('brainTractogram');
      const parcellation = document.getElementById('brainParcellation');
      const numRegions = document.getElementById('brainNumRegions');
      const globalCoupling = document.getElementById('brainGlobalCoupling');
      const conductionSpeed = document.getElementById('brainConductionSpeed');

      return {
        mode: 'brain',
        tractogram: tractogram?.value || undefined,
        parcellation: parcellation?.value || undefined,
        number_of_regions: numRegions?.value ? parseInt(numRegions.value) : undefined,
        global_coupling_strength: globalCoupling?.value ? parseFloat(globalCoupling.value) : undefined,
        conduction_speed: conductionSpeed?.value ? parseFloat(conductionSpeed.value) : undefined
      };
    } else if (networkMode === 'custom') {
      const label = document.getElementById('customNetworkLabel')?.value;
      const globalCoupling = document.getElementById('customGlobalCoupling')?.value;
      const conductionSpeed = document.getElementById('customConductionSpeed')?.value;

      // Collect nodes
      const nodeRows = document.querySelectorAll('#customNetworkNodes .builder-row');
      const nodes = Array.from(nodeRows).map(row => ({
        id: parseInt(row.querySelector('.node-id')?.value) || 0,
        label: row.querySelector('.node-label')?.value || '',
        position: {
          x: parseFloat(row.querySelector('.node-x')?.value) || 0,
          y: parseFloat(row.querySelector('.node-y')?.value) || 0,
          z: parseFloat(row.querySelector('.node-z')?.value) || 0
        },
        dynamics: {
          name: row.querySelector('.node-dynamics')?.value || undefined,
          dataLocation: row.querySelector('.node-dynamics')?.value
            ? `database/models/${row.querySelector('.node-dynamics')?.value}.yaml`
            : undefined
        }
      }));

      // Collect edges
      const edgeRows = document.querySelectorAll('#customNetworkEdges .builder-row');
      const edges = Array.from(edgeRows).map(row => ({
        source: parseInt(row.querySelector('.edge-source-select')?.value) || 0,
        target: parseInt(row.querySelector('.edge-target-select')?.value) || 1,
        weight: parseFloat(row.querySelector('.edge-weight')?.value) || 1.0,
        delay: parseFloat(row.querySelector('.edge-delay')?.value) || 0,
        coupling: {
          name: row.querySelector('.edge-coupling')?.value || 'Linear'
        }
      }));

      // Check if YAML was uploaded
      if (window.customNetworkYaml) {
        return {
          mode: 'yaml',
          yaml_content: window.customNetworkYaml,
          source: 'yaml_file'
        };
      }

      // Only return if nodes defined
      if (nodes.length === 0) {
        return { mode: 'not configured' };
      }

      return {
        mode: 'custom',
        label: label || 'Custom Network',
        nodes: nodes,
        edges: edges,
        number_of_nodes: nodes.length,
        global_coupling_strength: globalCoupling ? parseFloat(globalCoupling) : 1.0,
        conduction_speed: conductionSpeed ? parseFloat(conductionSpeed) : 3.0
      };
    }

    return { mode: 'not configured' };
  }

  /**
   * Generic section collector: reads all [data-field] elements within a [data-section] container.
   * Symmetrical to prefillSection(). Auto-parses numbers.
   * NO hardcoded field names — adding a new field = add data-field attribute to HTML.
   */
  function collectSection(sectionName) {
    const container = document.querySelector(`[data-section="${sectionName}"]`);
    if (!container) return null;
    const config = {};
    container.querySelectorAll('[data-field]').forEach(el => {
      const field = el.dataset.field;
      let val;
      if (el.type === 'checkbox') {
        val = el.checked;
        if (!val) return; // skip false checkboxes
      } else {
        val = el.value?.trim();
        if (!val) return; // skip empty
        // Auto-parse numeric inputs
        if (el.type === 'number' && !isNaN(parseFloat(val))) val = parseFloat(val);
      }
      config[field] = val;
    });
    return Object.keys(config).length > 0 ? config : null;
  }

  function collectIntegrationConfig() {
    return collectSection('integration') || {};
  }

  function collectObservationModelsConfig() {
    const models = [];
    if (window.observationModelsData) {
      Object.values(window.observationModelsData).forEach(modelData => {
        const modelConfig = {
          name: modelData.name || modelData.instanceName || 'unnamed',
          monitor_type: modelData.monitorLabel || 'Monitor'
        };

        // Add all present fields dynamically (handle both naming conventions)
        const fieldMap = {
          'label': 'label',
          'acronym': 'acronym',
          'description': 'description',
          'imaging_modality': 'imaging_modality',
          'imagingModality': 'imaging_modality',
          'period': 'period',
          'samplingPeriod': 'period',
          'time_scale': 'time_scale',
          'timeScale': 'time_scale'
        };

        Object.keys(fieldMap).forEach(sourceKey => {
          if (modelData[sourceKey]) {
            modelConfig[fieldMap[sourceKey]] = modelData[sourceKey];
          }
        });

        // Add pipeline steps
        if (modelData.pipeline && modelData.pipeline.length > 0) {
          modelConfig.pipeline = modelData.pipeline.map(step => {
            const stepConfig = {
              order: step.order,
              operation_type: step.operation_type,
              function: step.function
            };
            if (step.output_alias) stepConfig.output_alias = step.output_alias;
            if (step.apply_on_dimension) stepConfig.apply_on_dimension = step.apply_on_dimension;
            if (step.ensure_shape) stepConfig.ensure_shape = step.ensure_shape;
            return stepConfig;
          });
        }

        // Add other ObservationModel attributes
        if (modelData.dataInjections && modelData.dataInjections.length > 0) {
          modelConfig.data_injections = modelData.dataInjections;
        }
        if (modelData.argumentMappings && modelData.argumentMappings.length > 0) {
          modelConfig.argument_mappings = modelData.argumentMappings;
        }
        if (modelData.derivatives && modelData.derivatives.length > 0) {
          modelConfig.derivatives = modelData.derivatives;
        }

        models.push(modelConfig);
      });
    }
    return models.length > 0 ? models : null;
  }

  function collectStimulusConfig() {
    return collectSection('stimulation');
  }

  // ========================================================================
  // COLLECTION FUNCTIONS: New Sections
  // ========================================================================

  function collectFunctionsConfig() {
    const fnRows = document.querySelectorAll('#functionsRows .builder-row');
    if (fnRows.length === 0) return null;

    const functions = [];
    fnRows.forEach(row => {
      const name = row.querySelector('.fn-name')?.value?.trim();
      const equation = row.querySelector('.fn-equation')?.value?.trim();
      const module = row.querySelector('.fn-module')?.value?.trim();
      const callable = row.querySelector('.fn-callable')?.value?.trim();

      if (name) {
        const fn = { name };
        if (equation) fn.equation = { rhs: equation };
        if (module && callable) {
          fn.callable = { module, name: callable };
        }
        functions.push(fn);
      }
    });

    return functions.length > 0 ? functions : null;
  }

  function collectObservationsConfig() {
    const obsRows = document.querySelectorAll('#observationsRows .builder-row');
    if (obsRows.length === 0) return null;

    const observations = [];
    obsRows.forEach(row => {
      const name = row.querySelector('.obs-name')?.value?.trim();
      const type = row.querySelector('.obs-type')?.value;
      const source = row.querySelector('.obs-source')?.value?.trim();
      const period = row.querySelector('.obs-period')?.value?.trim();

      if (name) {
        const obs = { name, type: type || 'monitor' };
        if (source) obs.source = source;
        if (period) obs.period = parseFloat(period);
        observations.push(obs);
      }
    });

    return observations.length > 0 ? observations : null;
  }

  function collectDerivedObservationsConfig() {
    const dobsRows = document.querySelectorAll('#derivedObservationsRows .builder-row');
    if (dobsRows.length === 0) return null;

    const derivedObs = [];
    dobsRows.forEach(row => {
      const name = row.querySelector('.dobs-name')?.value?.trim();
      const sources = row.querySelector('.dobs-sources')?.value?.trim();
      const pipeline = row.querySelector('.dobs-pipeline')?.value?.trim();

      if (name && sources) {
        const dobs = { name, source_observations: sources.split(',').map(s => s.trim()) };
        if (pipeline) {
          dobs.pipeline = pipeline.split(',').map(f => ({ function: f.trim() }));
        }
        derivedObs.push(dobs);
      }
    });

    return derivedObs.length > 0 ? derivedObs : null;
  }

  function collectAlgorithmsConfig() {
    const algRows = document.querySelectorAll('#algorithmsRows .builder-row');
    if (algRows.length === 0) return null;

    const algorithms = [];
    algRows.forEach(row => {
      const name = row.querySelector('.alg-name')?.value?.trim();
      const type = row.querySelector('.alg-type')?.value;
      const nIter = row.querySelector('.alg-niter')?.value?.trim();
      const eta = row.querySelector('.alg-eta')?.value?.trim();

      if (name) {
        const alg = { name, type: type || 'fic' };
        if (nIter) alg.n_iterations = parseInt(nIter);
        if (eta) alg.learning_rate = parseFloat(eta);
        algorithms.push(alg);
      }
    });

    return algorithms.length > 0 ? algorithms : null;
  }

  function collectOptimizationConfig() {
    const optRows = document.querySelectorAll('#optimizationRows .builder-row');
    if (optRows.length === 0) return null;

    const stages = [];
    optRows.forEach(row => {
      const name = row.querySelector('.opt-name')?.value?.trim();
      const optimizer = row.querySelector('.opt-optimizer')?.value;
      const nIter = row.querySelector('.opt-niter')?.value?.trim();
      const lr = row.querySelector('.opt-lr')?.value?.trim();
      const params = row.querySelector('.opt-params')?.value?.trim();

      if (name) {
        const stage = { name, optimizer: optimizer || 'adam' };
        if (nIter) stage.n_iterations = parseInt(nIter);
        if (lr) stage.learning_rate = parseFloat(lr);
        if (params) stage.target_parameters = params.split(',').map(p => p.trim());
        stages.push(stage);
      }
    });

    return stages.length > 0 ? stages : null;
  }

  function collectExplorationsConfig() {
    const expRows = document.querySelectorAll('#explorationsRows .builder-row');
    if (expRows.length === 0) return null;

    const explorations = [];
    expRows.forEach(row => {
      const name = row.querySelector('.exp-name')?.value?.trim();
      const params = row.querySelector('.exp-params')?.value?.trim();
      const mode = row.querySelector('.exp-mode')?.value;

      if (name && params) {
        const exp = { name, mode: mode || 'product' };
        // Parse params (format: "a:0:1:10, b:0:1:10")
        exp.parameters = params.split(',').map(p => {
          const parts = p.trim().split(':');
          if (parts.length === 4) {
            return {
              name: parts[0],
              domain: {
                lo: parseFloat(parts[1]),
                hi: parseFloat(parts[2]),
                n: parseInt(parts[3])
              }
            };
          }
          return null;
        }).filter(p => p !== null);

        if (exp.parameters.length > 0) {
          explorations.push(exp);
        }
      }
    });

    return explorations.length > 0 ? explorations : null;
  }

  function collectExecutionConfig() {
    return collectSection('execution');
  }

  function generateYamlPreview(config) {
    const exp = config.simulation_experiment;
    let yaml = 'simulation_experiment:';

    // Basic experiment fields
    if (exp.name) {
      yaml += `\n  name: "${exp.name}"`;
    }
    if (exp.label) {
      yaml += `\n  label: "${exp.label}"`;
    }
    if (exp.description) {
      yaml += `\n  description: "${exp.description}"`;
    }
    if (exp.references) {
      yaml += `\n  references: "${exp.references}"`;
    }

    // Dynamics - only show if configured
    const dynamics = exp.dynamics;
    if (dynamics && (dynamics.model || dynamics.name)) {
      yaml += `\n\n  local_dynamics:`;
      if (dynamics.model) yaml += `\n    name: ${dynamics.model}`;
      else if (dynamics.name) yaml += `\n    name: ${dynamics.name}`;

      // Show parameters if available
      if (dynamics.parameters && dynamics.parameters.length > 0) {
        yaml += `\n    parameters:`;
        dynamics.parameters.forEach(p => {
          yaml += `\n      - name: ${p.name}`;
          if (p.value !== undefined) yaml += `\n        value: ${p.value}`;
          if (p.unit) yaml += `\n        unit: "${p.unit}"`;
          if (p.symbol) yaml += `\n        symbol: "${p.symbol}"`;
          if (p.domain) {
            yaml += `\n        domain:`;
            if (p.domain.lo !== undefined) yaml += `\n          lo: ${p.domain.lo}`;
            if (p.domain.hi !== undefined) yaml += `\n          hi: ${p.domain.hi}`;
          }
        });
      }

      // Show state variables if available
      if (dynamics.state_variables && dynamics.state_variables.length > 0) {
        yaml += `\n    state_variables:`;
        dynamics.state_variables.forEach(sv => {
          yaml += `\n      - name: ${sv.name}`;
          if (sv.equation && sv.equation.rhs) yaml += `\n        equation: "${sv.equation.rhs}"`;
          if (sv.symbol) yaml += `\n        symbol: "${sv.symbol}"`;
          if (sv.unit) yaml += `\n        unit: "${sv.unit}"`;
          if (sv.initial_value !== undefined) yaml += `\n        initial_value: ${sv.initial_value}`;
          if (sv.variable_of_interest !== undefined) yaml += `\n        variable_of_interest: ${sv.variable_of_interest}`;
          if (sv.coupling_variable !== undefined) yaml += `\n        coupling_variable: ${sv.coupling_variable}`;
        });
      }

      // Show derived parameters if available
      if (dynamics.derived_parameters && dynamics.derived_parameters.length > 0) {
        yaml += `\n    derived_parameters:`;
        dynamics.derived_parameters.forEach(dp => {
          yaml += `\n      - name: ${dp.name}`;
          if (dp.equation && dp.equation.rhs) yaml += `\n        equation: "${dp.equation.rhs}"`;
          if (dp.unit) yaml += `\n        unit: "${dp.unit}"`;
        });
      }

      // Show derived variables if available
      if (dynamics.derived_variables && dynamics.derived_variables.length > 0) {
        yaml += `\n    derived_variables:`;
        dynamics.derived_variables.forEach(dv => {
          yaml += `\n      - name: ${dv.name}`;
          if (dv.equation && dv.equation.rhs) yaml += `\n        equation: "${dv.equation.rhs}"`;
          if (dv.unit) yaml += `\n        unit: "${dv.unit}"`;
        });
      }

      // Show functions if available
      if (dynamics.functions && dynamics.functions.length > 0) {
        yaml += `\n    functions:`;
        dynamics.functions.forEach(fn => {
          yaml += `\n      - name: ${fn.name}`;
          if (fn.equation && fn.equation.rhs) yaml += `\n        equation: "${fn.equation.rhs}"`;
        });
      }
    }

    // Network - only show if there's actual configured content
    const networkConfig = exp.network;
    const hasNetworkContent = networkConfig && (
      networkConfig.mode === 'custom' ||
      networkConfig.mode === 'yaml' ||
      networkConfig.mode === 'brain' ||
      (networkConfig.mode === 'standard' && (
        networkConfig.network_id ||
        networkConfig.parcellation ||
        networkConfig.tractogram ||
        networkConfig.number_of_regions ||
        networkConfig.global_coupling_strength ||
        networkConfig.conduction_speed
      ))
    );

    if (hasNetworkContent) {
      yaml += `\n\n  network:`;

      if (networkConfig.mode === 'brain') {
        if (networkConfig.tractogram) yaml += `\n    tractogram: "${networkConfig.tractogram}"`;
        if (networkConfig.parcellation) yaml += `\n    parcellation: "${networkConfig.parcellation}"`;
        if (networkConfig.number_of_regions) yaml += `\n    number_of_regions: ${networkConfig.number_of_regions}`;
        if (networkConfig.global_coupling_strength) {
          yaml += `\n    global_coupling_strength:`;
          yaml += `\n      name: global_coupling_strength`;
          yaml += `\n      value: ${networkConfig.global_coupling_strength}`;
        }
        if (networkConfig.conduction_speed) {
          yaml += `\n    conduction_speed:`;
          yaml += `\n      name: conduction_speed`;
          yaml += `\n      value: ${networkConfig.conduction_speed}`;
        }
      } else if (networkConfig.mode === 'custom') {
        if (networkConfig.label) yaml += `\n    label: "${networkConfig.label}"`;
        if (networkConfig.number_of_nodes) yaml += `\n    number_of_nodes: ${networkConfig.number_of_nodes}`;
        if (networkConfig.global_coupling_strength) {
          yaml += `\n    global_coupling_strength:`;
          yaml += `\n      name: global_coupling_strength`;
          yaml += `\n      value: ${networkConfig.global_coupling_strength}`;
        }
        if (networkConfig.conduction_speed) {
          yaml += `\n    conduction_speed:`;
          yaml += `\n      name: conduction_speed`;
          yaml += `\n      value: ${networkConfig.conduction_speed}`;
        }

        if (networkConfig.nodes && networkConfig.nodes.length > 0) {
          yaml += `\n    nodes:`;
          networkConfig.nodes.forEach(node => {
            yaml += `\n      - id: ${node.id}`;
            if (node.label) yaml += `\n        label: "${node.label}"`;
            if (node.region) yaml += `\n        region: "${node.region}"`;
            if (node.position) {
              yaml += `\n        position:`;
              yaml += `\n          x: ${node.position.x}`;
              yaml += `\n          y: ${node.position.y}`;
              yaml += `\n          z: ${node.position.z}`;
            }
            if (node.dynamics && node.dynamics.name) {
              yaml += `\n        dynamics:`;
              yaml += `\n          name: ${node.dynamics.name}`;
              if (node.dynamics.dataLocation) {
                yaml += `\n          dataLocation: ${node.dynamics.dataLocation}`;
              }
            }
          });
        }

        if (networkConfig.edges && networkConfig.edges.length > 0) {
          yaml += `\n    edges:`;
          networkConfig.edges.forEach(edge => {
            yaml += `\n      - source: ${edge.source}`;
            yaml += `\n        target: ${edge.target}`;
            if (edge.weight) yaml += `\n        weight: ${edge.weight}`;
            if (edge.delay) yaml += `\n        delay: ${edge.delay}`;
            if (edge.coupling && edge.coupling.name) {
              yaml += `\n        coupling:`;
              yaml += `\n          name: ${edge.coupling.name}`;
            }
          });
        }
      } else if (networkConfig.mode === 'yaml') {
        yaml += `\n    # Network loaded from YAML file`;
        yaml += `\n    source: yaml_file`;
      } else if (networkConfig.mode === 'standard') {
        if (networkConfig.network_id) yaml += `\n    name: ${networkConfig.network_id}`;
        if (networkConfig.parcellation) yaml += `\n    parcellation: "${networkConfig.parcellation}"`;
        if (networkConfig.tractogram) yaml += `\n    tractogram: "${networkConfig.tractogram}"`;
        if (networkConfig.number_of_regions) yaml += `\n    number_of_regions: ${networkConfig.number_of_regions}`;
        if (networkConfig.global_coupling_strength) {
          yaml += `\n    global_coupling_strength:`;
          yaml += `\n      name: global_coupling_strength`;
          yaml += `\n      value: ${networkConfig.global_coupling_strength}`;
        }
        if (networkConfig.conduction_speed) {
          yaml += `\n    conduction_speed:`;
          yaml += `\n      name: conduction_speed`;
          yaml += `\n      value: ${networkConfig.conduction_speed}`;
        }
        if (networkConfig.normalization) yaml += `\n    normalization: "${networkConfig.normalization}"`;
      }
    }

    // Integration - always include with defaults if not configured
    const integration = exp.integration || {};
    yaml += `\n\n  integration:`;
    yaml += `\n    method: ${integration.method || 'Heun'}`;
    yaml += `\n    step_size: ${integration.step_size || 0.1}`;
    yaml += `\n    duration: ${integration.duration || 100}`;

    // Monitors - only show if configured
    const monitors = exp.observation_models;
    if (monitors && Array.isArray(monitors) && monitors.length > 0) {
      yaml += `\n\n  monitors:`;
      monitors.forEach(m => {
        yaml += `\n    - name: ${m.name}`;
        if (m.monitor_type) yaml += `\n      monitor_type: ${m.monitor_type}`;
        if (m.period) yaml += `\n      period: ${m.period}`;
        if (m.label) yaml += `\n      label: "${m.label}"`;
        if (m.acronym) yaml += `\n      acronym: "${m.acronym}"`;
        if (m.description) yaml += `\n      description: "${m.description}"`;
        if (m.imaging_modality) yaml += `\n      imaging_modality: "${m.imaging_modality}"`;

        if (m.pipeline && m.pipeline.length > 0) {
          yaml += `\n      pipeline:`;
          m.pipeline.forEach(step => {
            yaml += `\n        - order: ${step.order}`;
            yaml += `\n          operation_type: ${step.operation_type}`;
            if (step.function) yaml += `\n          function: ${step.function}`;
            if (step.output_alias) yaml += `\n          output_alias: "${step.output_alias}"`;
            if (step.apply_on_dimension) yaml += `\n          apply_on_dimension: ${step.apply_on_dimension}`;
            if (step.ensure_shape) yaml += `\n          ensure_shape: ${step.ensure_shape}`;
          });
        }
      });
    }

    // Stimulus - only show if configured
    const stimulus = exp.stimulus;
    if (stimulus && stimulus.type && stimulus.type !== 'none') {
      yaml += `\n\n  stimulation:`;
      yaml += `\n    type: ${stimulus.type}`;
      if (stimulus.amplitude) yaml += `\n    amplitude: ${stimulus.amplitude}`;
      if (stimulus.target_regions && stimulus.target_regions.length > 0) {
        yaml += `\n    target_regions: [${stimulus.target_regions.join(', ')}]`;
      }
    }

    return yaml;
  }

  // ============================================
  // SIMULATION RUNNER
  // ============================================

  let simulationResults = null;

  /**
   * Collect the full experiment configuration for running a simulation.
   *
   * REQUIRED fields (must be configured):
   *   - local_dynamics.name: Model name (e.g., 'Generic2dOscillator', 'JansenRit')
   *     Source: Model tab -> Base Model dropdown OR custom model name
   *
   *   - network.nodes: At least 2 nodes with positions
   *     Source: Network tab -> Custom network nodes
   *     Each node needs: id, label, position {x, y, z}
   *
   *   - network.edges: Connections between nodes
   *     Source: Network tab -> Edges section
   *     Each edge needs: source, target, weight
   *
   * OPTIONAL fields (have sensible defaults):
   *   - local_dynamics.parameters: Model parameters
   *     Default: Uses model's default parameter values
   *
   *   - integration.method: Integrator type
   *     Default: 'Heun'
   *     Options: Euler, Heun, Dopri5, Dopri853
   *
   *   - integration.step_size: Time step in ms
   *     Default: 0.1 (can be overridden in Run tab)
   *
   *   - integration.duration: Simulation duration in ms
   *     Default: 1000.0 (can be overridden in Run tab)
   *
   *   - coupling.name: Coupling function
   *     Default: 'Linear'
   *
   *   - coupling.global_coupling: Global coupling strength
   *     Default: 1.0
   *
   *   - network.conduction_speed: Signal propagation speed (m/s)
   *     Default: 3.0
   *
   *   - monitors: Observation models / monitors
   *     Default: Raw monitor with period=1.0
   *
   *   - stimulus: External stimulation
   *     Default: None
   *
   * @returns {Object} Experiment configuration for TVBO API
   */
  function collectFullExperiment() {
    console.log('[ModelBuilder] collectFullExperiment called');

    // 1. Collect local dynamics (REQUIRED)
    const dynamicsConfig = collectDynamicsConfig();
    console.log('[ModelBuilder] dynamicsConfig:', dynamicsConfig);

    if (!dynamicsConfig.model && !dynamicsConfig.name) {
      throw new Error('No model selected. Please select or configure a model.');
    }

    const local_dynamics = {
      name: dynamicsConfig.model || dynamicsConfig.name,
    };

    // Collect parameters from the model builder UI
    const paramRows = document.querySelectorAll('#modelParamsRows .builder-row');
    if (paramRows.length > 0) {
      local_dynamics.parameters = [];
      paramRows.forEach(row => {
        const name = row.querySelector('.p-name')?.value;
        const value = row.querySelector('.p-value')?.value;
        const unit = row.querySelector('.p-unit')?.value;
        const symbol = row.querySelector('.p-symbol')?.value;
        const domainLo = row.querySelector('.p-domain-lo')?.value;
        const domainHi = row.querySelector('.p-domain-hi')?.value;
        if (name) {
          const param = { name: name };
          if (value) param.value = parseFloat(value);
          if (unit) param.unit = unit;
          if (symbol) param.symbol = symbol;
          if (domainLo || domainHi) {
            param.domain = {};
            if (domainLo) param.domain.lo = parseFloat(domainLo);
            if (domainHi) param.domain.hi = parseFloat(domainHi);
          }
          local_dynamics.parameters.push(param);
        }
      });
    }

    // Collect state variables from the model builder UI
    // Classes: sv-name, sv-expr, sv-symbol, sv-unit, sv-initial, sv-voi, sv-coupling
    const svRows = document.querySelectorAll('#stateEqRows .builder-row');
    if (svRows.length > 0) {
      local_dynamics.state_variables = [];
      svRows.forEach(row => {
        const name = row.querySelector('.sv-name')?.value;
        const expr = row.querySelector('.sv-expr')?.value;
        const symbol = row.querySelector('.sv-symbol')?.value;
        const unit = row.querySelector('.sv-unit')?.value;
        const initial = row.querySelector('.sv-initial')?.value;
        const voi = row.querySelector('.sv-voi')?.checked;
        const coupling = row.querySelector('.sv-coupling')?.checked;
        if (name) {
          const sv = { name: name };
          if (expr) sv.equation = { rhs: expr };
          if (symbol) sv.symbol = symbol;
          if (unit) sv.unit = unit;
          if (initial) sv.initial_value = parseFloat(initial);
          if (voi !== undefined) sv.variable_of_interest = voi;
          if (coupling !== undefined) sv.coupling_variable = coupling;
          local_dynamics.state_variables.push(sv);
        }
      });
    }

    // Collect derived parameters
    // Classes: dp-name, dp-expr, dp-unit
    const dpRows = document.querySelectorAll('#derivedParamsRows .builder-row');
    if (dpRows.length > 0) {
      local_dynamics.derived_parameters = [];
      dpRows.forEach(row => {
        const name = row.querySelector('.dp-name')?.value;
        const expr = row.querySelector('.dp-expr')?.value;
        const unit = row.querySelector('.dp-unit')?.value;
        if (name) {
          const dp = { name: name };
          if (expr) dp.equation = { rhs: expr };
          if (unit) dp.unit = unit;
          local_dynamics.derived_parameters.push(dp);
        }
      });
    }

    // Collect derived variables
    // Classes: dv-name, dv-expr, dv-unit
    const dvRows = document.querySelectorAll('#derivedVarsRows .builder-row');
    if (dvRows.length > 0) {
      local_dynamics.derived_variables = [];
      dvRows.forEach(row => {
        const name = row.querySelector('.dv-name')?.value;
        const expr = row.querySelector('.dv-expr')?.value;
        const unit = row.querySelector('.dv-unit')?.value;
        if (name) {
          const dv = { name: name };
          if (expr) dv.equation = { rhs: expr };
          if (unit) dv.unit = unit;
          local_dynamics.derived_variables.push(dv);
        }
      });
    }

    // Collect functions
    // Classes: fn-name, fn-expr
    const fnRows = document.querySelectorAll('#functionsRows .builder-row');
    if (fnRows.length > 0) {
      local_dynamics.functions = [];
      fnRows.forEach(row => {
        const name = row.querySelector('.fn-name')?.value;
        const expr = row.querySelector('.fn-expr')?.value;
        if (name) {
          const fn = { name: name };
          if (expr) fn.equation = { rhs: expr };
          local_dynamics.functions.push(fn);
        }
      });
    }

    // 2. Collect network (REQUIRED)
    const networkConfig = collectNetworkConfig();
    console.log('[ModelBuilder] networkConfig:', networkConfig);

    const modelName = local_dynamics.name;
    const couplingName = document.getElementById('couplingFunction')?.value;

    if (!networkConfig || networkConfig.mode === 'not configured') {
      throw new Error('No network configured. Please configure a network in the Network tab.');
    }

    // Build network using matrix format (compatible with API)
    const nNodes = networkConfig.number_of_nodes || networkConfig.nodes?.length || 2;

    // Initialize weights and lengths matrices as flat arrays (row-major order)
    const weights = new Array(nNodes * nNodes).fill(0.0);
    const lengths = new Array(nNodes * nNodes).fill(0.0);

    // Populate from edges
    if (networkConfig.edges && networkConfig.edges.length > 0) {
      networkConfig.edges.forEach(e => {
        const src = parseInt(e.source);
        const tgt = parseInt(e.target);
        if (src >= 0 && src < nNodes && tgt >= 0 && tgt < nNodes) {
          const idx = src * nNodes + tgt;
          weights[idx] = e.weight ?? 1.0;
          // Use delay as length proxy, or compute from positions if available
          lengths[idx] = e.delay ?? 10.0;
        }
      });
    }

    // Build region labels from nodes if available
    const regionLabels = [];
    if (networkConfig.nodes && networkConfig.nodes.length > 0) {
      networkConfig.nodes.forEach((n, idx) => {
        regionLabels.push(n.label || `Region_${idx}`);
      });
    }

    const network = {
      label: networkConfig.label,
      number_of_regions: nNodes,
      weights: { values: weights },
      lengths: { values: lengths },
      node_labels: regionLabels.length > 0 ? regionLabels : undefined,
    };

    // Add global parameters if specified
    if (networkConfig.global_coupling_strength) {
      network.global_coupling_strength = { name: 'global_coupling_strength', value: networkConfig.global_coupling_strength };
    }
    if (networkConfig.conduction_speed) {
      network.conduction_speed = { name: 'conduction_speed', value: networkConfig.conduction_speed };
    }

    console.log('[ModelBuilder] Built network:', network);

    // 3. Collect integration (REQUIRED) - always include with defaults
    const integrationConfig = collectIntegrationConfig();
    console.log('[ModelBuilder] integrationConfig:', integrationConfig);

    const integration = {
      method: integrationConfig.method || 'Heun',
      step_size: integrationConfig.step_size || 0.1,
      duration: integrationConfig.duration || 100,
    };

    // 4. Collect coupling
    const couplingSelect = document.getElementById('couplingFunction');
    const coupling = {
      name: couplingSelect?.value || 'Linear',
    };
    console.log('[ModelBuilder] coupling:', coupling);

    // 5. Collect monitors (optional)
    const monitors = collectObservationModelsConfig();
    console.log('[ModelBuilder] monitors:', monitors);

    // 6. Collect stimulus (optional)
    const stimulus = collectStimulusConfig();
    console.log('[ModelBuilder] stimulus:', stimulus);

    // Build the full experiment object
    const experiment = {
      label: document.getElementById('builderSpecName')?.value || 'WebExperiment',
      local_dynamics: local_dynamics,
      network: network,
      integration: integration,
      coupling: coupling,
      monitors: monitors,
    };

    if (stimulus) {
      experiment.stimulus = stimulus;
    }

    log('Collected experiment:', experiment);
    return experiment;
  }

  function initializeRunTab() {
    log('Initializing Run tab');

    const runBtn = document.getElementById('runSimulationBtn');
    const plotTypeSelect = document.getElementById('plotType');
    const plotStateVarsContainer = document.getElementById('plotStateVars');
    const plotRegionsContainer = document.getElementById('plotRegions');
    const downloadBtn = document.getElementById('downloadResultsBtn');
    const selectAllBtn = document.getElementById('selectAllRegions');
    const selectNoneBtn = document.getElementById('selectNoneRegions');

    runBtn?.addEventListener('click', runSimulation);
    plotTypeSelect?.addEventListener('change', () => {
      updateStateVarHint();
      updatePlot();
    });
    // State variable checkboxes are handled via event delegation
    plotStateVarsContainer?.addEventListener('change', (e) => {
      enforceStateVarSelection(e.target);
      updatePlot();
    });
    // Region checkboxes are handled via event delegation
    plotRegionsContainer?.addEventListener('change', updatePlot);
    downloadBtn?.addEventListener('click', downloadResults);

    // Select All / Select None buttons
    selectAllBtn?.addEventListener('click', () => {
      const checkboxes = plotRegionsContainer?.querySelectorAll('input[type="checkbox"]');
      checkboxes?.forEach(cb => cb.checked = true);
      updatePlot();
    });
    selectNoneBtn?.addEventListener('click', () => {
      const checkboxes = plotRegionsContainer?.querySelectorAll('input[type="checkbox"]');
      checkboxes?.forEach(cb => cb.checked = false);
      updatePlot();
    });
  }

  function updateStateVarHint() {
    const plotType = document.getElementById('plotType')?.value;
    const hint = document.getElementById('stateVarHint');
    const plotTypeHint = document.getElementById('plotTypeHint');

    if (hint) {
      if (plotType === 'phasespace') {
        hint.textContent = 'Select exactly 2 variables for X and Y axes';
        hint.style.color = '#dc3545';
      } else if (plotType === 'heatmap') {
        hint.textContent = 'Select 1 variable for heatmap';
        hint.style.color = '#dc3545';
      } else {
        hint.textContent = 'Select variables to plot';
        hint.style.color = '#6c757d';
      }
    }
  }

  function enforceStateVarSelection(changedCheckbox) {
    const plotType = document.getElementById('plotType')?.value;
    const container = document.getElementById('plotStateVars');
    if (!container) return;

    const checkboxes = container.querySelectorAll('input.statevar-checkbox');
    const checked = Array.from(checkboxes).filter(cb => cb.checked);

    if (plotType === 'heatmap') {
      // Only 1 allowed - uncheck others when one is checked
      if (changedCheckbox.checked) {
        checkboxes.forEach(cb => {
          if (cb !== changedCheckbox) cb.checked = false;
        });
      }
    } else if (plotType === 'phasespace') {
      // Only 2 allowed - if more than 2, uncheck the oldest (first in DOM that isn't the current)
      if (checked.length > 2) {
        for (const cb of checkboxes) {
          if (cb.checked && cb !== changedCheckbox) {
            cb.checked = false;
            break;
          }
        }
      }
    }
    // timeseries: no limit
  }

  async function runSimulation() {
    console.log('[ModelBuilder] ========== SIMULATION START ==========');
    log('Running simulation...');

    const runBtn = document.getElementById('runSimulationBtn');
    const statusDiv = document.getElementById('runStatus');
    const statusText = document.getElementById('runStatusText');
    const progressBar = document.getElementById('runProgress');
    const errorDiv = document.getElementById('runError');
    const resultsDiv = document.getElementById('runResults');

    // Get run parameters
    const duration = parseFloat(document.getElementById('runDuration')?.value) || 1000;
    const stepSize = parseFloat(document.getElementById('runStepSize')?.value) || 0.1;
    const backend = document.getElementById('runBackend')?.value || 'jax';
    console.log('[ModelBuilder] Run parameters:', { duration, stepSize, backend });

    // Reset UI
    errorDiv.style.display = 'none';
    resultsDiv.style.display = 'none';
    statusDiv.style.display = 'block';
    runBtn.disabled = true;
    progressBar.style.width = '10%';
    statusText.textContent = 'Collecting experiment configuration...';

    try {
      // Collect the full experiment configuration
      console.log('[ModelBuilder] Collecting experiment configuration...');
      const experiment = collectFullExperiment();
      console.log('[ModelBuilder] Collected experiment:', JSON.stringify(experiment, null, 2));
      log('Experiment config:', experiment);

      progressBar.style.width = '20%';
      statusText.textContent = 'Sending to TVBO API...';

      // Call the Odoo endpoint which proxies to TVBO API
      const response = await fetch('/tvbo/configurator/run', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          params: {
            experiment: experiment,
            duration: duration,
            step_size: stepSize,
            backend: backend,
          },
          id: Date.now(),
        }),
      });

      progressBar.style.width = '80%';
      statusText.textContent = 'Processing results...';

      const result = await response.json();
      console.log('[ModelBuilder] Raw API response:', result);

      if (result.error) {
        console.error('[ModelBuilder] API returned error:', result.error);
        throw new Error(result.error.message || result.error.data?.message || 'API returned error');
      }

      const data = result.result;
      console.log('[ModelBuilder] Result data:', data);

      // MVP: Fail explicitly if data is missing
      if (!data) {
        throw new Error('API returned empty result. Check Odoo logs.');
      }
      if (!data.success) {
        console.error('[ModelBuilder] Simulation failed:', data.error);
        throw new Error(data.error);
      }
      if (!data.data) {
        throw new Error('Simulation returned no data array');
      }
      if (!data.time) {
        throw new Error('Simulation returned no time array');
      }
      if (!data.state_variables) {
        throw new Error('Simulation returned no state_variables');
      }

      console.log('[ModelBuilder] data.data length:', data.data.length);
      console.log('[ModelBuilder] data.time length:', data.time.length);
      console.log('[ModelBuilder] data.state_variables:', data.state_variables);
      console.log('[ModelBuilder] data.region_labels:', data.region_labels);

      // Store results - no fallbacks, fail if data missing
      simulationResults = {
        data: data.data,
        time: data.time,
        stateVariables: data.state_variables,
        regionLabels: data.region_labels,
        samplePeriod: data.sample_period,
      };
      console.log('[ModelBuilder] Stored simulationResults:', {
        dataShape: simulationResults.data ? `[${simulationResults.data.length}]` : 'null',
        timeLength: simulationResults.time?.length,
        stateVariables: simulationResults.stateVariables,
        regionLabels: simulationResults.regionLabels,
        samplePeriod: simulationResults.samplePeriod,
      });
      // Log first data point for debugging
      if (simulationResults.data && simulationResults.data.length > 0) {
        console.log('[ModelBuilder] First time point data:', simulationResults.data[0]);
        console.log('[ModelBuilder] Data structure: data[time][stateVar][region][mode]');
      }

      progressBar.style.width = '100%';
      statusText.textContent = 'Complete!';

      // Populate plot controls
      console.log('[ModelBuilder] Calling populatePlotControls...');
      populatePlotControls();

      // Show results and plot
      setTimeout(() => {
        statusDiv.style.display = 'none';
        resultsDiv.style.display = 'block';
        updatePlot();

        // Update info
        const infoDiv = document.getElementById('simInfo');
        if (infoDiv) {
          const nT = simulationResults.time?.length || 0;
          const nSV = simulationResults.stateVariables?.length || 0;
          const nR = simulationResults.regionLabels?.length || 0;
          infoDiv.textContent = `Duration: ${duration}ms | Step: ${stepSize}ms | Time points: ${nT} | State variables: ${nSV} | Regions: ${nR}`;
        }
      }, 500);

    } catch (err) {
      log('Simulation error:', err);
      statusDiv.style.display = 'none';
      errorDiv.style.display = 'block';
      errorDiv.textContent = `Error: ${err.message}`;
    } finally {
      runBtn.disabled = false;
    }
  }

  function populatePlotControls() {
    console.log('[ModelBuilder] populatePlotControls called, simulationResults:', simulationResults);
    if (!simulationResults) {
      throw new Error('populatePlotControls called but simulationResults is null');
    }

    const stateVarsContainer = document.getElementById('plotStateVars');
    const regionsContainer = document.getElementById('plotRegions');

    if (!stateVarsContainer) {
      throw new Error('plotStateVars container not found');
    }
    if (!regionsContainer) {
      throw new Error('plotRegions container not found');
    }

    // Populate state variables as checkboxes - first one selected by default
    stateVarsContainer.innerHTML = simulationResults.stateVariables
      .map((sv, i) => `
        <div class="form-check" style="margin-bottom: 2px;">
          <input class="form-check-input statevar-checkbox" type="checkbox" value="${i}" id="statevar_${i}" ${i === 0 ? 'checked' : ''}>
          <label class="form-check-label" for="statevar_${i}" style="font-size: 0.9em;">${escapeHtml(sv)}</label>
        </div>
      `)
      .join('');
    console.log('[ModelBuilder] State var checkboxes populated:', simulationResults.stateVariables);

    // Populate regions as checkboxes - generate labels if not provided by API
    const nRegions = simulationResults.data[0][0].length;
    const labels = simulationResults.regionLabels.length > 0
      ? simulationResults.regionLabels
      : Array.from({length: nRegions}, (_, i) => `Region_${i}`);
    console.log('[ModelBuilder] Region labels for checkboxes:', labels);

    regionsContainer.innerHTML = labels
      .map((label, i) => `
        <div class="form-check" style="margin-bottom: 2px;">
          <input class="form-check-input region-checkbox" type="checkbox" value="${i}" id="region_${i}" ${i < 5 ? 'checked' : ''}>
          <label class="form-check-label" for="region_${i}" style="font-size: 0.9em;">${escapeHtml(label)}</label>
        </div>
      `)
      .join('');

    // Update hint based on current plot type
    updateStateVarHint();
  }

  function updatePlot() {
    console.log('[ModelBuilder] updatePlot called, simulationResults:', simulationResults);
    if (!simulationResults) {
      throw new Error('updatePlot called but simulationResults is null');
    }
    if (!simulationResults.data) {
      throw new Error('updatePlot called but simulationResults.data is null');
    }
    if (!simulationResults.time) {
      throw new Error('updatePlot called but simulationResults.time is null');
    }

    const plotTypeSelect = document.getElementById('plotType');
    const stateVarsContainer = document.getElementById('plotStateVars');
    const regionsContainer = document.getElementById('plotRegions');
    const container = document.getElementById('plotContainer');

    if (!plotTypeSelect) throw new Error('plotType select not found');
    if (!stateVarsContainer) throw new Error('plotStateVars container not found');
    if (!regionsContainer) throw new Error('plotRegions container not found');
    if (!container) throw new Error('plotContainer not found');

    const plotType = plotTypeSelect.value;
    // Get selected state variables from checkboxes
    const selectedStateVars = Array.from(stateVarsContainer.querySelectorAll('input.statevar-checkbox:checked'))
      .map(cb => parseInt(cb.value));
    // Get selected regions from checkboxes
    const selectedRegions = Array.from(regionsContainer.querySelectorAll('input.region-checkbox:checked'))
      .map(cb => parseInt(cb.value));

    console.log('[ModelBuilder] Plot settings:', { plotType, selectedStateVars, selectedRegions });
    console.log('[ModelBuilder] Plot container dimensions:', container.clientWidth, 'x', container.clientHeight);

    const time = simulationResults.time;
    const data = simulationResults.data;

    // Validate selections based on plot type
    if (plotType === 'timeseries') {
      if (selectedStateVars.length === 0) {
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6c757d;">Please select at least one state variable</div>';
        return;
      }
      plotTimeSeries(container, time, data, selectedStateVars, selectedRegions);
    } else if (plotType === 'phasespace') {
      if (selectedStateVars.length !== 2) {
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6c757d;">Please select exactly 2 state variables for phase space plot</div>';
        return;
      }
      plotPhaseSpace(container, data, selectedStateVars, selectedRegions);
    } else if (plotType === 'heatmap') {
      if (selectedStateVars.length !== 1) {
        container.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#6c757d;">Please select exactly 1 state variable for heatmap</div>';
        return;
      }
      plotHeatmap(container, time, data, selectedStateVars[0]);
    }
  }

  function plotTimeSeries(container, time, data, stateVarIndices, regions) {
    // Create SVG-based time series plot
    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 20, right: 120, bottom: 40, left: 60 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    // Extract data for selected state variables and regions
    const traces = [];
    stateVarIndices.forEach(stateVarIdx => {
      regions.forEach(regionIdx => {
        const values = time.map((_, tIdx) => {
          // data shape: [time, state_vars, regions, modes]
          const val = data[tIdx]?.[stateVarIdx]?.[regionIdx]?.[0];
          return val !== undefined ? val : 0;
        });
        const svName = simulationResults.stateVariables[stateVarIdx] || `sv${stateVarIdx}`;
        const regionLabel = simulationResults.regionLabels[regionIdx] || `Region_${regionIdx}`;
        traces.push({ stateVarIdx, regionIdx, values, label: `${svName} - ${regionLabel}` });
      });
    });

    // Find data range
    const allValues = traces.flatMap(t => t.values);
    const yMin = Math.min(...allValues);
    const yMax = Math.max(...allValues);
    const yRange = yMax - yMin || 1;

    const xScale = (t) => margin.left + (t / time[time.length - 1]) * plotWidth;
    const yScale = (v) => margin.top + plotHeight - ((v - yMin) / yRange) * plotHeight;

    // Colors for different regions
    const colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#ffff33', '#a65628', '#f781bf', '#66c2a5', '#fc8d62'];

    let svg = `<svg width="${width}" height="${height}" style="background: white;">`;

    // Grid lines
    for (let i = 0; i <= 5; i++) {
      const y = margin.top + (plotHeight / 5) * i;
      const yVal = yMax - (yRange / 5) * i;
      svg += `<line x1="${margin.left}" y1="${y}" x2="${width - margin.right}" y2="${y}" stroke="#e0e0e0" stroke-width="1"/>`;
      svg += `<text x="${margin.left - 5}" y="${y + 4}" text-anchor="end" font-size="11" fill="#666">${yVal.toFixed(2)}</text>`;
    }

    // X axis labels
    const numXLabels = 5;
    for (let i = 0; i <= numXLabels; i++) {
      const tVal = (time[time.length - 1] / numXLabels) * i;
      const x = xScale(tVal);
      svg += `<text x="${x}" y="${height - 10}" text-anchor="middle" font-size="11" fill="#666">${tVal.toFixed(0)} ms</text>`;
    }

    // Plot traces
    traces.forEach((trace, idx) => {
      const color = colors[idx % colors.length];
      const points = trace.values.map((v, i) => `${xScale(time[i])},${yScale(v)}`).join(' ');
      svg += `<polyline points="${points}" fill="none" stroke="${color}" stroke-width="1.5"/>`;

      // Legend
      const legendY = margin.top + idx * 16;
      svg += `<rect x="${width - margin.right + 10}" y="${legendY}" width="10" height="10" fill="${color}"/>`;
      svg += `<text x="${width - margin.right + 24}" y="${legendY + 9}" font-size="10" fill="#333">${escapeHtml(trace.label)}</text>`;
    });

    // Axes
    svg += `<line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${height - margin.bottom}" stroke="#333" stroke-width="1"/>`;
    svg += `<line x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}" stroke="#333" stroke-width="1"/>`;

    // Axis labels
    svg += `<text x="${margin.left / 2}" y="${height / 2}" text-anchor="middle" transform="rotate(-90, ${margin.left / 2}, ${height / 2})" font-size="12" fill="#333">Value</text>`;
    svg += `<text x="${margin.left + plotWidth / 2}" y="${height - 2}" text-anchor="middle" font-size="12" fill="#333">Time (ms)</text>`;

    svg += '</svg>';
    container.innerHTML = svg;
  }

  function plotPhaseSpace(container, data, stateVarIndices, regions) {
    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 20, right: 100, bottom: 40, left: 60 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    // Need exactly 2 state variables for phase space
    if (stateVarIndices.length !== 2) {
      container.innerHTML = '<div class="alert alert-warning">Phase space plot requires exactly 2 state variables.</div>';
      return;
    }

    const sv0 = stateVarIndices[0];
    const sv1 = stateVarIndices[1];
    const colors = ['#e41a1c', '#377eb8', '#4daf4a', '#984ea3', '#ff7f00', '#66c2a5', '#fc8d62', '#8da0cb'];

    // Extract the two selected state variables for all selected regions
    const traces = regions.map(regionIdx => {
      const xVals = data.map(t => t[sv0]?.[regionIdx]?.[0] || 0);
      const yVals = data.map(t => t[sv1]?.[regionIdx]?.[0] || 0);
      const regionLabel = simulationResults.regionLabels[regionIdx] || `Region_${regionIdx}`;
      return { regionIdx, xVals, yVals, label: regionLabel };
    });

    const allX = traces.flatMap(t => t.xVals);
    const allY = traces.flatMap(t => t.yVals);
    const xMin = Math.min(...allX), xMax = Math.max(...allX);
    const yMin = Math.min(...allY), yMax = Math.max(...allY);
    const xRange = xMax - xMin || 1;
    const yRange = yMax - yMin || 1;

    const xScale = (v) => margin.left + ((v - xMin) / xRange) * plotWidth;
    const yScale = (v) => margin.top + plotHeight - ((v - yMin) / yRange) * plotHeight;

    let svg = `<svg width="${width}" height="${height}" style="background: white;">`;

    // Plot traces
    traces.forEach((trace, idx) => {
      const color = colors[idx % colors.length];
      const points = trace.xVals.map((x, i) => `${xScale(x)},${yScale(trace.yVals[i])}`).join(' ');
      svg += `<polyline points="${points}" fill="none" stroke="${color}" stroke-width="1" opacity="0.8"/>`;

      // Legend
      const legendY = margin.top + idx * 16;
      svg += `<rect x="${width - margin.right + 10}" y="${legendY}" width="10" height="10" fill="${color}"/>`;
      svg += `<text x="${width - margin.right + 24}" y="${legendY + 9}" font-size="10" fill="#333">${escapeHtml(trace.label)}</text>`;
    });

    // Axes
    svg += `<line x1="${margin.left}" y1="${margin.top}" x2="${margin.left}" y2="${height - margin.bottom}" stroke="#333" stroke-width="1"/>`;
    svg += `<line x1="${margin.left}" y1="${height - margin.bottom}" x2="${width - margin.right}" y2="${height - margin.bottom}" stroke="#333" stroke-width="1"/>`;

    // Labels using selected state variable names
    const sv1Name = simulationResults.stateVariables?.[sv1] || 'Y';
    const sv0Name = simulationResults.stateVariables?.[sv0] || 'X';
    svg += `<text x="${margin.left / 2}" y="${height / 2}" text-anchor="middle" transform="rotate(-90, ${margin.left / 2}, ${height / 2})" font-size="12">${sv1Name}</text>`;
    svg += `<text x="${margin.left + plotWidth / 2}" y="${height - 5}" text-anchor="middle" font-size="12">${sv0Name}</text>`;

    svg += '</svg>';
    container.innerHTML = svg;
  }

  function plotHeatmap(container, time, data, stateVarIdx) {
    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 20, right: 100, bottom: 40, left: 80 };

    const nTime = time.length;
    const nRegions = data[0]?.[stateVarIdx]?.length || 0;

    if (nTime === 0 || nRegions === 0) {
      container.innerHTML = '<div class="alert alert-warning">No data for heatmap.</div>';
      return;
    }

    // Downsample if too many time points
    const maxTimePoints = 500;
    const timeStep = Math.max(1, Math.floor(nTime / maxTimePoints));
    const sampledTime = time.filter((_, i) => i % timeStep === 0);
    const sampledData = data.filter((_, i) => i % timeStep === 0);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;
    const cellWidth = plotWidth / sampledTime.length;
    const cellHeight = plotHeight / nRegions;

    // Find data range
    let vMin = Infinity, vMax = -Infinity;
    sampledData.forEach(t => {
      for (let r = 0; r < nRegions; r++) {
        const v = t[stateVarIdx]?.[r]?.[0] || 0;
        vMin = Math.min(vMin, v);
        vMax = Math.max(vMax, v);
      }
    });
    const vRange = vMax - vMin || 1;

    // Color function (blue-white-red)
    const colorScale = (v) => {
      const norm = (v - vMin) / vRange;
      if (norm < 0.5) {
        const t = norm * 2;
        return `rgb(${Math.round(59 + 196 * t)}, ${Math.round(76 + 179 * t)}, ${Math.round(192 - 47 * t)})`;
      } else {
        const t = (norm - 0.5) * 2;
        return `rgb(255, ${Math.round(255 - 155 * t)}, ${Math.round(145 - 115 * t)})`;
      }
    };

    let svg = `<svg width="${width}" height="${height}" style="background: white;">`;

    // Draw cells
    sampledData.forEach((t, tIdx) => {
      for (let r = 0; r < nRegions; r++) {
        const v = t[stateVarIdx]?.[r]?.[0] || 0;
        const x = margin.left + tIdx * cellWidth;
        const y = margin.top + r * cellHeight;
        svg += `<rect x="${x}" y="${y}" width="${cellWidth + 0.5}" height="${cellHeight + 0.5}" fill="${colorScale(v)}"/>`;
      }
    });

    // Y axis labels (regions)
    const maxLabels = 20;
    const labelStep = Math.max(1, Math.floor(nRegions / maxLabels));
    for (let r = 0; r < nRegions; r += labelStep) {
      const y = margin.top + r * cellHeight + cellHeight / 2;
      const label = simulationResults.regionLabels[r] || `${r}`;
      svg += `<text x="${margin.left - 5}" y="${y + 4}" text-anchor="end" font-size="10" fill="#333">${label}</text>`;
    }

    // X axis labels (time)
    for (let i = 0; i <= 4; i++) {
      const tIdx = Math.floor(i * (sampledTime.length - 1) / 4);
      const x = margin.left + tIdx * cellWidth;
      svg += `<text x="${x}" y="${height - 10}" text-anchor="middle" font-size="10" fill="#333">${sampledTime[tIdx]?.toFixed(0) || 0} ms</text>`;
    }

    // Colorbar
    const cbX = width - margin.right + 20;
    const cbHeight = plotHeight;
    for (let i = 0; i < 50; i++) {
      const v = vMax - (i / 49) * vRange;
      const y = margin.top + (i / 49) * cbHeight;
      svg += `<rect x="${cbX}" y="${y}" width="20" height="${cbHeight / 49 + 1}" fill="${colorScale(v)}"/>`;
    }
    svg += `<text x="${cbX + 25}" y="${margin.top + 10}" font-size="10">${vMax.toFixed(2)}</text>`;
    svg += `<text x="${cbX + 25}" y="${margin.top + cbHeight}" font-size="10">${vMin.toFixed(2)}</text>`;

    svg += '</svg>';
    container.innerHTML = svg;
  }

  function downloadResults() {
    if (!simulationResults) {
      alert('No simulation results to download.');
      return;
    }

    // Convert to CSV
    const time = simulationResults.time;
    const data = simulationResults.data;
    const stateVars = simulationResults.stateVariables;
    const regions = simulationResults.regionLabels;
    const nRegions = data[0]?.[0]?.length || 0;

    // Header
    let csv = 'time';
    for (let sv = 0; sv < stateVars.length; sv++) {
      for (let r = 0; r < nRegions; r++) {
        const regionLabel = regions[r] || `region_${r}`;
        csv += `,${stateVars[sv]}_${regionLabel}`;
      }
    }
    csv += '\n';

    // Data rows
    for (let t = 0; t < time.length; t++) {
      csv += time[t].toFixed(4);
      for (let sv = 0; sv < stateVars.length; sv++) {
        for (let r = 0; r < nRegions; r++) {
          const val = data[t]?.[sv]?.[r]?.[0] || 0;
          csv += `,${val}`;
        }
      }
      csv += '\n';
    }

    // Download
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'simulation_results.csv';
    a.click();
    URL.revokeObjectURL(url);
  }


  // Eagerly initialize all tabs so prefill from loaded experiments works.
  // Also re-init preview each time the preview tab is shown.
  function initializeAllTabs() {
    initializeIntegratorTab();
    initializeCouplingTab();
    initializeNetworkTab();
    initializeStimulusTab();
    initializeFunctionsTab();
    initializeObservationsTab();
    initializeDerivedObservationsTab();
    initializeAlgorithmsTab();
    initializeOptimizationTab();
    initializeExplorationsTab();
    initializeExecutionTab();
    initializeObservationModelsTab();
    initializeRunTab();
  }
  window.initializeAllTabs = initializeAllTabs;
  window.initializePreviewTab = initializePreviewTab;

  document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tabs eagerly after a short delay to let data load
    setTimeout(initializeAllTabs, 500);

    // Re-initialize preview each time the tab is shown
    document.getElementById('preview-tab')?.addEventListener('shown.bs.tab', function() {
      initializePreviewTab();
    });
    // Re-initialize preview for the live YAML panel too
    document.getElementById('preview-tab')?.addEventListener('click', function() {
      setTimeout(initializePreviewTab, 100);
    });
    // Re-init network 3D when tab is shown
    document.getElementById('network-tab')?.addEventListener('shown.bs.tab', function() {
      initializeNetworkTab();
      initializeCouplingTab();
    });
  });
})();
