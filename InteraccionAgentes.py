from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.time import SimultaneousActivation
from mesa.datacollection import DataCollector
from collections import deque
import random
import numpy as np
from typing import Optional, List, Dict, Tuple, Any

class TrafficLightAgent(Agent):
    """Traffic light agent that adapts to approaching vehicles."""
    
    def __init__(self, model, position=None):
        super().__init__(model)
        self.position = position
        self.state = 'yellow'  # Default state as specified
        self.color = "yellow"
        self.timer = 0
        self.approaching_cars = {}  # Track approaching cars and ETAs
        self.min_green_time = 3
        self.max_green_time = 10
        self.detection_radius = 1
        
    def get_nearby_cars(self):
        """Detect cars within detection radius."""
        nearby_cars = []
        x, y = self.position
        for dx in range(-self.detection_radius, self.detection_radius + 1):
            for dy in range(-self.detection_radius, self.detection_radius + 1):
                pos = (x + dx, y + dy)
                if (0 <= pos[0] < self.model.grid.width and 
                    0 <= pos[1] < self.model.grid.height):
                    cell_contents = self.model.grid.get_cell_list_contents(pos)
                    cars = [agent for agent in cell_contents if isinstance(agent, CarAgent)]
                    nearby_cars.extend(cars)
        return nearby_cars
    
    def calculate_eta(self, car):
        """Calculate estimated arrival time for a car."""
        if car.path:
            steps_to_light = 0
            current_pos = car.position
            for pos in car.path:
                if pos == self.position:
                    break
                steps_to_light += 1
            return steps_to_light
        return float('inf')
    
    def update_traffic_schedule(self):
        """Update schedule based on approaching cars."""
        nearby_cars = self.get_nearby_cars()
        
        # Clear old entries
        self.approaching_cars.clear()
        
        # If no cars nearby, return to yellow
        if not nearby_cars:
            if self.state != 'yellow':
                self.state = 'yellow'
                self.color = 'yellow'
            return
        
        # Process approaching cars
        for car in nearby_cars:
            eta = self.calculate_eta(car)
            if eta != float('inf'):
                self.approaching_cars[car.unique_id] = {
                    'eta': eta,
                    'position': car.position
                }
        
        # If cars are approaching and light is yellow, change to green
        if self.approaching_cars and self.state == 'yellow':
            min_eta = min(data['eta'] for data in self.approaching_cars.values())
            if min_eta <= self.detection_radius:
                self.state = 'green'
                self.color = 'green'
                self.timer = 0
        
        # Manage light cycle
        if self.state == 'green':
            self.timer += 1
            if self.timer >= self.max_green_time:
                self.state = 'red'
                self.color = 'red'
                self.timer = 0
        elif self.state == 'red':
            self.timer += 1
            if self.timer >= self.min_green_time and not self.approaching_cars:
                self.state = 'yellow'
                self.color = 'yellow'
                self.timer = 0
    
    def step(self):
        """Execute traffic light step."""
        self.update_traffic_schedule()


class CarAgent(Agent):
    """Intelligent car agent with personality and emotional states."""
    
    def __init__(self, model):
        super().__init__(model)
        self.position: Optional[Tuple[int, int]] = None
        self.destination: Optional[Tuple[int, int]] = None
        self.path: List[Tuple[int, int]] = []
        self.traffic_light_detection_range = 3
        
        # Personality types with different behaviors
        self.personality = random.choice([
            'cooperative',    # Prefers yielding
            'aggressive',     # Prefers pushing through
            'cautious',      # Prefers safe routes
            'opportunistic', # Maximizes personal gain
            'reckless'       # May ignore red lights if stressed
        ])
        
        # Emotional and behavioral attributes
        self.state = 'normal'
        self.happiness = 100
        self.stress = 0
        self.patience = self.get_initial_patience()
        self.waiting_time = 0
        self.color = self.get_initial_color()
        self.risk_threshold = 0.5
        self.learning_rate = 0.1
        
        # Traffic light interaction
        self.approaching_light = None
        self.eta_to_light = None
        
        # Learning and memory
        self.memory = {
            'successful_negotiations': 0,
            'failed_negotiations': 0,
            'traffic_patterns': {},
            'risky_moves_outcome': []
        }
        
        # Visual representation markers based on personality
        self.marker = {
            'cooperative': '>',    # Right-pointing triangle
            'aggressive': '^',     # Up-pointing triangle
            'cautious': 'v',       # Down-pointing triangle
            'opportunistic': '<',  # Left-pointing triangle
            'reckless': 's'       # Square
        }[self.personality]

    def get_initial_patience(self) -> int:
        """Set initial patience based on personality."""
        base_patience = random.randint(3, 8)
        modifiers = {
            'cooperative': 2,
            'aggressive': -2,
            'cautious': 3,
            'opportunistic': 0,
            'reckless': -3
        }
        return max(1, base_patience + modifiers[self.personality])

    def get_initial_color(self) -> str:
        """Set initial color based on personality."""
        return {
            'cooperative': 'blue',
            'aggressive': 'red',
            'cautious': 'green',
            'opportunistic': 'purple',
            'reckless': 'orange'
        }[self.personality]

    def set_position_and_destination(self, pos: Tuple[int, int], dest: Tuple[int, int]) -> None:
        """Initialize car's position and destination."""
        self.position = pos
        self.destination = dest
        self.path = self.find_path() or []
        if not self.path:
            print(f"Warning: No path found for car {self.unique_id} from {pos} to {dest}")

    def detect_traffic_light_ahead(self):
        """Detect if there's a traffic light within detection range."""
        if not self.position:
            return None
            
        x, y = self.position
        for dx in range(1, self.traffic_light_detection_range + 1):
            check_pos = (x + dx, y)  # Only check ahead in the current lane
            if 0 <= check_pos[0] < self.model.grid.width:
                cell_contents = self.model.grid.get_cell_list_contents(check_pos)
                for agent in cell_contents:
                    if isinstance(agent, TrafficLightAgent):
                        return agent
        return None

    def calculate_eta_to_light(self, light) -> Optional[int]:
        """Calculate ETA to the detected traffic light."""
        if not light or not self.position:
            return None
        
        distance = abs(light.position[0] - self.position[0])
        return distance

    def notify_traffic_light(self) -> None:
        """Notify nearby traffic light of approach."""
        light = self.detect_traffic_light_ahead()
        if light and (self.approaching_light != light or self.eta_to_light is None):
            self.approaching_light = light
            self.eta_to_light = self.calculate_eta_to_light(light)
            if hasattr(light, 'register_approaching_car') and self.eta_to_light is not None:
                light.register_approaching_car(self, self.eta_to_light)

    def calculate_payoff(self, my_strategy: str, other_strategy: str) -> float:
        """Calculate payoff for game theory negotiation."""
        payoff_matrices = {
            'cooperative': {
                ('yield', 'yield'): (8, 8),
                ('yield', 'push_through'): (2, 6),
                ('push_through', 'yield'): (6, 2),
                ('push_through', 'push_through'): (-8, -8)
            },
            'aggressive': {
                ('yield', 'yield'): (4, 4),
                ('yield', 'push_through'): (-2, 12),
                ('push_through', 'yield'): (12, -2),
                ('push_through', 'push_through'): (-4, -4)
            },
            'cautious': {
                ('yield', 'yield'): (10, 10),
                ('yield', 'push_through'): (5, 3),
                ('push_through', 'yield'): (3, 5),
                ('push_through', 'push_through'): (-10, -10)
            },
            'opportunistic': {
                ('yield', 'yield'): (6, 6),
                ('yield', 'push_through'): (0, 8),
                ('push_through', 'yield'): (8, 0),
                ('push_through', 'push_through'): (-6, -6)
            },
            'reckless': {
                ('yield', 'yield'): (2, 2),
                ('yield', 'push_through'): (-4, 14),
                ('push_through', 'yield'): (14, -4),
                ('push_through', 'push_through'): (0, 0)
            }
        }
        
        base_payoff = payoff_matrices[self.personality].get(
            (my_strategy, other_strategy), (0, 0)
        )[0]
        
        # Apply emotional state modifiers
        if self.state == 'angry':
            base_payoff *= 1.5 if my_strategy == 'push_through' else 0.5
        elif self.state == 'happy':
            base_payoff *= 1.2 if my_strategy == 'yield' else 0.8
            
        # Apply learning from past experiences
        success_rate = (self.memory['successful_negotiations'] / 
                       max(1, self.memory['successful_negotiations'] + 
                           self.memory['failed_negotiations']))
        
        return base_payoff * (1 + 0.2 * success_rate)

    def get_strategy(self, other_agent) -> str:
        """Determine negotiation strategy based on personality and state."""
        if self.state == 'angry':
            return 'push_through'
        
        strategy_probabilities = {
            'cooperative': {'yield': 0.7, 'push_through': 0.3},
            'aggressive': {'yield': 0.2, 'push_through': 0.8},
            'cautious': {'yield': 0.8, 'push_through': 0.2},
            'opportunistic': {'yield': 0.5, 'push_through': 0.5},
            'reckless': {'yield': 0.1, 'push_through': 0.9}
        }
        
        probs = strategy_probabilities[self.personality].copy()
        
        # Modify probabilities based on state and stress
        if self.state == 'impatient':
            probs['push_through'] += 0.2
            probs['yield'] -= 0.2
        
        stress_factor = self.stress / 100
        probs['push_through'] += stress_factor * 0.3
        probs['yield'] -= stress_factor * 0.3
        
        # Normalize probabilities
        total = sum(probs.values())
        for key in probs:
            probs[key] /= total
        
        return 'push_through' if random.random() < probs['push_through'] else 'yield'

    def update_emotional_state(self) -> None:
        """Update emotional state based on multiple factors."""
        # Update stress based on personality
        stress_factor = 2 if self.personality == 'aggressive' else 1
        self.stress += self.waiting_time * stress_factor
        self.stress = min(100, max(0, self.stress))
        
        # Natural stress decay
        stress_decay = 2 if self.state == 'happy' else 1
        self.stress = max(0, self.stress - stress_decay)
        
        # Update state and color based on current conditions
        if self.happiness > 80 and self.stress < 30:
            new_state = 'happy'
            self.color = 'green'
            self.patience = min(8, self.patience + 1)
        elif self.happiness < 30 or self.stress > 70:
            new_state = 'angry'
            self.color = 'red'
            self.patience = max(1, self.patience - 1)
        elif self.waiting_time > self.patience:
            new_state = 'impatient'
            self.color = 'orange'
        else:
            new_state = 'normal'
            self.color = self.get_initial_color()
            
        # Update parameters based on state change
        if new_state != self.state:
            self.state = new_state
            self.update_state_parameters()

    def update_state_parameters(self) -> None:
        """Update agent parameters based on emotional state."""
        if self.state == 'angry':
            self.learning_rate = 0.2
            self.risk_threshold = 0.7
        elif self.state == 'happy':
            self.learning_rate = 0.05
            self.risk_threshold = 0.3
        else:
            self.learning_rate = 0.1
            self.risk_threshold = 0.5

    def negotiate_passage(self, other_agent) -> bool:
        """Negotiate movement priority with another car."""
        my_strategy = self.get_strategy(other_agent)
        other_strategy = other_agent.get_strategy(self)
        
        payoff = self.calculate_payoff(my_strategy, other_strategy)
        
        # Update memory based on negotiation outcome
        if payoff > 0:
            self.memory['successful_negotiations'] += 1
            if my_strategy == 'push_through':
                self.memory['risky_moves_outcome'].append(1)
        else:
            self.memory['failed_negotiations'] += 1
            if my_strategy == 'push_through':
                self.memory['risky_moves_outcome'].append(0)
                
        # Maintain recent history
        if len(self.memory['risky_moves_outcome']) > 10:
            self.memory['risky_moves_outcome'].pop(0)
        
        # Update happiness based on negotiation outcome
        self.happiness = min(100, max(0, self.happiness + payoff))
        
        return payoff > 0

    def find_path(self) -> Optional[List[Tuple[int, int]]]:
        """Find path to destination with improved traffic light handling."""
        if not self.position or not self.destination:
            return None
            
        frontier = deque([[self.position]])
        visited = {self.position}
        
        while frontier:
            path = frontier.popleft()
            current = path[-1]
            
            if current == self.destination:
                return path
                
            for next_pos in self.get_neighbors(current):
                # Skip if already visited
                if next_pos in visited:
                    continue
                    
                # Check if position contains a traffic light
                cell_contents = self.model.grid.get_cell_list_contents(next_pos)
                traffic_light = next((agent for agent in cell_contents 
                                   if isinstance(agent, TrafficLightAgent)), None)
                
                # Allow path through traffic light positions
                if traffic_light:
                    visited.add(next_pos)
                    new_path = list(path)
                    new_path.append(next_pos)
                    frontier.append(new_path)
                    continue
                
                # For non-traffic light positions, check if movement is possible
                if self.is_valid_position(next_pos):
                    visited.add(next_pos)
                    new_path = list(path)
                    new_path.append(next_pos)
                    frontier.append(new_path)
                    
        return None

    def get_neighbors(self, pos: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Get valid neighboring positions based on personality."""
        x, y = pos
        possible_moves = []
        
        # Different movement patterns based on personality
        if self.personality == 'aggressive':
            # Aggressive drivers prefer direct routes
            if x < self.destination[0]:
                possible_moves.append((x+1, y))
            elif x > self.destination[0]:
                possible_moves.append((x-1, y))
            if y < self.destination[1]:
                possible_moves.append((x, y+1))
            elif y > self.destination[1]:
                possible_moves.append((x, y-1))
        elif self.personality == 'cautious':
            # Cautious drivers prefer lane changes first
            if y < self.destination[1]:
                possible_moves.append((x, y+1))
            elif y > self.destination[1]:
                possible_moves.append((x, y-1))
            if x < self.destination[0]:
                possible_moves.append((x+1, y))
            elif x > self.destination[0]:
                possible_moves.append((x-1, y))
        else:
            # Other personalities consider all moves
            possible_moves = [
                (x+1, y), (x-1, y),
                (x, y+1), (x, y-1)
            ]
        
        # Filter moves within grid boundaries
        valid_moves = []
        for nx, ny in possible_moves:
            if 0 <= nx < self.model.grid.width and 0 <= ny < self.model.grid.height:
                valid_moves.append((nx, ny))
        
        return valid_moves

    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if a position is valid for pathfinding purposes."""
        # Check grid boundaries
        if not (0 <= pos[0] < self.model.grid.width and 
                0 <= pos[1] < self.model.grid.height):
            return False
        
        # Check for other cars (but not traffic lights)
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        if any(isinstance(agent, CarAgent) for agent in cell_contents):
            return False
            
        return True

    def can_move_to(self, pos: Tuple[int, int]) -> bool:
        """Check if immediate movement to position is possible."""
        if not (0 <= pos[0] < self.model.grid.width and 
                0 <= pos[1] < self.model.grid.height):
            return False
        
        cell_contents = self.model.grid.get_cell_list_contents(pos)
        
        # Check for other cars
        if any(isinstance(agent, CarAgent) for agent in cell_contents):
            return False
            
        # Check traffic lights with personality-based behavior
        light = next((agent for agent in cell_contents 
                     if isinstance(agent, TrafficLightAgent)), None)
        if light:
            if self.personality == 'reckless':
                # Reckless drivers might run red lights based on stress
                if light.state == 'red':
                    # Higher stress increases chance of running red light
                    risk_factor = self.stress / 100
                    if random.random() > risk_factor:
                        return False
                elif light.state == 'yellow':
                    # More likely to run yellow lights
                    risk_factor = (self.stress + 20) / 100
                    if random.random() > risk_factor:
                        return False
            else:
                # Other personalities always respect red/yellow
                if light.state == 'red' or light.state == 'yellow':
                    return False
            
        return True

    def handle_traffic_light(self, next_pos: Tuple[int, int]) -> bool:
        """Handle interaction with traffic light at next position."""
        cell_contents = self.model.grid.get_cell_list_contents(next_pos)
        traffic_light = next((agent for agent in cell_contents 
                            if isinstance(agent, TrafficLightAgent)), None)
        
        if not traffic_light:
            return True
            
        if traffic_light.state == 'green':
            return True
            
        if traffic_light.state == 'red':
            self.waiting_time += 1
            self.happiness = max(0, self.happiness - 5)
            self.stress += 2 if self.personality == 'aggressive' else 1
            return False
            
        if traffic_light.state == 'yellow':
            # Personality-based yellow light behavior
            if self.personality == 'reckless':
                risk_chance = min(0.8, self.stress / 100 + 0.3)
                return random.random() < risk_chance
            elif self.personality == 'aggressive':
                risk_chance = min(0.6, self.stress / 100 + 0.2)
                return random.random() < risk_chance
            else:
                return False
                
        return True

    def handle_car_interaction(self, next_pos: Tuple[int, int]) -> bool:
        """Handle interaction with other cars at next position."""
        cell_contents = self.model.grid.get_cell_list_contents(next_pos)
        other_car = next((agent for agent in cell_contents 
                         if isinstance(agent, CarAgent)), None)
        
        if not other_car:
            return True
            
        negotiation_result = self.negotiate_passage(other_car)
        
        if not negotiation_result:
            self.waiting_time += 1
            self.happiness = max(0, self.happiness - 3)
            self.stress = min(100, self.stress + 2)
            
        return negotiation_result

    def update_position_metrics(self, next_pos: Tuple[int, int]) -> None:
        """Update metrics after successful movement."""
        self.model.grid.move_agent(self, next_pos)
        self.position = next_pos
        self.path.pop(0)
        self.waiting_time = 0
        self.happiness = min(100, self.happiness + 5)
        self.stress = max(0, self.stress - 1)
        
        # Extra happiness boost for forward progress
        if self.destination and next_pos[0] > self.position[0]:
            self.happiness = min(100, self.happiness + 2)

    def step(self) -> None:
        """Execute one step of the car's movement with improved decision making."""
        self.update_emotional_state()
        self.notify_traffic_light()
        
        # Recalculate path if none exists or if blocked
        if not self.path or (len(self.path) > 1 and not self.can_move_to(self.path[1])):
            new_path = self.find_path()
            if new_path:
                self.path = new_path
            else:
                self.waiting_time += 1
                self.happiness = max(0, self.happiness - 5)
                self.stress = min(100, self.stress + 3)
                return

        if len(self.path) > 1:
            next_pos = self.path[1]
            
            # Handle traffic lights and other cars
            if not self.handle_traffic_light(next_pos):
                return
                
            if not self.handle_car_interaction(next_pos):
                return
            
            # Move if position is clear
            if self.can_move_to(next_pos):
                self.update_position_metrics(next_pos)
                
                # Check for destination arrival
                if self.position == self.destination:
                    self.arrive_at_destination()
            else:
                self.handle_blocked_movement()

    def arrive_at_destination(self) -> None:
        """Handle arrival at destination."""
        self.happiness = min(100, self.happiness + 20)
        self.stress = max(0, self.stress - 10)
        self.state = 'happy'
        self.color = 'green'
        print(f"Car {self.unique_id} ({self.personality}) reached destination!")
        
        # Update learning memory with successful trip
        self.memory['traffic_patterns'][self.destination] = {
            'path': self.path,
            'time': self.model.schedule.steps,
            'stress_level': self.stress
        }

    def handle_blocked_movement(self) -> None:
        """Handle case where movement is blocked."""
        self.waiting_time += 1
        self.happiness = max(0, self.happiness - 3)
        self.stress = min(100, self.stress + 2)
        
        # Personality-based waiting behavior
        if self.personality == 'aggressive':
            self.stress += 2
        elif self.personality == 'patient':
            self.stress += 0.5
        
        # Consider rerouting if waited too long
        if self.waiting_time > self.patience * 2:
            self.path = self.find_path()  # Try to find alternative path

    def __str__(self) -> str:
        """String representation of the car agent."""
        return (f"Car {self.unique_id} ({self.personality}) - "
                f"State: {self.state}, Happiness: {self.happiness}, "
                f"Stress: {self.stress}")

class TrafficModel(Model):
    def __init__(self, width=15, height=5, num_cars_per_direction=5, personality_type="aggressive"):
        """
        Initialize traffic model with cars going in both directions.
        Args:
            width (int): Grid width (default 15)
            height (int): Grid height (default 5)
            num_cars_per_direction (int): Number of cars to create in each direction
            personality_type (str): Type of personality for all cars or "random"
                                  Options: "random", "cooperative", "aggressive", 
                                  "cautious", "opportunistic", "reckless"
        """
        if num_cars_per_direction > height:
            print(f"Warning: {num_cars_per_direction} cars per direction requested but only {height} start positions available")
            num_cars_per_direction = height
            
        if width < 3:
            raise ValueError("Grid width must be at least 3")
        if height < 1:
            raise ValueError("Grid height must be at least 1")
            
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.schedule = SimultaneousActivation(self)
        self.personality_type = personality_type
        
        # Create traffic lights
        self.traffic_lights = self.create_traffic_lights()
        
        # Create cars going in both directions
        self.create_bidirectional_cars(num_cars_per_direction)
        
        # Set up data collection
        self.setup_datacollection()

    def create_traffic_lights(self):
        """Create and position traffic lights in the middle of each lane."""
        traffic_lights = []
        # Create a traffic light for each lane in the middle of the grid
        middle_x = self.grid.width // 2
        
        for y in range(self.grid.height):
            light = TrafficLightAgent(self, position=(middle_x, y))
            self.schedule.add(light)
            self.grid.place_agent(light, (middle_x, y))
            traffic_lights.append(light)
            
        return traffic_lights

    def create_car_with_personality(self):
        """Create a car with specified or random personality."""
        car = CarAgent(self)
        if self.personality_type != "random":
            car.personality = self.personality_type
            # Update initial color based on personality
            car.color = car.get_initial_color()
        return car

    def create_bidirectional_cars(self, num_cars_per_direction):
        """Create cars going in both directions with specified personalities."""
        # Generate all possible positions
        left_start_positions = [(0, y) for y in range(self.grid.height)]
        right_start_positions = [(self.grid.width-1, y) for y in range(self.grid.height)]
        
        # Shuffle positions for random distribution
        self.random.shuffle(left_start_positions)
        self.random.shuffle(right_start_positions)
        
        # Create cars going right (west to east)
        for i in range(num_cars_per_direction):
            if i < len(left_start_positions):
                car = self.create_car_with_personality()
                self.schedule.add(car)
                start_pos = left_start_positions[i]
                end_pos = (self.grid.width-1, self.random.randrange(self.grid.height))
                car.set_position_and_destination(start_pos, end_pos)
                self.grid.place_agent(car, start_pos)
        
        # Create cars going left (east to west)
        for i in range(num_cars_per_direction):
            if i < len(right_start_positions):
                car = self.create_car_with_personality()
                self.schedule.add(car)
                start_pos = right_start_positions[i]
                end_pos = (0, self.random.randrange(self.grid.height))
                car.set_position_and_destination(start_pos, end_pos)
                self.grid.place_agent(car, start_pos)

    def setup_datacollection(self):
        """Set up data collection for model metrics."""
        self.datacollector = DataCollector(
            model_reporters={
                "Average Happiness": lambda m: np.mean([a.happiness for a in m.schedule.agents 
                                                    if isinstance(a, CarAgent)]),
                "Average Stress": lambda m: np.mean([a.stress for a in m.schedule.agents 
                                                 if isinstance(a, CarAgent)]),
                "Traffic Flow": self.calculate_traffic_flow,
                "Cars Moving Right": lambda m: len([a for a in m.schedule.agents 
                                                if isinstance(a, CarAgent) and 
                                                a.destination[0] > a.position[0]]),
                "Cars Moving Left": lambda m: len([a for a in m.schedule.agents 
                                               if isinstance(a, CarAgent) and 
                                               a.destination[0] < a.position[0]])
            },
            agent_reporters={
                "Position": lambda a: a.position if hasattr(a, 'position') else None,
                "State": lambda a: a.state if hasattr(a, 'state') else None,
                "Personality": lambda a: getattr(a, 'personality', None),
                "Happiness": lambda a: getattr(a, 'happiness', None),
                "Stress": lambda a: getattr(a, 'stress', None),
                "Waiting Time": lambda a: getattr(a, 'waiting_time', None),
                "Direction": lambda a: "Right" if (hasattr(a, 'destination') and 
                                                 hasattr(a, 'position') and 
                                                 a.destination[0] > a.position[0]) 
                                     else "Left" if (hasattr(a, 'destination') and 
                                                   hasattr(a, 'position')) 
                                     else None
            }
        )

    def calculate_traffic_flow(self):
        """Calculate traffic flow metric."""
        cars = [agent for agent in self.schedule.agents if isinstance(agent, CarAgent)]
        if not cars:
            return 0
        
        moving_cars = sum(1 for car in cars if car.waiting_time == 0)
        return moving_cars / len(cars)

    def step(self):
        """Execute one step of the model."""
        self.datacollector.collect(self)
        self.schedule.step()