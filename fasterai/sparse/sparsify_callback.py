# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_sparsify_callback.ipynb (unless otherwise specified).

__all__ = ['SparsifyCallback', 'SparsifyCallback']

# Cell
from fastai.vision.all import *
from fastai.callback.all import *
from .sparsifier import *
from .criteria import *
from .schedule import *

import torch
import torch.nn as nn
import torch.nn.functional as F

# Cell
class SparsifyCallback(Callback):
    def __init__(self, sparsity, granularity, context, criteria, schedule, lth=False, rewind_epoch=0, reset_end=False, save_tickets=False, model=None, round_to=None, layer_type=nn.Conv2d):
        store_attr()
        self.sparsity = listify(self.sparsity)

    def before_fit(self):
        print(f'Pruning of {self.granularity} until a sparsity of {self.sparsity}%')
        assert self.schedule.start_pct*self.n_epoch>=self.rewind_epoch, 'You must rewind to an epoch before the start of the pruning process'
        model = self.model if self.model else self.learn.model
        self.sparsifier = Sparsifier(model, self.granularity, self.context, self.criteria, self.layer_type)

    def before_epoch(self):
        if self.epoch == self.rewind_epoch:
            print(f'Saving Weights at epoch {self.epoch}')
            self.sparsifier._save_weights()

    def before_batch(self):
        self.current_sparsity = self.schedule(self.sparsity, round(self.pct_train,3))
        if self.schedule.pruned and self.training:
            if self.lth and self.save_tickets:
                print('Saving Intermediate Ticket')
                self.sparsifier.save_model(f'winning_ticket_{self.previous_sparsity[0]:.2f}.pth', self.learn.model)
            self.sparsifier.prune_model(self.current_sparsity, self.round_to)

    def after_step(self):
        if self.lth and self.schedule.pruned:
            print(f'Resetting Weights to their epoch {self.rewind_epoch} values')
            self.sparsifier._reset_weights(self.learn.model)
        self.schedule.after_pruned()
        self.sparsifier._apply_masks()

    def after_epoch(self):
        sparsity_str = [float(f"%0.2f"%sp) for sp in self.current_sparsity]
        print(f'Sparsity at the end of epoch {self.epoch}: {sparsity_str}%')

    def after_fit(self):
        if self.save_tickets:
            print('Saving Final Ticket')
            self.sparsifier.save_model(f'winning_ticket_{self.previous_sparsity[0]:.2f}.pth', self.learn.model)
        print(f'Final Sparsity: {self.schedule.current_sparsity:}%')
        if self.reset_end: self.sparsifier._reset_weights()
        self.sparsifier._clean_buffers()
        self.schedule.reset()
        self.sparsifier.print_sparsity()

# Cell
from fastai.vision.all import *
from fastai.callback.all import *
from .sparsifier import *
from .criteria import *
from .schedule import *

import torch
import torch.nn as nn
import torch.nn.functional as F

# Cell
class SparsifyCallback(Callback):
    def __init__(self, sparsity, granularity, context, criteria, schedule, lth=False, rewind_epoch=0, reset_end=False, save_tickets=False, model=None, round_to=None, layer_type=nn.Conv2d):
        store_attr()
        self.sparsity = listify(self.sparsity)

    def before_fit(self):
        print(f'Pruning of {self.granularity} until a sparsity of {self.sparsity}%')
        assert self.schedule.start_pct*self.n_epoch>=self.rewind_epoch, 'You must rewind to an epoch before the start of the pruning process'
        model = self.model if self.model else self.learn.model
        self.sparsifier = Sparsifier(model, self.granularity, self.context, self.criteria, self.layer_type)

    def before_epoch(self):
        if self.epoch == self.rewind_epoch:
            print(f'Saving Weights at epoch {self.epoch}')
            self.sparsifier._save_weights()

    def before_batch(self):
        self.current_sparsity = self.schedule(self.sparsity, round(self.pct_train,3))
        if self.schedule.pruned and self.training:
            if self.lth and self.save_tickets:
                print('Saving Intermediate Ticket')
                self.sparsifier.save_model(f'winning_ticket_{self.previous_sparsity[0]:.2f}.pth', self.learn.model)
            self.sparsifier.prune_model(self.current_sparsity, self.round_to)

    def after_step(self):
        if self.lth and self.schedule.pruned:
            print(f'Resetting Weights to their epoch {self.rewind_epoch} values')
            self.sparsifier._reset_weights(self.learn.model)
        self.schedule.after_pruned()
        self.sparsifier._apply_masks()

    def after_epoch(self):
        sparsity_str = [float(f"%0.2f"%sp) for sp in self.current_sparsity]
        print(f'Sparsity at the end of epoch {self.epoch}: {sparsity_str}%')

    def after_fit(self):
        if self.save_tickets:
            print('Saving Final Ticket')
            self.sparsifier.save_model(f'winning_ticket_{self.previous_sparsity[0]:.2f}.pth', self.learn.model)
        print(f'Final Sparsity: {self.schedule.current_sparsity:}%')
        if self.reset_end: self.sparsifier._reset_weights()
        self.sparsifier._clean_buffers()
        self.schedule.reset()
        self.sparsifier.print_sparsity()