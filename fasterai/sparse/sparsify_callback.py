# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_sparsify_callback.ipynb (unless otherwise specified).

__all__ = ['SparsifyCallback']

# Cell
from fastai.vision.all import *
from fastai.callback.all import *
from .sparsifier import *
from .criteria import *

import torch
import torch.nn as nn
import torch.nn.functional as F

# Cell
class SparsifyCallback(Callback):

    def __init__(self, end_sparsity, granularity, method, criteria, sched_func, start_sparsity=0, start_epoch=0, end_epoch=None, lth=False, rewind_epoch=0, reset_end=False, model=None, round_to=None, layer_type=nn.Conv2d):
        store_attr()
        self.end_sparsity, self.current_sparsity, self.previous_sparsity = map(listify, [self.end_sparsity, self.start_sparsity, self.start_sparsity])

        assert self.start_epoch>=self.rewind_epoch, 'You must rewind to an epoch before the start of the pruning process'

    def before_fit(self):
        print(f'Pruning of {self.granularity} until a sparsity of {self.end_sparsity}%')
        self.end_epoch = self.n_epoch if self.end_epoch is None else self.end_epoch
        assert self.end_epoch <= self.n_epoch, 'Your end_epoch must be smaller than total number of epoch'

        model = self.learn.model if self.model is None else self.model # Pass a model if you don't want the whole model to be pruned
        self.sparsifier = Sparsifier(model, self.granularity, self.method, self.criteria, self.layer_type)

        self.n_batches = math.floor(len(self.learn.dls.dataset)/self.learn.dls.bs)
        self.total_iters = self.end_epoch * self.n_batches
        self.start_iter = self.start_epoch * self.n_batches

    def before_epoch(self):
        if self.epoch == self.rewind_epoch:
            print(f'Saving Weights at epoch {self.epoch}')
            self.sparsifier._save_weights()

    def before_batch(self):
        if self.epoch>=self.start_epoch:
            if self.epoch < self.end_epoch: self._set_sparsity()
            self.sparsifier.prune_model(self.current_sparsity, self.round_to)

    def after_step(self):
        if self.epoch>=self.start_epoch:
            if self.lth and self.current_sparsity!=self.previous_sparsity: # If sparsity has changed, the network has been pruned
                        print(f'Resetting Weights to their epoch {self.rewind_epoch} values')
                        self.sparsifier._reset_weights()

            self.previous_sparsity = self.current_sparsity
            self.sparsifier._apply_masks()

    def after_epoch(self):
        sparsity_str = [float(f"%0.2f"%sp) for sp in self.current_sparsity]
        print(f'Sparsity at the end of epoch {self.epoch}: {sparsity_str}%')

    def after_fit(self):
        print(f'Final Sparsity: {self.current_sparsity:}%')
        if self.reset_end:
            self.sparsifier._reset_weights()
        self.sparsifier._clean_buffers() # Remove buffers at the end of training
        self.sparsifier.print_sparsity()

    def _set_sparsity(self):
        self.current_sparsity = [self.sched_func(start=self.start_sparsity, end=end_sp, pos=(self.train_iter-self.start_iter)/(self.total_iters-self.start_iter)) for end_sp in self.end_sparsity]