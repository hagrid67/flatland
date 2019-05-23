from flatland.envs.generators import rail_from_manual_specifications_generator
from flatland.envs.rail_env import RailEnv
from flatland.envs.observations import TreeObsForRailEnv
from flatland.utils.rendertools import RenderTool

# Example generate a rail given a manual specification,
# a map of tuples (cell_type, rotation)
specs = [[(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)],
         [(0, 0), (0, 0), (0, 0), (0, 0), (7, 0), (0, 0)],
         [(7, 270), (1, 90), (1, 90), (1, 90), (2, 90), (7, 90)],
         [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]]

# CURVED RAIL + DEAD-ENDS TEST
# specs = [[(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)],
#          [(7, 270), (1, 90), (1, 90), (8, 90), (0, 0), (0, 0)],
#          [(0, 0),   (7, 270),(1, 90), (8, 180), (0, 00), (0, 0)],
#          [(0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)]]

env = RailEnv(width=6,
              height=4,
              rail_generator=rail_from_manual_specifications_generator(specs),
              number_of_agents=1,
              obs_builder_object=TreeObsForRailEnv(max_depth=2))

env.reset()

env_renderer = RenderTool(env, gl="QT")
env_renderer.renderEnv(show=True)

input("Press Enter to continue...")
