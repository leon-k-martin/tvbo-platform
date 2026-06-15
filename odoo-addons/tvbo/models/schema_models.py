# -*- coding: utf-8 -*-
# Auto-generated from the TVBO LinkML schema - DO NOT EDIT MANUALLY.
# Re-run: python scripts/generate_odoo_models.py
from odoo import models, fields


class AggregationType(models.Model):
    _name = 'tvbo.aggregation_type'
    _description = 'AggregationType'
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


class ContinuationAlgorithm(models.Model):
    _name = 'tvbo.continuation_algorithm'
    _description = 'ContinuationAlgorithm'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class DevelopmentStatus(models.Model):
    _name = 'tvbo.development_status'
    _description = 'DevelopmentStatus'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class DimensionType(models.Model):
    _name = 'tvbo.dimension_type'
    _description = 'DimensionType'
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


class EcosystemEnum(models.Model):
    _name = 'tvbo.ecosystem_enum'
    _description = 'EcosystemEnum'
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


class EnvironmentType(models.Model):
    _name = 'tvbo.environment_type'
    _description = 'EnvironmentType'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class EventType(models.Model):
    _name = 'tvbo.event_type'
    _description = 'EventType'
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


class ImagingModality(models.Model):
    _name = 'tvbo.imaging_modality'
    _description = 'ImagingModality'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class InitialStateMethod(models.Model):
    _name = 'tvbo.initial_state_method'
    _description = 'InitialStateMethod'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class ModelParadigm(models.Model):
    _name = 'tvbo.model_paradigm'
    _description = 'ModelParadigm'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class ModelType(models.Model):
    _name = 'tvbo.model_type'
    _description = 'ModelType'
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


class NumericalDiscretizationMethod(models.Model):
    _name = 'tvbo.numerical_discretization_method'
    _description = 'NumericalDiscretizationMethod'
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


class ParallelMode(models.Model):
    _name = 'tvbo.parallel_mode'
    _description = 'ParallelMode'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class PhysicalDimension(models.Model):
    _name = 'tvbo.physical_dimension'
    _description = 'PhysicalDimension'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class ProgrammingLanguageEnum(models.Model):
    _name = 'tvbo.programming_language_enum'
    _description = 'ProgrammingLanguageEnum'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class ReductionType(models.Model):
    _name = 'tvbo.reduction_type'
    _description = 'ReductionType'
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


class SamplingAxis(models.Model):
    _name = 'tvbo.sampling_axis'
    _description = 'SamplingAxis'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class SexEnum(models.Model):
    _name = 'tvbo.sex_enum'
    _description = 'SexEnum'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class SimulationScale(models.Model):
    _name = 'tvbo.simulation_scale'
    _description = 'SimulationScale'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class SparseFormat(models.Model):
    _name = 'tvbo.sparse_format'
    _description = 'SparseFormat'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class SpecimenEnum(models.Model):
    _name = 'tvbo.specimen_enum'
    _description = 'SpecimenEnum'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class StandardGraphType(models.Model):
    _name = 'tvbo.standard_graph_type'
    _description = 'StandardGraphType'
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


class ToolRole(models.Model):
    _name = 'tvbo.tool_role'
    _description = 'ToolRole'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class UnitEnum(models.Model):
    _name = 'tvbo.unit_enum'
    _description = 'UnitEnum'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True)
    technical_name = fields.Char(required=True, index=True)
    description = fields.Text()


class Aggregation(models.Model):
    _name = 'tvbo.aggregation'
    _description = 'Specifies how to aggregate values across a dimension. Used for loss functions to define per-element loss with reduction.'

    over = fields.Many2one(comodel_name='tvbo.dimension_type', help='Dimension to aggregate over (e.g., node, time, state)')
    type = fields.Many2one(comodel_name='tvbo.reduction_type', help='Aggregation operation (mean, sum, max, min, none)')


class Algorithm(models.Model):
    _name = 'tvbo.algorithm'
    _description = 'A complete specification of an iterative parameter tuning algorithm. Combines update rules, objectives, observations, and hyperparameters.'
    _rec_name = 'name'

    name = fields.Char(index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    execution = fields.Many2one(comodel_name='tvbo.execution_config', help='Per-algorithm execution configuration (overrides experiment-level defaults). Useful for setting random_seed per algorithm to ensure reproducibility.')
    type = fields.Char(help="Algorithm type: 'fic', 'eib', 'homeostatic', 'custom'")
    includes = fields.Many2many(comodel_name='tvbo.algorithm_include', relation='tvbo_algorithm_includes_rel', help='Include update rules from other algorithms with optional argument overrides. Unlike depends_on (sequential), includes means combined execution. Example: includes: [{algorithm: fic, arguments: [{name: eta, value: 0.1}]}]')
    objective = fields.Many2one(comodel_name='tvbo.tuning_objective', help='What the algorithm optimizes for')
    observations = fields.Many2many(comodel_name='tvbo.observation', relation='tvbo_algorithm_observations_rel', help='References to observations defined in the observations section. Includes both simulated observations and external data (via data_source).')
    update_rules = fields.Many2many(comodel_name='tvbo.update_rule', relation='tvbo_algorithm_update_rules_rel', help="How parameters are updated each iteration. When using 'includes', update_rules are inherited from included algorithms.")
    hyperparameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_algorithm_hyperparameters_rel', help='Additional algorithm-specific parameters')
    learning_rate = fields.Float(help='Learning rate (eta) for the tuning algorithm')
    learning_rate_warmup = fields.Boolean(default=False, help='Linear warmup of learning rate from 0 to learning_rate over n_iterations. eta_effective = eta * (i+1) / n_iterations')
    n_iterations = fields.Integer(help='Number of iterations to run')
    learning_rate_schedule = fields.Char(help="Learning rate schedule: 'constant', 'linear', 'exponential'")
    simulation_period = fields.Float(help='Duration of each simulation step (e.g., one BOLD TR)')
    apply_every = fields.Integer(help='Apply update every N iterations')
    functions = fields.Many2many(comodel_name='tvbo.function_call', relation='tvbo_algorithm_functions_rel', help="Function calls for tracking progress, computing metrics, etc. Each FunctionCall references a function from the experiment's functions section and specifies arguments for that specific algorithm context.")
    depends_on = fields.Many2many(comodel_name='tvbo.algorithm', relation='tvbo_algorithm_depends_on_rel', column1='algorithm_id', column2='depends_on_id', help='Other algorithms that must run first (e.g., EIB depends on FIC)')


class AlgorithmInclude(models.Model):
    _name = 'tvbo.algorithm_include'
    _description = 'Reference to an included algorithm with optional argument overrides. Allows combining algorithms with different hyperparameter values.'

    algorithm = fields.Many2one(comodel_name='tvbo.algorithm', help='Reference to the algorithm to include')
    arguments = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_algorithm_include_arguments_rel', help='Override hyperparameter values for the included algorithm. Maps parameter names to new values.')


class Argument(models.Model):
    _name = 'tvbo.argument'
    _description = 'A function argument with explicit value specification. Value can be: literal (number/string), reference to input (input.key), or cross-observation reference (observation_name.output_key).'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    value = fields.Json(help='Argument value. Can be: - Literal: 1.0, "string", boolean, etc. - Input reference: "input.frequencies" (from source_observation outputs) - Cross-observation: "target_frequencies.peak_freqs" (from another observation)')
    unit = fields.Char()


class BidsEntities(models.Model):
    _name = 'tvbo.bids_entities'
    _description = 'BIDS filename entities (BEP017-aligned) for provenance and data discovery. Reusable on Network, BrainAtlas, Tractogram, or any dataset with BIDS-conformant naming.'

    template = fields.Char(help='BIDS tpl- entity (e.g., FSLMNI152, MNI152NLin2009cAsym)')
    cohort = fields.Char(help='BIDS cohort- entity (e.g., HCPYA, PPMI85)')
    reconstruction = fields.Char(help='BIDS rec- entity (e.g., dTOR)')
    segmentation = fields.Char(help='BIDS seg- entity (e.g., ordered, ranked, 17Networks)')
    scale = fields.Char(help='BIDS scale- entity (BEP017, e.g., 1000)')
    atlas = fields.Char(help='BIDS atlas- entity (e.g., Schaefer2018, HCPMMP1)')
    acquisition = fields.Char(help='BIDS acq- entity (e.g., EEGstandard1005, MEGBrainstorm)')
    hemi = fields.Char(help='BIDS hemi- entity (L or R) for hemisphere-specific surface/volume data')


class BoundaryCondition(models.Model):
    _name = 'tvbo.boundary_condition'
    _description = 'BoundaryCondition'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    bc_type = fields.Many2one(comodel_name='tvbo.boundary_condition_type')
    on_region = fields.Char(help='Mesh/atlas subset where BC applies.')
    value = fields.Many2one(comodel_name='tvbo.equation', help='Constant, parameter, or equation.')
    time_dependent = fields.Boolean()


class BrainAtlas(models.Model):
    _name = 'tvbo.brain_atlas'
    _description = 'A schema for representing a version of a brain atlas.'
    _rec_name = 'name'

    coordinateSpace = fields.Many2one(comodel_name='tvbo.common_coordinate_space', help='Common coordinate space (e.g. FSLMNI152, MNI152NLin2009cAsym). Reference by name; the CommonCoordinateSpace must be defined in tvbo/database/coordinate_spaces/ (or future equivalent location).')
    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    abbreviation = fields.Char(help='Slot for the abbreviation of a resource.')
    author = fields.Text()
    isVersionOf = fields.Char(help='Linked type for the version of a brain atlas or coordinate space.')
    versionIdentifier = fields.Char(help='Enter the version identifier of this brain atlas or coordinate space version.')
    terminology = fields.Many2one(comodel_name='tvbo.parcellation_terminology', help='Add the parcellation terminology version used for this brain atlas version.')


class BrainRegionSeries(models.Model):
    _name = 'tvbo.brain_region_series'
    _description = 'A series whose values represent latitude'

    values = fields.Text()


class BranchSwitch(models.Model):
    _name = 'tvbo.branch_switch'
    _description = 'Specification for switching from a detected bifurcation point to a new branch (periodic orbits from Hopf, fold continuation, etc.). Each BranchSwitch says: "from which special point on the parent branch, continue what...'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_branch_switch_parameters_rel')
    source_point = fields.Char(help="Which bifurcation point to start from. Syntax: - 'hopf:-1' = last Hopf (default) - 'hopf:all' = all Hopf points - 'hopf:1' = first Hopf - 'fold:2' = second fold - integer = specific special point index")
    delta_p = fields.Float(help='Initial parameter offset from the bifurcation point.')
    continuation = fields.Many2one(comodel_name='tvbo.continuation', help="Override solver settings for this branch. Uses the same Continuation type — only explicitly set attributes override the parent's values.")
    discretization = fields.Many2one(comodel_name='tvbo.discretization', help='Discretization method for the branch solution. Required for periodic orbit branches (Hopf → PO). Not needed for codim-2 branches (fold/Hopf continuation).')
    bothside = fields.Boolean(help='Continue branch in both directions.')
    options = fields.Many2many(comodel_name='tvbo.option', relation='tvbo_branch_switch_options_rel', help='Toolkit-specific string options for this branch (linear solver, etc.).')


class Callable(models.Model):
    _name = 'tvbo.callable'
    _description = 'Callable'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    module = fields.Char()
    software = fields.Many2one(comodel_name='tvbo.software_requirement')


class Case(models.Model):
    _name = 'tvbo.case'
    _description = 'Case'

    condition = fields.Char()
    equation = fields.Many2one(comodel_name='tvbo.equation')


class ClassReference(models.Model):
    _name = 'tvbo.class_reference'
    _description = 'Reference to a class that can be instantiated and called. Used for external library classes (e.g., tvboptim.Bold, custom monitors). The class is instantiated with constructor_args, then called with call_args. Generali...'
    _rec_name = 'name'

    constructor_args = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_class_reference_constructor_args_rel', help='Arguments passed to __init__ when instantiating the class. Example: period=1000.0, downsample_period=4.0 for Bold monitor.')
    call_args = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_class_reference_call_args_rel', help='Arguments passed when calling the instance (__call__). Usually the input data from simulation result. Example: result (simulation output array).')
    warmup_source = fields.Char(help="Reference to transient simulation result for history initialization. Some monitors (e.g., Bold) require history from warmup simulation. Value should reference a simulation result name (e.g., 'result_init').")
    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    module = fields.Char()
    software = fields.Many2one(comodel_name='tvbo.software_requirement')


class ClinicalImprovement(models.Model):
    _name = 'tvbo.clinical_improvement'
    _description = 'Relative improvement on a defined clinical score.'

    score = fields.Many2one(comodel_name='tvbo.clinical_score')
    baseline_value = fields.Float(help='Preoperative baseline value of the score')
    absolute_value = fields.Float(help='Absolute value of the score at the time of assessment')
    percent_change = fields.Float(help='Percent change compared to preoperative baseline (positive = improvement)')
    time_post_surgery = fields.Float(help='Timepoint of assessment in days or months after implantation')
    evaluator = fields.Char(help='Who performed the rating (e.g., rater initials, clinician ID, or system)')
    timepoint = fields.Char(help='Timepoint of assessment (e.g., "1 month post-op", "6 months post-op")')


class ClinicalScale(models.Model):
    _name = 'tvbo.clinical_scale'
    _description = 'A clinical assessment inventory or structured scale composed of multiple scores or items.'
    _rec_name = 'name'

    acronym = fields.Char(help='Short abbreviation (e.g., UPDRS)')
    name = fields.Char(index=True, help='Full name of the scale (e.g., Unified Parkinson’s Disease Rating Scale)')
    version = fields.Char(help='Version of the instrument (e.g., 3.0)')
    domain = fields.Char(help='Overall clinical domain (e.g., motor, cognition)')
    reference = fields.Char(help='DOI, PMID or persistent identifier')


class ClinicalScore(models.Model):
    _name = 'tvbo.clinical_score'
    _description = 'Metadata about a clinical score or scale.'
    _rec_name = 'name'

    acronym = fields.Char()
    name = fields.Char(index=True, help="Full name of the score (e.g., Unified Parkinson's Disease Rating Scale - Part III)")
    description = fields.Text()
    domain = fields.Char(help='Domain assessed (e.g. motor, mood, pain)')
    reference = fields.Char(help='PubMed ID, DOI, or other reference to the score definition')
    scale = fields.Many2one(comodel_name='tvbo.clinical_scale', help='The scale this score belongs to, if applicable')
    parent_score = fields.Many2one(comodel_name='tvbo.clinical_score', help='If this score is a subscore of a broader composite')


class CommonCoordinateSpace(models.Model):
    _name = 'tvbo.common_coordinate_space'
    _description = 'A schema for representing a version of a common coordinate space.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    abbreviation = fields.Char(help='Slot for the abbreviation of a resource.')
    alternateName = fields.Text(help='Enter any alternate names, including abbreviations, for this entity.')
    unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Physical unit of measurement. Values are drawn from the QUDT ontology (http://qudt.org/vocab/unit/) with UO cross-references where available.')
    license = fields.Char(help='Linked type for the license of the brain atlas or coordinate space version.')
    anatomicalAxesOrientation = fields.Char(help='Add the axes orientation in standard anatomical terms (XYZ).')
    axesOrigin = fields.Char(help='Enter the origin (central point where all axes intersect).')
    nativeUnit = fields.Char(help='Add the native unit that is used for this common coordinate space version.')
    defaultImage = fields.Text(help='Add all image files used as visual representation of this common coordinate space version.')


class ConditionalBlock(models.Model):
    _name = 'tvbo.conditional_block'
    _description = 'A single condition and its corresponding equation segment.'

    condition = fields.Char(help='The condition for this block (e.g., t > onset).')
    expression = fields.Char(help='The equation to apply when the condition is met.')


class Contact(models.Model):
    _name = 'tvbo.contact'
    _description = 'Individual contact on a DBS electrode.'
    _rec_name = 'label'

    contact_id = fields.Integer(help='Identifier (e.g., 0, 1, 2)')
    coordinate = fields.Many2one(comodel_name='tvbo.coordinate', help='3D coordinate of the contact center in the defined coordinate space')
    label = fields.Char(index=True, help='Optional human-readable label (e.g., "1a")')


class Continuation(models.Model):
    _name = 'tvbo.continuation'
    _description = 'Complete specification of a numerical continuation / bifurcation analysis. All universal solver settings live directly here. Toolkit-specific string options go in the options slot. When used inside a BranchSwitch, onl...'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    description = fields.Text()
    dynamics = fields.Many2one(comodel_name='tvbo.dynamics', help="Reference to the dynamical system model (by name). Resolved from the experiment's dynamics dict at runtime.")
    free_parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_continuation_free_parameters_rel', help='Parameters to vary. First parameter is primary (codim-1); second enables codim-2 continuation. Each Parameter has name + domain (Range with lo/hi bounds).')
    ds = fields.Float(help='Initial arc-length step size.')
    ds_min = fields.Float(help='Minimum adaptive step size.')
    ds_max = fields.Float(help='Maximum adaptive step size.')
    max_steps = fields.Integer(help='Maximum continuation steps.')
    newton_tol = fields.Float(help='Absolute tolerance for Newton corrector convergence.')
    newton_max_iterations = fields.Integer(help='Maximum Newton corrector iterations per step.')
    nev = fields.Integer(help='Number of eigenvalues to compute. Must be >= number of state variables for reliable Hopf detection.')
    tol_stability = fields.Float(help='Tolerance on real part of eigenvalue for stability boundary.')
    detect_bifurcation = fields.Integer(help='Bifurcation detection level. 0 = off, 1 = eigenvalues only, 2 = detect, 3 = locate precisely.')
    detect_fold = fields.Boolean(help='Enable fold (limit point) detection.')
    n_inversion = fields.Integer(help='Number of eigenvalue sign inversions to flag a bifurcation. Must be even. Higher = fewer false positives.')
    max_bisection_steps = fields.Integer(help='Maximum bisection steps for bifurcation point localization.')
    algorithm = fields.Many2one(comodel_name='tvbo.continuation_algorithm', help='Predictor-corrector algorithm.')
    initial_state = fields.Many2one(comodel_name='tvbo.initial_state', help='How to obtain the initial equilibrium. Default: time integration to steady state.')
    branches = fields.Many2many(comodel_name='tvbo.branch_switch', relation='tvbo_continuation_branches_rel', help='Child branches to continue from detected bifurcation points (PO from Hopf, fold continuation, etc.).')
    bothside = fields.Boolean(help='Continue in both directions from the starting point.')
    execution = fields.Many2one(comodel_name='tvbo.execution_config', help='Per-analysis execution configuration.')
    software = fields.Many2one(comodel_name='tvbo.software_requirement', help='Backend engine (BifurcationKit, AUTO-07p, MatCont, etc.).')
    options = fields.Many2many(comodel_name='tvbo.option', relation='tvbo_continuation_options_rel', help='Toolkit-specific string options (tangent method, solver name, etc.).')


class Coordinate(models.Model):
    _name = 'tvbo.coordinate'
    _description = 'A 3D coordinate with X, Y, Z values.'

    coordinateSpace = fields.Many2one(comodel_name='tvbo.common_coordinate_space', help='Common coordinate space (e.g. FSLMNI152, MNI152NLin2009cAsym). Reference by name; the CommonCoordinateSpace must be defined in tvbo/database/coordinate_spaces/ (or future equivalent location).')
    x = fields.Float(help='X coordinate')
    y = fields.Float(help='Y coordinate')
    z = fields.Float(help='Z coordinate')


class Coupling(models.Model):
    _name = 'tvbo.coupling'
    _description = 'Coupling'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    iri = fields.Char(help='Optional stable IRI (or compact URI) for this entity in an external ontology or knowledge base. Used to load metadata from an external source; not required when the entity is fully self-contained (equations, parameters, etc. defined in the file itself).')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_coupling_parameters_rel')
    description = fields.Text()
    coupling_function = fields.Many2one(comodel_name='tvbo.equation', help='Mathematical function defining the coupling')
    sparse = fields.Boolean(help='Whether the coupling uses sparse representations')
    pre_expression = fields.Many2one(comodel_name='tvbo.equation', help='Pre-processing expression applied before coupling')
    post_expression = fields.Many2one(comodel_name='tvbo.equation', help='Post-processing expression applied after coupling')
    incoming_states = fields.Many2many(comodel_name='tvbo.state_variable', relation='tvbo_coupling_incoming_states_rel', help='References to state variables from connected (source) nodes. Auto-populated from state_variables with coupling_variable=true when omitted. Used by name in pre_expression.')
    local_states = fields.Many2many(comodel_name='tvbo.state_variable', relation='tvbo_coupling_local_states_rel', help='References to state variables from the local (target) node. Used by name in pre_expression.')
    delayed = fields.Boolean(help='Whether coupling includes transmission delays')
    symmetry = fields.Char(default='directed', help="Edge symmetry type for NetworkDynamics.jl EdgeModel: 'directed' (default), 'antisymmetric', or 'symmetric'. AntiSymmetric edges flip sign for the reverse direction.")
    outsym = fields.Text(help="Output symbol names for the edge model. E.g. ['P'] for a scalar power flow, ['Fx', 'Fy'] for 2D forces. Maps directly to outsym in ND.jl EdgeModel. If not specified, derived from coupling variables of the connected vertex dynamics.")
    observed = fields.Many2many(comodel_name='tvbo.derived_variable', relation='tvbo_coupling_observed_rel', help='Observable functions computed from edge inputs and parameters after simulation. Maps to obsf/obssym in ND.jl EdgeModel. Example: absolute force magnitude computed from force components.')
    inner_coupling = fields.Many2one(comodel_name='tvbo.coupling', help='For hierarchical coupling: inner coupling applied at regional level')
    region_mapping = fields.Many2one(comodel_name='tvbo.region_mapping', help='For hierarchical coupling: vertex-to-region mapping for aggregation')
    regional_connectivity = fields.Many2one(comodel_name='tvbo.network', help='For hierarchical coupling: region-to-region connectivity with weights and delays')
    aggregation = fields.Char(help="For hierarchical coupling: aggregation method ('sum', 'mean', 'max') or custom Function")
    distribution = fields.Char(help="For hierarchical coupling: distribution method ('broadcast', 'weighted') or custom Function")


class CouplingInput(models.Model):
    _name = 'tvbo.coupling_input'
    _description = 'Specification of a coupling input channel for multi-coupling dynamics'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    source = fields.Char(help='Name of the coupling function that feeds this input. When omitted, resolved automatically: (1) same name as a coupling function → direct match, (2) single coupling input and single coupling function → auto-mapped, (3) multiple of each → positional order.')
    dimension = fields.Integer(help='Dimensionality of the coupling input (number of coupled values)')
    keys = fields.Text(help='Named keys for multi-dimensional coupling. When dimension > 1, provides symbolic names for each index (e.g., keys: [lre, ffi] for dimension: 2). Used in equations as variable names.')


class DBSDataset(models.Model):
    _name = 'tvbo.dbs_dataset'
    _description = 'Collection of data related to a specific DBS study.'
    _rec_name = 'label'

    clinical_scores = fields.Many2many(comodel_name='tvbo.clinical_score', relation='tvbo_dbs_dataset_clinical_scores_rel')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space')
    dataset_id = fields.Char(required=True, help='Unique identifier for the dataset.')
    subjects = fields.Many2many(comodel_name='tvbo.dbs_subject', relation='tvbo_dbs_dataset_subjects_rel', help='Subjects in a dataset.')
    label = fields.Char(index=True, help='Human-readable dataset name.')
    description = fields.Text()
    bids_root = fields.Char(help='Path to BIDS dataset root directory. When set, subject networks and empirical data paths are resolved relative to this root.')
    conditions = fields.Text(help="Global condition labels applied across all subjects (e.g., ['rest', 'task-nback', 'task-motor']).")
    reference = fields.Char(help='DOI or citation for this dataset.')


class DBSProtocol(models.Model):
    _name = 'tvbo.dbs_protocol'
    _description = 'A protocol describing DBS therapy, potentially bilateral or multi-lead.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    electrodes = fields.Many2many(comodel_name='tvbo.electrode', relation='tvbo_dbs_protocol_electrodes_rel')
    settings = fields.Many2many(comodel_name='tvbo.stimulation_setting', relation='tvbo_dbs_protocol_settings_rel')
    timing_info = fields.Char()
    notes = fields.Char()
    clinical_improvement = fields.Many2many(comodel_name='tvbo.clinical_improvement', relation='tvbo_dbs_protocol_clinical_improvement_rel', help='Observed improvement relative to baseline based on a defined score.')


class DBSSubject(models.Model):
    _name = 'tvbo.dbs_subject'
    _description = 'Human or animal subject receiving DBS.'
    _rec_name = 'label'

    diagnosis = fields.Char()
    handedness = fields.Char()
    protocols = fields.Many2many(comodel_name='tvbo.dbs_protocol', relation='tvbo_dbs_subject_protocols_rel', help='All DBS protocols assigned to this subject.')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space', help="Coordinate space used for this subject's data")
    subject_id = fields.Char(required=True, help="BIDS-compatible subject identifier (without 'sub-' prefix). Examples: '01', 'ctrl03', 'patient17'.")
    label = fields.Char(index=True, help='Human-readable label for the subject.')
    group = fields.Char(help="Group assignment (e.g., 'control', 'patient', 'healthy'). Maps to participants.tsv 'group' column in BIDS.")
    age = fields.Float(help='Age at time of study (years).')
    sex = fields.Many2one(comodel_name='tvbo.sex_enum', help='Biological sex.')
    sessions = fields.Many2many(comodel_name='tvbo.session', relation='tvbo_dbs_subject_sessions_rel', help='Data collection sessions for this subject. Each session can have its own network, empirical data, and conditions.')
    network = fields.Char(help='Path to subject-specific connectome (when not session-dependent). Relative to dataset root or BIDS derivatives. For session-specific networks, use Session.network instead.')
    metadata = fields.Char(help='Additional subject metadata as key-value pairs or path to a sidecar JSON file.')


class DataSource(models.Model):
    _name = 'tvbo.data_source'
    _description = 'Specification for loading external/empirical data.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    description = fields.Text()
    path = fields.Char(help='File path or URI to the data')
    loader = fields.Many2one(comodel_name='tvbo.callable', help='Callable that loads the data (e.g., load_functional_connectivity)')
    format = fields.Char(help="Data format: 'npy', 'mat', 'csv', 'nifti', etc.")
    key = fields.Char(help='Key/variable name within the file (for .mat, .npz, etc.)')
    preprocessing = fields.Many2one(comodel_name='tvbo.function', help='Optional preprocessing to apply after loading')


class Dataset(models.Model):
    _name = 'tvbo.dataset'
    _description = 'A collection of subjects for a multi-subject study. Provides the subject/session structure needed for workflow rendering. Optionally backed by a BIDS directory layout.'
    _rec_name = 'label'

    dataset_id = fields.Char(required=True, help='Unique identifier for the dataset.')
    subjects = fields.Many2many(comodel_name='tvbo.subject', relation='tvbo_dataset_subjects_rel', help='Subjects in a dataset.')
    label = fields.Char(index=True, help='Human-readable dataset name.')
    description = fields.Text()
    bids_root = fields.Char(help='Path to BIDS dataset root directory. When set, subject networks and empirical data paths are resolved relative to this root.')
    conditions = fields.Text(help="Global condition labels applied across all subjects (e.g., ['rest', 'task-nback', 'task-motor']).")
    reference = fields.Char(help='DOI or citation for this dataset.')


class DerivedParameter(models.Model):
    _name = 'tvbo.derived_parameter'
    _description = 'DerivedParameter'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    symbol = fields.Char()
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Physical unit of measurement. Values are drawn from the QUDT ontology (http://qudt.org/vocab/unit/) with UO cross-references where available.')
    label = fields.Char(index=True)
    definition = fields.Char()
    value = fields.Json(help='Numeric, string, or boolean value. ScalarValue accepts any literal primitive type, allowing parameters to carry control flags (e.g., booleans) or symbolic placeholders alongside numeric defaults.')
    default = fields.Char()
    domain = fields.Many2one(comodel_name='tvbo.range')
    reported_optimum = fields.Float()
    dataset_path = fields.Char(help='Dataset path for array-valued parameters. When set, the parameter value is stored in the binary companion file (HDF5 or Zarr) at this path. The value slot is omitted.')
    grounding = fields.Text(help='External ontology IRIs (typically GO, ChEBI, UBERON, CL, MeSH) that this entity is a surrogate / abstraction / model of. Replaces the legacy OWL pattern `tvbo:surrogate_of` by carrying the link inline with the YAML data instance. Multiple IRIs allowed: a single parameter may abstract several biological processes (e.g. a synaptic conductance grounding both GO:0060079 (excitatory PSP) and GO:0007268 (chemical synaptic transmission)).')
    comment = fields.Char()
    heterogeneous = fields.Boolean()
    distribution = fields.Many2one(comodel_name='tvbo.distribution', help='Distribution for heterogeneous per-node parameter sampling. Implies heterogeneous=true.')
    source = fields.Char(help="Data source for this parameter's value. When set, the value is loaded from the referenced entity rather than being a YAML literal. The referent is typically a Network with per-node parameters (dscalar pattern) or a flat dataset (HDF5, TSV). Combine with `measure:` when the source exposes multiple named measures. Distinct from the global `iri:` slot, which is reserved for ontology grounding.")
    measure = fields.Char(help='Selector into the source. When `source` points at a Network with per-node parameters (or a dscalar with multiple maps), picks which named measure to load. Aligns with names listed in Network.structural_measures / Network.observational_measures. Ignored when the source resolves to a scalar/array dataset.')
    free = fields.Boolean()
    shape = fields.Char()
    explored_values = fields.Text()
    element_domains = fields.Many2many(comodel_name='tvbo.range', relation='tvbo_derived_parameter_element_domains_rel', help='Per-element domain overrides for heterogeneous parameters. When specified, element_domains[i] overrides domain for element i during exploration auto-expansion. Length must match parameter shape (e.g., n_nodes for shape "(n_nodes,)"). If not set, all elements share the same domain.')


class DerivedVariable(models.Model):
    _name = 'tvbo.derived_variable'
    _description = 'DerivedVariable'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    symbol = fields.Char()
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Physical unit of measurement. Values are drawn from the QUDT ontology (http://qudt.org/vocab/unit/) with UO cross-references where available.')
    record = fields.Boolean(help='Whether to include this element in simulation output files. Applicable to state variables (default true), derived variables (default false), and network nodes (default true). Set false to suppress recording.')
    grounding = fields.Text(help='External ontology IRIs (typically GO, ChEBI, UBERON, CL, MeSH) that this entity is a surrogate / abstraction / model of. Replaces the legacy OWL pattern `tvbo:surrogate_of` by carrying the link inline with the YAML data instance. Multiple IRIs allowed: a single parameter may abstract several biological processes (e.g. a synaptic conductance grounding both GO:0060079 (excitatory PSP) and GO:0007268 (chemical synaptic transmission)).')
    conditional = fields.Boolean()
    cases = fields.Many2many(comodel_name='tvbo.case', relation='tvbo_derived_variable_cases_rel')


class DifferentialOperator(models.Model):
    _name = 'tvbo.differential_operator'
    _description = 'DifferentialOperator'
    _rec_name = 'label'

    label = fields.Char(index=True)
    definition = fields.Char()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    operator_type = fields.Many2one(comodel_name='tvbo.operator_type')
    coefficient = fields.Many2one(comodel_name='tvbo.parameter')
    tensor_coefficient = fields.Many2one(comodel_name='tvbo.parameter', help='Optional anisotropic tensor (e.g., diffusion).')
    expression = fields.Many2one(comodel_name='tvbo.equation', help="Symbolic form (e.g., '-div(D * grad(u))').")


class Discretization(models.Model):
    _name = 'tvbo.discretization'
    _description = 'Discretization method for boundary value problems in continuation (periodic orbits, connecting orbits, quasi-periodic tori). Specifies the method; method-specific numerics go in parameters.'

    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_discretization_parameters_rel')
    method = fields.Many2one(comodel_name='tvbo.numerical_discretization_method', help='Discretization method.')
    ode_solver = fields.Many2one(comodel_name='tvbo.solver', help='ODE solver for flow-based methods (shooting, poincaré). Specifies algorithm (e.g. Vern9, Rodas5) and tolerances. Not needed for collocation or trapezoid.')
    linear_solver = fields.Many2one(comodel_name='tvbo.solver', help='Linear solver for the Newton bordered system. E.g. COPBLS (collocation), MatrixBLS (shooting/poincaré).')
    mesh_intervals = fields.Integer(default=50, help='Number of mesh intervals (time slices) for collocation or trapezoid methods. Collocation: N in PeriodicOrbitOCollProblem(N, m). Trapezoid: M in PeriodicOrbitTrapProblem(M=...).')
    degree = fields.Integer(default=4, help='Polynomial degree per mesh interval for collocation. The m in PeriodicOrbitOCollProblem(N, m).')
    n_sections = fields.Integer(default=3, help='Number of shooting sections for shooting or Poincaré methods.')
    options = fields.Many2many(comodel_name='tvbo.option', relation='tvbo_discretization_options_rel', help='Toolkit-specific string options (jacobian type, etc.).')


class Distribution(models.Model):
    _name = 'tvbo.distribution'
    _description = 'A probability distribution for sampling parameters or initial conditions. Standard distributions (Uniform, Gaussian) are specified by name and domain/parameters. Custom distributions use a Function for the PDF/samplin...'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, default='Uniform', help='Globally unique identifier for the entity.')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_distribution_parameters_rel')
    domain = fields.Many2one(comodel_name='tvbo.range', help='Support of the distribution (sampling bounds). For Uniform this fully defines the distribution.')
    function = fields.Many2one(comodel_name='tvbo.function', help='Custom distribution function (PDF or sampling callable). Only needed for non-standard distributions.')
    seed = fields.Integer(help='Random seed for reproducible sampling.')
    axis = fields.Many2one(comodel_name='tvbo.sampling_axis', help="Dimension along which the distribution is sampled. 'space' = per-node (default), 'time' = per-timestep (stochastic input).")
    correlation = fields.Many2one(comodel_name='tvbo.matrix')


class Dynamics(models.Model):
    _name = 'tvbo.dynamics'
    _description = 'Dynamics'
    _rec_name = 'name'

    has_reference = fields.Char()
    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    iri = fields.Char(help='Optional stable IRI (or compact URI) for this entity in an external ontology or knowledge base. Used to load metadata from an external source; not required when the entity is fully self-contained (equations, parameters, etc. defined in the file itself).')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_dynamics_parameters_rel')
    description = fields.Text()
    source = fields.Char()
    references = fields.Text()
    dataLocation = fields.Char(help='Add the location of the data file containing the parcellation terminology.')
    derived_parameters = fields.Many2many(comodel_name='tvbo.derived_parameter', relation='tvbo_dynamics_derived_parameters_rel')
    derived_variables = fields.Many2many(comodel_name='tvbo.derived_variable', relation='tvbo_dynamics_derived_variables_rel')
    coupling_terms = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_dynamics_coupling_terms_rel')
    coupling_inputs = fields.Many2many(comodel_name='tvbo.coupling_input', relation='tvbo_dynamics_coupling_inputs_rel')
    state_variables = fields.Many2many(comodel_name='tvbo.state_variable', relation='tvbo_dynamics_state_variables_rel')
    is_modified = fields.Boolean()
    output = fields.Text(help='Output variable names to include in simulation results. References to state_variables or derived_variables by name.')
    derived_from_model = fields.Many2one(comodel_name='tvbo.dynamics')
    number_of_modes = fields.Integer()
    local_coupling_term = fields.Many2one(comodel_name='tvbo.parameter')
    functions = fields.Many2many(comodel_name='tvbo.function', relation='tvbo_dynamics_functions_rel')
    stimulus = fields.Many2one(comodel_name='tvbo.stimulus')
    modes = fields.Many2many(comodel_name='tvbo.dynamics', relation='tvbo_dynamics_modes_rel', column1='dynamics_id', column2='modes_id')
    model_type = fields.Many2one(comodel_name='tvbo.model_type', help='Coarse classification of this model (mean_field, neural_mass, phase_oscillator, phenomenological, spiking, generic, field). Used for filtering in Dynamics.list_db(model_type=...).')
    system_type = fields.Many2one(comodel_name='tvbo.system_type')
    autonomous = fields.Boolean(default=True, help='Whether the system is autonomous (equations do not depend explicitly on time t). Non-autonomous systems have explicit time dependence, e.g. f*cos(omega*t).')
    observed = fields.Many2many(comodel_name='tvbo.derived_variable', relation='tvbo_dynamics_observed_rel', help='Observable functions computed from states, inputs, and parameters after simulation. Unlike derived_variables (which are intermediate algebraic expressions used within the ODE), observed variables are post-hoc quantities recoverable from the solution. Maps to obsf/obssym in ND.jl EdgeModel/VertexModel. Example: absolute force magnitude computed from force components.')
    events = fields.Many2many(comodel_name='tvbo.event', relation='tvbo_dynamics_events_rel', help="Discrete state transitions intrinsic to the dynamical system, such as threshold-triggered resets in spiking neuron models. Unlike experiment-level events (stimulation, perturbation), these define the model's own discontinuous behavior.")


class EField(models.Model):
    _name = 'tvbo.e_field'
    _description = 'Simulated electric field from DBS modeling.'

    volume_data = fields.Char(help='Reference to raw or thresholded volume')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space', help='Reference to a common coordinate space (e.g. MNI152)')
    threshold_applied = fields.Float(help='Threshold value applied to the E-field simulation')


class Edge(models.Model):
    _name = 'tvbo.edge'
    _description = 'An edge in a network. Two modes: explicit (source+target set, scalar parameters in YAML) or template (no source/target, N×N matrix measure in HDF5). Both coexist in the same edges list.'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_edge_parameters_rel')
    source = fields.Integer(help='Source node ID (set for explicit edges, absent for template edges)')
    target = fields.Integer(help='Target node ID (set for explicit edges, absent for template edges)')
    weight = fields.Float(help='Connection weight (explicit edges)')
    delay = fields.Float(help='Conduction delay (explicit edges, ms)')
    distance = fields.Float(help='Edge length / tract distance (explicit edges, mm)')
    unit = fields.Char(help='Unit for matrix values (template edges only)')
    format = fields.Many2one(comodel_name='tvbo.sparse_format', help='Storage format in HDF5 (template edges only)')
    weighted = fields.Boolean(default=True, help='Matrix entries carry weights (not just 0/1)')
    valid_diagonal = fields.Boolean(default=False, help='Self-connections are meaningful')
    non_negative = fields.Boolean(default=True, help='All values >= 0')
    source_var = fields.Char(help="Output variable from source node to use (e.g., 'x_out'). If not specified, uses first output variable from source dynamics.")
    target_var = fields.Char(help="Input variable on target node to connect to (e.g., 'c_in'). If not specified, uses first coupling input from target dynamics.")
    coupling = fields.Many2one(comodel_name='tvbo.coupling', help="Coupling function for this edge. Can be a reference (by name) to coupling or inline definition. If not provided, uses experiment's default coupling.")
    directed = fields.Boolean(help='Whether the edge is directed. If false, represents a symmetric/bidirectional connection.')
    source_network = fields.Char(help='Path or name of the Network whose nodes define the source endpoints of this Edge. Symmetric counterpart to `target_network`. Together they let an Edge bridge any two Networks: both unset (within-Network edge), one set (this Network ↔ the named one), or both set (peer-to-peer projection between two other Networks). Accepts either an absolute IRI (peer Network) or the relative-path sentinel `parent` / `parent/parent` (cross-scale up/down via the Node.subnetwork hierarchy).')
    target_network = fields.Char(help='Path or name of the Network whose nodes define the target endpoints (e.g. the columns of a non-square projection matrix such as a gain matrix region → EEG sensors). Also accepts the relative-path sentinel `parent` / `parent/parent` for cross-scale signal flow up the Node.subnetwork hierarchy. One mechanism handles both projection matrices (absolute IRI) and multi-scale boundaries (sentinel).')
    dimension_labels = fields.Text(help="Ordered labels for the matrix columns (dim-1) when the matrix is non-square.  Row labels (dim-0) are the parent Network's node labels.  Stored as HDF5 dimension scales in the companion file.")
    dynamics = fields.Many2one(comodel_name='tvbo.dynamics', help='Dynamics model for this edge. When specified, the edge has its own state variables and ODE (EdgeModel with f in ND.jl). Uses the same Dynamics class as nodes — state_variables define edge states, derived_variables define observables, output defines what is visible for plotting/analysis. The coupling_function on Coupling still defines how vertex outputs map to edge outputs for aggregation at vertices.')
    events = fields.Many2many(comodel_name='tvbo.event', relation='tvbo_edge_events_rel', help='Events attached to this edge (e.g., threshold-based line tripping).')


class Electrode(models.Model):
    _name = 'tvbo.electrode'
    _description = 'Implanted DBS electrode and contact geometry.'

    electrode_id = fields.Char(help='Unique identifier for this electrode')
    manufacturer = fields.Char()
    model = fields.Char()
    hemisphere = fields.Char(help='Hemisphere of electrode (left/right)')
    contacts = fields.Many2many(comodel_name='tvbo.contact', relation='tvbo_electrode_contacts_rel', help='List of physical contacts along the electrode')
    head = fields.Many2one(comodel_name='tvbo.coordinate')
    tail = fields.Many2one(comodel_name='tvbo.coordinate')
    trajectory = fields.Many2many(comodel_name='tvbo.coordinate', relation='tvbo_electrode_trajectory_rel', help='The planned trajectory for electrode implantation')
    target_structure = fields.Many2one(comodel_name='tvbo.parcellation_entity', help='Anatomical target structure from a brain atlas')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space', help='Coordinate space used for implantation planning')
    recon_path = fields.Char()


class Equation(models.Model):
    _name = 'tvbo.equation'
    _description = 'Equation'
    _rec_name = 'label'

    label = fields.Char(index=True)
    definition = fields.Char()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_equation_parameters_rel')
    description = fields.Text()
    lhs = fields.Char()
    rhs = fields.Char()
    conditionals = fields.Many2many(comodel_name='tvbo.conditional_block', relation='tvbo_equation_conditionals_rel', help='Conditional logic for piecewise equations.')
    engine = fields.Many2one(comodel_name='tvbo.software_requirement', help="Primary engine (must appear in environment.requirements; migration target replacing deprecated 'software').")
    pycode = fields.Char(help='Python code for the equation.')
    latex = fields.Boolean()


class Event(models.Model):
    _name = 'tvbo.event'
    _description = 'A discrete or continuous event that modifies the system during simulation. Generalizes Stimulus: can represent external inputs (stimulus type), threshold-triggered state changes (continuous/discrete type), or time-sch...'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    description = fields.Text()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_event_parameters_rel')
    event_type = fields.Many2one(comodel_name='tvbo.event_type', help='Type of event trigger mechanism.')
    condition = fields.Many2one(comodel_name='tvbo.equation', help='Condition function. For continuous events: triggers when expression crosses zero. For discrete events: triggers when expression evaluates to true. Not used for preset_time or stimulus types.')
    condition_states = fields.Text(help='State variable symbols accessible in the condition function. For edges, can include source/destination vertex outputs.')
    condition_parameters = fields.Text(help='Parameter symbols accessible in the condition function.')
    affect = fields.Many2one(comodel_name='tvbo.equation', help='Affect function: what happens when the event triggers. Can modify state variables and/or parameters. For stimulus type, this is the stimulus equation.')
    affect_states = fields.Text(help='State variable symbols modifiable in the affect function.')
    affect_parameters = fields.Text(help='Parameter symbols modifiable in the affect function.')
    affect_negative = fields.Many2one(comodel_name='tvbo.equation', help='Affect on downcrossing (continuous events only). If not specified, uses the same affect for both crossings.')
    trigger_times = fields.Text(help='Predetermined trigger times for preset_time events. The solver will step exactly to these times.')
    target_component = fields.Char(help="Component to attach this event to. Can be a node label, edge label, or 'all_edges'/'all_vertices' for broadcast. If not specified, event is experiment-level.")
    equation = fields.Many2one(comodel_name='tvbo.equation', help='Stimulus equation for stimulus-type events. Legacy compatibility with Stimulus class.')
    regions = fields.Text(help='Target regions for stimulus-type events.')
    weighting = fields.Text(help='Per-region weighting for stimulus-type events.')
    duration = fields.Float(help='Duration of stimulus-type events.')


class ExecutionConfig(models.Model):
    _name = 'tvbo.execution_config'
    _description = 'Configuration for computational execution (parallelization, precision, hardware).'

    n_workers = fields.Integer(help='Number of parallel workers (maps to pmap devices in JAX, processes in multiprocessing)')
    n_threads = fields.Integer(help='Number of CPU threads per worker (-1 = auto-detect)')
    precision = fields.Char(default='float64', help="Floating point precision: 'float32' or 'float64'")
    accelerator = fields.Char(default='cpu', help="Hardware accelerator: 'cpu', 'gpu', 'tpu'")
    batch_size = fields.Integer(help='Batch size for vectorized operations (None = auto)')
    random_seed = fields.Integer(help='Base random seed for reproducibility')
    find_fixpoint = fields.Boolean(help='Whether to find a fixed point (steady state) before time integration. Used as initial condition for ODEProblem. Maps to NLsolve.fixpoint! in ND.jl or similar in other backends.')


class Exploration(models.Model):
    _name = 'tvbo.exploration'
    _description = 'Parameter space exploration (grid search, sweep).'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    description = fields.Text()
    execution = fields.Many2one(comodel_name='tvbo.execution_config', help='Per-exploration execution configuration (overrides experiment-level defaults). Useful for setting random_seed, n_workers for parallel grid search.')
    space = fields.Many2many(comodel_name='tvbo.exploration_axis', relation='tvbo_exploration_space_rel', help='Ordered list of exploration axes spanning the search space. Each axis references an existing Parameter (by dotted name, e.g. "ReducedWongWang.w" or "FastLinearCoupling.G") and supplies the Range to sweep. No new Parameter is created here.')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_exploration_parameters_rel', help='Hyper-parameters of the exploration itself (e.g. tolerances, sampler settings, grid-refinement controls). Distinct from `space`, which defines what is being swept.')
    mode = fields.Char(default='product', help="Combination mode: 'product' (full grid), 'zip' (paired)")
    observable = fields.Many2one(comodel_name='tvbo.function_call', help='Observable to compute at each point. Use function: obs_name for simple observation, or function: func_name + arguments for FunctionCall.')
    n_parallel = fields.Integer(help='Parallel evaluations')
    n_trials = fields.Integer(help='Number of independent trials per grid point. Each trial uses a different noise seed. Used for averaging stochastic simulations (e.g., VEP = average of 20 trials).')
    average = fields.Char(help="Averaging mode across trials. 'trials' = average over n_trials independent runs (evoked potential paradigm). None = return all trials.")
    parallel_mode = fields.Many2one(comodel_name='tvbo.parallel_mode', help='How trial-axis parallelism is realised at codegen time. ``vmap`` batches all trials in parallel (fast, peak memory ~n_trials × per-trial working set). ``lax_map`` runs them sequentially via ``jax.lax.map`` (slower, peak memory bounded by one trial). ``pmap`` shards across devices for multi-GPU. ``auto`` (default) picks ``vmap`` when the estimated batched memory fits, ``lax_map`` otherwise.')
    parallel_batch_size = fields.Integer(help='Chunk size for ``lax_map`` and chunked-``vmap`` modes. ``1`` = strictly sequential (minimum memory). Larger values amortise compile overhead across trials at the cost of memory. Ignored when parallel_mode is ``vmap`` (which always uses the full n_trials axis).')


class ExplorationAxis(models.Model):
    _name = 'tvbo.exploration_axis'
    _description = 'One axis of a parameter exploration grid. Points to an existing Parameter (by dotted reference, e.g. "ReducedWongWang.w" or "FastLinearCoupling.G") and supplies the sweep specification (domain, explored_values, or per...'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    parameter = fields.Many2one(comodel_name='tvbo.parameter', help='Dotted reference to the Parameter being swept. Format: "<scope>.<param_name>" where <scope> is either a Dynamics class name (e.g. "ReducedWongWang") or a coupling key (e.g. "FastLinearCoupling"). Resolved against the enclosing experiment at runtime.')
    domain = fields.Many2one(comodel_name='tvbo.range', help='Sweep range for this axis (lo, hi, n, step, log_scale).')
    explored_values = fields.Text(help='Explicit list of values to sweep (overrides domain).')
    element_domains = fields.Many2many(comodel_name='tvbo.range', relation='tvbo_exploration_axis_element_domains_rel', help='Per-element sweep overrides for heterogeneous parameters (e.g. shape "(n_nodes,)"). When set, element_domains[i] replaces the shared domain for element i.')
    unit = fields.Char(help="Optional axis unit (defaults to the referenced Parameter's unit).")


class FieldStateVariable(models.Model):
    _name = 'tvbo.field_state_variable'
    _description = 'FieldStateVariable'
    _rec_name = 'name'

    label = fields.Char(index=True)
    description = fields.Text()
    mesh = fields.Many2one(comodel_name='tvbo.mesh')
    boundary_conditions = fields.Many2many(comodel_name='tvbo.boundary_condition', relation='tvbo_field_state_variable_boundary_conditions_rel')
    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    symbol = fields.Char()
    definition = fields.Char()
    domain = fields.Many2one(comodel_name='tvbo.range')
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Physical unit of measurement. Values are drawn from the QUDT ontology (http://qudt.org/vocab/unit/) with UO cross-references where available.')
    record = fields.Boolean(help='Whether to include this element in simulation output files. Applicable to state variables (default true), derived variables (default false), and network nodes (default true). Set false to suppress recording.')
    grounding = fields.Text(help='External ontology IRIs (typically GO, ChEBI, UBERON, CL, MeSH) that this entity is a surrogate / abstraction / model of. Replaces the legacy OWL pattern `tvbo:surrogate_of` by carrying the link inline with the YAML data instance. Multiple IRIs allowed: a single parameter may abstract several biological processes (e.g. a synaptic conductance grounding both GO:0060079 (excitatory PSP) and GO:0007268 (chemical synaptic transmission)).')
    variable_of_interest = fields.Boolean()
    coupling_variable = fields.Boolean(help='Whether this state variable is transmitted to connected nodes through the coupling function. In TVB terms, this determines the cvar indices (state variables extracted from history and fed into the coupling function). The coupling function may override this via its incoming_states attribute.')
    equation_type = fields.Char(default='differential', help="Type of equation: 'differential' (default) means dx/dt = rhs, 'algebraic' means 0 = rhs or x ~ rhs (DAE constraint). Algebraic equations are used by ModelingToolkit.jl backend.")
    equation_order = fields.Integer(default=1, help='Order of the time derivative on the LHS. Default 1 means dx/dt = rhs (first-order ODE). Order 2 means d²x/dt² = rhs (second-order ODE), etc. Higher-order ODEs are automatically lowered to coupled first-order systems by backends like ModelingToolkit.jl via mtkcompile.')
    noise = fields.Many2one(comodel_name='tvbo.noise')
    stimulation_variable = fields.Boolean()
    boundaries = fields.Many2one(comodel_name='tvbo.range')
    initial_value = fields.Float(default=0.1)
    derivative_initial_value = fields.Float(help='Initial value for the first time derivative, used when equation_order > 1. For a second-order ODE d²x/dt² = f, this sets dx/dt(0). Required by ModelingToolkit.jl to fully specify higher-order initial value problems.')
    distribution = fields.Many2one(comodel_name='tvbo.distribution', help='Distribution for sampling initial conditions per node. If present, initial_value is used as fallback/mean.')
    history = fields.Many2one(comodel_name='tvbo.time_series')


class File(models.Model):
    _name = 'tvbo.file'
    _description = 'File'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    type = fields.Char()
    path = fields.Char()
    extension = fields.Char()


class FreeParameter(models.Model):
    _name = 'tvbo.free_parameter'
    _description = 'One degree of freedom in an OptimizationStage. References an existing Parameter by dotted scope (e.g. "ReducedWongWang.w" or "FastLinearCoupling.G") and supplies optimization-specific metadata (heterogeneous, shape, b...'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    parameter = fields.Many2one(comodel_name='tvbo.parameter', help='Dotted reference to the Parameter to optimize. Format: "<scope>.<param_name>" where <scope> is either a Dynamics class name or a coupling key.')
    heterogeneous = fields.Boolean(default=False, help='If true, the parameter is optimized per-element (broadcast to `shape`). If false, a single scalar is optimized and broadcast at runtime.')
    shape = fields.Char(help='Optimization shape as a Python-tuple-style string (e.g. "(n_nodes,)" or "(n_nodes, n_nodes)"). Required when heterogeneous is true.')
    initial_value = fields.Json(help="Optional initial value for the optimizer (overrides the referenced Parameter's value).")
    domain = fields.Many2one(comodel_name='tvbo.range', help='Optional bounds (lo, hi) for constrained optimization.')


class Function(models.Model):
    _name = 'tvbo.function'
    _description = 'A function with explicit input -> transformation -> output flow. Can be equation-based (symbolic) or software-based (callable). In a pipeline, functions are chained: output of one becomes input of next.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    acronym = fields.Char()
    label = fields.Char(index=True)
    iri = fields.Char(help='Optional stable IRI (or compact URI) for this entity in an external ontology or knowledge base. Used to load metadata from an external source; not required when the entity is fully self-contained (equations, parameters, etc. defined in the file itself).')
    equation = fields.Many2one(comodel_name='tvbo.equation')
    definition = fields.Char()
    description = fields.Text()
    requirements = fields.Many2many(comodel_name='tvbo.software_requirement', relation='tvbo_function_requirements_rel')
    input = fields.Many2one(comodel_name='tvbo.function', help="Simple input reference: name of previous function's output in pipeline. For multi-argument functions, use arguments with value references instead.")
    output = fields.Char(help="Name for this function's output (referenced by subsequent functions)")
    arguments = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_function_arguments_rel', help='Variables consumed by the function (referenced in the equation). Each argument has a name and optional metadata (description, default value, unit).')
    output_equation = fields.Many2one(comodel_name='tvbo.equation', help='Output transformation equation (if equation-based)')
    source_code = fields.Char()
    callable = fields.Many2one(comodel_name='tvbo.callable', help='Software implementation reference (if software-based)')
    apply_on_dimension = fields.Many2one(comodel_name='tvbo.dimension_type', help='Which dimension to apply the transformation on')
    aggregate = fields.Many2one(comodel_name='tvbo.aggregation', help='How to aggregate the result across dimensions. E.g., aggregate.over=node computes per-row (per-node) with keepdims. The type field controls whether to reduce (mean/sum) or keep dimensions (none).')
    time_range = fields.Many2one(comodel_name='tvbo.range', help='Time range for generated TimeSeries (for kernel generators). Equation is evaluated at each time point.')


class FunctionCall(models.Model):
    _name = 'tvbo.function_call'
    _description = 'Invocation of a function in a pipeline. Can reference a defined Function by name, OR inline a callable directly for external library functions, OR inline an equation, OR use class_call for class instantiation. Mirrors...'
    _rec_name = 'name'

    acronym = fields.Char()
    label = fields.Char(index=True)
    equation = fields.Many2one(comodel_name='tvbo.equation')
    description = fields.Text()
    name = fields.Char(index=True, help='Optional step label; used in pipelines to key step outputs.')
    function = fields.Many2one(comodel_name='tvbo.function', help='Reference to a defined Function (by name)')
    callable = fields.Many2one(comodel_name='tvbo.callable', help='Direct callable specification (alternative to function reference)')
    class_call = fields.Many2one(comodel_name='tvbo.class_reference', help='Class instantiation and call (alternative to callable/function). Use for external library classes that need __init__ then __call__. Example: Bold monitor from tvboptim.')
    input = fields.Char(help="Reference to previous function's output in pipeline (by name)")
    output = fields.Char(help="Name for this step's output (referenced by subsequent functions)")
    apply_on_dimension = fields.Many2one(comodel_name='tvbo.dimension_type', help="Dimension to apply function over (generates vmap in code). E.g., 'node' applies per-node.")
    aggregate = fields.Many2one(comodel_name='tvbo.aggregation', help='How to aggregate the result across dimensions. Example: aggregate.over=node, aggregate.type=mean applies function per node, then averages. Used in loss functions.')
    arguments = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_function_call_arguments_rel')
    time_range = fields.Many2one(comodel_name='tvbo.range', help='Time range for generated TimeSeries (for kernel generators)')
    source_code = fields.Char()


class GraphGenerator(models.Model):
    _name = 'tvbo.graph_generator'
    _description = 'Backend-agnostic graph generator specification.  Captures the mathematical family (type) and its parameters so that each backend can emit the correct constructor call (Graphs.jl, NetworkX, etc.). The number of nodes i...'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    type = fields.Char(required=True, help='Graph family name.  Use a StandardGraphType value for automatic backend mapping, or any custom string for documentation purposes.')
    seed = fields.Integer(help='Random seed for reproducible graph generation.')
    directed = fields.Boolean(default=False, help='Whether to generate a directed graph.')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_graph_generator_parameters_rel', help='Generator parameters (e.g. k, p, dims).  Names are matched by the backend mapping to construct the call.')
    builder = fields.Many2one(comodel_name='tvbo.callable', help='Optional Python callable that builds the network at YAML load time. When set, ``Network._resolve`` imports ``<module>.<name>`` and invokes it with the ``parameters`` block as keyword arguments. The callable must return either a ``Network`` instance or a tuple ``(weights, lengths, node_params)``. Use the existing ``Callable`` slots (``name`` is the function name, ``module`` is its dotted module path). Reuses the same idiom as TVB monitor class references; no free ``module:function`` strings.')


class InitialState(models.Model):
    _name = 'tvbo.initial_state'
    _description = 'How to obtain the starting equilibrium or periodic orbit for continuation. Most robust: time-integrate to steady state.'

    method = fields.Many2one(comodel_name='tvbo.initial_state_method', help='Strategy for finding the initial state.')
    duration = fields.Float(default=2000.0, help='Integration duration for time_integration method.')
    abs_tol = fields.Float(default=1e-10, help='Absolute tolerance for ODE integration.')
    rel_tol = fields.Float(default=1e-10, help='Relative tolerance for ODE integration.')
    solver = fields.Many2one(comodel_name='tvbo.solver', help='ODE solver for time_integration method. Specify method (e.g., Tsit5, Heun, RK4) and tolerances.')
    source_branch = fields.Char(help='Name of a previously computed branch (for from_branch method).')
    source_point = fields.Char(help="Which point on the source branch: 'endpoint', 'hopf:1', 'fold:2', a step number, etc.")


class Integrator(models.Model):
    _name = 'tvbo.integrator'
    _description = "Fixed-step or adaptive ODE integrator with TVB-specific extensions (noise, transient time, etc.). Inherits abs_tol, rel_tol from Solver. Overrides method default to 'euler'."

    time_scale = fields.Many2one(comodel_name='tvbo.unit_enum', help='Time unit for the integration / simulation. Determines the physical time meaning of one model time-step.')
    unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Physical unit of measurement. Values are drawn from the QUDT ontology (http://qudt.org/vocab/unit/) with UO cross-references where available.')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_integrator_parameters_rel')
    duration = fields.Float(default=1000.0)
    description = fields.Text()
    method = fields.Char(default='euler', help='Integration method (euler, heun, rk4, etc.)')
    step_size = fields.Float(default=0.01220703125)
    steps = fields.Integer()
    noise = fields.Many2one(comodel_name='tvbo.noise')
    state_wise_sigma = fields.Text()
    transient_time = fields.Float(default=0.0)
    scipy_ode_base = fields.Boolean()
    number_of_stages = fields.Integer()
    intermediate_expressions = fields.Many2many(comodel_name='tvbo.derived_variable', relation='tvbo_integrator_intermediate_expressions_rel')
    update_expression = fields.Many2one(comodel_name='tvbo.derived_variable')
    delayed = fields.Boolean()
    abs_tol = fields.Float(default=1e-10, help='Absolute tolerance for adaptive solvers.')
    rel_tol = fields.Float(default=1e-10, help='Relative tolerance for adaptive solvers.')


class LossFunction(models.Model):
    _name = 'tvbo.loss_function'
    _description = 'A loss function for optimization with optional aggregation. Extends Function with aggregation specification for per-element losses.'
    _rec_name = 'name'

    aggregate = fields.Many2one(comodel_name='tvbo.aggregation', help='How to aggregate the loss across dimensions. Example: aggregate.over=node, aggregate.type=mean computes loss per node, then averages.')
    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    acronym = fields.Char()
    label = fields.Char(index=True)
    iri = fields.Char(help='Optional stable IRI (or compact URI) for this entity in an external ontology or knowledge base. Used to load metadata from an external source; not required when the entity is fully self-contained (equations, parameters, etc. defined in the file itself).')
    equation = fields.Many2one(comodel_name='tvbo.equation')
    definition = fields.Char()
    description = fields.Text()
    requirements = fields.Many2many(comodel_name='tvbo.software_requirement', relation='tvbo_loss_function_requirements_rel')
    input = fields.Many2one(comodel_name='tvbo.function', help="Simple input reference: name of previous function's output in pipeline. For multi-argument functions, use arguments with value references instead.")
    output = fields.Char(help="Name for this function's output (referenced by subsequent functions)")
    arguments = fields.Many2many(comodel_name='tvbo.argument', relation='tvbo_loss_function_arguments_rel', help='Variables consumed by the function (referenced in the equation). Each argument has a name and optional metadata (description, default value, unit).')
    output_equation = fields.Many2one(comodel_name='tvbo.equation', help='Output transformation equation (if equation-based)')
    source_code = fields.Char()
    callable = fields.Many2one(comodel_name='tvbo.callable', help='Software implementation reference (if software-based)')
    apply_on_dimension = fields.Many2one(comodel_name='tvbo.dimension_type', help='Which dimension to apply the transformation on')
    time_range = fields.Many2one(comodel_name='tvbo.range', help='Time range for generated TimeSeries (for kernel generators). Equation is evaluated at each time point.')


class Matrix(models.Model):
    _name = 'tvbo.matrix'
    _description = 'Adjacency matrix of a network.'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(help='Add the location of the data file containing the parcellation terminology.')
    x = fields.Many2one(comodel_name='tvbo.brain_region_series')
    y = fields.Many2one(comodel_name='tvbo.brain_region_series')
    values = fields.Text()
    format = fields.Many2one(comodel_name='tvbo.sparse_format', help='Storage format in binary companion (dense, csr, coo)')
    shape = fields.Text(help='Matrix dimensions [N, M]')
    dtype = fields.Char(default='float32', help='Data type for matrix values')


class MeasureSpec(models.Model):
    _name = 'tvbo.measure_spec'
    _description = 'Metadata for one phenotype measure. Optional per-measure entry on ``Phenotype.measure_specs``.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Must match the measure name in ``Phenotype.measures``.')
    task_iri = fields.Char(help='Cognitive Atlas (``cogat:``) IRI of the assessment instrument / task that produced this measure (e.g. ``cogat:trm_4a3fd79d09cba`` for PMAT24).')
    concept_iri = fields.Char(help='Cognitive Atlas IRI of the cognitive construct measured (e.g. ``cogat:trm_521ef89ce5e84`` for fluid intelligence).')
    unit = fields.Char(help="Unit annotation (e.g. 'count', 'ms', 'z-score').")
    measure_type = fields.Char(help="Sub-type within the phenotype (e.g. 'raw', 'unadjusted', 'age-corrected', 'derived', 'RT', 'accuracy').")
    description = fields.Text()


class Mesh(models.Model):
    _name = 'tvbo.mesh'
    _description = 'Triangle (or higher-order) mesh geometry. May stand alone (via ``mesh_file`` pointing at an external GIFTI/VTK/MSH file) OR be inlined on a Network as ``Network.mesh``. In the inlined-on-Network case, the vertices are...'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(help='Add the location of the data file containing the parcellation terminology.')
    element_type = fields.Many2one(comodel_name='tvbo.element_type')
    coordinates = fields.Many2many(comodel_name='tvbo.coordinate', relation='tvbo_mesh_coordinates_rel', help='Node coordinates (x,y,z) in the given coordinate space.')
    elements = fields.Char(help="Topology indices: either a file reference, or (when inlined on a Network) a dotted path inside the parent Network's h5 companion to the (M, 3) int triangle face array. Default convention: ``mesh/faces``.")
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space')
    mesh_file = fields.Char(help='Path to external mesh file (GIFTI, VTK, MSH, FreeSurfer, etc.).')
    mesh_format = fields.Char(help='Explicit format override (gifti, freesurfer, meshio, vtk, gmsh). Auto-detected from extension if null.')
    number_of_vertices = fields.Integer(help='Number of vertices in the mesh.')
    number_of_elements = fields.Integer(help='Number of elements (triangles, quads, tetrahedra, etc.).')
    parcellation = fields.Many2one(comodel_name='tvbo.parcellation', help="Brain parcellation this mesh's parcel_map indexes into. Inlined to match Network.parcellation's existing pattern. When the mesh is inlined on a Network that already declares ``parcellation``, this slot is optional and defaults to the parent's value.")
    normals = fields.Char(help="Optional path inside the parent Network's h5 (or an external file) to per-vertex normals (N, 3) float. Default convention: ``mesh/normals``.")
    curvature = fields.Char(help='Optional path to per-vertex curvature (N,) float. Default convention: ``mesh/curvature``.')
    vertices_field = fields.Char(help="When the mesh is inlined on a Network, the dotted path inside the parent's h5 to vertex coordinates. Default: ``nodes/coordinates``.")
    parcel_map_field = fields.Char(help="When the mesh is inlined on a Network with a parcellation, the dotted path inside the parent's h5 to the per-vertex parcel id array. Default: ``nodes/parent_index``.")


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


class NamedArray(models.Model):
    _name = 'tvbo.named_array'
    _description = 'A named numeric array. Used as a sidecar slot value where a schema-typed object (e.g. ``ExperimentResult.parameters``) holds multiple arrays addressable by name (``w_LRE``, ``w_FFI``, ``J_i``, ...). The actual numeric...'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Field name; matches the h5 dataset path under ``parameters/``.')
    shape = fields.Text(help='Array dimensions.')
    dtype = fields.Char(default='float32', help='Numpy dtype string.')
    unit = fields.Char(help="Optional unit annotation (e.g. 'nA').")
    description = fields.Text()


class Network(models.Model):
    _name = 'tvbo.network'
    _description = 'Network specification with nodes, edges, and reusable coupling configurations. Supports both explicit node/edge representation and matrix-based connectivity (Connectome compatibility).'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_network_parameters_rel')
    nodes = fields.Many2many(comodel_name='tvbo.node', relation='tvbo_network_nodes_rel', help='List of nodes with individual dynamics (optional, for heterogeneous networks)')
    edges = fields.Many2many(comodel_name='tvbo.edge', relation='tvbo_network_edges_rel', help='List of directed edges with coupling references (optional, for explicit edge definition)')
    primary_weight = fields.Char(help='Name of the edge group that should serve as the canonical weights matrix when ``weights_matrix`` is queried. Lets a single Network sidecar bundle several connectivity variants (e.g. band-specific NMF reweightings, distance-modulated SC, shuffled controls) under different edge names while still presenting one of them as the active weight to consumers (simulators, observation pipelines). Defaults to ``weight`` / ``weights`` / ``sc`` lookup when not set.')
    coupling = fields.Many2many(comodel_name='tvbo.coupling', relation='tvbo_network_coupling_rel', help="Reusable coupling configurations referenced by edges (e.g., 'instant', 'delayed', 'inhibitory')")
    dynamics = fields.Many2many(comodel_name='tvbo.dynamics', relation='tvbo_network_dynamics_rel', help='Dictionary of dynamics models keyed by name. Nodes reference these by name. For heterogeneous networks with per-node dynamics.')
    node_template = fields.Many2one(comodel_name='tvbo.node', help='Default Node attributes applied to every Node in this Network. Explicit entries in `nodes:` override the template field-by-field (shallow replace, same semantics as `dict.update`). Reserved per-Node slots (id, label, position, region) come from the data backbone (Network.iri-loaded parcellation or procedural generator) and are ignored if set on the template. Lets a homogeneous Network declare its per-Node configuration once without enumerating regions.')
    edge_template = fields.Many2one(comodel_name='tvbo.edge', help='Default Edge attributes applied to every Edge in this Network. Explicit entries in `edges:` override the template field-by-field. Reserved per-Edge slots (source, target, weight, delay, distance) come from the data backbone (loaded matrix or procedural generator) and are ignored if set on the template.')
    number_of_nodes = fields.Integer(help='Number of nodes in the network (derived from nodes if not set)')
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space', help='Coordinate space for node positions (e.g., MNI152NLin2009c). Mirrors BrainAtlas.coordinateSpace so network node positions are unambiguous.')
    parcellation = fields.Many2one(comodel_name='tvbo.parcellation', help='Brain parcellation/atlas reference')
    tractogram = fields.Many2one(comodel_name='tvbo.tractogram', help='Reference to tractography data')
    mesh = fields.Many2one(comodel_name='tvbo.mesh', help='Optional triangle mesh geometry. When set, the Network carries triangle faces (and optionally normals, curvature) alongside its node coordinates. Used by surface-based observations (cortical wave detection, Helmholtz-Hodge decomposition, spectrospatial mode analysis). Mesh face data lives in the same h5 companion under a ``mesh/`` group.')
    transforms = fields.Many2many(comodel_name='tvbo.function', relation='tvbo_network_transforms_rel', help="Ordered list of transforms applied to edge property matrices. Each Function's name identifies the target edge property (e.g. 'weight', 'length'). Supports equation-based (symbolic) or callable-based (software) transforms. Multiple transforms on the same target are applied sequentially.")
    data_file = fields.Char(help='Path to companion data file. Supported extensions: .h5 (HDF5), .zarr/ (Zarr), .csv (legacy single-matrix). Null if no companion data needed.')
    descriptor = fields.Char(help="Short alphanumeric identifier for the BIDS desc- filename entity (e.g., SC, FC, EC, SCFC). Classifies the connectivity modality of the network's edge measures.")
    bids_dir = fields.Char(help='Path to BEP017-compliant BIDS directory for loading connectivity matrices')
    bids = fields.Many2one(comodel_name='tvbo.bids_entities', help='BIDS filename entities for this dataset')
    structural_measures = fields.Text(help='BEP017 measure names for structural connectivity (e.g., streamlineCount, tractLength)')
    observational_measures = fields.Text(help='BEP017 measure names for observational targets (e.g., BoldCorrelation)')
    provenance = fields.Many2one(comodel_name='tvbo.provenance', help='W3C PROV-O aligned provenance')
    parent_network = fields.Char(help='Path/URI to parent (coarser) Network. When set, this network is a refinement where each node maps to exactly one parent node via node_mapping.')
    node_mapping = fields.Char(help='HDF5 dataset path for node-to-parent mapping. Int32 array of shape (N,) where entry i is the parent node ID. Required when parent_network is set.')
    distance_unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Unit for distances/lengths in the network')
    time_unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Default time unit for the network')
    edge_matrix_files = fields.Many2many(comodel_name='tvbo.file', relation='tvbo_network_edge_matrix_files_rel')
    graph_generator = fields.Many2one(comodel_name='tvbo.graph_generator', help='Graph generator specification.  When set, overrides explicit edges/nodes for graph construction.  The type field is a free string; StandardGraphType lists well-known types that get automatic code generation across backends.')


class Node(models.Model):
    _name = 'tvbo.node'
    _description = 'A node in a network with its own dynamics and properties'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_node_parameters_rel')
    record = fields.Boolean(help='Whether to include this element in simulation output files. Applicable to state variables (default true), derived variables (default false), and network nodes (default true). Set false to suppress recording.')
    record_id = fields.Integer(required=True, help='Unique node identifier')
    dynamics = fields.Many2one(comodel_name='tvbo.dynamics', help="Dynamics model governing this node's behavior. Can be a reference (by name) or inline definition. If not provided, uses experiment's dynamics.")
    position = fields.Many2one(comodel_name='tvbo.coordinate', help='Spatial coordinates (x, y, z) of the node')
    region = fields.Char(help='Brain region or anatomical label')
    state = fields.Many2many(comodel_name='tvbo.state_value', relation='tvbo_node_state_rel', help='Per-node initial state variable values, keyed by state variable name.')
    events = fields.Many2many(comodel_name='tvbo.event', relation='tvbo_node_events_rel', help='Events attached to this node (e.g., threshold-based state changes).')
    subnetwork = fields.Many2one(comodel_name='tvbo.network', help='Optional finer-scale Network that "lives inside" this Node (network-of-networks / multi-scale primitive). The subnetwork\'s nodes map (one-to-many) to this single parent Node. Cross-scale signal flow is declared as ordinary Edges in the subnetwork\'s `edges` list, using `source_network` / `target_network` with the `parent` sentinel to traverse up the hierarchy. The subnetwork may carry its own `graph_generator` (discrete sub-network — reservoir, spiking population, jaxley compartments) and/or `mesh` (continuous surface field) — one unified slot for reservoirs-per-region, spiking-populations-per-region, cells-per-region, and surface-mesh-patches-per-region. Recursive: a subnetwork\'s Nodes can themselves carry subnetworks.')


class Noise(models.Model):
    _name = 'tvbo.noise'
    _description = 'Noise'

    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_noise_parameters_rel')
    equation = fields.Many2one(comodel_name='tvbo.equation')
    noise_type = fields.Char()
    correlated = fields.Boolean()
    gaussian = fields.Boolean(help='Indicates whether the noise is Gaussian')
    additive = fields.Boolean(help='Indicates whether the noise is additive')
    seed = fields.Integer()
    random_state = fields.Many2one(comodel_name='tvbo.random_stream')
    intensity = fields.Many2one(comodel_name='tvbo.parameter', help='Optional scalar or vector intensity parameter for noise.')
    distribution = fields.Many2one(comodel_name='tvbo.distribution', help='Optional probability distribution from which the noise draws its samples. When set, takes precedence over the `noise_type` / `gaussian` flags — any Distribution family is accepted (Uniform { lo, hi }, Normal { mean, std }, LogNormal { mu, sigma }, Beta, …). Reuses the existing Distribution class also used by Parameter.distribution.')
    function = fields.Many2one(comodel_name='tvbo.function', help='Optional functional form of the noise (callable specification).')
    pycode = fields.Char(help='Inline Python code representation of the noise process.')
    targets = fields.Many2many(comodel_name='tvbo.state_variable', relation='tvbo_noise_targets_rel', help='State variables this noise applies to; if omitted, applies globally.')


class Observation(models.Model):
    _name = 'tvbo.observation'
    _description = 'Unified class for all observation/measurement specifications. Covers monitors (BOLD, EEG), tuning observables, and derived quantities. Pipeline is a sequence of Functions with input -> output flow.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    acronym = fields.Char()
    label = fields.Char(index=True)
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_observation_parameters_rel')
    environment = fields.Many2one(comodel_name='tvbo.software_environment')
    time_scale = fields.Many2one(comodel_name='tvbo.unit_enum', help='Time unit for the integration / simulation. Determines the physical time meaning of one model time-step.')
    source = fields.Text(help='Ordered list of inputs this observation derives from. Each entry is either a StateVariable reference (raw observation of an integrated trajectory, e.g. ``S_e``) or an Observation reference (derived observation, e.g. ``bold``). Codegen checks each source name against ``experiment.observations``; names matching an existing observation flag the parent as derived.')
    aux_data = fields.Many2many(comodel_name='tvbo.reference', relation='tvbo_observation_aux_data_rel', help="Ordered list of auxiliary inputs the observation pipeline consumes. Examples: a Surface mesh's faces array, an empirical FC matrix on a reference Network, or another Observation's output. Resolved load-time eagerly; rendered code is self-contained.")
    period = fields.Float(help='Sampling period for monitors (ms). For BOLD: TR in ms.')
    downsample_period = fields.Float(help='Intermediate downsampling period (ms). For BOLD: typically matches dt.')
    voi = fields.Integer(help='Variable of interest index (which state variable to monitor). Default: 0.')
    imaging_modality = fields.Many2one(comodel_name='tvbo.imaging_modality', help='Type of imaging modality (BOLD, EEG, MEG, etc.)')
    warmup_source = fields.Char(help="Reference to transient simulation result for history initialization (e.g., 'result_init').")
    data_source = fields.Many2one(comodel_name='tvbo.data_source', help='Load data from external source (file, database, API). When specified, this observation represents empirical/external data rather than simulated data. Enables unified treatment of all data.')
    skip_t = fields.Integer(help='Number of samples to skip at the start (transient removal). For FC: typically 10-20 TRs.')
    tail_samples = fields.Integer(help='Number of samples from the end to use. Takes the last N samples before aggregation. E.g., tail_samples: 500 means use data[-500:].')
    aggregation = fields.Many2one(comodel_name='tvbo.aggregation_type', help='How to aggregate over time')
    window_size = fields.Integer(help='Number of samples for windowed aggregation')
    pipeline = fields.Many2many(comodel_name='tvbo.function_call', relation='tvbo_observation_pipeline_rel', help='Ordered sequence of Functions. Each step has a unique `name` (used to key step outputs) and transforms input -> output. List form preserves execution order.')
    class_reference = fields.Many2one(comodel_name='tvbo.class_reference', help='Direct class reference (alternative to pipeline). Use for external library classes like tvboptim.Bold, custom monitors, or any callable class. The class is instantiated with constructor_args and called with call_args. Example: {name: Bold, module: tvboptim.observations.tvb_monitors.bold, constructor_args: [{name: period, value: 1000.0}]}')


class Optimization(models.Model):
    _name = 'tvbo.optimization'
    _description = "Configuration for parameter optimization. Inherits single-stage fields from OptimizationStage. For multi-stage workflows, use 'stages' (ignores inherited single-stage fields). Loss equation references observations dir..."
    _rec_name = 'name'

    execution = fields.Many2one(comodel_name='tvbo.execution_config', help='Per-optimization execution configuration (overrides experiment-level defaults). Useful for setting random_seed, precision, or hardware for optimization phase.')
    integration = fields.Many2one(comodel_name='tvbo.integrator', help='Integration settings for optimization simulations (overrides experiment defaults). If specified, creates a fresh model_fn and state with prepare() before optimization. Can specify different duration, step_size, method than the experiment. If not specified, uses experiment-level integration settings.')
    loss = fields.Many2one(comodel_name='tvbo.function_call', help='Loss function call. Uses FunctionCall to either: 1. Reference existing function: function: rmse 2. Inline callable: callable: {module: ..., name: ...} Arguments specify inputs (simulated_fc, empirical_fc, etc.)')
    stages = fields.Many2many(comodel_name='tvbo.optimization_stage', relation='tvbo_optimization_stages_rel', help='Ordered list of optimization stages. Stages run sequentially. Stage n+1 starts from optimized values of stage n. When defined, inherited single-stage fields are ignored.')
    depends_on = fields.Many2one(comodel_name='tvbo.algorithm', help="Algorithm to use as starting point for optimization. If specified, optimization starts from algorithm's result state. If not specified, optimization starts from initial simulation state.")
    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    description = fields.Text()
    free_parameters = fields.Many2many(comodel_name='tvbo.free_parameter', relation='tvbo_optimization_free_parameters_rel', help='Parameters to optimize in this stage. Each entry is a FreeParameter that references an existing Parameter by dotted scope (e.g. "ReducedWongWang.w" or "FastLinearCoupling.G") and supplies optimization-specific metadata (heterogeneous, shape, bounds). No new Parameter is created here.')
    algorithm = fields.Char(default='adam', help="Optimizer for this stage: 'adam', 'adamw', 'sgd', etc.")
    learning_rate = fields.Float(default=0.001)
    max_iterations = fields.Integer()
    hyperparameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_optimization_hyperparameters_rel', help='Stage-specific hyperparameters (e.g., b2=0.9999 for adam)')
    freeze_parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_optimization_freeze_parameters_rel', help='Parameters from previous stages to freeze (keep at optimized value but not update)')
    warmup_from = fields.Many2one(comodel_name='tvbo.optimization_stage', help='Previous stage to initialize from. Final values from that stage become initial values for this stage.')


class OptimizationStage(models.Model):
    _name = 'tvbo.optimization_stage'
    _description = 'A single stage in a multi-stage optimization workflow. Stages run sequentially, with each stage potentially using different parameters, shapes, learning rates, and algorithms.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    description = fields.Text()
    free_parameters = fields.Many2many(comodel_name='tvbo.free_parameter', relation='tvbo_optimization_stage_free_parameters_rel', help='Parameters to optimize in this stage. Each entry is a FreeParameter that references an existing Parameter by dotted scope (e.g. "ReducedWongWang.w" or "FastLinearCoupling.G") and supplies optimization-specific metadata (heterogeneous, shape, bounds). No new Parameter is created here.')
    algorithm = fields.Char(default='adam', help="Optimizer for this stage: 'adam', 'adamw', 'sgd', etc.")
    learning_rate = fields.Float(default=0.001)
    max_iterations = fields.Integer()
    hyperparameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_optimization_stage_hyperparameters_rel', help='Stage-specific hyperparameters (e.g., b2=0.9999 for adam)')
    freeze_parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_optimization_stage_freeze_parameters_rel', help='Parameters from previous stages to freeze (keep at optimized value but not update)')
    warmup_from = fields.Many2one(comodel_name='tvbo.optimization_stage', help='Previous stage to initialize from. Final values from that stage become initial values for this stage.')


class Option(models.Model):
    _name = 'tvbo.option'
    _description = 'A toolkit-specific key-value option (string name + string value). Used for backend settings that are not universal numeric parameters (e.g., solver name, tangent method, jacobian type).'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Option name (key).')
    value = fields.Char(required=True, help='Option value.')


class PDE(models.Model):
    _name = 'tvbo.pde'
    _description = 'Partial differential equation problem definition.'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_pde_parameters_rel')
    domain = fields.Many2one(comodel_name='tvbo.spatial_domain')
    mesh = fields.Many2one(comodel_name='tvbo.mesh', help='Shared mesh for all field state variables in this PDE.')
    state_variables = fields.Many2many(comodel_name='tvbo.field_state_variable', relation='tvbo_pde_state_variables_rel')
    field = fields.Many2one(comodel_name='tvbo.spatial_field', help='Primary field being solved for (deprecated; use state_variables).')
    operators = fields.Many2many(comodel_name='tvbo.differential_operator', relation='tvbo_pde_operators_rel')
    sources = fields.Many2many(comodel_name='tvbo.equation', relation='tvbo_pde_sources_rel')
    boundary_conditions = fields.Many2many(comodel_name='tvbo.boundary_condition', relation='tvbo_pde_boundary_conditions_rel')
    solver = fields.Many2one(comodel_name='tvbo.pde_solver')
    derived_parameters = fields.Many2many(comodel_name='tvbo.derived_parameter', relation='tvbo_pde_derived_parameters_rel')
    derived_variables = fields.Many2many(comodel_name='tvbo.derived_variable', relation='tvbo_pde_derived_variables_rel')
    functions = fields.Many2many(comodel_name='tvbo.function', relation='tvbo_pde_functions_rel')


class PDESolver(models.Model):
    _name = 'tvbo.pde_solver'
    _description = 'PDESolver'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    requirements = fields.Many2many(comodel_name='tvbo.software_requirement', relation='tvbo_pde_solver_requirements_rel')
    environment = fields.Many2one(comodel_name='tvbo.software_environment')
    discretization = fields.Many2one(comodel_name='tvbo.discretization_method')
    time_integrator = fields.Char(help='e.g., implicit Euler, Crank-Nicolson.')
    dt = fields.Float(help='Time step (s).')
    tolerances = fields.Char(help='Abs/rel tolerances.')
    preconditioner = fields.Char()


class Parameter(models.Model):
    _name = 'tvbo.parameter'
    _description = 'Parameter'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    symbol = fields.Char()
    definition = fields.Char()
    value = fields.Json(help='Numeric, string, or boolean value. ScalarValue accepts any literal primitive type, allowing parameters to carry control flags (e.g., booleans) or symbolic placeholders alongside numeric defaults.')
    default = fields.Char()
    domain = fields.Many2one(comodel_name='tvbo.range')
    reported_optimum = fields.Float()
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Physical unit of measurement. Values are drawn from the QUDT ontology (http://qudt.org/vocab/unit/) with UO cross-references where available.')
    dataset_path = fields.Char(help='Dataset path for array-valued parameters. When set, the parameter value is stored in the binary companion file (HDF5 or Zarr) at this path. The value slot is omitted.')
    grounding = fields.Text(help='External ontology IRIs (typically GO, ChEBI, UBERON, CL, MeSH) that this entity is a surrogate / abstraction / model of. Replaces the legacy OWL pattern `tvbo:surrogate_of` by carrying the link inline with the YAML data instance. Multiple IRIs allowed: a single parameter may abstract several biological processes (e.g. a synaptic conductance grounding both GO:0060079 (excitatory PSP) and GO:0007268 (chemical synaptic transmission)).')
    comment = fields.Char()
    heterogeneous = fields.Boolean()
    distribution = fields.Many2one(comodel_name='tvbo.distribution', help='Distribution for heterogeneous per-node parameter sampling. Implies heterogeneous=true.')
    source = fields.Char(help="Data source for this parameter's value. When set, the value is loaded from the referenced entity rather than being a YAML literal. The referent is typically a Network with per-node parameters (dscalar pattern) or a flat dataset (HDF5, TSV). Combine with `measure:` when the source exposes multiple named measures. Distinct from the global `iri:` slot, which is reserved for ontology grounding.")
    measure = fields.Char(help='Selector into the source. When `source` points at a Network with per-node parameters (or a dscalar with multiple maps), picks which named measure to load. Aligns with names listed in Network.structural_measures / Network.observational_measures. Ignored when the source resolves to a scalar/array dataset.')
    free = fields.Boolean()
    shape = fields.Char()
    explored_values = fields.Text()
    element_domains = fields.Many2many(comodel_name='tvbo.range', relation='tvbo_parameter_element_domains_rel', help='Per-element domain overrides for heterogeneous parameters. When specified, element_domains[i] overrides domain for element i during exploration auto-expansion. Length must match parameter shape (e.g., n_nodes for shape "(n_nodes,)"). If not set, all elements share the same domain.')


class Parcellation(models.Model):
    _name = 'tvbo.parcellation'
    _description = 'Parcellation'
    _rec_name = 'label'

    label = fields.Char(index=True)
    iri = fields.Char(help='Optional stable IRI (or compact URI) for this entity in an external ontology or knowledge base. Used to load metadata from an external source; not required when the entity is fully self-contained (equations, parameters, etc. defined in the file itself).')
    data_source = fields.Char()
    atlas = fields.Many2one(comodel_name='tvbo.brain_atlas')


class ParcellationEntity(models.Model):
    _name = 'tvbo.parcellation_entity'
    _description = 'A schema for representing a parcellation entity, which is an anatomical location or study target.'
    _rec_name = 'name'

    abbreviation = fields.Char(help='Slot for the abbreviation of a resource.')
    alternateName = fields.Text(help='Enter any alternate names, including abbreviations, for this entity.')
    lookupLabel = fields.Integer(help='Enter the label used for looking up this entity in the parcellation terminology.')
    hasParent = fields.Many2many(comodel_name='tvbo.parcellation_entity', relation='tvbo_parcellation_entity_hasParent_rel', column1='parcellation_entity_id', column2='hasParent_id', help='Add all anatomical parent structures for this entity as defined within the corresponding brain atlas.')
    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    ontologyIdentifier = fields.Text(help='Enter the internationalized resource identifier (IRI) to the related ontological terms.')
    versionIdentifier = fields.Char(help='Enter the version identifier of this brain atlas or coordinate space version.')
    relatedUBERONTerm = fields.Char(help='Add the related anatomical entity as defined by the UBERON ontology.')
    originalLookupLabel = fields.Integer(help='Add the original label of this entity as defined in the parcellation terminology.')
    hemisphere = fields.Many2one(comodel_name='tvbo.hemisphere', help='Add the hemisphere of this entity.')
    center = fields.Many2one(comodel_name='tvbo.coordinate', help='Add the center coordinate of this entity.')
    color = fields.Char(help='Add the color code used for visual representation of this entity.')


class ParcellationTerminology(models.Model):
    _name = 'tvbo.parcellation_terminology'
    _description = 'A schema for representing a parcellation terminology, which consists of parcellation entities.'
    _rec_name = 'label'

    label = fields.Char(index=True)
    dataLocation = fields.Char(help='Add the location of the data file containing the parcellation terminology.')
    ontologyIdentifier = fields.Text(help='Enter the internationalized resource identifier (IRI) to the related ontological terms.')
    versionIdentifier = fields.Char(help='Enter the version identifier of this brain atlas or coordinate space version.')
    entities = fields.Many2many(comodel_name='tvbo.parcellation_entity', relation='tvbo_parcellation_terminology_entities_rel')


class Phenotype(models.Model):
    _name = 'tvbo.phenotype'
    _description = 'Per-subject phenotype table (BIDS ``phenotype/`` directory convention). Carries cognitive scores, clinical scales, demographic variables, behavioral task outputs, physiological measures, or any other per-subject numer...'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataset_id = fields.Char(required=True, help='Unique identifier for this phenotype bundle.')
    subjects = fields.Text(help='Ordered list of subject IDs (e.g. HCP-YA 6-digit IDs). Each ``measures/<name>`` array in the h5 companion is indexed by this order.')
    measures = fields.Text(help='Names of the measures present in the h5 companion (one ``measures/<name>`` dataset per name). Example: ``[g_factor, PMAT24_A_CR, PMAT24_A_RTCR, CardSort_Unadj, ProcSpeed_Unadj]``.')
    measure_specs = fields.Many2many(comodel_name='tvbo.measure_spec', relation='tvbo_phenotype_measure_specs_rel', help="Optional per-measure metadata (Cognitive Atlas IRIs, units, description). When present, each entry's ``name`` must match an entry in ``measures``.")
    category = fields.Char(default='cognitive', help='Coarse classification of the phenotype bundle, used for filtering in larger study libraries. Canonical values: ``cognitive`` (intelligence / memory / attention scores), ``clinical`` (UPDRS, MMSE, …), ``behavioral`` (raw task outputs), ``demographic``, ``physiological``, ``derived`` (composite scores like g-factor or brain-age). Free string — extend as needed.')
    data_file = fields.Char(required=True, help='Path to the h5 companion (relative to the yaml).')
    cohort = fields.Char(help="Cohort label (e.g. 'HCPYA', 'PPMI').")
    provenance = fields.Many2one(comodel_name='tvbo.provenance', help='W3C PROV-O metadata for the source of these scores.')


class Provenance(models.Model):
    _name = 'tvbo.provenance'
    _description = 'W3C PROV-O aligned provenance. Reusable on any entity (Network, TimeSeries, Dynamics, etc.).'

    derived_from = fields.Char()
    references = fields.Text()
    date_created = fields.Char(help='ISO 8601 (prov:generatedAtTime)')
    license = fields.Char()
    generated_by = fields.Char(help='Software/agent identifier (prov:wasGeneratedBy)')
    experiment_yaml_hash = fields.Char(help="SHA-256 hex digest of the normalised experiment YAML that produced this artifact. Used by the cross-experiment cache (see :class:`SimulationStudy.from_file`) to detect when a cached upstream result has gone stale because the experiment's spec was edited. Computed as ``hashlib.sha256(yaml.safe_dump(normalized_yaml).encode()).hexdigest()`` over the fully resolved (post-``!include``) experiment block.")
    inputs = fields.Many2many(comodel_name='tvbo.reference_fingerprint', relation='tvbo_provenance_inputs_rel', help='Per-input fingerprints for cache invalidation. Each entry records the IRI + dotted-field path of an ``aux_data`` reference plus the (mtime, size, sha256) of the underlying file at the time the artifact was produced. A downstream cache hit requires every fingerprint to match the current file state.')


class RandomStream(models.Model):
    _name = 'tvbo.random_stream'
    _description = 'RandomStream'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(help='Add the location of the data file containing the parcellation terminology.')


class Range(models.Model):
    _name = 'tvbo.range'
    _description = 'Specifies a range for array generation, parameter bounds, or grid exploration.'

    lo = fields.Json(help='Lower bound or starting value. Can be a number or argument name.')
    hi = fields.Json(help='Upper bound or stopping value. Can be a number or argument name.')
    step = fields.Json(help='Step size. Can be: number, argument name, or expression.')
    n = fields.Integer(help='Number of points (alternative to step for grid exploration).')
    log_scale = fields.Boolean(help='Whether to use logarithmic spacing.')
    explored_values = fields.Text(help="Explicit explored values for this element. When set on an element_domain entry, overrides the parent parameter's explored_values for this specific element.")
    element = fields.Integer(help='Element/node index this range applies to. Used in element_domains to explicitly link a domain to a specific element of a heterogeneous parameter (e.g., element: 0 for node 0). Required when used in element_domains to avoid ambiguous positional indexing.')


class Reference(models.Model):
    _name = 'tvbo.reference'
    _description = 'A small typed pointer to another TVBO entity (Network, Mesh, Observation, …). The ``iri`` identifies the target via the registry; the optional ``field`` is a dotted-path subkey resolved by attribute walk on the loaded...'

    iri = fields.Char(required=True, help='CURIE or full IRI of the referenced TVBO entity.')
    field = fields.Char(help="Optional dotted-path subkey into the referenced entity (e.g. ``weight_alpha`` for a Network's named edge matrix, ``mesh.faces`` for the face array, or ``nodes.ef_alpha`` for a per-node scalar field). Resolved by attribute walk at load time.")


class ReferenceFingerprint(models.Model):
    _name = 'tvbo.reference_fingerprint'
    _description = 'Cache-invalidation fingerprint for one ``aux_data`` reference. Captures enough about the upstream artifact that a downstream cache can decide cheaply (via mtime + size) whether to trust the cached result, falling back...'

    iri = fields.Char(required=True, help='IRI of the referenced artifact (Network, ExperimentResult, BehavioralData, ...).')
    field = fields.Char(help='Dotted-path subkey within the referenced entity (optional).')
    mtime = fields.Float(help='File modification time at fingerprinting (POSIX timestamp).')
    size = fields.Integer(help='File size in bytes at fingerprinting.')
    hash = fields.Char(help='SHA-256 hex digest of the file at fingerprinting (recomputed lazily when mtime/size differ).')


class RegionMapping(models.Model):
    _name = 'tvbo.region_mapping'
    _description = 'Maps vertices to parent regions for hierarchical/aggregated coupling'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(help='Add the location of the data file containing the parcellation terminology.')
    vertex_to_region = fields.Text(help='Array mapping each vertex index to its parent region index. Can use dataLocation instead for large arrays.')
    n_vertices = fields.Integer(help='Total number of vertices')
    n_regions = fields.Integer(help='Total number of regions')


class Sample(models.Model):
    _name = 'tvbo.sample'
    _description = 'Sample'

    groups = fields.Text()
    size = fields.Integer()


class Session(models.Model):
    _name = 'tvbo.session'
    _description = "A data collection session for a subject. Corresponds to a BIDS 'ses-' entity. Sessions capture longitudinal timepoints (baseline, follow-up), different experimental conditions, or repeated measures."
    _rec_name = 'label'

    session_id = fields.Char(required=True, help="BIDS session identifier (without 'ses-' prefix). Examples: 'baseline', '6month', 'pre', 'post'.")
    label = fields.Char(index=True, help='Human-readable session label.')
    network = fields.Char(help='Path to session-specific connectome. Overrides Subject.network when set. Relative to dataset root or BIDS derivatives.')
    empirical_data = fields.Text(help='Paths to empirical recordings for this session (e.g., BOLD time series, MEG/EEG). Relative to dataset root.')
    condition = fields.Char(help="Experimental condition label (e.g., 'rest', 'task-nback'). Maps to BIDS 'task-' entity.")


class SimulationExperiment(models.Model):
    _name = 'tvbo.simulation_experiment'
    _description = 'SimulationExperiment'
    _rec_name = 'label'

    model = fields.Many2one(comodel_name='tvbo.dynamics')
    references = fields.Text()
    record_id = fields.Integer()
    description = fields.Text()
    additional_equations = fields.Many2many(comodel_name='tvbo.equation', relation='tvbo_simulation_experiment_additional_equations_rel')
    label = fields.Char(index=True)
    dynamics = fields.Many2one(comodel_name='tvbo.dynamics', help='Default dynamics model for all nodes. For heterogeneous networks with multiple dynamics, use network.dynamics instead.')
    integration = fields.Many2one(comodel_name='tvbo.integrator')
    connectivity = fields.Many2one(comodel_name='tvbo.network')
    network = fields.Many2one(comodel_name='tvbo.network')
    coupling = fields.Many2one(comodel_name='tvbo.coupling')
    observations = fields.Many2many(comodel_name='tvbo.observation', relation='tvbo_simulation_experiment_observations_rel', help='All observations on this experiment, keyed by name. An Observation is considered derived (computed from other observations rather than directly from state variables) when any item in its multivalued ``source`` slot names another observation in this same dict.')
    functions = fields.Many2many(comodel_name='tvbo.function', relation='tvbo_simulation_experiment_functions_rel', help='Reusable function definitions. Referenced by name in observation pipelines. Enables DRY: define compute_fc once, use in both simulated and empirical paths.')
    stimulation = fields.Many2one(comodel_name='tvbo.stimulus')
    events = fields.Many2many(comodel_name='tvbo.event', relation='tvbo_simulation_experiment_events_rel', help='Events that apply at the experiment level. For component-level events, attach them to individual nodes or edges instead.')
    field_dynamics = fields.Many2one(comodel_name='tvbo.pde')
    optimizations = fields.Many2many(comodel_name='tvbo.optimization', relation='tvbo_simulation_experiment_optimizations_rel', help='Parameter optimization configurations')
    explorations = fields.Many2many(comodel_name='tvbo.exploration', relation='tvbo_simulation_experiment_explorations_rel', help='Parameter exploration/grid search specifications')
    algorithms = fields.Many2many(comodel_name='tvbo.algorithm', relation='tvbo_simulation_experiment_algorithms_rel', help='Iterative parameter tuning algorithms (FIC, EIB, etc.)')
    continuations = fields.Many2many(comodel_name='tvbo.continuation', relation='tvbo_simulation_experiment_continuations_rel', help='Numerical continuation and bifurcation analysis specifications. Each entry defines a continuation experiment (equilibrium branch, codim-2 curve, periodic orbit family, etc.).            # Either reference a full reusable environment (preferred) or, for')
    environment = fields.Many2one(comodel_name='tvbo.software_environment', help='Execution environment (collection of requirements).')
    execution = fields.Many2one(comodel_name='tvbo.execution_config', help='Computational execution configuration (parallelization, devices).')
    software = fields.Many2one(comodel_name='tvbo.software_requirement', help="(Deprecated) Single software requirement; prefer 'environment' with aggregated requirements.")
    dataset = fields.Many2one(comodel_name='tvbo.dataset', help='Multi-subject dataset for workflow rendering. When set, render_workflow() uses dataset.subjects/sessions to generate per-subject parallel jobs.')


class SimulationStudy(models.Model):
    _name = 'tvbo.simulation_study'
    _description = 'SimulationStudy'
    _rec_name = 'label'

    label = fields.Char(index=True)
    derived_from = fields.Char()
    model = fields.Many2one(comodel_name='tvbo.dynamics')
    description = fields.Text()
    references = fields.Text()
    key = fields.Char()
    title = fields.Char()
    year = fields.Integer()
    doi = fields.Char()
    sample = fields.Many2one(comodel_name='tvbo.sample')
    experiments = fields.Many2many(comodel_name='tvbo.simulation_experiment', relation='tvbo_simulation_study_experiments_rel')


class SimulationTool(models.Model):
    _name = 'tvbo.simulation_tool'
    _description = 'A software tool for computational neuroscience simulation, analysis, or model specification. Extends SoftwarePackage with neuroscience-specific controlled vocabularies for scale, paradigm, role, and interoperability. ...'
    _rec_name = 'name'

    application_category = fields.Char(help='High-level category (e.g., simulation, analysis, specification).')
    scale = fields.Many2many(comodel_name='tvbo.simulation_scale', relation='tvbo_simulation_tool_scale_rel', help='Spatial/organizational scales the tool operates at.')
    model_paradigm = fields.Many2many(comodel_name='tvbo.model_paradigm', relation='tvbo_simulation_tool_model_paradigm_rel', help='Computational paradigms supported.')
    tool_role = fields.Many2many(comodel_name='tvbo.tool_role', relation='tvbo_simulation_tool_tool_role_rel', help='Primary function(s) in a simulation workflow.')
    programming_language = fields.Many2many(comodel_name='tvbo.programming_language_enum', relation='tvbo_simulation_tool_programming_language_rel', help='Implementation languages.')
    runtime_platform = fields.Text(help='Execution backends or platforms (e.g., MPI, OpenMP, CUDA, JAX).')
    operating_system = fields.Text(help='Supported operating systems (e.g., Linux, macOS, Windows).')
    interoperates_with = fields.Many2many(comodel_name='tvbo.simulation_tool', relation='tvbo_simulation_tool_interoperates_with_rel', column1='simulation_tool_id', column2='interoperates_with_id', help='Tools this tool can exchange data with or delegate to.')
    version = fields.Char(help='Current or latest stable version string.')
    date_created = fields.Date(help='Date the software was first released (YYYY-MM-DD).')
    date_modified = fields.Date(help='Date of the most recent release or significant update.')
    development_status = fields.Many2one(comodel_name='tvbo.development_status', help='Development status (repostatus.org aligned).')
    author = fields.Text(help='Original author(s) or creating organization(s).')
    maintainer = fields.Text(help='Current maintainer(s) or responsible organization(s).')
    funder = fields.Text(help="Funding bodies or grants (e.g., 'EU H2020 945539', 'NIH R01...').")
    reference_publication = fields.Char(help='DOI of the primary reference publication for this tool.')
    citation = fields.Text(help='Additional citation strings or DOIs.')
    keywords = fields.Text(help='Tags for topic-based discovery and clustering.')
    same_as = fields.Text(help='URIs that unambiguously identify this tool (Wikidata, bio.tools, RRID, SciCrunch).')
    issue_tracker = fields.Char(help='URL of the bug tracker or issue board.')
    is_accessible_for_free = fields.Boolean(help='Whether the tool is free/open-source.')
    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    homepage = fields.Char(help='Project homepage URL.')
    license = fields.Char(help='SPDX license identifier (e.g., MIT, GPL-3.0-only).')
    repository = fields.Char(help='Source code repository URL.')
    doi = fields.Char(help='Digital Object Identifier for the software or its reference publication.')
    ecosystem = fields.Many2many(comodel_name='tvbo.ecosystem_enum', relation='tvbo_simulation_tool_ecosystem_rel', help='Package ecosystem(s) through which the software is distributed.')


class SoftwareEnvironment(models.Model):
    _name = 'tvbo.software_environment'
    _description = 'A reproducible software environment aggregating one or more SoftwareRequirement entries. Used by SimulationExperiment to specify the execution context.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char()
    version = fields.Char(help='Environment definition version (not a package version).')
    platform = fields.Char(help='OS / architecture (e.g., linux-64, macos-arm64).')
    environment_type = fields.Many2one(comodel_name='tvbo.environment_type', help='Category: conda, venv, docker, etc.')
    container_image = fields.Char(help='Container image reference (e.g., ghcr.io/org/img:tag@sha256:...).')
    build_hash = fields.Char(help='Deterministic hash of the resolved dependency set.')
    requirements = fields.Many2many(comodel_name='tvbo.software_requirement', relation='tvbo_software_environment_requirements_rel', help='Constituent software requirements.')


class SoftwarePackage(models.Model):
    _name = 'tvbo.software_package'
    _description = 'Identity and metadata for a software package, aligned with schema.org/SoftwareApplication and CodeMeta v3.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    homepage = fields.Char(help='Project homepage URL.')
    license = fields.Char(help='SPDX license identifier (e.g., MIT, GPL-3.0-only).')
    repository = fields.Char(help='Source code repository URL.')
    doi = fields.Char(help='Digital Object Identifier for the software or its reference publication.')
    ecosystem = fields.Many2many(comodel_name='tvbo.ecosystem_enum', relation='tvbo_software_package_ecosystem_rel', help='Package ecosystem(s) through which the software is distributed.')


class SoftwareRequirement(models.Model):
    _name = 'tvbo.software_requirement'
    _description = 'An individual software requirement binding a package to a version constraint and a role within an environment.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    dataLocation = fields.Char()
    package = fields.Many2one(comodel_name='tvbo.software_package', help='Reference to the software package identity.')
    version_spec = fields.Char(help="Version or constraint specifier (e.g., '==2.7.3', '>=1.2,<2').")
    role = fields.Many2one(comodel_name='tvbo.requirement_role')
    optional = fields.Boolean()
    hash = fields.Char(help='Build or artifact hash for exact reproducibility.')
    source_url = fields.Char(help='Canonical source or repository URL.')
    url = fields.Char(help='(Deprecated) Use source_url.')
    license = fields.Char()
    modules = fields.Text(help='(Deprecated) Use environment.requirements list instead.')
    version = fields.Char(help='(Deprecated) Use version_spec.')


class Solver(models.Model):
    _name = 'tvbo.solver'
    _description = 'Lightweight specification of a numerical ODE solver / integrator. Covers adaptive solvers (Vern9, Rodas5, Tsit5, etc.) used in shooting methods, initial-state integration, and other contexts where only the algorithm a...'

    method = fields.Char(default='Tsit5', help='Solver algorithm name (e.g., Vern9, Rodas5, Tsit5, euler, heun, rk4).')
    abs_tol = fields.Float(default=1e-10, help='Absolute tolerance for adaptive solvers.')
    rel_tol = fields.Float(default=1e-10, help='Relative tolerance for adaptive solvers.')


class SpatialDomain(models.Model):
    _name = 'tvbo.spatial_domain'
    _description = 'SpatialDomain'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    coordinate_space = fields.Many2one(comodel_name='tvbo.common_coordinate_space')
    region = fields.Char(help='Optional named region/ROI in the atlas/parcellation.')
    geometry = fields.Char(help='Optional file for geometry/ROI mask (e.g., NIfTI, GIfTI).')


class SpatialField(models.Model):
    _name = 'tvbo.spatial_field'
    _description = 'SpatialField'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    quantity_kind = fields.Char(help='Scalar, vector, or tensor.')
    unit = fields.Char()
    mesh = fields.Many2one(comodel_name='tvbo.mesh')
    values = fields.Many2one(comodel_name='tvbo.nd_array')
    time_dependent = fields.Boolean()
    initial_value = fields.Float(default=0.1, help='Constant initial value for the field.')
    initial_expression = fields.Many2one(comodel_name='tvbo.equation', help='Analytic initial condition for the field.')


class StateValue(models.Model):
    _name = 'tvbo.state_value'
    _description = 'A named state variable value for per-node initialization.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    value = fields.Json(help='Numeric, string, or boolean value. ScalarValue accepts any literal primitive type, allowing parameters to carry control flags (e.g., booleans) or symbolic placeholders alongside numeric defaults.')


class StateVariable(models.Model):
    _name = 'tvbo.state_variable'
    _description = 'StateVariable'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    symbol = fields.Char()
    label = fields.Char(index=True)
    definition = fields.Char()
    domain = fields.Many2one(comodel_name='tvbo.range')
    description = fields.Text()
    equation = fields.Many2one(comodel_name='tvbo.equation')
    unit = fields.Many2one(comodel_name='tvbo.unit_enum', help='Physical unit of measurement. Values are drawn from the QUDT ontology (http://qudt.org/vocab/unit/) with UO cross-references where available.')
    record = fields.Boolean(help='Whether to include this element in simulation output files. Applicable to state variables (default true), derived variables (default false), and network nodes (default true). Set false to suppress recording.')
    grounding = fields.Text(help='External ontology IRIs (typically GO, ChEBI, UBERON, CL, MeSH) that this entity is a surrogate / abstraction / model of. Replaces the legacy OWL pattern `tvbo:surrogate_of` by carrying the link inline with the YAML data instance. Multiple IRIs allowed: a single parameter may abstract several biological processes (e.g. a synaptic conductance grounding both GO:0060079 (excitatory PSP) and GO:0007268 (chemical synaptic transmission)).')
    variable_of_interest = fields.Boolean()
    coupling_variable = fields.Boolean(help='Whether this state variable is transmitted to connected nodes through the coupling function. In TVB terms, this determines the cvar indices (state variables extracted from history and fed into the coupling function). The coupling function may override this via its incoming_states attribute.')
    equation_type = fields.Char(default='differential', help="Type of equation: 'differential' (default) means dx/dt = rhs, 'algebraic' means 0 = rhs or x ~ rhs (DAE constraint). Algebraic equations are used by ModelingToolkit.jl backend.")
    equation_order = fields.Integer(default=1, help='Order of the time derivative on the LHS. Default 1 means dx/dt = rhs (first-order ODE). Order 2 means d²x/dt² = rhs (second-order ODE), etc. Higher-order ODEs are automatically lowered to coupled first-order systems by backends like ModelingToolkit.jl via mtkcompile.')
    noise = fields.Many2one(comodel_name='tvbo.noise')
    stimulation_variable = fields.Boolean()
    boundaries = fields.Many2one(comodel_name='tvbo.range')
    initial_value = fields.Float(default=0.1)
    derivative_initial_value = fields.Float(help='Initial value for the first time derivative, used when equation_order > 1. For a second-order ODE d²x/dt² = f, this sets dx/dt(0). Required by ModelingToolkit.jl to fully specify higher-order initial value problems.')
    distribution = fields.Many2one(comodel_name='tvbo.distribution', help='Distribution for sampling initial conditions per node. If present, initial_value is used as fallback/mean.')
    history = fields.Many2one(comodel_name='tvbo.time_series')


class StimulationSetting(models.Model):
    _name = 'tvbo.stimulation_setting'
    _description = 'DBS parameters for a specific session.'

    electrode_reference = fields.Many2one(comodel_name='tvbo.electrode')
    amplitude = fields.Many2one(comodel_name='tvbo.parameter')
    frequency = fields.Many2one(comodel_name='tvbo.parameter')
    pulse_width = fields.Many2one(comodel_name='tvbo.parameter')
    mode = fields.Char()
    active_contacts = fields.Text()
    efield = fields.Many2one(comodel_name='tvbo.e_field', help='Metadata about the E-field result for this setting')


class Stimulus(models.Model):
    _name = 'tvbo.stimulus'
    _description = 'Stimulus'
    _rec_name = 'label'

    equation = fields.Many2one(comodel_name='tvbo.equation')
    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_stimulus_parameters_rel')
    description = fields.Text()
    dataLocation = fields.Char(help='Add the location of the data file containing the parcellation terminology.')
    duration = fields.Float(default=1000.0)
    label = fields.Char(index=True)
    regions = fields.Text()
    weighting = fields.Text()
    noise = fields.Many2one(comodel_name='tvbo.noise', help="Optional stochastic contribution to the stimulus. Mirrors state_variables.noise on the Dynamics side. The stimulus value at each integration step is the sum of `equation`'s evaluation (deterministic, if set) and a draw from this Noise process. When only `noise` is set and `equation` is absent, the stimulus IS the noise (pure stochastic source — e.g. iid uniform driver for memory-capacity benchmarks; signal+noise paradigms for psychophysics).")


class Subject(models.Model):
    _name = 'tvbo.subject'
    _description = "A participant in a study. Each subject typically has their own brain network (connectome) and empirical recordings. Corresponds to a BIDS 'sub-' entity."
    _rec_name = 'label'

    subject_id = fields.Char(required=True, help="BIDS-compatible subject identifier (without 'sub-' prefix). Examples: '01', 'ctrl03', 'patient17'.")
    label = fields.Char(index=True, help='Human-readable label for the subject.')
    group = fields.Char(help="Group assignment (e.g., 'control', 'patient', 'healthy'). Maps to participants.tsv 'group' column in BIDS.")
    age = fields.Float(help='Age at time of study (years).')
    sex = fields.Many2one(comodel_name='tvbo.sex_enum', help='Biological sex.')
    sessions = fields.Many2many(comodel_name='tvbo.session', relation='tvbo_subject_sessions_rel', help='Data collection sessions for this subject. Each session can have its own network, empirical data, and conditions.')
    network = fields.Char(help='Path to subject-specific connectome (when not session-dependent). Relative to dataset root or BIDS derivatives. For session-specific networks, use Session.network instead.')
    metadata = fields.Char(help='Additional subject metadata as key-value pairs or path to a sidecar JSON file.')


class TemporalApplicableEquation(models.Model):
    _name = 'tvbo.temporal_applicable_equation'
    _description = 'TemporalApplicableEquation'
    _rec_name = 'label'

    parameters = fields.Many2many(comodel_name='tvbo.parameter', relation='tvbo_temporal_applicable_equation_parameters_rel')
    time_dependent = fields.Boolean()
    label = fields.Char(index=True)
    definition = fields.Char()
    description = fields.Text()
    lhs = fields.Char()
    rhs = fields.Char()
    conditionals = fields.Many2many(comodel_name='tvbo.conditional_block', relation='tvbo_temporal_applicable_equation_conditionals_rel', help='Conditional logic for piecewise equations.')
    engine = fields.Many2one(comodel_name='tvbo.software_requirement', help="Primary engine (must appear in environment.requirements; migration target replacing deprecated 'software').")
    pycode = fields.Char(help='Python code for the equation.')
    latex = fields.Boolean()


class TimeSeries(models.Model):
    _name = 'tvbo.time_series'
    _description = 'Time series data from simulations or measurements. Supports BIDS-compatible export for computational modeling (BEP034).'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    dataLocation = fields.Char(help='Add the location of the data file containing the parcellation terminology.')
    data = fields.Many2one(comodel_name='tvbo.matrix')
    time = fields.Many2one(comodel_name='tvbo.matrix')
    sampling_rate = fields.Float(help='Sampling rate in Hz.')
    sampling_period = fields.Float(help='Time between samples (inverse of sampling_rate).')
    sampling_period_unit = fields.Char(help="Unit of the sampling period (e.g., 'ms', 's').")
    unit = fields.Char(help='Physical unit of the time series values.')
    labels_ordering = fields.Text(help='Ordering of dimensions: Time, State Variable, Space, Mode.')
    labels_dimensions = fields.Char(help='Mapping of dimension names to their labels (JSON-encoded dict).')
    source_experiment = fields.Many2one(comodel_name='tvbo.simulation_experiment', help='Reference to the SimulationExperiment that generated this TimeSeries.')
    generated_at = fields.Datetime(help='Timestamp when this TimeSeries was generated.')
    software_environment = fields.Many2one(comodel_name='tvbo.software_environment', help='Software environment used to generate this data.')
    task_name = fields.Char(help="BIDS task name for the simulation (e.g., 'rest', 'simulation').")
    subject_id = fields.Char(help='BIDS subject identifier.')
    session_id = fields.Char(help='BIDS session identifier.')
    run_id = fields.Integer(help='BIDS run number.')
    modality = fields.Many2one(comodel_name='tvbo.imaging_modality', help='Imaging modality or simulation output type.')
    model_equation_ref = fields.Char(help='BIDS ModelEq reference: path to _eq.xml LEMS file.')
    model_param_ref = fields.Char(help='BIDS ModelParam reference: path to _param.xml LEMS file.')
    connectivity_ref = fields.Char(help='Reference to connectivity data (_conndata-network_connectivity.tsv).')


class Tractogram(models.Model):
    _name = 'tvbo.tractogram'
    _description = 'Reference to tractography/diffusion MRI data used to derive structural connectivity'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    label = fields.Char(index=True)
    iri = fields.Char(help='Optional stable IRI (or compact URI) for this entity in an external ontology or knowledge base. Used to load metadata from an external source; not required when the entity is fully self-contained (equations, parameters, etc. defined in the file itself).')
    description = fields.Text()
    data_source = fields.Char(help='Path or URI to the tractography data file')
    number_of_subjects = fields.Integer(help='Number of subjects in the tractography dataset')
    acquisition = fields.Char(help='Acquisition protocol or scanner information')
    processing_pipeline = fields.Char(help='Processing pipeline used to generate the tractography')
    reference = fields.Char(help='Publication or DOI reference for this tractography dataset')


class TuningObjective(models.Model):
    _name = 'tvbo.tuning_objective'
    _description = 'Defines what the tuning algorithm optimizes for. Can be an activity target (FIC) or a connectivity target (EIB).'
    _rec_name = 'label'

    label = fields.Char(index=True)
    description = fields.Text()
    type = fields.Char(help="Type of objective: 'activity_target', 'fc_matching', 'custom'")
    target_variable = fields.Many2one(comodel_name='tvbo.state_variable', help='State variable for activity targets (e.g., S_e)')
    target_value = fields.Float(help='Target value for activity objectives')
    target_data = fields.Many2one(comodel_name='tvbo.observation', help='Reference to empirical data observation for matching objectives')
    metric = fields.Many2one(comodel_name='tvbo.equation', help='Metric equation for matching (e.g., correlation, rmse)')


class UpdateRule(models.Model):
    _name = 'tvbo.update_rule'
    _description = 'Defines how a parameter is updated based on observables. Represents iterative learning rules like FIC or EIB updates. Functions from experiment.functions are available in the equation.'
    _rec_name = 'name'

    name = fields.Char(required=True, index=True, help='Globally unique identifier for the entity.')
    description = fields.Text()
    target_parameter = fields.Many2one(comodel_name='tvbo.parameter', help='The parameter to update (e.g., J_i, wLRE)')
    equation = fields.Many2one(comodel_name='tvbo.equation', help="Update equation (e.g., 'J_i + eta * delta'). Can use functions defined in experiment.functions section.")
    bounds = fields.Many2one(comodel_name='tvbo.range', help='Constraints on parameter values after update')
    warmup = fields.Boolean(help='Whether to apply learning rate warmup to this update rule. When true, the learning rate (eta) is scaled by (i+1)/n_iterations.')
    requires = fields.Many2many(comodel_name='tvbo.observation', relation='tvbo_update_rule_requires_rel', help='Observables required by this update rule')
