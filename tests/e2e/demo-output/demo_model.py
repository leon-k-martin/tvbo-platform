from tvbo import Dynamics, SimulationExperiment

# Specify a model: named parameters + state variables governed by ODEs
lorenz = Dynamics(
    parameters={
        "sigma": {"value": 10.0},
        "rho": {"value": 28.0},
        "beta": {"value": 8 / 3},
    },
    state_variables={
        "X": {"equation": {"rhs": "sigma * (Y - X)"}},
        "Y": {"equation": {"rhs": "X * (rho - Z) - Y"}},
        "Z": {"equation": {"rhs": "X * Y - beta * Z"}},
    },
)

# Wrap it in an experiment and run
exp = SimulationExperiment(dynamics=lorenz)
result = exp.run(duration=1000)

# Visualise: the attractor, then the state variables over time
result.plot(type="phase")
result.sel(time=slice(0, 60)).plot()
