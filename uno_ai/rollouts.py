"""
Gather trajectories from agents on a game.
"""

import numpy as np
import torch

from .actions import ACTION_VECTOR_SIZE
from .game import OBS_VECTOR_SIZE


class Rollout:
    """
    A single episode from the perspective of a single
    agent.

    Stores the observation for every timestamp, the output
    of the agent at every timestamp, and the reward of the
    final episode from the agent's perspective.
    """

    def __init__(self, observations, outputs, reward):
        self.observations = observations
        self.outputs = outputs
        self.reward = reward

    @property
    def num_steps(self):
        return len(self.observations)

    @classmethod
    def empty(cls):
        return cls([], [], 0.0)

    @classmethod
    def rollout(cls, game, agents):
        rollouts = [cls.empty() for _ in agents]
        states = [None] * len(agents)
        while not game.winner():
            for i, agent in enumerate(agents):
                res = agent.step(game, i, states[i])
                states[i] = res['state']
                r = rollouts[i]
                r.observations.append(game.obs(i))
                r.outputs.append(res)
        for i, r in enumerate(rollouts):
            if i == game.winner():
                r.reward = 1.0
        return rollouts


class RolloutBatch:
    """
    A packed batch of rollouts.

    Specifically, stores the following:
      observations: a (seq_len, batch, OBS_VECTOR_SIZE)
        Tensor of observations.
      actions: a (seq_len, batch, ACTION_VECTOR_SIZE)
        Tensor of one-hot vectors indicating which action
        was taken at every timestep.
      masks: a (seq_len, batch, ACTION_VECTOR_SIZE) Tensor
        of values where a 1 indicates that an action was
        allowed, and a 0 indicates otherwise.
    """

    def __init__(self, rollouts, device):
        seq_len = max(r.num_steps for r in rollouts)
        observations = []
        actions = []
        masks = []
        for r in rollouts:
            obs_seq = r.observations.copy()
            act_seq = [_one_hot_action(o['action']) for o in r.outputs]
            mask_seq = [_option_mask(o['options']) for o in r.outputs]
            for _ in range(seq_len - r.num_steps):
                obs_seq.append([0] * OBS_VECTOR_SIZE)
                act_seq.append(_one_hot_action(0))
                mask_seq.append(_one_hot_action(0))
            observations.append(obs_seq)
            actions.append(act_seq)
            masks.append(mask_seq)
        self.observations = torch.from_numpy(np.transpose(
            np.array(observations), axes=[1, 0, 2])).to(device)
        self.actions = torch.from_numpy(np.transpose(np.array(actions), axes=[1, 0, 2])).to(device)
        self.masks = torch.from_numpy(np.transpose(np.array(masks), axes=[1, 0, 2])).to(device)


def _one_hot_action(action):
    res = [0.0] * ACTION_VECTOR_SIZE
    res[action.index()] = 1.0
    return res


def _option_mask(options):
    res = [0.0] * ACTION_VECTOR_SIZE
    for a in options:
        res[a.index()] = 1.0
    return res