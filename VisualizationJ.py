from mesa.visualization import SolaraViz, make_space_component, make_plot_component
import numpy as np
from Juntos import (
    IntersectionModel, IntersectionCar, IntersectionLight, 
    IntersectionBuilding, IntersectionSpawnPoint
)

def agent_portrayal(agent):
    """Define how to portray each type of agent in the visualization."""
    
    if isinstance(agent, IntersectionCar):
        # Base portrayal for cars
        portrayal = {
            "color": agent.color,
            "size": 80,
            "alpha": 0.8
        }
        
        # Determine direction based on path or position/destination
        if agent.destination and agent.position:
            going_right = agent.destination[0] > agent.position[0]
            going_down = agent.destination[1] < agent.position[1]
            
            if going_right:
                portrayal["marker"] = ">"
            elif going_down:
                portrayal["marker"] = "v"
            else:
                portrayal["marker"] = "<"
        
        # Make waiting cars more visible
        if agent.waiting_time > 0:
            portrayal["size"] = 90
            portrayal["alpha"] = 1.0
        
        return portrayal
        
    elif isinstance(agent, IntersectionLight):
        return {
            "color": agent.color,
            "marker": "s",
            "size": 100,
            "alpha": 1.0
        }
        
    elif isinstance(agent, IntersectionBuilding):
        return {
            "color": agent.color,
            "marker": "s",
            "size": 120,
            "alpha": 0.7
        }
        
    elif isinstance(agent, IntersectionSpawnPoint):
        return {
            "color": agent.color,
            "marker": "^",
            "size": 80,
            "alpha": 0.9
        }
    
    return {}

def post_process(ax):
    """Customize the plot appearance."""
    # Set equal aspect ratio and limits
    ax.set_aspect('equal')
    ax.set_xlim(-0.5, 23.5)
    ax.set_ylim(-0.5, 23.5)
    
    # Draw grid
    ax.grid(True, linestyle='-', alpha=0.3)
    
    # Set ticks and labels
    ax.set_xticks(np.arange(0, 24, 2))
    ax.set_yticks(np.arange(0, 24, 2))
    ax.tick_params(axis='both', which='major', labelsize=8)
    
    # Add axis labels
    ax.set_xlabel('X Coordinate', fontsize=10)
    ax.set_ylabel('Y Coordinate', fontsize=10)
    
    # Rotate x-axis labels for better readability
    ax.tick_params(axis='x', rotation=45)
    
    # Add legend
    from matplotlib.patches import Patch, Circle
    legend_elements = [
        Patch(facecolor='#87CEEB', alpha=0.7, label='Building'),
        Patch(facecolor='brown', alpha=0.7, label='Central Building'),
        Patch(facecolor='yellow', label='Traffic Light (Yellow)'),
        Patch(facecolor='green', label='Traffic Light (Green)'),
        Patch(facecolor='red', label='Traffic Light (Red)'),
        Circle(xy=(0, 0), radius=1, facecolor='blue', label='Cooperative Car'),
        Circle(xy=(0, 0), radius=1, facecolor='red', label='Aggressive Car'),
        Circle(xy=(0, 0), radius=1, facecolor='green', label='Cautious Car'),
        Circle(xy=(0, 0), radius=1, facecolor='purple', label='Opportunistic Car'),
        Circle(xy=(0, 0), radius=1, facecolor='orange', label='Reckless Car'),
        Patch(facecolor='yellow', alpha=0.9, label='Spawn Point')
    ]
    ax.legend(handles=legend_elements, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)

def happiness_plot_postprocess(ax):
    """Customize happiness plot."""
    ax.set_title("Average Happiness")
    ax.set_xlabel("Steps")
    ax.set_ylabel("Happiness Level")
    ax.set_ylim(0, 100)  # Set fixed range for happiness
    ax.grid(True)

def stress_plot_postprocess(ax):
    """Customize stress plot."""
    ax.set_title("Average Stress")
    ax.set_xlabel("Steps")
    ax.set_ylabel("Stress Level")
    ax.set_ylim(0, 100)  # Set fixed range for stress
    ax.grid(True)

def cars_plot_postprocess(ax):
    """Customize active cars plot."""
    ax.set_title("Active Cars")
    ax.set_xlabel("Steps")
    ax.set_ylabel("Number of Cars")
    ax.set_ylim(0, None)  # Allow upper limit to adjust but keep 0 as minimum
    ax.grid(True)

# Model parameters
model_params = {
    "width": 24,
    "height": 24,
    "spawn_rate": {
        "type": "SliderFloat",
        "value": 0.05,  # Default spawn rate of 5%
        "min": 0.001,    # Minimum 1%
        "max": 0.1,     # Maximum 10%
        "step": 0.01,
        "label": "Car Spawn Rate"
    }
}

# Create model instance
model = IntersectionModel()

# Create visualization components
space = make_space_component(
    agent_portrayal,
    post_process=post_process,
    draw_grid=True
)

happiness_plot = make_plot_component(
    {"Average Happiness": "green"},
    post_process=happiness_plot_postprocess
)

stress_plot = make_plot_component(
    {"Average Stress": "red"},
    post_process=stress_plot_postprocess
)

cars_plot = make_plot_component(
    {"Active Cars": "blue"},
    post_process=cars_plot_postprocess
)

# Create the visualization page
page = SolaraViz(
    model,
    [
        space,
        cars_plot,
        happiness_plot,
        stress_plot
    ],
    model_params=model_params,
    name="Intelligent Traffic Intersection"
)

if __name__ == "__main__":
    page  # noqa