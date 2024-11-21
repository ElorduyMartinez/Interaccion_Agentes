# server.py
from mesa.visualization import SolaraViz, make_space_component
import numpy as np
from Map import IntersectionModel

def agent_portrayal(agent):
    """Define how to portray each type of agent in the visualization."""
    portrayal = {
        "color": agent.color,
        "marker": "s",  # Square marker for all agents
        "size": 100     # Same size for all agents
    }
    return portrayal

def post_process(ax):
    """Customize the plot appearance."""
    # Set equal aspect ratio and limits
    ax.set_aspect('equal')
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(-0.5, 23.5)
    
    # Draw grid
    ax.grid(True, linestyle='-', alpha=0.3)
    
    # Set ticks and labels for 0-23 range
    ax.set_xticks(np.arange(0, 24, 1))
    ax.set_yticks(np.arange(0, 24, 1))
    ax.tick_params(axis='both', which='major', labelsize=8)
    
    # Add axis labels
    ax.set_xlabel('X Coordinate (0-23)', fontsize=10)
    ax.set_ylabel('Y Coordinate (0-23)', fontsize=10)
    
    # Rotate x-axis labels for better readability
    ax.tick_params(axis='x', rotation=45)

# Create model params
model_params = {
    "width": 24,
    "height": 24
}

# Create model instance
model = IntersectionModel()

# Create visualization
space = make_space_component(
    agent_portrayal,
    post_process=post_process,
    draw_grid=True
)

# Create the visualization page
page = SolaraViz(
    model,
    [space],
    model_params=model_params,
    name="Traffic Grid Layout (0-23 x 0-23)"
)

if __name__ == "_main_":
    page  # noqa