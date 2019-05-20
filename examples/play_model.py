import random
import time
from collections import deque

import numpy as np
import torch

from flatland.baselines.dueling_double_dqn import Agent
from flatland.envs.generators import complex_rail_generator
from flatland.envs.rail_env import RailEnv
from flatland.utils.rendertools import RenderTool


class Player(object):
    def __init__(self, env):
        self.env = env
        self.handle = env.get_agent_handles()

        self.state_size = 105
        self.action_size = 4
        self.n_trials = 9999
        self.eps = 1.
        self.eps_end = 0.005
        self.eps_decay = 0.998
        self.action_dict = dict()
        self.scores_window = deque(maxlen=100)
        self.done_window = deque(maxlen=100)
        self.scores = []
        self.dones_list = []
        self.action_prob = [0] * 4
        self.agent = Agent(self.state_size, self.action_size, "FC", 0)
        # self.agent.qnetwork_local.load_state_dict(torch.load('../flatland/baselines/Nets/avoid_checkpoint9900.pth'))
        self.agent.qnetwork_local.load_state_dict(torch.load(
            '../flatland/flatland/baselines/Nets/avoid_checkpoint15000.pth'))

        self.iFrame = 0
        self.tStart = time.time()

        # Reset environment
        # self.obs = self.env.reset()
        self.env.obs_builder.reset()
        self.obs = self.env._get_observations()
        for envAgent in range(self.env.get_num_agents()):
            norm = max(1, max_lt(self.obs[envAgent], np.inf))
            self.obs[envAgent] = np.clip(np.array(self.obs[envAgent]) / norm, -1, 1)

        # env.obs_builder.util_print_obs_subtree(tree=obs[0], num_elements_per_node=5)

        self.score = 0
        self.env_done = 0

    def step(self):
        env = self.env

        # Pass the (stored) observation to the agent network and retrieve the action
        for handle in env.get_agent_handles():
            action = self.agent.act(np.array(self.obs[handle]), eps=self.eps)
            self.action_prob[action] += 1
            self.action_dict.update({handle: action})

        # Environment step - pass the agent actions to the environment,
        # retrieve the response - observations, rewards, dones
        next_obs, all_rewards, done, _ = self.env.step(self.action_dict)

        for handle in env.get_agent_handles():
            norm = max(1, max_lt(next_obs[handle], np.inf))
            next_obs[handle] = np.clip(np.array(next_obs[handle]) / norm, -1, 1)

        # Update replay buffer and train agent
        for handle in self.env.get_agent_handles():
            self.agent.step(self.obs[handle], self.action_dict[handle],
                            all_rewards[handle], next_obs[handle], done[handle],
                            train=False)
            self.score += all_rewards[handle]

        self.iFrame += 1

        self.obs = next_obs.copy()
        if done['__all__']:
            self.env_done = 1


def max_lt(seq, val):
    """
    Return greatest item in seq for which item < val applies.
    None is returned if seq was empty or all items in seq were >= val.
    """

    idx = len(seq) - 1
    while idx >= 0:
        if seq[idx] < val and seq[idx] >= 0:
            return seq[idx]
        idx -= 1
    return None


def main(render=True, delay=0.0):
    random.seed(1)
    np.random.seed(1)

    # Example generate a random rail
    env = RailEnv(width=15, height=15,
                  rail_generator=complex_rail_generator(nr_start_goal=5, nr_extra=20, min_dist=12),
                  number_of_agents=5)

    if render:
        env_renderer = RenderTool(env, gl="QTSVG")
        # env_renderer = RenderTool(env, gl="QT")

    state_size = 105
    action_size = 4
    n_trials = 9999
    eps = 1.
    eps_end = 0.005
    eps_decay = 0.998
    action_dict = dict()
    scores_window = deque(maxlen=100)
    done_window = deque(maxlen=100)
    scores = []
    dones_list = []
    action_prob = [0] * 4
    agent = Agent(state_size, action_size, "FC", 0)

    # agent.qnetwork_local.load_state_dict(torch.load('../flatland/baselines/Nets/avoid_checkpoint9900.pth'))

    def max_lt(seq, val):
        """
        Return greatest item in seq for which item < val applies.
        None is returned if seq was empty or all items in seq were >= val.
        """

        idx = len(seq) - 1
        while idx >= 0:
            if seq[idx] < val and seq[idx] >= 0:
                return seq[idx]
            idx -= 1
        return None

    iFrame = 0
    tStart = time.time()
    for trials in range(1, n_trials + 1):

        # Reset environment
        obs = env.reset()
        if render:
            env_renderer.set_new_rail()

        for a in range(env.get_num_agents()):
            norm = max(1, max_lt(obs[a], np.inf))
            obs[a] = np.clip(np.array(obs[a]) / norm, -1, 1)

        # env.obs_builder.util_print_obs_subtree(tree=obs[0], num_elements_per_node=5)

        score = 0
        env_done = 0

        # Run episode
        for step in range(100):
            # if trials > 114:
            # env_renderer.renderEnv(show=True)
            # print(step)
            # Action
            for a in range(env.get_num_agents()):
                action = agent.act(np.array(obs[a]), eps=eps)
                action_prob[action] += 1
                action_dict.update({a: action})

            if render:
                env_renderer.renderEnv(show=True, frames=True, iEpisode=trials, iStep=step, action_dict=action_dict)
                if delay > 0:
                    time.sleep(delay)

            iFrame += 1

            # Environment step
            next_obs, all_rewards, done, _ = env.step(action_dict)
            for a in range(env.get_num_agents()):
                norm = max(1, max_lt(next_obs[a], np.inf))
                next_obs[a] = np.clip(np.array(next_obs[a]) / norm, -1, 1)
            # Update replay buffer and train agent
            for a in range(env.get_num_agents()):
                agent.step(obs[a], action_dict[a], all_rewards[a], next_obs[a], done[a])
                score += all_rewards[a]

            obs = next_obs.copy()
            if done['__all__']:
                env_done = 1
                break
        # Epsilon decay
        eps = max(eps_end, eps_decay * eps)  # decrease epsilon

        done_window.append(env_done)
        scores_window.append(score)  # save most recent score
        scores.append(np.mean(scores_window))
        dones_list.append((np.mean(done_window)))

        print(('\rTraining {} Agents.\tEpisode {}\tAverage Score: {:.0f}\tDones: {:.2f}%' +
               '\tEpsilon: {:.2f} \t Action Probabilities: \t {}').format(
            env.get_num_agents(),
            trials,
            np.mean(scores_window),
            100 * np.mean(done_window),
            eps, action_prob / np.sum(action_prob)),
            end=" ")
        if trials % 100 == 0:
            tNow = time.time()
            rFps = iFrame / (tNow - tStart)
            print(('\rTraining {} Agents.\tEpisode {}\tAverage Score: {:.0f}\tDones: {:.2f}%' +
                   '\tEpsilon: {:.2f} fps: {:.2f} \t Action Probabilities: \t {}').format(
                env.get_num_agents(),
                trials,
                np.mean(scores_window),
                100 * np.mean(done_window),
                eps, rFps, action_prob / np.sum(action_prob)))
            torch.save(agent.qnetwork_local.state_dict(),
                       '../flatland/baselines/Nets/avoid_checkpoint' + str(trials) + '.pth')
            action_prob = [1] * 4


if __name__ == "__main__":
    main(render=True, delay=0)
