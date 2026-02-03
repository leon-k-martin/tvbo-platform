#!/usr/bin/env python3
"""
Generate Odoo XML data files from TVBO database YAML files.
Converts database/*.yaml files to Odoo importable XML format.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any
import re


def camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()


def sanitize_xml_id(name: str) -> str:
    """Convert name to valid XML ID."""
    # Remove file extensions and special characters
    xml_id = name.replace('.yaml', '').replace('.yml', '')
    xml_id = re.sub(r'[^a-zA-Z0-9_]', '_', xml_id)
    xml_id = re.sub(r'_+', '_', xml_id)
    return xml_id.lower()


def escape_xml(text: str) -> str:
    """Escape special XML characters."""
    if not isinstance(text, str):
        return str(text)
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&apos;'))


def generate_dynamics_data_xml(yaml_files: List[Path], output_file: Path, model_type: str = "dynamics"):
    """Generate XML data file for general dynamics models (Julia models)."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        ''
    ]

    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not data or 'name' not in data:
                continue

            name = data['name']
            xml_id = f"{model_type}_{sanitize_xml_id(yaml_file.stem)}"

            lines.append(f'        <record id="{xml_id}" model="tvbo.dynamics">')
            lines.append(f'            <field name="name">{escape_xml(name)}</field>')

            # Add label if present
            if 'label' in data:
                lines.append(f'            <field name="label">{escape_xml(data["label"])}</field>')

            # Add description from references or source
            description_parts = []
            if 'references' in data:
                refs = data['references']
                if isinstance(refs, list):
                    description_parts.append(f"References: {', '.join(str(r) for r in refs)}")
                else:
                    description_parts.append(f"Reference: {refs}")

            if 'source' in data:
                description_parts.append(f"Source: {data['source']}")

            if description_parts:
                description = '; '.join(description_parts)
                lines.append(f'            <field name="description">{escape_xml(description)}</field>')

            lines.append('        </record>')
            lines.append('')

        except Exception as e:
            print(f"  ✗ Error processing {yaml_file.name}: {e}")

    lines.append('    </data>')
    lines.append('</odoo>')

    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))


def generate_model_data_xml(yaml_files: List[Path], output_file: Path):
    """Generate XML data file for neural mass models with proper related records."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        ''
    ]

    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not data or 'name' not in data:
                continue

            model_name = data['name']
            model_id = sanitize_xml_id(model_name)

            # Create Parameter records first
            param_refs = []
            if 'parameters' in data and data['parameters']:
                for param_name, param_data in data['parameters'].items():
                    param_id = f"param_{model_id}_{sanitize_xml_id(param_name)}"
                    param_refs.append(param_id)

                    # Create Range first if needed
                    range_id = None
                    if isinstance(param_data, dict) and 'domain' in param_data and isinstance(param_data['domain'], dict):
                        domain = param_data['domain']
                        range_id = f"range_{param_id}"
                        lines.append(f'        <record id="{range_id}" model="tvbo.range">')
                        if 'lo' in domain:
                            lo_val = domain['lo']
                            if lo_val == float('inf') or lo_val == float('-inf'):
                                lo_val = None
                            if lo_val is not None:
                                lines.append(f'            <field name="lo">{lo_val}</field>')
                        if 'hi' in domain:
                            hi_val = domain['hi']
                            if hi_val == float('inf') or hi_val == float('-inf'):
                                hi_val = None
                            if hi_val is not None:
                                lines.append(f'            <field name="hi">{hi_val}</field>')
                        if 'step' in domain:
                            lines.append(f'            <field name="step">{domain["step"]}</field>')
                        lines.append(f'        </record>')
                        lines.append('')

                    # Now create Parameter with all fields in one record
                    lines.append(f'        <record id="{param_id}" model="tvbo.parameter">')
                    lines.append(f'            <field name="name">{escape_xml(param_name)}</field>')

                    if isinstance(param_data, dict):
                        if 'value' in param_data:
                            lines.append(f'            <field name="value">{param_data["value"]}</field>')
                        if 'description' in param_data:
                            lines.append(f'            <field name="description">{escape_xml(param_data["description"])}</field>')
                        if 'unit' in param_data:
                            lines.append(f'            <field name="unit">{escape_xml(param_data["unit"])}</field>')
                        if 'default' in param_data:
                            lines.append(f'            <field name="default">{param_data["default"]}</field>')
                        if range_id:
                            lines.append(f'            <field name="domain" ref="{range_id}"/>')

                    lines.append(f'        </record>')
                    lines.append('')            # Create StateVariable records
            state_var_refs = []
            if 'state_variables' in data and data['state_variables']:
                for var_name, var_data in data['state_variables'].items():
                    var_id = f"state_var_{model_id}_{sanitize_xml_id(var_name)}"
                    state_var_refs.append(var_id)

                    # Create dependencies first
                    eq_id = None
                    domain_range_id = None
                    boundaries_range_id = None

                    if isinstance(var_data, dict):
                        # Create Equation
                        if 'equation' in var_data and isinstance(var_data['equation'], dict):
                            eq = var_data['equation']
                            if 'lhs' in eq or 'rhs' in eq:
                                eq_id = f"eq_{var_id}"
                                lines.append(f'        <record id="{eq_id}" model="tvbo.equation">')
                                if 'lhs' in eq:
                                    lines.append(f'            <field name="lefthandside">{escape_xml(eq["lhs"])}</field>')
                                if 'rhs' in eq:
                                    lines.append(f'            <field name="righthandside">{escape_xml(eq["rhs"])}</field>')
                                lines.append(f'        </record>')
                                lines.append('')

                        # Create domain Range
                        if 'domain' in var_data and isinstance(var_data['domain'], dict):
                            domain = var_data['domain']
                            domain_range_id = f"range_domain_{var_id}"
                            lines.append(f'        <record id="{domain_range_id}" model="tvbo.range">')
                            if 'lo' in domain:
                                lo_val = domain['lo']
                                if lo_val == float('inf') or lo_val == float('-inf'):
                                    lo_val = None
                                if lo_val is not None:
                                    lines.append(f'            <field name="lo">{lo_val}</field>')
                            if 'hi' in domain:
                                hi_val = domain['hi']
                                if hi_val == float('inf') or hi_val == float('-inf'):
                                    hi_val = None
                                if hi_val is not None:
                                    lines.append(f'            <field name="hi">{hi_val}</field>')
                            lines.append(f'        </record>')
                            lines.append('')

                        # Create boundaries Range
                        if 'boundaries' in var_data and isinstance(var_data['boundaries'], dict):
                            boundaries = var_data['boundaries']
                            boundaries_range_id = f"range_boundaries_{var_id}"
                            lines.append(f'        <record id="{boundaries_range_id}" model="tvbo.range">')
                            if 'lo' in boundaries:
                                lo_val = boundaries['lo']
                                if lo_val == float('inf') or lo_val == float('-inf'):
                                    lo_val = None
                                if lo_val is not None:
                                    lines.append(f'            <field name="lo">{lo_val}</field>')
                            if 'hi' in boundaries:
                                hi_val = boundaries['hi']
                                if hi_val == float('inf') or hi_val == float('-inf'):
                                    hi_val = None
                                if hi_val is not None:
                                    lines.append(f'            <field name="hi">{hi_val}</field>')
                            lines.append(f'        </record>')
                            lines.append('')

                    # Now create StateVariable once with all refs
                    lines.append(f'        <record id="{var_id}" model="tvbo.state_variable">')
                    lines.append(f'            <field name="name">{escape_xml(var_name)}</field>')

                    if isinstance(var_data, dict):
                        if 'description' in var_data:
                            lines.append(f'            <field name="description">{escape_xml(var_data["description"])}</field>')
                        if 'unit' in var_data:
                            lines.append(f'            <field name="unit">{escape_xml(var_data["unit"])}</field>')
                        if 'initial_value' in var_data:
                            lines.append(f'            <field name="initial_value">{var_data["initial_value"]}</field>')
                        if eq_id:
                            lines.append(f'            <field name="equation" ref="{eq_id}"/>')
                        if domain_range_id:
                            lines.append(f'            <field name="domain" ref="{domain_range_id}"/>')
                        if boundaries_range_id:
                            lines.append(f'            <field name="boundaries" ref="{boundaries_range_id}"/>')

                    lines.append(f'        </record>')
                    lines.append('')

            # Create DerivedVariable records
            derived_var_refs = []
            if 'derived_variables' in data and data['derived_variables']:
                for var_name, var_data in data['derived_variables'].items():
                    var_id = f"derived_var_{model_id}_{sanitize_xml_id(var_name)}"
                    derived_var_refs.append(var_id)

                    lines.append(f'        <record id="{var_id}" model="tvbo.derived_variable">')
                    lines.append(f'            <field name="name">{escape_xml(var_name)}</field>')

                    if isinstance(var_data, dict):
                        if 'description' in var_data:
                            lines.append(f'            <field name="description">{escape_xml(var_data["description"])}</field>')
                        if 'unit' in var_data:
                            lines.append(f'            <field name="unit">{escape_xml(var_data["unit"])}</field>')

                        # Handle equation
                        if 'equation' in var_data and isinstance(var_data['equation'], dict):
                            eq = var_data['equation']
                            if 'lhs' in eq or 'rhs' in eq:
                                eq_id = f"eq_{var_id}"
                                lines.append(f'        </record>')
                                lines.append(f'        <record id="{eq_id}" model="tvbo.equation">')
                                if 'lhs' in eq:
                                    lines.append(f'            <field name="lefthandside">{escape_xml(eq["lhs"])}</field>')
                                if 'rhs' in eq:
                                    lines.append(f'            <field name="righthandside">{escape_xml(eq["rhs"])}</field>')
                                lines.append(f'        </record>')
                                lines.append(f'        <record id="{var_id}" model="tvbo.derived_variable">')
                                lines.append(f'            <field name="equation" ref="{eq_id}"/>')

                    lines.append(f'        </record>')
                    lines.append('')

            # Create coupling term Parameter records
            coupling_refs = []
            if 'coupling_terms' in data and data['coupling_terms']:
                for term_name, term_data in data['coupling_terms'].items():
                    term_id = f"coupling_{model_id}_{sanitize_xml_id(term_name)}"
                    coupling_refs.append(term_id)

                    lines.append(f'        <record id="{term_id}" model="tvbo.parameter">')
                    lines.append(f'            <field name="name">{escape_xml(term_name)}</field>')

                    if isinstance(term_data, dict):
                        if 'value' in term_data:
                            lines.append(f'            <field name="value">{term_data["value"]}</field>')
                        if 'description' in term_data:
                            lines.append(f'            <field name="description">{escape_xml(term_data["description"])}</field>')

                    lines.append(f'        </record>')
                    lines.append('')

            # Now create the Dynamics record with references
            xml_id = f"dynamics_{model_id}"
            lines.extend([
                f'        <record id="{xml_id}" model="tvbo.dynamics">',
                f'            <field name="name">{escape_xml(model_name)}</field>',
                f'            <field name="label">{escape_xml(model_name)}</field>',
            ])

            if 'description' in data:
                lines.append(f'            <field name="description">{escape_xml(data["description"])}</field>')

            if 'number_of_modes' in data:
                lines.append(f'            <field name="number_of_modes">{data["number_of_modes"]}</field>')

            # Link parameters using Many2many
            if param_refs:
                ref_list = ','.join([f"ref('{r}')" for r in param_refs])
                lines.append(f'            <field name="parameters" eval="[(6, 0, [{ref_list}])]"/>')

            # Link state variables
            if state_var_refs:
                ref_list = ','.join([f"ref('{r}')" for r in state_var_refs])
                lines.append(f'            <field name="state_variables" eval="[(6, 0, [{ref_list}])]"/>')

            # Link derived variables
            if derived_var_refs:
                ref_list = ','.join([f"ref('{r}')" for r in derived_var_refs])
                lines.append(f'            <field name="derived_variables" eval="[(6, 0, [{ref_list}])]"/>')

            # Link coupling terms
            if coupling_refs:
                ref_list = ','.join([f"ref('{r}')" for r in coupling_refs])
                lines.append(f'            <field name="coupling_terms" eval="[(6, 0, [{ref_list}])]"/>')

            # Add references as text
            if 'references' in data:
                refs = data['references']
                if isinstance(refs, list):
                    refs_str = ', '.join(str(r) for r in refs)
                else:
                    refs_str = str(refs)
                lines.append(f'            <field name="references">{escape_xml(refs_str)}</field>')

            lines.extend(['        </record>', ''])

        except Exception as e:
            print(f"✗ Error processing {yaml_file.name}: {e}")
            import traceback
            traceback.print_exc()

    lines.extend(['    </data>', '</odoo>'])
    output_file.write_text('\n'.join(lines))
def generate_integrator_data_xml(yaml_files: List[Path], output_file: Path):
    """Generate XML data file for integrators."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        ''
    ]

    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            integrator_name = yaml_file.stem
            integrator_id = sanitize_xml_id(integrator_name)

            # Create DerivedVariable for update_expression if present
            update_expr_ref = None
            if 'update_expression' in data and data['update_expression']:
                expr_data = data['update_expression']
                expr_id = f"update_expr_{integrator_id}"
                update_expr_ref = expr_id

                lines.append(f'        <record id="{expr_id}" model="tvbo.derived_variable">')
                if 'name' in expr_data:
                    lines.append(f'            <field name="name">{escape_xml(expr_data["name"])}</field>')

                if 'description' in expr_data:
                    lines.append(f'            <field name="description">{escape_xml(expr_data["description"])}</field>')

                # Handle equation
                if 'equation' in expr_data and isinstance(expr_data['equation'], dict):
                    eq = expr_data['equation']
                    if 'lhs' in eq or 'rhs' in eq:
                        eq_id = f"eq_{expr_id}"
                        lines.append(f'        </record>')
                        lines.append(f'        <record id="{eq_id}" model="tvbo.equation">')
                        if 'lhs' in eq:
                            lines.append(f'            <field name="lefthandside">{escape_xml(eq["lhs"])}</field>')
                        if 'rhs' in eq:
                            lines.append(f'            <field name="righthandside">{escape_xml(eq["rhs"])}</field>')
                        lines.append(f'        </record>')
                        lines.append(f'        <record id="{expr_id}" model="tvbo.derived_variable">')
                        lines.append(f'            <field name="equation" ref="{eq_id}"/>')

                lines.append(f'        </record>')
                lines.append('')

            xml_id = f"integrator_{integrator_id}"
            lines.extend([
                f'        <record id="{xml_id}" model="tvbo.integrator">',
            ])

            if 'method' in data:
                lines.append(f'            <field name="method">{escape_xml(data["method"])}</field>')

            if 'step_size' in data:
                lines.append(f'            <field name="step_size">{data["step_size"]}</field>')

            if 'duration' in data:
                lines.append(f'            <field name="duration">{data["duration"]}</field>')

            if 'transient_time' in data:
                lines.append(f'            <field name="transient_time">{data["transient_time"]}</field>')

            if 'number_of_stages' in data:
                lines.append(f'            <field name="number_of_stages">{data["number_of_stages"]}</field>')

            if 'scipy_ode_base' in data:
                lines.append(f'            <field name="scipy_ode_base">{str(data["scipy_ode_base"]).lower()}</field>')

            if 'delayed' in data:
                lines.append(f'            <field name="delayed">{str(data["delayed"]).lower()}</field>')

            # Link update_expression as Many2one
            if update_expr_ref:
                lines.append(f'            <field name="update_expression" ref="{update_expr_ref}"/>')

            lines.extend(['        </record>', ''])

        except Exception as e:
            print(f"✗ Error processing {yaml_file.name}: {e}")

    lines.extend(['    </data>', '</odoo>'])
    output_file.write_text('\n'.join(lines))


def generate_network_data_xml(yaml_files: List[Path], output_file: Path):
    """Generate XML data file for connectivity networks (Network records)."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        ''
    ]

    # Collect unique atlases to create BrainAtlas and Parcellation records first
    atlases = {}
    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)
            if data and 'parcellation' in data and 'atlas' in data['parcellation']:
                atlas_name = data['parcellation']['atlas'].get('name', '')
                if atlas_name and atlas_name not in atlases:
                    atlases[atlas_name] = sanitize_xml_id(atlas_name)
        except Exception:
            pass

    # Create BrainAtlas records first (Parcellation depends on them)
    for atlas_name, atlas_id in atlases.items():
        lines.extend([
            f'        <record id="brain_atlas_{atlas_id}" model="tvbo.brain_atlas">',
            f'            <field name="name">{escape_xml(atlas_name)}</field>',
            '        </record>',
            ''
        ])

    # Create Parcellation records (which reference BrainAtlas via 'atlas' field)
    # Note: Parcellation model only has 'label', not 'name'
    for atlas_name, atlas_id in atlases.items():
        lines.extend([
            f'        <record id="parcellation_{atlas_id}" model="tvbo.parcellation">',
            f'            <field name="label">{escape_xml(atlas_name)}</field>',
            f'            <field name="atlas" ref="brain_atlas_{atlas_id}"/>',
            '        </record>',
            ''
        ])

    # Now create network records
    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            network_id = sanitize_xml_id(yaml_file.stem)
            xml_id = f"network_{network_id}"

            lines.append(f'        <record id="{xml_id}" model="tvbo.network">')

            # Network model only has 'label', not 'name'
            if 'label' in data:
                lines.append(f'            <field name="label">{escape_xml(data["label"])}</field>')
            elif 'name' in data:
                lines.append(f'            <field name="label">{escape_xml(data["name"])}</field>')

            if 'number_of_regions' in data:
                lines.append(f'            <field name="number_of_regions">{data["number_of_regions"]}</field>')

            if 'number_of_nodes' in data:
                lines.append(f'            <field name="number_of_nodes">{data["number_of_nodes"]}</field>')

            if 'tractogram' in data:
                lines.append(f'            <field name="tractogram">{escape_xml(data["tractogram"])}</field>')

            # Link to parcellation by atlas name
            if 'parcellation' in data and 'atlas' in data['parcellation']:
                atlas_name = data['parcellation']['atlas'].get('name', '')
                if atlas_name:
                    atlas_id = sanitize_xml_id(atlas_name)
                    lines.append(f'            <field name="parcellation" ref="parcellation_{atlas_id}"/>')

            # node_labels as Text field
            if 'node_labels' in data:
                if isinstance(data['node_labels'], list):
                    labels_str = ','.join(str(l) for l in data['node_labels'])
                    lines.append(f'            <field name="node_labels">{escape_xml(labels_str)}</field>')
                else:
                    lines.append(f'            <field name="node_labels">{escape_xml(str(data["node_labels"]))}</field>')

            lines.extend(['        </record>', ''])

        except Exception as e:
            print(f"✗ Error processing {yaml_file.name}: {e}")
            import traceback
            traceback.print_exc()

    lines.extend(['    </data>', '</odoo>'])
    output_file.write_text('\n'.join(lines))


def generate_study_data_xml(yaml_files: List[Path], output_file: Path):
    """Generate XML data file for simulation studies."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        ''
    ]

    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            study_name = yaml_file.stem
            xml_id = f"study_{sanitize_xml_id(study_name)}"

            lines.extend([
                f'        <record id="{xml_id}" model="tvbo.simulation_study">',
                f'            <field name="label">{escape_xml(study_name)}</field>',
            ])

            if 'description' in data:
                lines.append(f'            <field name="description">{escape_xml(data["description"])}</field>')

            if 'key' in data:
                lines.append(f'            <field name="key">{escape_xml(data["key"])}</field>')

            lines.extend(['        </record>', ''])

        except Exception as e:
            print(f"✗ Error processing {yaml_file.name}: {e}")

    lines.extend(['    </data>', '</odoo>'])
    output_file.write_text('\n'.join(lines))


def generate_experiment_data_xml(yaml_files: List[Path], output_file: Path):
    """Generate XML data file for simulation experiments with full nested records.
    
    Creates complete record structure matching the experiment YAML:
    - Dynamics (with parameters, state_variables, derived_variables)
    - Network (with coupling functions and their parameters)
    - Integration (integrator settings)
    - Functions (reusable computation blocks)
    - Observations (monitors with pipelines)
    - Algorithms (FIC, EIB tuning)
    - Optimization (gradient-based fitting stages)
    - Explorations (parameter sweeps)
    """
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        ''
    ]

    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            exp_id = sanitize_xml_id(yaml_file.stem)
            exp_label = data.get('label', yaml_file.stem)
            exp_desc = data.get('description', '')

            # Track all created record IDs for linking
            dynamics_refs = []
            function_refs = []
            observation_refs = []
            derived_observation_refs = []
            algorithm_refs = []
            optimization_refs = []
            exploration_refs = []
            ld_id = None
            network_id = None
            integrator_id = None
            execution_id = None

            # =============== DYNAMICS (local_dynamics) ===============
            if 'local_dynamics' in data:
                ld = data['local_dynamics']
                ld_id = f"exp_{exp_id}_dynamics"
                dynamics_refs.append(ld_id)

                # Create parameters
                param_refs = []
                if 'parameters' in ld and ld['parameters']:
                    for pname, pdata in ld['parameters'].items():
                        if not isinstance(pdata, dict):
                            pdata = {'value': pdata}
                        pid = f"exp_{exp_id}_dyn_param_{sanitize_xml_id(pname)}"
                        param_refs.append(pid)

                        # Create Range record if domain has lo/hi
                        range_id = None
                        if 'domain' in pdata and pdata['domain']:
                            domain = pdata['domain']
                            if 'lo' in domain or 'hi' in domain:
                                range_id = f"{pid}_range"
                                lines.append(f'        <record id="{range_id}" model="tvbo.range">')
                                if 'lo' in domain:
                                    lo_val = domain['lo']
                                    if lo_val != float('inf') and lo_val != float('-inf'):
                                        lines.append(f'            <field name="lo">{lo_val}</field>')
                                if 'hi' in domain:
                                    hi_val = domain['hi']
                                    if hi_val != float('inf') and hi_val != float('-inf'):
                                        lines.append(f'            <field name="hi">{hi_val}</field>')
                                if 'step' in domain:
                                    lines.append(f'            <field name="step">{domain["step"]}</field>')
                                lines.append('        </record>')
                                lines.append('')

                        # Create parameter record
                        lines.append(f'        <record id="{pid}" model="tvbo.parameter">')
                        lines.append(f'            <field name="name">{escape_xml(pname)}</field>')
                        if 'label' in pdata:
                            lines.append(f'            <field name="label">{escape_xml(str(pdata["label"]))}</field>')
                        if 'value' in pdata:
                            lines.append(f'            <field name="value">{pdata["value"]}</field>')
                        if 'unit' in pdata:
                            lines.append(f'            <field name="unit">{escape_xml(str(pdata["unit"]))}</field>')
                        if 'description' in pdata:
                            lines.append(f'            <field name="description">{escape_xml(str(pdata["description"]))}</field>')
                        if pdata.get('free'):
                            lines.append(f'            <field name="free">True</field>')
                        if range_id:
                            lines.append(f'            <field name="domain" ref="{range_id}"/>')
                        lines.append('        </record>')
                        lines.append('')

                # Create state variables with proper equation records
                state_refs = []
                if 'state_variables' in ld and ld['state_variables']:
                    for svname, svdata in ld['state_variables'].items():
                        if not isinstance(svdata, dict):
                            svdata = {}
                        svid = f"exp_{exp_id}_dyn_sv_{sanitize_xml_id(svname)}"
                        state_refs.append(svid)

                        # Create equation record if present
                        sv_eq_id = None
                        if 'equation' in svdata and isinstance(svdata['equation'], dict):
                            if 'rhs' in svdata['equation']:
                                sv_eq_id = f"exp_{exp_id}_dyn_sv_{sanitize_xml_id(svname)}_eq"
                                lines.append(f'        <record id="{sv_eq_id}" model="tvbo.equation">')
                                lines.append(f'            <field name="label">d{escape_xml(svname)}/dt</field>')
                                lines.append(f'            <field name="lefthandside">d{escape_xml(svname)}/dt</field>')
                                lines.append(f'            <field name="righthandside">{escape_xml(str(svdata["equation"]["rhs"]))}</field>')
                                lines.append('        </record>')
                                lines.append('')

                        # Create state variable record
                        lines.append(f'        <record id="{svid}" model="tvbo.state_variable">')
                        lines.append(f'            <field name="name">{escape_xml(svname)}</field>')
                        if 'label' in svdata:
                            lines.append(f'            <field name="label">{escape_xml(str(svdata["label"]))}</field>')
                        if 'initial_value' in svdata:
                            lines.append(f'            <field name="initial_value">{svdata["initial_value"]}</field>')
                        if svdata.get('coupling_variable'):
                            lines.append(f'            <field name="coupling_variable">True</field>')
                        if 'description' in svdata:
                            lines.append(f'            <field name="description">{escape_xml(str(svdata["description"]))}</field>')
                        if sv_eq_id:
                            lines.append(f'            <field name="equation" ref="{sv_eq_id}"/>')
                        lines.append('        </record>')
                        lines.append('')

                # Create derived variables with proper equation records
                derived_refs = []
                if 'derived_variables' in ld and ld['derived_variables']:
                    for dvname, dvdata in ld['derived_variables'].items():
                        if not isinstance(dvdata, dict):
                            dvdata = {}
                        dvid = f"exp_{exp_id}_dyn_dv_{sanitize_xml_id(dvname)}"
                        derived_refs.append(dvid)

                        # Create equation record if present
                        dv_eq_id = None
                        if 'equation' in dvdata and isinstance(dvdata['equation'], dict):
                            if 'rhs' in dvdata['equation']:
                                dv_eq_id = f"exp_{exp_id}_dyn_dv_{sanitize_xml_id(dvname)}_eq"
                                lines.append(f'        <record id="{dv_eq_id}" model="tvbo.equation">')
                                lines.append(f'            <field name="label">{escape_xml(dvname)}</field>')
                                lines.append(f'            <field name="lefthandside">{escape_xml(dvname)}</field>')
                                lines.append(f'            <field name="righthandside">{escape_xml(str(dvdata["equation"]["rhs"]))}</field>')
                                lines.append('        </record>')
                                lines.append('')

                        # Create derived variable record
                        lines.append(f'        <record id="{dvid}" model="tvbo.derived_variable">')
                        lines.append(f'            <field name="name">{escape_xml(dvname)}</field>')
                        if 'label' in dvdata:
                            lines.append(f'            <field name="label">{escape_xml(str(dvdata["label"]))}</field>')
                        if 'description' in dvdata:
                            lines.append(f'            <field name="description">{escape_xml(str(dvdata["description"]))}</field>')
                        if dv_eq_id:
                            lines.append(f'            <field name="equation" ref="{dv_eq_id}"/>')
                        lines.append('        </record>')
                        lines.append('')

                # Create Dynamics record
                lines.append(f'        <record id="{ld_id}" model="tvbo.dynamics">')
                lines.append(f'            <field name="name">{escape_xml(ld.get("name", yaml_file.stem))}</field>')
                if 'label' in ld:
                    lines.append(f'            <field name="label">{escape_xml(str(ld["label"]))}</field>')
                if 'description' in ld:
                    lines.append(f'            <field name="description">{escape_xml(str(ld["description"]))}</field>')
                if param_refs:
                    lines.append(f'            <field name="parameters" eval="[(6, 0, [{", ".join(f"ref(\'{r}\')" for r in param_refs)}])]"/>')
                if state_refs:
                    lines.append(f'            <field name="state_variables" eval="[(6, 0, [{", ".join(f"ref(\'{r}\')" for r in state_refs)}])]"/>')
                if derived_refs:
                    lines.append(f'            <field name="derived_variables" eval="[(6, 0, [{", ".join(f"ref(\'{r}\')" for r in derived_refs)}])]"/>')
                lines.append('        </record>')
                lines.append('')

            # =============== NETWORK (includes coupling) ===============
            coupling_refs = []
            if 'network' in data:
                net = data['network']
                network_id = f"exp_{exp_id}_network"

                # Create coupling functions (inside network)
                if 'coupling' in net and net['coupling']:
                    for cname, cdata in net['coupling'].items():
                        if not isinstance(cdata, dict):
                            cdata = {}
                        cid = f"exp_{exp_id}_coupling_{sanitize_xml_id(cname)}"
                        coupling_refs.append(cid)

                        # Create coupling parameters
                        cparam_refs = []
                        if 'parameters' in cdata and cdata['parameters']:
                            for cpname, cpdata in cdata['parameters'].items():
                                if not isinstance(cpdata, dict):
                                    cpdata = {'value': cpdata}
                                cpid = f"exp_{exp_id}_cp_{sanitize_xml_id(cname)}_{sanitize_xml_id(cpname)}"
                                cparam_refs.append(cpid)

                                # Create Range for domain first if needed
                                range_id = None
                                if 'domain' in cpdata and cpdata['domain']:
                                    domain = cpdata['domain']
                                    has_lo = 'lo' in domain and domain['lo'] not in [float('inf'), float('-inf')]
                                    has_hi = 'hi' in domain and domain['hi'] not in [float('inf'), float('-inf')]
                                    if has_lo or has_hi:
                                        range_id = f"{cpid}_range"
                                        lines.append(f'        <record id="{range_id}" model="tvbo.range">')
                                        if has_lo:
                                            lines.append(f'            <field name="lo">{domain["lo"]}</field>')
                                        if has_hi:
                                            lines.append(f'            <field name="hi">{domain["hi"]}</field>')
                                        lines.append('        </record>')
                                        lines.append('')

                                # Now create the Parameter record
                                lines.append(f'        <record id="{cpid}" model="tvbo.parameter">')
                                lines.append(f'            <field name="name">{escape_xml(cpname)}</field>')
                                if 'label' in cpdata:
                                    lines.append(f'            <field name="label">{escape_xml(str(cpdata["label"]))}</field>')
                                if 'value' in cpdata:
                                    lines.append(f'            <field name="value">{cpdata["value"]}</field>')
                                if 'description' in cpdata:
                                    lines.append(f'            <field name="description">{escape_xml(str(cpdata["description"]))}</field>')
                                if cpdata.get('free'):
                                    lines.append(f'            <field name="free">True</field>')
                                if range_id:
                                    lines.append(f'            <field name="domain" ref="{range_id}"/>')
                                lines.append('        </record>')
                                lines.append('')

                        # Create coupling function record
                        # Create Equation for pre_expression if present
                        pre_expr_ref = None
                        if 'pre_expression' in cdata and cdata['pre_expression']:
                            pre_expr = cdata['pre_expression']
                            pre_expr_id = f"{cid}_pre_expr"
                            pre_expr_ref = pre_expr_id
                            lines.append(f'        <record id="{pre_expr_id}" model="tvbo.equation">')
                            if isinstance(pre_expr, dict) and 'lhs' in pre_expr:
                                lines.append(f'            <field name="lefthandside">{escape_xml(str(pre_expr["lhs"]))}</field>')
                            if isinstance(pre_expr, dict) and 'rhs' in pre_expr:
                                lines.append(f'            <field name="righthandside">{escape_xml(str(pre_expr["rhs"]))}</field>')
                            elif isinstance(pre_expr, str):
                                lines.append(f'            <field name="righthandside">{escape_xml(pre_expr)}</field>')
                            lines.append('        </record>')
                            lines.append('')
                        # Create Equation for post_expression if present
                        post_expr_ref = None
                        if 'post_expression' in cdata and cdata['post_expression']:
                            post_expr = cdata['post_expression']
                            post_expr_id = f"{cid}_post_expr"
                            post_expr_ref = post_expr_id
                            lines.append(f'        <record id="{post_expr_id}" model="tvbo.equation">')
                            if isinstance(post_expr, dict) and 'lhs' in post_expr:
                                lines.append(f'            <field name="lefthandside">{escape_xml(str(post_expr["lhs"]))}</field>')
                            if isinstance(post_expr, dict) and 'rhs' in post_expr:
                                lines.append(f'            <field name="righthandside">{escape_xml(str(post_expr["rhs"]))}</field>')
                            elif isinstance(post_expr, str):
                                lines.append(f'            <field name="righthandside">{escape_xml(post_expr)}</field>')
                            lines.append('        </record>')
                            lines.append('')
                        # Now create the Coupling record
                        lines.append(f'        <record id="{cid}" model="tvbo.coupling">')
                        lines.append(f'            <field name="name">{escape_xml(cname)}</field>')
                        if 'label' in cdata:
                            lines.append(f'            <field name="label">{escape_xml(str(cdata["label"]))}</field>')
                        if 'description' in cdata:
                            lines.append(f'            <field name="description">{escape_xml(str(cdata["description"]))}</field>')
                        if 'delayed' in cdata:
                            lines.append(f'            <field name="delayed">{str(cdata["delayed"])}"</field>')
                        if pre_expr_ref:
                            lines.append(f'            <field name="pre_expression" ref="{pre_expr_ref}"/>')
                        if post_expr_ref:
                            lines.append(f'            <field name="post_expression" ref="{post_expr_ref}"/>')
                        if cparam_refs:
                            lines.append(f'            <field name="parameters" eval="[(6, 0, [{", ".join(f"ref('{r}')" for r in cparam_refs)}])]"/>')
                        lines.append('        </record>')
                        lines.append('')

                # Create network record
                lines.append(f'        <record id="{network_id}" model="tvbo.network">')
                if 'label' in net:
                    lines.append(f'            <field name="label">{escape_xml(str(net["label"]))}</field>')
                if 'description' in net:
                    lines.append(f'            <field name="description">{escape_xml(str(net["description"]))}</field>')
                if 'bids_dir' in net:
                    lines.append(f'            <field name="bids_dir">{escape_xml(str(net["bids_dir"]))}</field>')
                if coupling_refs:
                    lines.append(f'            <field name="coupling" eval="[(6, 0, [{", ".join(f"ref(\'{c}\')" for c in coupling_refs)}])]"/>')
                lines.append('        </record>')
                lines.append('')

            # =============== INTEGRATION ===============
            if 'integration' in data:
                integ = data['integration']
                integrator_id = f"exp_{exp_id}_integrator"

                lines.append(f'        <record id="{integrator_id}" model="tvbo.integrator">')
                if 'method' in integ:
                    lines.append(f'            <field name="method">{escape_xml(str(integ["method"]))}</field>')
                if 'step_size' in integ:
                    lines.append(f'            <field name="step_size">{integ["step_size"]}</field>')
                if 'duration' in integ:
                    lines.append(f'            <field name="duration">{integ["duration"]}</field>')
                if 'transient_time' in integ:
                    lines.append(f'            <field name="transient_time">{integ["transient_time"]}</field>')
                lines.append('        </record>')
                lines.append('')

            # =============== EXECUTION CONFIG ===============
            if 'execution' in data:
                exec_data = data['execution']
                execution_id = f"exp_{exp_id}_execution"

                lines.append(f'        <record id="{execution_id}" model="tvbo.execution_config">')
                if 'n_workers' in exec_data:
                    lines.append(f'            <field name="n_workers">{exec_data["n_workers"]}</field>')
                if 'n_threads' in exec_data:
                    lines.append(f'            <field name="n_threads">{exec_data["n_threads"]}</field>')
                if 'precision' in exec_data:
                    lines.append(f'            <field name="precision">{escape_xml(str(exec_data["precision"]))}</field>')
                if 'accelerator' in exec_data:
                    lines.append(f'            <field name="accelerator">{escape_xml(str(exec_data["accelerator"]))}</field>')
                if 'batch_size' in exec_data:
                    lines.append(f'            <field name="batch_size">{exec_data["batch_size"]}</field>')
                if 'random_seed' in exec_data:
                    lines.append(f'            <field name="random_seed">{exec_data["random_seed"]}</field>')
                lines.append('        </record>')
                lines.append('')

            # =============== FUNCTIONS ===============
            if 'functions' in data and data['functions']:
                for fname, fdata in data['functions'].items():
                    if not isinstance(fdata, dict):
                        fdata = {}
                    fid = f"exp_{exp_id}_func_{sanitize_xml_id(fname)}"
                    function_refs.append(fid)

                    lines.append(f'        <record id="{fid}" model="tvbo.function">')
                    lines.append(f'            <field name="name">{escape_xml(fname)}</field>')
                    if 'description' in fdata:
                        lines.append(f'            <field name="description">{escape_xml(str(fdata["description"]))}</field>')
                    if 'source_code' in fdata:
                        lines.append(f'            <field name="source_code">{escape_xml(str(fdata["source_code"]))}</field>')
                    if 'equation' in fdata and isinstance(fdata['equation'], dict):
                        if 'rhs' in fdata['equation']:
                            lines.append(f'            <field name="definition">{escape_xml(str(fdata["equation"]["rhs"]))}</field>')
                    lines.append('        </record>')
                    lines.append('')

            # =============== OBSERVATIONS ===============
            if 'observations' in data and data['observations']:
                for oname, odata in data['observations'].items():
                    if not isinstance(odata, dict):
                        odata = {}
                    oid = f"exp_{exp_id}_obs_{sanitize_xml_id(oname)}"
                    observation_refs.append(oid)

                    lines.append(f'        <record id="{oid}" model="tvbo.observation">')
                    lines.append(f'            <field name="name">{escape_xml(oname)}</field>')
                    if 'label' in odata:
                        lines.append(f'            <field name="label">{escape_xml(str(odata["label"]))}</field>')
                    if 'description' in odata:
                        lines.append(f'            <field name="description">{escape_xml(str(odata["description"]))}</field>')
                    lines.append('        </record>')
                    lines.append('')

            # =============== DERIVED OBSERVATIONS ===============
            if 'derived_observations' in data and data['derived_observations']:
                for doname, dodata in data['derived_observations'].items():
                    if not isinstance(dodata, dict):
                        dodata = {}
                    doid = f"exp_{exp_id}_dobs_{sanitize_xml_id(doname)}"
                    derived_observation_refs.append(doid)  # Use separate list for derived observations

                    lines.append(f'        <record id="{doid}" model="tvbo.derived_observation">')
                    lines.append(f'            <field name="name">{escape_xml(doname)}</field>')
                    if 'label' in dodata:
                        lines.append(f'            <field name="label">{escape_xml(str(dodata["label"]))}</field>')
                    if 'description' in dodata:
                        lines.append(f'            <field name="description">{escape_xml(str(dodata["description"]))}</field>')
                    lines.append('        </record>')
                    lines.append('')

            # =============== ALGORITHMS (FIC, EIB) ===============
            if 'algorithms' in data and data['algorithms']:
                algo_data = data['algorithms']
                # Handle both dict and list formats
                if isinstance(algo_data, list):
                    algo_items = {item.get('name', f'algo_{i}'): item for i, item in enumerate(algo_data)}
                elif isinstance(algo_data, dict):
                    algo_items = algo_data
                else:
                    algo_items = {}

                for aname, adata in algo_items.items():
                    if not isinstance(adata, dict):
                        adata = {}
                    aid = f"exp_{exp_id}_algo_{sanitize_xml_id(aname)}"
                    algorithm_refs.append(aid)

                    lines.append(f'        <record id="{aid}" model="tvbo.algorithm">')
                    lines.append(f'            <field name="name">{escape_xml(aname)}</field>')
                    if 'label' in adata:
                        lines.append(f'            <field name="label">{escape_xml(str(adata["label"]))}</field>')
                    if 'description' in adata:
                        lines.append(f'            <field name="description">{escape_xml(str(adata["description"]))}</field>')
                    if 'target_variable' in adata:
                        lines.append(f'            <field name="target_variable">{escape_xml(str(adata["target_variable"]))}</field>')
                    if 'target_value' in adata:
                        lines.append(f'            <field name="target_value">{adata["target_value"]}</field>')
                    if 'n_iterations' in adata:
                        lines.append(f'            <field name="n_iterations">{adata["n_iterations"]}</field>')
                    if 'iteration_duration' in adata:
                        lines.append(f'            <field name="iteration_duration">{adata["iteration_duration"]}</field>')
                    if 'warmup_duration' in adata:
                        lines.append(f'            <field name="warmup_duration">{adata["warmup_duration"]}</field>')
                    lines.append('        </record>')
                    lines.append('')

            # =============== OPTIMIZATION ===============
            if 'optimization' in data:
                opt_data = data['optimization']
                # Handle both dict and list formats
                if isinstance(opt_data, list):
                    opt_items = {item.get('name', f'opt_{i}'): item for i, item in enumerate(opt_data)}
                else:
                    opt_items = opt_data if isinstance(opt_data, dict) else {}

                for optname, optdata in opt_items.items():
                    if not isinstance(optdata, dict):
                        optdata = {}
                    optid = f"exp_{exp_id}_opt_{sanitize_xml_id(optname)}"
                    optimization_refs.append(optid)

                    lines.append(f'        <record id="{optid}" model="tvbo.optimization">')
                    lines.append(f'            <field name="name">{escape_xml(optname)}</field>')
                    if 'label' in optdata:
                        lines.append(f'            <field name="label">{escape_xml(str(optdata["label"]))}</field>')
                    if 'description' in optdata:
                        lines.append(f'            <field name="description">{escape_xml(str(optdata["description"]))}</field>')
                    lines.append('        </record>')
                    lines.append('')

            # =============== EXPLORATIONS ===============
            if 'explorations' in data:
                exp_data = data['explorations']
                # Handle both dict and list formats
                if isinstance(exp_data, list):
                    exp_items = {item.get('name', f'exp_{i}'): item for i, item in enumerate(exp_data)}
                else:
                    exp_items = exp_data if isinstance(exp_data, dict) else {}

                for expname, expdata in exp_items.items():
                    if not isinstance(expdata, dict):
                        expdata = {}
                    exprid = f"exp_{exp_id}_explr_{sanitize_xml_id(expname)}"
                    exploration_refs.append(exprid)

                    lines.append(f'        <record id="{exprid}" model="tvbo.exploration">')
                    lines.append(f'            <field name="name">{escape_xml(expname)}</field>')
                    if 'label' in expdata:
                        lines.append(f'            <field name="label">{escape_xml(str(expdata["label"]))}</field>')
                    if 'description' in expdata:
                        lines.append(f'            <field name="description">{escape_xml(str(expdata["description"]))}</field>')
                    if 'mode' in expdata:
                        lines.append(f'            <field name="mode">{escape_xml(str(expdata["mode"]))}</field>')
                    lines.append('        </record>')
                    lines.append('')

            # =============== SIMULATION EXPERIMENT ===============
            exp_xml_id = f"experiment_{exp_id}"
            lines.append(f'        <record id="{exp_xml_id}" model="tvbo.simulation_experiment">')
            lines.append(f'            <field name="label">{escape_xml(exp_label)}</field>')
            if exp_desc:
                lines.append(f'            <field name="description">{escape_xml(exp_desc)}</field>')

            # Link dynamics
            if dynamics_refs:
                lines.append(f'            <field name="dynamics" eval="[(6, 0, [{", ".join(f"ref(\'{d}\')" for d in dynamics_refs)}])]"/>')

            # Link network
            if network_id:
                lines.append(f'            <field name="network" ref="{network_id}"/>')

            # Link integrator
            if integrator_id:
                lines.append(f'            <field name="integration" ref="{integrator_id}"/>')

            # Link functions
            if function_refs:
                lines.append(f'            <field name="functions" eval="[(6, 0, [{", ".join(f"ref(\'{f}\')" for f in function_refs)}])]"/>')

            # Link observations
            if observation_refs:
                lines.append(f'            <field name="observations" eval="[(6, 0, [{", ".join(f"ref(\'{o}\')" for o in observation_refs)}])]"/>')

            # Link derived observations
            if derived_observation_refs:
                lines.append(f'            <field name="derived_observations" eval="[(6, 0, [{", ".join(f"ref(\'{d}\')" for d in derived_observation_refs)}])]"/>')

            # Link algorithms
            if algorithm_refs:
                lines.append(f'            <field name="algorithms" eval="[(6, 0, [{", ".join(f"ref(\'{a}\')" for a in algorithm_refs)}])]"/>')

            # Link optimization
            if optimization_refs:
                lines.append(f'            <field name="optimization" eval="[(6, 0, [{", ".join(f"ref(\'{o}\')" for o in optimization_refs)}])]"/>')

            # Link explorations
            if exploration_refs:
                lines.append(f'            <field name="explorations" eval="[(6, 0, [{", ".join(f"ref(\'{e}\')" for e in exploration_refs)}])]"/>')

            # Link execution config (created before the experiment record)
            if execution_id:
                lines.append(f'            <field name="execution" ref="{execution_id}"/>')

            # References
            if 'references' in data and data['references']:
                refs_text = '\n'.join(f'- {r}' for r in data['references']) if isinstance(data['references'], list) else str(data['references'])
                lines.append(f'            <field name="references">{escape_xml(refs_text)}</field>')

            lines.append('        </record>')
            lines.append('')

        except Exception as e:
            print(f"Error processing experiment {yaml_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    lines.extend(['    </data>', '</odoo>'])
    output_file.write_text('\n'.join(lines))


def generate_coupling_function_data_xml(yaml_files: List[Path], output_file: Path):
    """Generate XML data file for coupling functions."""
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        '<odoo>',
        '    <data noupdate="0">',
        ''
    ]

    for yaml_file in yaml_files:
        try:
            with open(yaml_file) as f:
                data = yaml.safe_load(f)

            if not data:
                continue

            func_name = data.get('name', yaml_file.stem)
            coupling_id = sanitize_xml_id(yaml_file.stem)

            # Create Parameter records
            param_refs = []
            if 'parameters' in data and data['parameters']:
                for param_name, param_data in data['parameters'].items():
                    param_id = f"param_coupling_{coupling_id}_{sanitize_xml_id(param_name)}"
                    param_refs.append(param_id)

                    lines.append(f'        <record id="{param_id}" model="tvbo.parameter">')
                    lines.append(f'            <field name="name">{escape_xml(param_name)}</field>')

                    if isinstance(param_data, dict):
                        if 'value' in param_data:
                            lines.append(f'            <field name="value">{param_data["value"]}</field>')
                        if 'description' in param_data:
                            lines.append(f'            <field name="description">{escape_xml(param_data["description"])}</field>')

                    lines.append(f'        </record>')
                    lines.append('')

            # Create Equation for pre_expression
            pre_expr_ref = None
            if 'pre_expression' in data and data['pre_expression']:
                expr = data['pre_expression']
                expr_id = f"pre_expr_{coupling_id}"
                pre_expr_ref = expr_id

                lines.append(f'        <record id="{expr_id}" model="tvbo.equation">')
                if 'lhs' in expr:
                    lines.append(f'            <field name="lefthandside">{escape_xml(expr["lhs"])}</field>')
                if 'rhs' in expr:
                    lines.append(f'            <field name="righthandside">{escape_xml(expr["rhs"])}</field>')
                lines.append(f'        </record>')
                lines.append('')

            # Create Equation for post_expression
            post_expr_ref = None
            if 'post_expression' in data and data['post_expression']:
                expr = data['post_expression']
                expr_id = f"post_expr_{coupling_id}"
                post_expr_ref = expr_id

                lines.append(f'        <record id="{expr_id}" model="tvbo.equation">')
                if 'lhs' in expr:
                    lines.append(f'            <field name="lefthandside">{escape_xml(expr["lhs"])}</field>')
                if 'rhs' in expr:
                    lines.append(f'            <field name="righthandside">{escape_xml(expr["rhs"])}</field>')
                lines.append(f'        </record>')
                lines.append('')

            # Create Coupling record
            xml_id = f"coupling_{coupling_id}"
            lines.extend([
                f'        <record id="{xml_id}" model="tvbo.coupling">',
                f'            <field name="name">{escape_xml(func_name)}</field>',
            ])

            if 'description' in data:
                lines.append(f'            <field name="description">{escape_xml(data["description"])}</field>')

            if 'sparse' in data:
                lines.append(f'            <field name="sparse">{str(data["sparse"]).lower()}</field>')

            if 'delayed' in data:
                lines.append(f'            <field name="delayed">{str(data["delayed"]).lower()}</field>')

            # Link parameters
            if param_refs:
                ref_list = ','.join([f"ref('{r}')" for r in param_refs])
                lines.append(f'            <field name="parameters" eval="[(6, 0, [{ref_list}])]"/>')

            # Link pre_expression
            if pre_expr_ref:
                lines.append(f'            <field name="pre_expression" ref="{pre_expr_ref}"/>')

            # Link post_expression
            if post_expr_ref:
                lines.append(f'            <field name="post_expression" ref="{post_expr_ref}"/>')

            lines.extend(['        </record>', ''])

        except Exception as e:
            print(f"✗ Error processing {yaml_file.name}: {e}")

    lines.extend(['    </data>', '</odoo>'])
    output_file.write_text('\n'.join(lines))


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    # Database is in tools/tvbo/database
    database_dir = Path('/Users/leonmartin_bih/tools/tvbo/database')
    # Output to odoo-addons structure for multiple addons support
    output_dir = project_root / 'odoo-addons' / 'tvbo' / 'data'

    output_dir.mkdir(exist_ok=True)

    print("Generating Odoo data files from TVBO database...")
    print(f"Database directory: {database_dir}")
    print()

    data_files = []

    # Process models
    models_dir = database_dir / 'models'
    if models_dir.exists():
        yaml_files = list(models_dir.glob('*.yaml'))
        if yaml_files:
            output_file = output_dir / 'database_neural_models.xml'
            generate_model_data_xml(yaml_files, output_file)
            data_files.append('data/database_neural_models.xml')
            print(f"✓ Generated {output_file.name} with {len(yaml_files)} neural mass models")

    # Process Julia dynamics models
    julia_dir = database_dir / 'models' / 'julia'
    if julia_dir.exists():
        # Process continuous dynamics
        yaml_files = [f for f in julia_dir.glob('*.yaml') if f.is_file()]

        # Also process discrete dynamics
        discrete_dir = julia_dir / 'discrete'
        if discrete_dir.exists():
            yaml_files.extend(discrete_dir.glob('*.yaml'))

        if yaml_files:
            output_file = output_dir / 'database_julia_dynamics.xml'
            generate_dynamics_data_xml(yaml_files, output_file, model_type="julia_dynamics")
            data_files.append('data/database_julia_dynamics.xml')
            print(f"✓ Generated {output_file.name} with {len(yaml_files)} Julia dynamics models")

    # Process integrators
    integrators_dir = database_dir / 'integrators'
    if integrators_dir.exists():
        yaml_files = list(integrators_dir.glob('*.yaml'))
        if yaml_files:
            output_file = output_dir / 'database_integrators.xml'
            generate_integrator_data_xml(yaml_files, output_file)
            data_files.append('data/database_integrators.xml')
            print(f"✓ Generated {output_file.name} with {len(yaml_files)} integrators")

    # Process networks (Connectome records)
    networks_dir = database_dir / 'networks'
    if networks_dir.exists():
        yaml_files = list(networks_dir.glob('*.yaml'))
        if yaml_files:
            output_file = output_dir / 'database_networks.xml'
            generate_network_data_xml(yaml_files, output_file)
            data_files.append('data/database_networks.xml')
            print(f"✓ Generated {output_file.name} with {len(yaml_files)} connectomes")

    # Process studies
    studies_dir = database_dir / 'studies'
    if studies_dir.exists():
        yaml_files = list(studies_dir.glob('*.yaml'))
        if yaml_files:
            output_file = output_dir / 'database_studies.xml'
            generate_study_data_xml(yaml_files, output_file)
            data_files.append('data/database_studies.xml')
            print(f"✓ Generated {output_file.name} with {len(yaml_files)} studies")

    # Process coupling functions
    coupling_dir = database_dir / 'coupling_functions'
    if coupling_dir.exists():
        yaml_files = list(coupling_dir.glob('*.yaml'))
        if yaml_files:
            output_file = output_dir / 'database_coupling_functions.xml'
            generate_coupling_function_data_xml(yaml_files, output_file)
            data_files.append('data/database_coupling_functions.xml')
            print(f"✓ Generated {output_file.name} with {len(yaml_files)} coupling functions")

    # Process experiments
    experiments_dir = database_dir / 'experiments'
    if experiments_dir.exists():
        yaml_files = list(experiments_dir.glob('*.yaml'))
        if yaml_files:
            output_file = output_dir / 'database_experiments.xml'
            generate_experiment_data_xml(yaml_files, output_file)
            data_files.append('data/database_experiments.xml')
            print(f"✓ Generated {output_file.name} with {len(yaml_files)} experiments")

    print()
    print(f"✓ Generated {len(data_files)} database data files")
    print()
    print("Data files to add to __manifest__.py:")
    for df in data_files:
        print(f"  '{df}',")


if __name__ == '__main__':
    main()
