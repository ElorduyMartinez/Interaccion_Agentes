from mesa import Agent, Model
from mesa.space import MultiGrid
from mesa.datacollection import DataCollector

class SmartTrafficLight(Agent):
    def __init__(self, model, position, direction="NS"):
        super().__init__(model)
        self.state = "yellow"  # Default state when no vehicles nearby
        self.timer = 2
        self.pos = position
        self.direction = direction
        self.vehicle_queue = []  # Store incoming vehicle arrival times
        self.last_vehicle_detected = 0  # Time since last vehicle detection

    def get_monitored_positions(self):
        x, y = self.pos
        if self.direction == "NS":
            return [(x, y - i) for i in range(1, 6)]  # Check below light for NS
        elif self.direction == "EW":
            return [(x - i, y) for i in range(1, 6)]  # Check left of light for EW
        return []

    def detect_vehicles(self):
        detected = False
        for pos in self.get_monitored_positions():
            if not self.model.grid.out_of_bounds(pos):
                cell_contents = self.model.grid.get_cell_list_contents(pos)
                for agent in cell_contents:
                    if isinstance(agent, Vehicle):
                        detected = True
                        # Calculate estimated arrival time
                        distance = abs(pos[0] - self.pos[0]) + abs(pos[1] - self.pos[1])
                        arrival_time = self.model.steps + distance
                        self.vehicle_queue.append(arrival_time)
                        agent.send_arrival_time(arrival_time, self)
        if detected:
            self.last_vehicle_detected = self.model.steps
            self.model.request_green_light(self)
        elif self.model.steps - self.last_vehicle_detected > 5:
            # If no vehicles detected for 5 steps, return to yellow
            self.state = "yellow"
            self.timer = 2

    def step(self):
        self.detect_vehicles()
        self.timer -= 1
        if self.timer <= 0:
            if self.state == "green":
                self.state = "yellow"
                self.timer = 2
            elif self.state == "yellow" and self.vehicle_queue:
                self.state = "red"
                self.timer = 5
            elif self.state == "red":
                self.state = "yellow"
                self.timer = 2


class Vehicle(Agent):
    def __init__(self, model, position, direction, lane=1):
        super().__init__(model)
        self.pos = position
        self.direction = direction
        self.approaching = True
        self.lane = lane
        self.arrival_time = None
        self.target_light = None
        # Set color based on direction
        directions = {
            (0, 1): "#0000FF",   # North (blue)
            (0, -1): "#FF0000",  # South (red)
            (1, 0): "#00FF00",   # East (green)
            (-1, 0): "#800080"   # West (purple)
        }
        self.color = directions.get(direction, "#000000")

    def send_arrival_time(self, time, light):
        """Send estimated arrival time to traffic light"""
        self.arrival_time = time
        self.target_light = light

    def step(self):
        if not self.approaching or self.pos is None:
            return
        x, y = self.pos
        dx, dy = self.direction
        new_position = (x + dx, y + dy)
        if not self.model.grid.out_of_bounds(new_position) and self.can_move(new_position):
            self.model.grid.move_agent(self, new_position)

    def can_move(self, new_position):
        if self.pos is None or self.model.grid.out_of_bounds(new_position):
            return False
        # Check for other vehicles
        cellmates = self.model.grid.get_cell_list_contents(new_position)
        if any(isinstance(agent, Vehicle) for agent in cellmates):
            return False
        # Check traffic light ahead
        traffic_light = self.get_traffic_light_ahead()
        if traffic_light:
            x, y = self.pos
            light_x, light_y = traffic_light.pos
            distance = abs(x - light_x) + abs(y - light_y)
            if distance <= 2 and traffic_light.state in ["red", "yellow"]:
                return False
        return True

    def get_traffic_light_ahead(self):
        if self.pos is None:
            return None
        x, y = self.pos
        dx, dy = self.direction
        for i in range(1, 4):
            next_pos = (x + dx * i, y + dy * i)
            if not self.model.grid.out_of_bounds(next_pos):
                cell_contents = self.model.grid.get_cell_list_contents(next_pos)
                for agent in cell_contents:
                    if isinstance(agent, SmartTrafficLight):
                        if (dy != 0 and agent.direction == "NS") or \
                           (dx != 0 and agent.direction == "EW"):
                            return agent
        return None


class IntersectionModel(Model):
    def __init__(self, width=20, height=20, spawn_probability=0.1):
        super().__init__()
        self.grid = MultiGrid(width, height, torus=False)
        self.width = width
        self.height = height
        self.spawn_probability = spawn_probability
        self.steps = 0  # Step counter
        self.center_x = width // 2
        self.center_y = height // 2
        self.traffic_lights = []
        self.datacollector = DataCollector(
            model_reporters={
                "Green_Lights": lambda m: len([a for a in m.agents if isinstance(a, SmartTrafficLight) and a.state == "green"])
            },
            agent_reporters={
                "State": lambda a: getattr(a, "state", None)
            }
        )
        self._create_traffic_lights()

    def _create_traffic_lights(self):
        # Create four traffic lights for each direction, two for each approach

        # North-South traffic lights
        # Northbound (two lanes)
        pos_n2 = (self.center_x - 1, self.center_y + 2)
        light_n2 = SmartTrafficLight(self, pos_n2, "NS")
        self.grid.place_agent(light_n2, pos_n2)
        self.traffic_lights.append(light_n2)

        # Southbound (two lanes)
        pos_s1 = (self.center_x + 1, self.center_y - 2)
        light_s1 = SmartTrafficLight(self, pos_s1, "NS")
        self.grid.place_agent(light_s1, pos_s1)
        self.traffic_lights.append(light_s1)
        

        # East-West traffic lights
        # Eastbound (two lanes)
        pos_e1 = (self.center_x + 2, self.center_y + 1)
        light_e1 = SmartTrafficLight(self, pos_e1, "EW")
        self.grid.place_agent(light_e1, pos_e1)
        self.traffic_lights.append(light_e1)
        
       

        # Westbound (two lanes)
    
        
        pos_w2 = (self.center_x - 2, self.center_y - 1)
        light_w2 = SmartTrafficLight(self, pos_w2, "EW")
        self.grid.place_agent(light_w2, pos_w2)
        self.traffic_lights.append(light_w2)

    def request_green_light(self, requesting_light):
        """Handle green light requests from traffic lights"""
        earliest_arrival = float('inf')
        light_to_turn_green = None
        for light in self.traffic_lights:
            if light.vehicle_queue:
                min_arrival = min(light.vehicle_queue)
                if min_arrival < earliest_arrival:
                    earliest_arrival = min_arrival
                    light_to_turn_green = light
        if light_to_turn_green:
            for light in self.traffic_lights:
                if light == light_to_turn_green:
                    light.state = "green"
                    light.timer = 5
                else:
                    light.state = "red"
                    light.timer = 5

    def spawn_vehicle(self, direction, start_pos):
        """Spawn a new vehicle in a single designated lane for each direction."""
        if self.random.random() < self.spawn_probability:
            if not self.grid.get_cell_list_contents(start_pos):  # Ensure cell is empty
                vehicle = Vehicle(self, start_pos, direction)
                self.grid.place_agent(vehicle, start_pos)

    def step(self):
        self.steps += 1
        # Spawn vehicles in offset lanes to avoid collision
        self.spawn_vehicle((0, 1), (self.center_x + 1, 0))  # Northbound right lane
        self.spawn_vehicle((0, -1), (self.center_x - 1, self.height - 1))  # Southbound left lane
        self.spawn_vehicle((1, 0), (0, self.center_y - 1))  # Eastbound bottom lane
        self.spawn_vehicle((-1, 0), (self.width - 1, self.center_y + 1))  # Westbound top lane
       
        for agent in self.agents:
            if isinstance(agent, SmartTrafficLight):
                agent.step()
        for agent in self.agents:
            if isinstance(agent, Vehicle):
                agent.step()
        self.datacollector.collect(self)
