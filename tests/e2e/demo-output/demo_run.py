from tvbo.classes.experiment import SimulationExperiment

# Load the experiment you downloaded (experiment.yaml + connectome.h5)
exp = SimulationExperiment.from_file("experiment.yaml")

# Plot the structural connectome on the cortical surface
exp.network.plot_brain_surface()

# Run the simulation, then plot one region's activity
result = exp.run()
result.sel(node="L.PrCG").plot()

# Render a Markdown report of the full experiment
exp.render("markdown")
