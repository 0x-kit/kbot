# kbot/core/movement_manager.py
import time
import random
from typing import Dict
from core.input_controller import InputController
from core.window_manager import WindowManager
from utils.logger import BotLogger


class MovementManager:
    """
    Handles intelligent movement by executing a deterministic, radial-click pattern
    to explore the area and escape stuck situations reliably.
    """

    def __init__(
        self,
        input_controller: InputController,
        window_manager: WindowManager,
        logger: BotLogger,
    ):
        self.input_controller = input_controller
        self.window_manager = window_manager
        self.logger = logger

        # Nueva configuración para el patrón de exploración radial
        self.movement_config = {
            "base_radius": 250,  # Distancia base desde el centro para los clics (en píxeles).
            "scatter_radius": 40,  # Radio de dispersión aleatoria alrededor del punto base.
            "clicks_per_direction": 3,  # Número de clics a realizar por cada punto cardinal.
            "delay_between_clicks": 0.7,  # Pausa entre cada clic en la secuencia.
        }


# kbot/core/movement_manager.py
import time
import random
from typing import Dict
from core.input_controller import InputController
from core.window_manager import WindowManager
from utils.logger import BotLogger


class MovementManager:
    """
    Handles intelligent movement by executing a deterministic, radial-click pattern
    to explore the area and escape stuck situations reliably.
    """

    def __init__(
        self,
        input_controller: InputController,
        window_manager: WindowManager,
        logger: BotLogger,
    ):
        self.input_controller = input_controller
        self.window_manager = window_manager
        self.logger = logger

        # Nueva configuración para el patrón de exploración radial
        self.movement_config = {
            "base_radius": 250,  # Distancia base desde el centro para los clics (en píxeles).
            "scatter_radius": 40,  # Radio de dispersión aleatoria alrededor del punto base.
            "clicks_per_direction": 3,  # Número de clics a realizar por cada punto cardinal.
            "delay_between_clicks": 0.7,  # Pausa entre cada clic en la secuencia.
        }

    def execute_anti_stuck_maneuver(self, reason: str) -> bool:
        """
        NUEVA LÓGICA MEJORADA: Ejecuta un patrón de exploración radial
        seleccionando 2 PUNTOS CARDINALES ALEATORIOS y haciendo clic en ellos.
        """
        self.logger.info(
            f"Executing randomized 2-point radial anti-stuck maneuver. Reason: {reason}"
        )

        if not self.window_manager.target_window:
            self.logger.error("Cannot perform movement, no target window.")
            return False

        try:
            window_rect = self.window_manager.target_window.rect
            center_x = (window_rect[0] + window_rect[2]) // 2
            center_y = (window_rect[1] + window_rect[3]) // 2

            # Define el pool completo de direcciones cardinales.
            all_directions: Dict[str, tuple[int, int]] = {
                "North": (0, -1),
                "East": (1, 0),
                "South": (0, 1),
                "West": (-1, 0),
            }

            # --- CAMBIO CLAVE: Seleccionar 2 direcciones al azar sin repetición ---
            direction_names_to_try = random.sample(list(all_directions.keys()), 2)
            self.logger.info(
                f"Randomly selected directions: {direction_names_to_try[0]} & {direction_names_to_try[1]}"
            )

            # Construimos un diccionario solo con las direcciones elegidas.
            directions_to_execute = {
                name: all_directions[name] for name in direction_names_to_try
            }
            # --------------------------------------------------------------------

            # Itera a través de las 2 direcciones seleccionadas.
            for direction_name, (dir_x, dir_y) in directions_to_execute.items():
                self.logger.debug(f"--- Maneuver: Targeting {direction_name} ---")

                # Calcula el punto de clic principal para esta dirección.
                base_click_x = center_x + int(
                    dir_x * self.movement_config["base_radius"]
                )
                base_click_y = center_y + int(
                    dir_y * self.movement_config["base_radius"]
                )

                # Realiza el número configurado de clics en esa dirección.
                for i in range(self.movement_config["clicks_per_direction"]):
                    # Añade una dispersión aleatoria para que los clics no sean idénticos.
                    scatter_x = random.randint(
                        -self.movement_config["scatter_radius"],
                        self.movement_config["scatter_radius"],
                    )
                    scatter_y = random.randint(
                        -self.movement_config["scatter_radius"],
                        self.movement_config["scatter_radius"],
                    )

                    final_click_x = base_click_x + scatter_x
                    final_click_y = base_click_y + scatter_y

                    # Asegura que el clic final esté dentro de los límites de la ventana.
                    final_click_x = max(
                        window_rect[0] + 20, min(window_rect[2] - 20, final_click_x)
                    )
                    final_click_y = max(
                        window_rect[1] + 20, min(window_rect[3] - 20, final_click_y)
                    )

                    self.logger.debug(
                        f"Click #{i+1} for {direction_name} at screen ({final_click_x}, {final_click_y})"
                    )
                    self.input_controller.click_at(final_click_x, final_click_y, "left")

                    # Pausa para que el personaje reaccione al clic.
                    time.sleep(self.movement_config["delay_between_clicks"])

            self.logger.info("Randomized 2-point maneuver completed.")
            return True

        except Exception as e:
            self.logger.error(f"Randomized 2-point maneuver failed: {e}")
            return False
