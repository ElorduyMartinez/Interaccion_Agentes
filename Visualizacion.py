from mesa.visualization import SolaraViz, make_space_component
from InteraccionAgentes import IntersectionModel

def agent_portrayal(agent):
    if hasattr(agent, 'state'):  # Traffic light
        colors = {
            "red": "#FF0000",
            "yellow": "#FFFF00", 
            "green": "#00FF00"
        }
        return {
            "color": colors[agent.state],
            "marker": "s",  # Square marker for traffic lights
            "size": 100,
        }
    else:  # Vehicle
        return {
            "color": agent.color if agent.approaching else "#808080",
            "marker": "o",  # Circle marker for vehicles
            "size": 80,
        }

def post_process(ax):
    """Customize the plot appearance"""
    ax.set_aspect('equal')
    ax.grid(True)
    
    # Draw lane markers
    center_x = 10  # Center of the grid
    center_y = 10  # Center of the grid
    
    # Vertical lanes
    for i in range(3):
        ax.axvline(x=center_x + i - 1, color='gray', linestyle='--', alpha=0.5)
        
    # Horizontal lanes
    for i in range(3):
        ax.axhline(y=center_y + i - 1, color='gray', linestyle='--', alpha=0.5)

model_params = {
    "spawn_probability": {
        "type": "SliderFloat",
        "value": 0.1,
        "min": 0.05,
        "max": 0.05,
        "step": 0.05,
        "label": "Vehicle Spawn Probability"
    }
}

# Create initial model instance
model = IntersectionModel()

# Create visualization components
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
    name="Smart Traffic Intersection"
)

page  # noqa