from tvbo.classes.experiment import SimulationExperiment

# 1. Load the experiment you downloaded (YAML + connectome.h5 in the same folder)
exp = SimulationExperiment.from_file("experiment.yaml")

# 2. Run the simulation and plot the results
exp.plot()

# 3. Render a Markdown report of the experiment
exp.render("markdown")
