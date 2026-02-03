# -*- coding: utf-8 -*-
# Auto-generated from TVBO schemas - DO NOT EDIT MANUALLY
# Re-run scripts/generate_odoo_models.py to update
from odoo import models, fields, api


class ImagingModality(models.Model):
    _name = 'tvbo.imaging_modality'
    _description = 'ImagingModality'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class SystemType(models.Model):
    _name = 'tvbo.system_type'
    _description = 'SystemType'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class BoundaryConditionType(models.Model):
    _name = 'tvbo.boundary_condition_type'
    _description = 'BoundaryConditionType'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class DiscretizationMethod(models.Model):
    _name = 'tvbo.discretization_method'
    _description = 'DiscretizationMethod'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class ElementType(models.Model):
    _name = 'tvbo.element_type'
    _description = 'ElementType'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class OperatorType(models.Model):
    _name = 'tvbo.operator_type'
    _description = 'OperatorType'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class NoiseType(models.Model):
    _name = 'tvbo.noise_type'
    _description = 'NoiseType'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class AggregationType(models.Model):
    _name = 'tvbo.aggregation_type'
    _description = 'How to aggregate time series data'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class RequirementRole(models.Model):
    _name = 'tvbo.requirement_role'
    _description = 'RequirementRole'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class EnvironmentType(models.Model):
    _name = 'tvbo.environment_type'
    _description = 'EnvironmentType'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class DimensionType(models.Model):
    _name = 'tvbo.dimension_type'
    _description = 'Dimensions along which operations can be applied'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class ReductionType(models.Model):
    _name = 'tvbo.reduction_type'
    _description = 'Operations for reducing/aggregating values across dimensions'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class SpecimenEnum(models.Model):
    _name = 'tvbo.specimen_enum'
    _description = 'A set of permissible types for specimens used in brain atlas creation.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class Hemisphere(models.Model):
    _name = 'tvbo.hemisphere'
    _description = 'Hemisphere'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class Range(models.Model):
    _name = 'tvbo.range'
    _description = 'Specifies a range for array generation, parameter bounds, or grid exploration.'


    lo = fields.Char(string='Lower bound or starting value. Can be a number or argument name.', default='0')
    hi = fields.Char(string='Upper bound or stopping value. Can be a number or argument name.')
    step = fields.Char(string='Step size. Can be: number, argument name, or expression.')
    n = fields.Integer(string='Number of points (alternative to step for grid exploration).')
    log_scale = fields.Boolean(string='Whether to use logarithmic spacing.')


class Equation(models.Model):
    _name = 'tvbo.equation'
    _description = 'Equation'

    _rec_name = 'label'

    label = fields.Char(index=True)
    definition = fields.Char()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_equation_parameters_rel')
    description = fields.Text()
    lefthandside = fields.Char()
    righthandside = fields.Char()
    conditionals = fields.Many2many(comodel_name='tvbo.conditional_block', relation='tvbo_equation_conditionals_rel', string='Conditional logic for piecewise equations.')
    engine = fields.Many2one(comodel_name='tvbo.software_requirement', string="Primary engine (must appear in environment.requirements; migration target replacing deprecated 'software').")
    pycode = fields.Char(string='Python code for the equation.')
    latex = fields.Boolean()


class ConditionalBlock(models.Model):
    _name = 'tvbo.conditional_block'
    _description = 'A single condition and its corresponding equation segment.'


    condition = fields.Char(string='The condition for this block (e.g., t > onset).')
    expression = fields.Char(string='The equation to apply when the condition is met.')


class Stimulus(models.Model):
    _name = 'tvbo.stimulus'
    _description = 'Stimulus'

    _rec_name = 'label'

    equation = fields.Many2one(comodel_name='tvbo.equation')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_stimulus_parameters_rel')
    description = fields.Text()
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')
    duration = fields.Float(default=1000.0)
    label = fields.Char(index=True)
    regions = fields.Text()
    weighting = fields.Text()


class TemporalApplicableEquation(models.Model):
    _name = 'tvbo.temporal_applicable_equation'
    _description = 'TemporalApplicableEquation'

    _inherits = {'tvbo.equation': 'equation_id'}

    equation_id = fields.Many2one('tvbo.equation', required=True, ondelete='cascade')

    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_temporal_applicable_equation_parameters_rel')
    time_dependent = fields.Boolean()


class Parcellation(models.Model):
    _name = 'tvbo.parcellation'
    _description = 'Parcellation'

    _rec_name = 'label'

    label = fields.Char(index=True)
    region_labels = fields.Text()
    center_coordinates = fields.Text()
    data_source = fields.Char()
    atlas = fields.Many2one(comodel_name='tvbo.brain_atlas', required=True)


class Tractogram(models.Model):
    _name = 'tvbo.tractogram'
    _description = 'Reference to tractography/diffusion MRI data used to derive structural connectivity'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    label = fields.Char(index=True)
    description = fields.Text()
    data_source = fields.Char(string='Path or URI to the tractography data file')
    number_of_subjects = fields.Integer(string='Number of subjects in the tractography dataset')
    acquisition = fields.Char(string='Acquisition protocol or scanner information')
    processing_pipeline = fields.Char(string='Processing pipeline used to generate the tractography')
    reference = fields.Char(string='Publication or DOI reference for this tractography dataset')


class Matrix(models.Model):
    _name = 'tvbo.matrix'
    _description = 'Adjacency matrix of a network.'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')
    x = fields.Many2one(comodel_name='tvbo.brain_region_series')
    y = fields.Many2one(comodel_name='tvbo.brain_region_series')
    values = fields.Text()


class BrainRegionSeries(models.Model):
    _name = 'tvbo.brain_region_series'
    _description = 'A series whose values represent latitude'


    values = fields.Text()


class Network(models.Model):
    _name = 'tvbo.network'
    _description = 'Network specification with nodes, edges, and reusable coupling configurations. Supports both explicit node/edge representation and matrix-based connectivity (Connectome compatibility).'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    nodes = fields.Many2many(comodel_name='tvbo.node', relation='tvbo_network_nodes_rel', string='List of nodes with individual dynamics (optional, for heterogeneous networks)')
    edges = fields.Many2many(comodel_name='tvbo.edge', relation='tvbo_network_edges_rel', string='List of directed edges with coupling references (optional, for explicit edge definition)')
    coupling = fields.Many2many(comodel_name='tvbo.coupling', relation='tvbo_network_coupling_rel', string="Reusable coupling configurations referenced by edges (e.g., 'instant', 'delayed', 'inhibitory')")
    number_of_regions = fields.Integer(string='Number of regions (derived from nodes if not set)', default=1)
    number_of_nodes = fields.Integer(string='Number of nodes in the network (derived from nodes if not set)', default=1)
    parcellation = fields.Many2one(comodel_name='tvbo.parcellation', string='Brain parcellation/atlas reference')
    tractogram = fields.Char(string='Reference to tractography data')
    normalization = fields.Many2one(comodel_name='tvbo.equation', string='Normalization equation for connectivity weights')
    global_coupling_strength = fields.Many2one(comodel_name='tvbo.parameter', string='Global scaling factor for all coupling weights')
    conduction_speed = fields.Many2one(comodel_name='tvbo.parameter', string='Conduction speed for computing delays from distances')
    bids_dir = fields.Char(string='Path to BEP017-compliant BIDS directory for loading connectivity matrices')
    structural_measures = fields.Text(string='BEP017 measure names for structural connectivity (e.g., streamlineCount, tractLength)')
    observational_measures = fields.Text(string='BEP017 measure names for observational targets (e.g., BoldCorrelation)')
    distance_unit = fields.Char(string="Unit for distances/lengths in the network (e.g., 'mm', 'm', 'cm')", default='mm')
    time_unit = fields.Char(string="Default time unit for the network (e.g., 'ms', 's')", default='ms')
    edge_matrix_files = fields.Many2many(comodel_name='tvbo.file', relation='tvbo_network_edge_matrix_files_rel')


class File(models.Model):
    _name = 'tvbo.file'
    _description = 'File'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    type = fields.Char()
    path = fields.Char()
    extension = fields.Char()


class Node(models.Model):
    _name = 'tvbo.node'
    _description = 'A node in a network with its own dynamics and properties'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    record_id = fields.Integer(string='Unique node identifier', required=True)
    dynamics = fields.Many2one(comodel_name='tvbo.dynamics', string="Dynamics model governing this node's behavior. Can be a reference (by name) or inline definition. If not provided, uses experiment's local_dynamics.")
    position = fields.Many2one(comodel_name='tvbo.coordinate', string='Spatial coordinates (x, y, z) of the node')
    region = fields.Char(string='Brain region or anatomical label')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_node_parameters_rel', string='Node-specific parameter overrides')
    initial_state = fields.Text(string='Initial values for state variables')


class Edge(models.Model):
    _name = 'tvbo.edge'
    _description = 'A directed edge in a network with coupling and connectivity properties. Edge properties (weight, delay, distance) are stored in the parameters slot with optional units.'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_edge_parameters_rel')
    source = fields.Integer(string='Source node ID', required=True)
    target = fields.Integer(string='Target node ID', required=True)
    source_var = fields.Char(string="Output variable from source node to use (e.g., 'x_out'). If not specified, uses first output variable from source dynamics.")
    target_var = fields.Char(string="Input variable on target node to connect to (e.g., 'c_in'). If not specified, uses first coupling input from target dynamics.")
    coupling = fields.Many2one(comodel_name='tvbo.coupling', string="Coupling function for this edge. Can be a reference (by name) to coupling or inline definition. If not provided, uses experiment's default coupling.")
    directed = fields.Boolean(string='Whether the edge is directed. If false, represents a symmetric/bidirectional connection.')


class Observation(models.Model):
    _name = 'tvbo.observation'
    _description = 'Unified class for all observation/measurement specifications. Covers monitors (BOLD, EEG), tuning observables, and derived quantities. Pipeline is a sequence of Functions with input → output flow.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    acronym = fields.Char()
    label = fields.Char(index=True)
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_observation_parameters_rel')
    environment = fields.Many2one(comodel_name='tvbo.software_environment')
    time_scale = fields.Char()
    source = fields.Many2one(comodel_name='tvbo.state_variable', string='State variable to observe (e.g., S_e for excitatory activity). For observations derived from other observations, use DerivedObservation.')
    period = fields.Float(string='Sampling period for monitors (ms). For BOLD: TR in ms.')
    downsample_period = fields.Float(string='Intermediate downsampling period (ms). For BOLD: typically matches dt.')
    voi = fields.Integer(string='Variable of interest index (which state variable to monitor). Default: 0.')
    imaging_modality = fields.Many2one(comodel_name='tvbo.imaging_modality', string='Type of imaging modality (BOLD, EEG, MEG, etc.)')
    warmup_source = fields.Char(string="Reference to transient simulation result for history initialization (e.g., 'result_init').")
    data_source = fields.Many2one(comodel_name='tvbo.data_source', string='Load data from external source (file, database, API). When specified, this observation represents empirical/external data rather than simulated data. Enables unified treatment of all data.')
    skip_t = fields.Integer(string='Number of samples to skip at the start (transient removal). For FC: typically 10-20 TRs.')
    tail_samples = fields.Integer(string='Number of samples from the end to use. Takes the last N samples before aggregation. E.g., tail_samples: 500 means use data[-500:].')
    aggregation = fields.Many2one(comodel_name='tvbo.aggregation_type', string='How to aggregate over time')
    window_size = fields.Integer(string='Number of samples for windowed aggregation')
    pipeline = fields.Many2many(comodel_name='tvbo.function_call', relation='tvbo_observation_pipeline_rel', string='Ordered sequence of Functions. Each Function transforms input → output.')
    class_reference = fields.Many2one(comodel_name='tvbo.class_reference', string='Direct class reference (alternative to pipeline). Use for external library classes like tvboptim.Bold, custom monitors, or any callable class. The class is instantiated with constructor_args and called with call_args. Example: {name: Bold, module: tvboptim.observations.tvb_monitors.bold, constructor_args: [{name: period, value: 1000.0}]}')


class DerivedObservation(models.Model):
    _name = 'tvbo.derived_observation'
    _description = 'Observation derived from one or more other observations. Examples: - fc (from bold) - single source transformation - fc_corr (from fc and fc_target) - multi-source comparison Unlike regular Observa...'

    _inherits = {'tvbo.observation': 'observation_id'}

    observation_id = fields.Many2one('tvbo.observation', required=True, ondelete='cascade')

    source_observations = fields.Many2many(comodel_name='tvbo.observation', relation='tvbo_derived_observation_source_observations_rel', string='One or more observations to derive from. For transformations (e.g., fc from bold), use single source. For comparisons (e.g., fc_corr from fc and fc_target), use multiple sources. Order may matter for asymmetric operations.', required=True)


class Dynamics(models.Model):
    _name = 'tvbo.dynamics'
    _description = 'Dynamics'

    _rec_name = 'name'

    has_reference = fields.Char()
    name = fields.Char(required=True, index=True)
    label = fields.Char(index=True)
    iri = fields.Char()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_dynamics_parameters_rel')
    description = fields.Text()
    source = fields.Char()
    references = fields.Text()
    derived_parameters = fields.Many2many(comodel_name='tvbo.derived_parameter', relation='tvbo_dynamics_derived_parameters_rel')
    derived_variables = fields.Many2many(comodel_name='tvbo.derived_variable', relation='tvbo_dynamics_derived_variables_rel')
    coupling_terms = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_dynamics_coupling_terms_rel')
    coupling_inputs = fields.Many2many(comodel_name='tvbo.coupling_input', relation='tvbo_dynamics_coupling_inputs_rel')
    state_variables = fields.Many2many(comodel_name='tvbo.state_variable', relation='tvbo_dynamics_state_variables_rel')
    is_modified = fields.Boolean(string="MODIFIED (renamed from 'modified')")
    output = fields.Text(string='Output variable names to include in simulation results. References to state_variables or derived_variables by name.')
    derived_from_model = fields.Many2one(comodel_name='tvbo.dynamics')
    number_of_modes = fields.Integer(default=1)
    local_coupling_term = fields.Many2one(comodel_name='tvbo.parameter')
    functions = fields.Many2many(comodel_name='tvbo.function', relation='tvbo_dynamics_functions_rel')
    stimulus = fields.Many2one(comodel_name='tvbo.stimulus')
    modes = fields.Many2many(comodel_name='tvbo.dynamics', relation='tvbo_dynamics_modes_rel', column1='dynamics_id', column2='modes_id')
    system_type = fields.Many2one(comodel_name='tvbo.system_type')


class StateVariable(models.Model):
    _name = 'tvbo.state_variable'
    _description = 'StateVariable'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    symbol = fields.Char()
    label = fields.Char(index=True)
    definition = fields.Char()
    domain = fields.Many2one(comodel_name='tvbo.range')
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Char()
    variable_of_interest = fields.Boolean()
    coupling_variable = fields.Boolean()
    noise = fields.Many2one(comodel_name='tvbo.noise')
    stimulation_variable = fields.Boolean()
    boundaries = fields.Many2one(comodel_name='tvbo.range')
    initial_value = fields.Float(default=0.1)
    history = fields.Many2one(comodel_name='tvbo.time_series')


class Distribution(models.Model):
    _name = 'tvbo.distribution'
    _description = 'Distribution'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    equation = fields.Many2one(comodel_name='tvbo.equation')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_distribution_parameters_rel')
    dependencies = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_distribution_dependencies_rel')
    correlation = fields.Many2one(comodel_name='tvbo.matrix')


class Parameter(models.Model):
    _name = 'tvbo.parameter'
    _description = 'Parameter'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    label = fields.Char(index=True)
    symbol = fields.Char()
    definition = fields.Char()
    value = fields.Float()
    default = fields.Char()
    domain = fields.Many2one(comodel_name='tvbo.range')
    reported_optimum = fields.Float()
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Char()
    comment = fields.Char()
    heterogeneous = fields.Boolean()
    free = fields.Boolean()
    shape = fields.Char()
    explored_values = fields.Text()


class CouplingInput(models.Model):
    _name = 'tvbo.coupling_input'
    _description = 'Specification of a coupling input channel for multi-coupling dynamics'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    dimension = fields.Integer(string='Dimensionality of the coupling input (number of coupled values)', default=1)
    keys = fields.Text(string='Named keys for multi-dimensional coupling. When dimension > 1, provides symbolic names for each index (e.g., keys: [lre, ffi] for dimension: 2). Used in equations as variable names.')


class Argument(models.Model):
    _name = 'tvbo.argument'
    _description = 'A function argument with explicit value specification. Value can be: literal (number/string), reference to input (input.key), or cross-observation reference (observation_name.output_key).'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    value = fields.Char(string='Argument value. Can be: - Literal: 1.0, "string", etc. - Input reference: "input.frequencies" (from source_observation outputs) - Cross-observation: "target_frequencies.peak_freqs" (from another observation)')
    unit = fields.Char()


class Function(models.Model):
    _name = 'tvbo.function'
    _description = 'A function with explicit input → transformation → output flow. Can be equation-based (symbolic) or software-based (callable). In a pipeline, functions are chained: output of one becomes input of next.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    acronym = fields.Char()
    label = fields.Char(index=True)
    equation = fields.Many2one(comodel_name='tvbo.equation')
    definition = fields.Char()
    description = fields.Text()
    requirements = fields.Many2many(comodel_name='tvbo.software_requirement', relation='tvbo_function_requirements_rel')
    input = fields.Many2one(comodel_name='tvbo.function', string="Simple input reference: name of previous function's output in pipeline. For multi-argument functions, use arguments with value references instead.")
    output = fields.Char(string="Name for this function's output (referenced by subsequent functions)")
    iri = fields.Char()
    arguments = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_function_arguments_rel', string='Parameters/arguments for the function')
    output_equation = fields.Many2one(comodel_name='tvbo.equation', string='Output transformation equation (if equation-based)')
    source_code = fields.Char()
    callable = fields.Many2one(comodel_name='tvbo.callable', string='Software implementation reference (if software-based)')
    apply_on_dimension = fields.Many2one(comodel_name='tvbo.dimension_type', string='Which dimension to apply the transformation on')
    aggregate = fields.Many2one(comodel_name='tvbo.aggregation', string='How to aggregate the result across dimensions. E.g., aggregate.over=node computes per-row (per-node) with keepdims. The type field controls whether to reduce (mean/sum) or keep dimensions (none).')
    time_range = fields.Many2one(comodel_name='tvbo.range', string='Time range for generated TimeSeries (for kernel generators). Equation is evaluated at each time point.')


class Aggregation(models.Model):
    _name = 'tvbo.aggregation'
    _description = 'Specifies how to aggregate values across a dimension. Used for loss functions to define per-element loss with reduction.'


    over = fields.Many2one(comodel_name='tvbo.dimension_type', string='Dimension to aggregate over (e.g., node, time, state)')
    type = fields.Many2one(comodel_name='tvbo.reduction_type', string='Aggregation operation (mean, sum, max, min, none)', default='mean')


class LossFunction(models.Model):
    _name = 'tvbo.loss_function'
    _description = 'A loss function for optimization with optional aggregation. Extends Function with aggregation specification for per-element losses.'

    _inherits = {'tvbo.function': 'function_id'}

    function_id = fields.Many2one('tvbo.function', required=True, ondelete='cascade')



class FunctionCall(models.Model):
    _name = 'tvbo.function_call'
    _description = 'Invocation of a function in a pipeline. Can reference a defined Function by name, OR inline a callable directly for external library functions. OR inline a class_call for classes that need instanti...'


    function = fields.Many2one(comodel_name='tvbo.function', string='Reference to a defined Function (by name)')
    callable = fields.Many2one(comodel_name='tvbo.callable', string='Direct callable specification (alternative to function reference)')
    class_call = fields.Many2one(comodel_name='tvbo.class_reference', string='Class instantiation and call (alternative to callable/function). Use for external library classes that need __init__ then __call__. Example: Bold monitor from tvboptim.')
    output = fields.Char(string="Name for this step's output (referenced by subsequent functions)")
    apply_on_dimension = fields.Many2one(comodel_name='tvbo.dimension_type', string="Dimension to apply function over (generates vmap in code). E.g., 'node' applies per-node.")
    aggregate = fields.Many2one(comodel_name='tvbo.aggregation', string='How to aggregate the result across dimensions. Example: aggregate.over=node, aggregate.type=mean applies function per node, then averages. Used in loss functions.')
    arguments = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_function_call_arguments_rel')


class Callable(models.Model):
    _name = 'tvbo.callable'
    _description = 'Callable'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    module = fields.Char()
    software = fields.Many2one(comodel_name='tvbo.software_requirement')


class ClassReference(models.Model):
    _name = 'tvbo.class_reference'
    _description = 'Reference to a class that can be instantiated and called. Used for external library classes (e.g., tvboptim.Bold, custom monitors). The class is instantiated with constructor_args, then called with...'

    _inherits = {'tvbo.callable': 'callable_id'}

    callable_id = fields.Many2one('tvbo.callable', required=True, ondelete='cascade')

    constructor_args = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_class_reference_constructor_args_rel', string='Arguments passed to __init__ when instantiating the class. Example: period=1000.0, downsample_period=4.0 for Bold monitor.')
    call_args = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_class_reference_call_args_rel', string='Arguments passed when calling the instance (__call__). Usually the input data from simulation result. Example: result (simulation output array).')
    warmup_source = fields.Char(string="Reference to transient simulation result for history initialization. Some monitors (e.g., Bold) require history from warmup simulation. Value should reference a simulation result name (e.g., 'result_init').")


class Case(models.Model):
    _name = 'tvbo.case'
    _description = 'Case'


    condition = fields.Char()
    equation = fields.Many2one(comodel_name='tvbo.equation')


class DerivedParameter(models.Model):
    _name = 'tvbo.derived_parameter'
    _description = 'DerivedParameter'

    _inherits = {'tvbo.parameter': 'parameter_id'}

    parameter_id = fields.Many2one('tvbo.parameter', required=True, ondelete='cascade')

    name = fields.Char(required=True, index=True)
    symbol = fields.Char()
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Char()


class DerivedVariable(models.Model):
    _name = 'tvbo.derived_variable'
    _description = 'DerivedVariable'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    label = fields.Char(index=True)
    symbol = fields.Char()
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Char()
    conditional = fields.Boolean()
    cases = fields.Many2many(comodel_name='tvbo.case', relation='tvbo_derived_variable_cases_rel')


class Noise(models.Model):
    _name = 'tvbo.noise'
    _description = 'Noise'


    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_noise_parameters_rel')
    equation = fields.Many2one(comodel_name='tvbo.equation')
    noise_type = fields.Char()
    correlated = fields.Boolean()
    gaussian = fields.Boolean(string='Indicates whether the noise is Gaussian')
    additive = fields.Boolean(string='Indicates whether the noise is additive')
    seed = fields.Integer(default=42)
    random_state = fields.Many2one(comodel_name='tvbo.random_stream')
    intensity = fields.Many2one(comodel_name='tvbo.parameter', string='Optional scalar or vector intensity parameter for noise.')
    function = fields.Many2one(comodel_name='tvbo.function', string='Optional functional form of the noise (callable specification).')
    pycode = fields.Char(string='Inline Python code representation of the noise process.')
    targets = fields.Many2many(comodel_name='tvbo.state_variable', relation='tvbo_noise_targets_rel', string='State variables this noise applies to; if omitted, applies globally.')


class RandomStream(models.Model):
    _name = 'tvbo.random_stream'
    _description = 'RandomStream'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')


class DataSource(models.Model):
    _name = 'tvbo.data_source'
    _description = 'Specification for loading external/empirical data.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    label = fields.Char(index=True)
    description = fields.Text()
    path = fields.Char(string='File path or URI to the data')
    loader = fields.Many2one(comodel_name='tvbo.callable', string='Callable that loads the data (e.g., load_functional_connectivity)')
    format = fields.Char(string="Data format: 'npy', 'mat', 'csv', 'nifti', etc.")
    key = fields.Char(string='Key/variable name within the file (for .mat, .npz, etc.)')
    preprocessing = fields.Many2one(comodel_name='tvbo.function', string='Optional preprocessing to apply after loading')


class OptimizationStage(models.Model):
    _name = 'tvbo.optimization_stage'
    _description = 'A single stage in a multi-stage optimization workflow. Stages run sequentially, with each stage potentially using different parameters, shapes, learning rates, and algorithms.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    label = fields.Char(index=True)
    description = fields.Text()
    free_parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_optimization_stage_free_parameters_rel', string='Parameters to optimize in this stage. Use \'shape\' attribute to specify scalar vs regional. Example: {name: w, shape: "(n_nodes,)"} for heterogeneous.')
    algorithm = fields.Char(string="Optimizer for this stage: 'adam', 'adamw', 'sgd', etc.", default='adam')
    learning_rate = fields.Float(default=0.001)
    max_iterations = fields.Integer(default=100)
    hyperparameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_optimization_stage_hyperparameters_rel', string='Stage-specific hyperparameters (e.g., b2=0.9999 for adam)')
    freeze_parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_optimization_stage_freeze_parameters_rel', string='Parameters from previous stages to freeze (keep at optimized value but not update)')
    warmup_from = fields.Many2one(comodel_name='tvbo.optimization_stage', string='Previous stage to initialize from. Final values from that stage become initial values for this stage.')


class Optimization(models.Model):
    _name = 'tvbo.optimization'
    _description = 'Configuration for parameter optimization. Inherits single-stage fields from OptimizationStage. For multi-stage workflows, use \'stages\' (ignores inherited single-stage fields). Loss equation refer...'

    _inherits = {'tvbo.optimization_stage': 'optimization_stage_id'}

    optimization_stage_id = fields.Many2one('tvbo.optimization_stage', required=True, ondelete='cascade')

    execution = fields.Many2one(comodel_name='tvbo.execution_config', string='Per-optimization execution configuration (overrides experiment-level defaults). Useful for setting random_seed, precision, or hardware for optimization phase.')
    integration = fields.Many2one(comodel_name='tvbo.integrator', string='Integration settings for optimization simulations (overrides experiment defaults). If specified, creates a fresh model_fn and state with prepare() before optimization. Can specify different duration, step_size, method than the experiment. If not specified, uses experiment-level integration settings.')
    loss = fields.Many2one(comodel_name='tvbo.function_call', string='Loss function call. Uses FunctionCall to either: 1. Reference existing function: function: rmse 2. Inline callable: callable: {module: ..., name: ...} Arguments specify inputs (simulated_fc, empirical_fc, etc.)')
    stages = fields.Many2many(comodel_name='tvbo.optimization_stage', relation='tvbo_optimization_stages_rel', string='Ordered list of optimization stages. Stages run sequentially. Stage n+1 starts from optimized values of stage n. When defined, inherited single-stage fields are ignored.')
    depends_on = fields.Many2one(comodel_name='tvbo.algorithm', string="Algorithm to use as starting point for optimization. If specified, optimization starts from algorithm's result state. If not specified, optimization starts from initial simulation state.")


class Exploration(models.Model):
    _name = 'tvbo.exploration'
    _description = 'Parameter space exploration (grid search, sweep).'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    label = fields.Char(index=True)
    description = fields.Text()
    execution = fields.Many2one(comodel_name='tvbo.execution_config', string='Per-exploration execution configuration (overrides experiment-level defaults). Useful for setting random_seed, n_workers for parallel grid search.')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_exploration_parameters_rel', string='Parameters with domain ranges to explore (uses domain.lo, domain.hi, domain.n)', required=True)
    mode = fields.Char(string="Combination mode: 'product' (full grid), 'zip' (paired)", default='product')
    observable = fields.Many2one(comodel_name='tvbo.function_call', string='Observable to compute at each point. Use function: obs_name for simple observation, or function: func_name + arguments for FunctionCall.')
    n_parallel = fields.Integer(string='Parallel evaluations', default=1)


class UpdateRule(models.Model):
    _name = 'tvbo.update_rule'
    _description = 'Defines how a parameter is updated based on observables. Represents iterative learning rules like FIC or EIB updates. Functions from experiment.functions are available in the equation.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    target_parameter = fields.Many2one(comodel_name='tvbo.parameter', string='The parameter to update (e.g., J_i, wLRE)', required=True)
    equation = fields.Many2one(comodel_name='tvbo.equation', string="Update equation (e.g., 'J_i + eta * delta'). Can use functions defined in experiment.functions section.", required=True)
    bounds = fields.Many2one(comodel_name='tvbo.range', string='Constraints on parameter values after update')
    warmup = fields.Boolean(string='Whether to apply learning rate warmup to this update rule. When true, the learning rate (eta) is scaled by (i+1)/n_iterations.')
    requires = fields.Many2many(comodel_name='tvbo.observation', relation='tvbo_update_rule_requires_rel', string='Observables required by this update rule')


class AlgorithmInclude(models.Model):
    _name = 'tvbo.algorithm_include'
    _description = 'Reference to an included algorithm with optional argument overrides. Allows combining algorithms with different hyperparameter values.'


    algorithm = fields.Many2one(comodel_name='tvbo.algorithm', string='Reference to the algorithm to include', required=True)
    arguments = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_algorithm_include_arguments_rel', string='Override hyperparameter values for the included algorithm. Maps parameter names to new values.')


class TuningObjective(models.Model):
    _name = 'tvbo.tuning_objective'
    _description = 'Defines what the tuning algorithm optimizes for. Can be an activity target (FIC) or a connectivity target (EIB).'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    type = fields.Char(string="Type of objective: 'activity_target', 'fc_matching', 'custom'")
    target_variable = fields.Many2one(comodel_name='tvbo.state_variable', string='State variable for activity targets (e.g., S_e)')
    target_value = fields.Float(string='Target value for activity objectives')
    target_data = fields.Many2one(comodel_name='tvbo.observation', string='Reference to empirical data observation for matching objectives')
    metric = fields.Many2one(comodel_name='tvbo.equation', string='Metric equation for matching (e.g., correlation, rmse)')


class Algorithm(models.Model):
    _name = 'tvbo.algorithm'
    _description = 'A complete specification of an iterative parameter tuning algorithm. Combines update rules, objectives, observations, and hyperparameters.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    execution = fields.Many2one(comodel_name='tvbo.execution_config', string='Per-algorithm execution configuration (overrides experiment-level defaults). Useful for setting random_seed per algorithm to ensure reproducibility.')
    type = fields.Char(string="Algorithm type: 'fic', 'eib', 'homeostatic', 'custom'")
    includes = fields.Many2many(comodel_name='tvbo.algorithm_include', relation='tvbo_algorithm_includes_rel', string='Include update rules from other algorithms with optional argument overrides. Unlike depends_on (sequential), includes means combined execution. Example: includes: [{algorithm: fic, arguments: [{name: eta, value: 0.1}]}]')
    objective = fields.Many2one(comodel_name='tvbo.tuning_objective', string='What the algorithm optimizes for')
    observations = fields.Many2many(comodel_name='tvbo.observation', relation='tvbo_algorithm_observations_rel', string='References to observations defined in the observations section. Includes both simulated observations and external data (via data_source).')
    update_rules = fields.Many2many(comodel_name='tvbo.update_rule', relation='tvbo_algorithm_update_rules_rel', string="How parameters are updated each iteration. When using 'includes', update_rules are inherited from included algorithms.")
    hyperparameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_algorithm_hyperparameters_rel', string='Additional algorithm-specific parameters')
    learning_rate = fields.Float(string='Learning rate (eta) for the tuning algorithm')
    learning_rate_warmup = fields.Boolean(string='Linear warmup of learning rate from 0 to learning_rate over n_iterations. eta_effective = eta * (i+1) / n_iterations')
    n_iterations = fields.Integer(string='Number of iterations to run')
    learning_rate_schedule = fields.Char(string="Learning rate schedule: 'constant', 'linear', 'exponential'")
    simulation_period = fields.Float(string='Duration of each simulation step (e.g., one BOLD TR)')
    apply_every = fields.Integer(string='Apply update every N iterations', default=1)
    functions = fields.Many2many(comodel_name='tvbo.function_call', relation='tvbo_algorithm_functions_rel', string="Function calls for tracking progress, computing metrics, etc. Each FunctionCall references a function from the experiment's functions section and specifies arguments for that specific algorithm context.")
    depends_on = fields.Many2many(comodel_name='tvbo.algorithm', relation='tvbo_algorithm_depends_on_rel', column1='algorithm_id', column2='depends_on_id', string='Other algorithms that must run first (e.g., EIB depends on FIC)')


class Integrator(models.Model):
    _name = 'tvbo.integrator'
    _description = 'Integrator'


    time_scale = fields.Char()
    unit = fields.Char()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_integrator_parameters_rel')
    duration = fields.Float(default=1000.0)
    description = fields.Text()
    method = fields.Char(string='Integration method (euler, heun, rk4, etc.)', default='euler')
    step_size = fields.Float(default=0.01220703125)
    steps = fields.Integer()
    noise = fields.Many2one(comodel_name='tvbo.noise')
    state_wise_sigma = fields.Text()
    transient_time = fields.Float(default=0.0)
    scipy_ode_base = fields.Boolean()
    number_of_stages = fields.Integer(default=1)
    intermediate_expressions = fields.Many2many(comodel_name='tvbo.derived_variable', relation='tvbo_integrator_intermediate_expressions_rel')
    update_expression = fields.Many2one(comodel_name='tvbo.derived_variable')
    delayed = fields.Boolean()


class Coupling(models.Model):
    _name = 'tvbo.coupling'
    _description = 'Coupling'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    label = fields.Char(index=True)
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_coupling_parameters_rel')
    description = fields.Text()
    coupling_function = fields.Many2one(comodel_name='tvbo.equation', string='Mathematical function defining the coupling')
    sparse = fields.Boolean(string='Whether the coupling uses sparse representations')
    pre_expression = fields.Many2one(comodel_name='tvbo.equation', string='Pre-processing expression applied before coupling')
    post_expression = fields.Many2one(comodel_name='tvbo.equation', string='Post-processing expression applied after coupling')
    incoming_states = fields.Many2many(comodel_name='tvbo.state_variable', relation='tvbo_coupling_incoming_states_rel', string='References to state variables from connected nodes (source)')
    local_states = fields.Many2many(comodel_name='tvbo.state_variable', relation='tvbo_coupling_local_states_rel', string='References to state variables from local node (target)')
    delayed = fields.Boolean(string='Whether coupling includes transmission delays')
    inner_coupling = fields.Many2one(comodel_name='tvbo.coupling', string='For hierarchical coupling: inner coupling applied at regional level')
    region_mapping = fields.Many2one(comodel_name='tvbo.region_mapping', string='For hierarchical coupling: vertex-to-region mapping for aggregation')
    regional_connectivity = fields.Many2one(comodel_name='tvbo.network', string='For hierarchical coupling: region-to-region connectivity with weights and delays')
    aggregation = fields.Char(string="For hierarchical coupling: aggregation method ('sum', 'mean', 'max') or custom Function")
    distribution = fields.Char(string="For hierarchical coupling: distribution method ('broadcast', 'weighted') or custom Function")


class RegionMapping(models.Model):
    _name = 'tvbo.region_mapping'
    _description = 'Maps vertices to parent regions for hierarchical/aggregated coupling'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')
    vertex_to_region = fields.Text(string='Array mapping each vertex index to its parent region index. Can use dataLocation instead for large arrays.')
    n_vertices = fields.Integer(string='Total number of vertices')
    n_regions = fields.Integer(string='Total number of regions')


class Sample(models.Model):
    _name = 'tvbo.sample'
    _description = 'Sample'


    groups = fields.Text()
    size = fields.Integer()


class ExecutionConfig(models.Model):
    _name = 'tvbo.execution_config'
    _description = 'Configuration for computational execution (parallelization, precision, hardware).'


    n_workers = fields.Integer(string='Number of parallel workers (maps to pmap devices in JAX, processes in multiprocessing)', default=1)
    n_threads = fields.Integer(string='Number of CPU threads per worker (-1 = auto-detect)', default=-1)
    precision = fields.Char(string="Floating point precision: 'float32' or 'float64'", default='float64')
    accelerator = fields.Char(string="Hardware accelerator: 'cpu', 'gpu', 'tpu'", default='cpu')
    batch_size = fields.Integer(string='Batch size for vectorized operations (None = auto)')
    random_seed = fields.Integer(string='Base random seed for reproducibility', default=42)


class SimulationExperiment(models.Model):
    _name = 'tvbo.simulation_experiment'
    _description = 'SimulationExperiment'

    _rec_name = 'label'

    model = fields.Many2one(comodel_name='tvbo.dynamics')
    record_id = fields.Integer(string="ID (renamed from 'id')")
    description = fields.Text()
    additional_equations = fields.Many2many(comodel_name='tvbo.equation', relation='tvbo_simulation_experiment_additional_equations_rel')
    label = fields.Char(index=True)
    local_dynamics = fields.Many2one(comodel_name='tvbo.dynamics', string='Default dynamics model for all nodes (used when node.dynamics not specified or as fallback)')
    dynamics = fields.Many2many(comodel_name='tvbo.dynamics', relation='tvbo_simulation_experiment_dynamics_rel', string='Dictionary of dynamics models keyed by name. Nodes reference these by name.')
    integration = fields.Many2one(comodel_name='tvbo.integrator')
    connectivity = fields.Many2one(comodel_name='tvbo.network')
    network = fields.Many2one(comodel_name='tvbo.network')
    coupling = fields.Many2one(comodel_name='tvbo.coupling')
    observations = fields.Many2many(comodel_name='tvbo.observation', relation='tvbo_simulation_experiment_observations_rel')
    derived_observations = fields.Many2many(comodel_name='tvbo.derived_observation', relation='tvbo_simulation_experiment_derived_observations_rel', string='Observations derived from combining other observations. Computed after all regular observations are available. Examples: fc_corr (from fc, fc_target), rmse, etc.')
    functions = fields.Many2many(comodel_name='tvbo.function', relation='tvbo_simulation_experiment_functions_rel', string='Reusable function definitions. Referenced by name in observation pipelines. Enables DRY: define compute_fc once, use in both simulated and empirical paths.')
    stimulation = fields.Many2one(comodel_name='tvbo.stimulus')
    field_dynamics = fields.Many2one(comodel_name='tvbo.pde')
    optimization = fields.Many2many(comodel_name='tvbo.optimization', relation='tvbo_simulation_experiment_optimization_rel', string='Parameter optimization configurations')
    explorations = fields.Many2many(comodel_name='tvbo.exploration', relation='tvbo_simulation_experiment_explorations_rel', string='Parameter exploration/grid search specifications')
    algorithms = fields.Many2many(comodel_name='tvbo.algorithm', relation='tvbo_simulation_experiment_algorithms_rel', string='Iterative parameter tuning algorithms (FIC, EIB, etc.)')
    environment = fields.Many2one(comodel_name='tvbo.software_environment', string='Execution environment (collection of requirements).')
    execution = fields.Many2one(comodel_name='tvbo.execution_config', string='Computational execution configuration (parallelization, devices).')
    software = fields.Many2one(comodel_name='tvbo.software_requirement', string="(Deprecated) Single software requirement; prefer 'environment' with aggregated requirements.")
    references = fields.Text()


class SimulationStudy(models.Model):
    _name = 'tvbo.simulation_study'
    _description = 'SimulationStudy'

    _rec_name = 'label'

    label = fields.Char(index=True)
    model = fields.Many2one(comodel_name='tvbo.dynamics')
    description = fields.Text()
    key = fields.Char()
    title = fields.Char()
    year = fields.Integer()
    doi = fields.Char()
    sample = fields.Many2one(comodel_name='tvbo.sample')
    simulation_experiments = fields.Many2many(comodel_name='tvbo.simulation_experiment', relation='tvbo_simulation_study_simulation_experiments_rel')


class TimeSeries(models.Model):
    _name = 'tvbo.time_series'
    _description = 'Time series data from simulations or measurements. Supports BIDS-compatible export for computational modeling (BEP034).'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')
    data = fields.Many2one(comodel_name='tvbo.matrix')
    time = fields.Many2one(comodel_name='tvbo.matrix')
    sampling_rate = fields.Float(string='Sampling rate in Hz.')
    sampling_period = fields.Float(string='Time between samples (inverse of sampling_rate).')
    sampling_period_unit = fields.Char(string="Unit of the sampling period (e.g., 'ms', 's').")
    unit = fields.Char(string='Physical unit of the time series values.')
    labels_ordering = fields.Text(string='Ordering of dimensions: Time, State Variable, Space, Mode.')
    labels_dimensions = fields.Char(string='Mapping of dimension names to their labels (JSON-encoded dict).')
    source_experiment = fields.Many2one(comodel_name='tvbo.simulation_experiment', string='Reference to the SimulationExperiment that generated this TimeSeries.')
    generated_at = fields.Datetime(string='Timestamp when this TimeSeries was generated.')
    software_environment = fields.Many2one(comodel_name='tvbo.software_environment', string='Software environment used to generate this data.')
    task_name = fields.Char(string="BIDS task name for the simulation (e.g., 'rest', 'simulation').")
    subject_id = fields.Char(string='BIDS subject identifier.')
    session_id = fields.Char(string='BIDS session identifier.')
    run_id = fields.Integer(string='BIDS run number.')
    modality = fields.Many2one(comodel_name='tvbo.imaging_modality', string='Imaging modality or simulation output type.')
    model_equation_ref = fields.Char(string='BIDS ModelEq reference: path to _eq.xml LEMS file.')
    model_param_ref = fields.Char(string='BIDS ModelParam reference: path to _param.xml LEMS file.')
    connectivity_ref = fields.Char(string='Reference to connectivity data (_conndata-network_connectivity.tsv).')


class SoftwareEnvironment(models.Model):
    _name = 'tvbo.software_environment'
    _description = 'SoftwareEnvironment'

    _rec_name = 'name'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')
    name = fields.Char(required=True, index=True, string="Human-readable environment label/name (deprecated alias was 'software').")
    version = fields.Char(string='Optional version tag for the environment definition (not a package version).')
    platform = fields.Char(string='OS / architecture description (e.g., linux-64).')
    environment_type = fields.Many2one(comodel_name='tvbo.environment_type', string='Category: conda, venv, docker, etc.')
    container_image = fields.Char(string='Container image reference (e.g., ghcr.io/org/img:tag@sha256:...).')
    build_hash = fields.Char(string='Deterministic hash/fingerprint of the resolved dependency set.')
    requirements = fields.Many2many(comodel_name='tvbo.software_requirement', relation='tvbo_software_environment_requirements_rel', string='Constituent software/module requirements that define this environment.')


class SoftwareRequirement(models.Model):
    _name = 'tvbo.software_requirement'
    _description = 'SoftwareRequirement'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True, string="Human-readable environment label/name (deprecated alias was 'software').")
    description = fields.Text()
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')
    package = fields.Many2one(comodel_name='tvbo.software_package', string='Reference to the software package identity.')
    version_spec = fields.Char(string="Version or constraint specifier (e.g., '==2.7.3', '>=1.2,<2').")
    role = fields.Many2one(comodel_name='tvbo.requirement_role')
    optional = fields.Boolean()
    hash = fields.Char(string='Build or artifact hash for exact reproducibility (wheel, sdist, image layer).')
    source_url = fields.Char(string='Canonical source or repository URL.')
    url = fields.Char(string='(Deprecated) Use source_url.')
    license = fields.Char()
    modules = fields.Text(string='(Deprecated) Former ad-hoc list; use environment.requirements list instead.')
    version = fields.Char(string='(Deprecated) Use version_spec.')


class SoftwarePackage(models.Model):
    _name = 'tvbo.software_package'
    _description = 'Identity information about a software package independent of a specific version requirement.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True, string="Human-readable environment label/name (deprecated alias was 'software').")
    description = fields.Text()
    homepage = fields.Char()
    license = fields.Char()
    repository = fields.Char()
    doi = fields.Char()
    ecosystem = fields.Char(string='Package ecosystem or index (e.g., pypi, conda-forge).')


class NDArray(models.Model):
    _name = 'tvbo.nd_array'
    _description = 'NDArray'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    shape = fields.Text()
    dtype = fields.Char()
    dataLocation = fields.Char()
    unit = fields.Char()


class SpatialDomain(models.Model):
    _name = 'tvbo.spatial_domain'
    _description = 'SpatialDomain'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space')
    region = fields.Char(string='Optional named region/ROI in the atlas/parcellation.')
    geometry = fields.Char(string='Optional file for geometry/ROI mask (e.g., NIfTI, GIfTI).')


class Mesh(models.Model):
    _name = 'tvbo.mesh'
    _description = 'Mesh'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')
    element_type = fields.Many2one(comodel_name='tvbo.element_type')
    coordinates = fields.Many2many(comodel_name='tvbo.coordinate', relation='tvbo_mesh_coordinates_rel', string='Node coordinates (x,y,z) in the given coordinate space.')
    elements = fields.Char(string='Connectivity (indices) or file reference to topology.')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space')


class SpatialField(models.Model):
    _name = 'tvbo.spatial_field'
    _description = 'SpatialField'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    quantity_kind = fields.Char(string='Scalar, vector, or tensor.')
    unit = fields.Char()
    mesh = fields.Many2one(comodel_name='tvbo.mesh')
    values = fields.Many2one(comodel_name='tvbo.nd_array')
    time_dependent = fields.Boolean()
    initial_value = fields.Float(string='Constant initial value for the field.', default=0.1)
    initial_expression = fields.Many2one(comodel_name='tvbo.equation', string='Analytic initial condition for the field.')


class FieldStateVariable(models.Model):
    _name = 'tvbo.field_state_variable'
    _description = 'FieldStateVariable'

    _inherits = {'tvbo.state_variable': 'state_variable_id'}

    state_variable_id = fields.Many2one('tvbo.state_variable', required=True, ondelete='cascade')

    label = fields.Char(index=True)
    description = fields.Text()
    mesh = fields.Many2one(comodel_name='tvbo.mesh')
    boundary_conditions = fields.Many2many(comodel_name='tvbo.boundary_condition', relation='tvbo_field_state_variable_boundary_conditions_rel')


class DifferentialOperator(models.Model):
    _name = 'tvbo.differential_operator'
    _description = 'DifferentialOperator'

    _rec_name = 'label'

    label = fields.Char(index=True)
    definition = fields.Char()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    operator_type = fields.Many2one(comodel_name='tvbo.operator_type')
    coefficient = fields.Many2one(comodel_name='tvbo.parameter')
    tensor_coefficient = fields.Many2one(comodel_name='tvbo.parameter', string='Optional anisotropic tensor (e.g., diffusion).')
    expression = fields.Many2one(comodel_name='tvbo.equation', string="Symbolic form (e.g., '-div(D * grad(u))').")


class BoundaryCondition(models.Model):
    _name = 'tvbo.boundary_condition'
    _description = 'BoundaryCondition'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    bc_type = fields.Many2one(comodel_name='tvbo.boundary_condition_type')
    on_region = fields.Char(string='Mesh/atlas subset where BC applies.')
    value = fields.Many2one(comodel_name='tvbo.equation', string='Constant, parameter, or equation.')
    time_dependent = fields.Boolean()


class PDESolver(models.Model):
    _name = 'tvbo.pde_solver'
    _description = 'PDESolver'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    requirements = fields.Many2many(comodel_name='tvbo.software_requirement', relation='tvbo_pde_solver_requirements_rel')
    environment = fields.Many2one(comodel_name='tvbo.software_environment')
    discretization = fields.Many2one(comodel_name='tvbo.discretization_method')
    time_integrator = fields.Char(string='e.g., implicit Euler, Crank–Nicolson.')
    dt = fields.Float(string='Time step (s).')
    tolerances = fields.Char(string='Abs/rel tolerances.')
    preconditioner = fields.Char()


class PDE(models.Model):
    _name = 'tvbo.pde'
    _description = 'Partial differential equation problem definition.'

    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_pde_parameters_rel')
    domain = fields.Many2one(comodel_name='tvbo.spatial_domain')
    mesh = fields.Many2one(comodel_name='tvbo.mesh', string='Shared mesh for all field state variables in this PDE.')
    state_variables = fields.Many2many(comodel_name='tvbo.field_state_variable', relation='tvbo_pde_state_variables_rel')
    field = fields.Many2one(comodel_name='tvbo.spatial_field', string='Primary field being solved for (deprecated; use state_variables).')
    operators = fields.Many2many(comodel_name='tvbo.differential_operator', relation='tvbo_pde_operators_rel')
    sources = fields.Many2many(comodel_name='tvbo.equation', relation='tvbo_pde_sources_rel')
    boundary_conditions = fields.Many2many(comodel_name='tvbo.boundary_condition', relation='tvbo_pde_boundary_conditions_rel')
    solver = fields.Many2one(comodel_name='tvbo.pde_solver')
    derived_parameters = fields.Many2many(comodel_name='tvbo.derived_parameter', relation='tvbo_pde_derived_parameters_rel')
    derived_variables = fields.Many2many(comodel_name='tvbo.derived_variable', relation='tvbo_pde_derived_variables_rel')
    functions = fields.Many2many(comodel_name='tvbo.function', relation='tvbo_pde_functions_rel')


class Dataset(models.Model):
    _name = 'tvbo.dataset'
    _description = 'Collection of data related to a specific DBS study.'

    _rec_name = 'label'

    label = fields.Char(index=True)
    dataset_id = fields.Char()
    subjects = fields.Many2many(comodel_name='tvbo.subject', relation='tvbo_dataset_subjects_rel')
    clinical_scores = fields.Many2many(comodel_name='tvbo.clinical_score', relation='tvbo_dataset_clinical_scores_rel')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space')


class Subject(models.Model):
    _name = 'tvbo.subject'
    _description = 'Human or animal subject receiving DBS.'


    subject_id = fields.Char(string='Unique identifier for a subject within a dataset.', required=True)
    age = fields.Float()
    sex = fields.Char()
    diagnosis = fields.Char()
    handedness = fields.Char()
    protocols = fields.Many2many(comodel_name='tvbo.dbs_protocol', relation='tvbo_subject_protocols_rel', string='All DBS protocols assigned to this subject.')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space', string="Coordinate space used for this subject's data")


class Electrode(models.Model):
    _name = 'tvbo.electrode'
    _description = 'Implanted DBS electrode and contact geometry.'


    electrode_id = fields.Char(string='Unique identifier for this electrode')
    manufacturer = fields.Char()
    model = fields.Char()
    hemisphere = fields.Char(string='Hemisphere of electrode (left/right)')
    contacts = fields.Many2many(comodel_name='tvbo.contact', relation='tvbo_electrode_contacts_rel', string='List of physical contacts along the electrode')
    head = fields.Many2one(comodel_name='tvbo.coordinate')
    tail = fields.Many2one(comodel_name='tvbo.coordinate')
    trajectory = fields.Many2many(comodel_name='tvbo.coordinate', relation='tvbo_electrode_trajectory_rel', string='The planned trajectory for electrode implantation')
    target_structure = fields.Many2one(comodel_name='tvbo.parcellation_entity', string='Anatomical target structure from a brain atlas')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space', string='Coordinate space used for implantation planning')
    recon_path = fields.Char()


class Contact(models.Model):
    _name = 'tvbo.contact'
    _description = 'Individual contact on a DBS electrode.'

    _rec_name = 'label'

    contact_id = fields.Integer(string='Identifier (e.g., 0, 1, 2)')
    coordinate = fields.Many2one(comodel_name='tvbo.coordinate', string='3D coordinate of the contact center in the defined coordinate space')
    label = fields.Char(index=True, string='Optional human-readable label (e.g., "1a")')


class StimulationSetting(models.Model):
    _name = 'tvbo.stimulation_setting'
    _description = 'DBS parameters for a specific session.'


    electrode_reference = fields.Many2one(comodel_name='tvbo.electrode')
    amplitude = fields.Many2one(comodel_name='tvbo.parameter')
    frequency = fields.Many2one(comodel_name='tvbo.parameter')
    pulse_width = fields.Many2one(comodel_name='tvbo.parameter')
    mode = fields.Char()
    active_contacts = fields.Text()
    efield = fields.Many2one(comodel_name='tvbo.e_field', string='Metadata about the E-field result for this setting')


class DBSProtocol(models.Model):
    _name = 'tvbo.dbs_protocol'
    _description = 'A protocol describing DBS therapy, potentially bilateral or multi-lead.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True, string="Human-readable environment label/name (deprecated alias was 'software').")
    electrodes = fields.Many2many(comodel_name='tvbo.electrode', relation='tvbo_dbs_protocol_electrodes_rel')
    settings = fields.Many2many(comodel_name='tvbo.stimulation_setting', relation='tvbo_dbs_protocol_settings_rel')
    timing_info = fields.Char()
    notes = fields.Char()
    clinical_improvement = fields.Many2many(comodel_name='tvbo.clinical_improvement', relation='tvbo_dbs_protocol_clinical_improvement_rel', string='Observed improvement relative to baseline based on a defined score.')


class ClinicalScale(models.Model):
    _name = 'tvbo.clinical_scale'
    _description = 'A clinical assessment inventory or structured scale composed of multiple scores or items.'

    _rec_name = 'name'

    acronym = fields.Char()
    name = fields.Char(required=True, index=True, string='Full name of the scale (e.g., Unified Parkinson’s Disease Rating Scale)')
    version = fields.Char(string='Version of the instrument (e.g., 3.0)')
    domain = fields.Char(string='Overall clinical domain (e.g., motor, cognition)')
    reference = fields.Char(string='DOI, PMID or persistent identifier')


class ClinicalScore(models.Model):
    _name = 'tvbo.clinical_score'
    _description = 'Metadata about a clinical score or scale.'

    _rec_name = 'name'

    acronym = fields.Char()
    name = fields.Char(required=True, index=True, string="Full name of the score (e.g., Unified Parkinson's Disease Rating Scale - Part III)")
    description = fields.Text()
    domain = fields.Char(string='Domain assessed (e.g. motor, mood, pain)')
    reference = fields.Char(string='PubMed ID, DOI, or other reference to the score definition')
    scale = fields.Many2one(comodel_name='tvbo.clinical_scale', string='The scale this score belongs to, if applicable')
    parent_score = fields.Many2one(comodel_name='tvbo.clinical_score', string='If this score is a subscore of a broader composite')


class ClinicalImprovement(models.Model):
    _name = 'tvbo.clinical_improvement'
    _description = 'Relative improvement on a defined clinical score.'


    score = fields.Many2one(comodel_name='tvbo.clinical_score')
    baseline_value = fields.Float(string='Preoperative baseline value of the score')
    absolute_value = fields.Float(string='Absolute value of the score at the time of assessment')
    percent_change = fields.Float(string='Percent change compared to preoperative baseline (positive = improvement)')
    time_post_surgery = fields.Float(string='Timepoint of assessment in days or months after implantation')
    evaluator = fields.Char(string='Who performed the rating (e.g., rater initials, clinician ID, or system)')
    timepoint = fields.Char(string='Timepoint of assessment (e.g., "1 month post-op", "6 months post-op")')


class EField(models.Model):
    _name = 'tvbo.e_field'
    _description = 'Simulated electric field from DBS modeling.'


    volume_data = fields.Char(string='Reference to raw or thresholded volume')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space', string='Reference to a common coordinate space (e.g. MNI152)')
    threshold_applied = fields.Float(string='Threshold value applied to the E-field simulation')


class Coordinate(models.Model):
    _name = 'tvbo.coordinate'
    _description = 'A 3D coordinate with X, Y, Z values.'


    coordinateSpace = fields.Many2one(comodel_name='tvbo.common_coordinate_space', string='Add the common coordinate space used for this brain atlas version.')
    x = fields.Float(string='X coordinate')
    y = fields.Float(string='Y coordinate')
    z = fields.Float(string='Z coordinate')


class BrainAtlas(models.Model):
    _name = 'tvbo.brain_atlas'
    _description = 'A schema for representing a version of a brain atlas.'

    _rec_name = 'name'

    coordinateSpace = fields.Many2one(comodel_name='tvbo.common_coordinate_space', string='Add the common coordinate space used for this brain atlas version.')
    name = fields.Char(required=True, index=True, string="Full name of the score (e.g., Unified Parkinson's Disease Rating Scale - Part III)")
    abbreviation = fields.Char(string='Slot for the abbreviation of a resource.')
    author = fields.Text()
    isVersionOf = fields.Char(string='Linked type for the version of a brain atlas or coordinate space.')
    versionIdentifier = fields.Char(string='Enter the version identifier of this brain atlas or coordinate space version.')


class CommonCoordinateSpace(models.Model):
    _name = 'tvbo.common_coordinate_space'
    _description = 'A schema for representing a version of a common coordinate space.'

    _rec_name = 'name'

    name = fields.Char(required=True, index=True, string="Full name of the score (e.g., Unified Parkinson's Disease Rating Scale - Part III)")
    abbreviation = fields.Char(string='Slot for the abbreviation of a resource.')
    unit = fields.Char()
    license = fields.Char(string='Linked type for the license of the brain atlas or coordinate space version.')
    anatomicalAxesOrientation = fields.Char(string='Add the axes orientation in standard anatomical terms (XYZ).')
    axesOrigin = fields.Char(string='Enter the origin (central point where all axes intersect).')
    nativeUnit = fields.Char(string='Add the native unit that is used for this common coordinate space version.')
    defaultImage = fields.Text(string='Add all image files used as visual representation of this common coordinate space version.')


class ParcellationEntity(models.Model):
    _name = 'tvbo.parcellation_entity'
    _description = 'A schema for representing a parcellation entity, which is an anatomical location or study target.'

    _rec_name = 'name'

    abbreviation = fields.Char(string='Slot for the abbreviation of a resource.')
    alternateName = fields.Text(string='Enter any alternate names, including abbreviations, for this entity.')
    lookupLabel = fields.Integer(string='Enter the label used for looking up this entity in the parcellation terminology.')
    hasParent = fields.Many2many(comodel_name='tvbo.parcellation_entity', relation='tvbo_parcellation_entity_hasParent_rel', column1='parcellation_entity_id', column2='hasParent_id', string='Add all anatomical parent structures for this entity as defined within the corresponding brain atlas.')
    name = fields.Char(required=True, index=True, string="Full name of the score (e.g., Unified Parkinson's Disease Rating Scale - Part III)")
    ontologyIdentifier = fields.Text(string='Enter the internationalized resource identifier (IRI) to the related ontological terms.')
    versionIdentifier = fields.Char(string='Enter the version identifier of this brain atlas or coordinate space version.')


class ParcellationTerminology(models.Model):
    _name = 'tvbo.parcellation_terminology'
    _description = 'A schema for representing a parcellation terminology, which consists of parcellation entities.'

    _rec_name = 'label'

    label = fields.Char(index=True, string='Optional human-readable label (e.g., "1a")')
    dataLocation = fields.Char(string='Add the location of the data file containing the parcellation terminology.')
    ontologyIdentifier = fields.Text(string='Enter the internationalized resource identifier (IRI) to the related ontological terms.')
    versionIdentifier = fields.Char(string='Enter the version identifier of this brain atlas or coordinate space version.')

