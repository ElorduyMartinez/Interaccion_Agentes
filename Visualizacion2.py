from mesa.visualization import SolaraViz, make_space_component, make_plot_component
import numpy as np
from InteraccionAgentes import TrafficModel, CarAgent, TrafficLightAgent

def agent_portrayal(agent):
    """Define how to portray each type of agent."""
    if isinstance(agent, CarAgent):
        # Base portrayal
        portrayal = {
            "color": agent.color,
            "size": 80,
            "alpha": 0.8
        }
        
        # Adjust marker based on direction and personality
        if agent.destination[0] > agent.position[0]:  # Moving right
            portrayal["marker"] = {
                'cooperative': '>',
                'aggressive': '>',
                'cautious': '>',
                'opportunistic': '>',
                'reckless': '>'
            }[agent.personality]
        else:  # Moving left
            portrayal["marker"] = {
                'cooperative': '<',
                'aggressive': '<',
                'cautious': '<',
                'opportunistic': '<',
                'reckless': '<'
            }[agent.personality]
        
        # Modify size for waiting cars
        if agent.waiting_time > 0:
            portrayal["size"] = 90
            portrayal["alpha"] = 1.0
        
        return portrayal
        
    elif isinstance(agent, TrafficLightAgent):
        portrayal = {
            "color": agent.color,
            "marker": "s", 
            "size": 100,
            "alpha": 1.0
        }
        
        if len(agent.approaching_cars) > 0:
            portrayal["size"] = 120
        
        return portrayal
    
    return {}

def post_process(ax):
    """Customize the plot appearance."""
    ax.set_aspect('equal')
    ax.grid(True, linestyle='-', alpha=0.3)
    
    ax.set_xlim(-0.5, 14.5)
    ax.set_ylim(-0.5, 4.5)
    
    ax.set_xticks(np.arange(0, 15, 1))
    ax.set_yticks(np.arange(0, 5, 1))
    
    ax.set_xlabel('Distancia', fontsize=10)
    ax.set_ylabel('Carril', fontsize=10)
    ax.tick_params(axis='both', which='major', labelsize=8)
    
    ax.axvline(x=7, color='gray', linestyle='--', alpha=0.5)
    
    from matplotlib.patches import Patch, Circle
    legend_elements = [
        Patch(facecolor='yellow', label='Semáforo Amarillo'),
        Patch(facecolor='green', label='Semáforo Verde'),
        Patch(facecolor='red', label='Semáforo Rojo'),
        Circle(xy=(0, 0), radius=1, facecolor='blue', label='Coche Cooperativo'),
        Circle(xy=(0, 0), radius=1, facecolor='red', label='Coche Agresivo'),
        Circle(xy=(0, 0), radius=1, facecolor='orange', label='Coche Cauteloso')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8)

def happiness_plot_postprocess(ax):
    """Customize happiness plot."""
    ax.set_title("Felicidad Promedio")
    ax.set_xlabel("Pasos")
    ax.set_ylabel("Nivel de Felicidad")
    ax.grid(True)

def stress_plot_postprocess(ax):
    """Customize stress plot."""
    ax.set_title("Estrés Promedio")
    ax.set_xlabel("Pasos")
    ax.set_ylabel("Nivel de Estrés")
    ax.grid(True)

def flow_plot_postprocess(ax):
    """Customize flow plot."""
    ax.set_title("Flujo de Tráfico")
    ax.set_xlabel("Pasos")
    ax.set_ylabel("Proporción de Coches en Movimiento")
    ax.grid(True)

# Model parameters - single definition
model_params = {
    "width": {
        "type": "SliderInt",
        "value": 15,
        "min": 10,
        "max": 20,
        "step": 1,
        "label": "Ancho del grid"
    },
    "height": {
        "type": "SliderInt",
        "value": 5,
        "min": 3,
        "max": 7,
        "step": 1,
        "label": "Alto del grid"
    },
    "num_cars_per_direction": {  # Changed from num_cars to match model
        "type": "SliderInt",
        "value": 3,
        "min": 1,
        "max": 10,
        "step": 1,
        "label": "Coches por dirección"
    }
}

# Create space visualization component
space = make_space_component(
    agent_portrayal=agent_portrayal,
    post_process=post_process,
    draw_grid=True
)

# Create plot components for monitoring
happiness_plot = make_plot_component(
    {"Average Happiness": "green"},
    post_process=happiness_plot_postprocess
)

stress_plot = make_plot_component(
    {"Average Stress": "red"},
    post_process=stress_plot_postprocess
)

flow_plot = make_plot_component(
    {"Traffic Flow": "blue"},
    post_process=flow_plot_postprocess
)

# Create initial model instance
model = TrafficModel(width=15, height=5, num_cars_per_direction=3)  # Changed from num_cars

# Create visualization page
page = SolaraViz(
    model,
    [
        space,
        happiness_plot,
        stress_plot,
        flow_plot
    ],
    model_params=model_params,
    name="Simulación de Tráfico Inteligente"
)

if __name__ == "__main__":
    page  # noqa