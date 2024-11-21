import pandas as pd
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt
from Modelo import TrafficModel

def run_multiple_simulations(num_simulations=100, steps_per_sim=10, model_params=None):
    """
    Run multiple simulations and collect aggregate data.
    
    Args:
        num_simulations (int): Number of simulations to run
        steps_per_sim (int): Number of steps per simulation
        model_params (dict): Parameters for model initialization
    
    Returns:
        dict: Aggregate statistics for all simulations
    """
    if model_params is None:
        model_params = {
            'width': 15,
            'height': 5,
            'num_cars_per_direction': 5,
            'personality_type': 'random'
        }
    
    # Initialize containers for metrics
    all_results = {
        'happiness': [],
        'stress': [],
        'traffic_flow': []
    }
    
    # Run simulations with progress bar
    print(f"Running {num_simulations} simulations...")
    for sim in tqdm(range(num_simulations)):
        # Create new model instance
        model = TrafficModel(**model_params)
        
        # Run for specified steps
        sim_happiness = []
        sim_stress = []
        sim_flow = []
        
        for _ in range(steps_per_sim):
            model.step()
            
            # Collect data
            data = model.datacollector.get_model_vars_dataframe().iloc[-1]
            sim_happiness.append(data['Average Happiness'])
            sim_stress.append(data['Average Stress'])
            sim_flow.append(data['Traffic Flow'])
        
        # Store average metrics for this simulation
        all_results['happiness'].append(np.mean(sim_happiness))
        all_results['stress'].append(np.mean(sim_stress))
        all_results['traffic_flow'].append(np.mean(sim_flow))
    
    # Calculate aggregate statistics
    results = {
        'happiness_mean': np.mean(all_results['happiness']),
        'happiness_std': np.std(all_results['happiness']),
        'stress_mean': np.mean(all_results['stress']),
        'stress_std': np.std(all_results['stress']),
        'flow_mean': np.mean(all_results['traffic_flow']),
        'flow_std': np.std(all_results['traffic_flow']),
        'raw_data': all_results
    }
    
    return results

def plot_simulation_results(results):
    """
    Create visualization of simulation results.
    
    Args:
        results (dict): Results from run_multiple_simulations
    """
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
    
    # Plot happiness distribution
    ax1.hist(results['raw_data']['happiness'], bins=20, color='green', alpha=0.7)
    ax1.axvline(results['happiness_mean'], color='darkgreen', linestyle='--')
    ax1.set_title(f'Distribución de Felicidad\nPromedio: {results["happiness_mean"]:.2f} ± {results["happiness_std"]:.2f}')
    ax1.set_xlabel('Nivel de Felicidad')
    ax1.set_ylabel('Frecuencia')
    
    # Plot stress distribution
    ax2.hist(results['raw_data']['stress'], bins=20, color='red', alpha=0.7)
    ax2.axvline(results['stress_mean'], color='darkred', linestyle='--')
    ax2.set_title(f'Distribución de Estrés\nPromedio: {results["stress_mean"]:.2f} ± {results["stress_std"]:.2f}')
    ax2.set_xlabel('Nivel de Estrés')
    
    # Plot traffic flow distribution
    ax3.hist(results['raw_data']['traffic_flow'], bins=20, color='blue', alpha=0.7)
    ax3.axvline(results['flow_mean'], color='darkblue', linestyle='--')
    ax3.set_title(f'Distribución de Flujo de Tráfico\nPromedio: {results["flow_mean"]:.2f} ± {results["flow_std"]:.2f}')
    ax3.set_xlabel('Flujo de Tráfico')
    
    plt.tight_layout()
    plt.show()

def compare_personalities():
    """
    Compare metrics across different personality types.
    """
    personalities = ['random', 'cooperative', 'aggressive', 'cautious', 'opportunistic', 'reckless']
    results = {}
    
    for personality in personalities:
        print(f"\nSimulating {personality} personality...")
        model_params = {
            'width': 15,
            'height': 5,
            'num_cars_per_direction': 5,
            'personality_type': personality
        }
        results[personality] = run_multiple_simulations(
            num_simulations=100,
            steps_per_sim=10,
            model_params=model_params
        )
    
    # Create comparison dataframe
    comparison = pd.DataFrame({
        personality: {
            'Happiness': results[personality]['happiness_mean'],
            'Stress': results[personality]['stress_mean'],
            'Traffic Flow': results[personality]['flow_mean']
        }
        for personality in personalities
    }).T
    
    # Plot comparison
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    metrics = ['Happiness', 'Stress', 'Traffic Flow']
    colors = ['green', 'red', 'blue']
    
    for ax, metric, color in zip(axes, metrics, colors):
        comparison[metric].plot(kind='bar', ax=ax, color=color, alpha=0.7)
        ax.set_title(f'{metric} por Tipo de Personalidad')
        ax.set_ylabel(metric)
        ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.show()
    
    return comparison

# Usage example
if __name__ == "__main__":
    # Run basic analysis
    print("Running basic analysis...")
    results = run_multiple_simulations()
    plot_simulation_results(results)
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Average Happiness: {results['happiness_mean']:.2f} ± {results['happiness_std']:.2f}")
    print(f"Average Stress: {results['stress_mean']:.2f} ± {results['stress_std']:.2f}")
    print(f"Average Traffic Flow: {results['flow_mean']:.2f} ± {results['flow_std']:.2f}")
    
    # Run personality comparison
    print("\nComparing different personalities...")
    comparison_df = compare_personalities()
    print("\nDetailed Comparison:")
    print(comparison_df.round(2))