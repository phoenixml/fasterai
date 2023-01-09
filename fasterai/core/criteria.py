# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/00b_core.criteria.ipynb.

# %% auto 0
__all__ = ['random', 'large_final', 'squared_final', 'small_final', 'large_init', 'small_init', 'large_init_large_final',
           'small_init_small_final', 'magnitude_increase', 'movement', 'updating_magnitude_increase',
           'updating_movement', 'movmag', 'updating_movmag', 'criterias', 'Criteria', 'available_criterias',
           'grad_crit']

# %% ../../nbs/00b_core.criteria.ipynb 2
import torch
import torch.nn as nn
import torch.nn.functional as F
from fastcore.basics import *
from fastcore.imports import *
from .granularity import *

# %% ../../nbs/00b_core.criteria.ipynb 6
class Criteria():
    def __init__(self, f, needs_init=False, needs_update=False, output_f=None, return_init=False):
        store_attr()
        assert (needs_init and needs_update)==False, "The init values will be overwritten by the updating ones."
        self.min_value=None
        
    def __call__(self, m):
        if self.needs_update and hasattr(m, '_old_weights') == False:
            m.register_buffer("_old_weights", m._init_weights.clone()) # If the previous value of weights is not known, take the initial value

        wf = self.f(m.weight)
        if self.needs_init: wi = self.f(m._init_weights)
        if self.needs_update: wi = self.f(m._old_weights)

        if hasattr(m, '_mask') == False: m.register_buffer("_mask", torch.ones_like(wf)) # Put the mask into a buffer

        if self.output_f: output = self.output_f(wf, wi)
        elif self.return_init: output = wi
        else: output = wf
        return output
    
    def granularize(self, m, scores, g): # Put the scores into granularities
        if g in granularities[m.__class__.__name__]:
            dim = granularities[m.__class__.__name__][g]
            scores = scores[None].mean(dim=dim, keepdim=True).squeeze(0)
        else: raise NameError('Invalid Granularity')
        return scores
    
    def get_scores(self, m, g, rescale=False, min_value=None):  
        if rescale: scores = self._rescale(self(m), min_value).mul_(m._mask)
        scores = self.granularize(m, self(m), g)
        return scores
    
    def _rescale(self, w, min_value): # Rescale scores to be >0, thus avoiding not pruning previously pruned weight (with a value of 0)
        self.min_value = min_value if min_value else w.min()
        output =  w + self.min_value.abs() + torch.finfo(torch.float32).eps
        return output
    
    def update_weights(self, m):
        if self.needs_update: 
            m._old_weights = m.weight.data.clone() # The current value becomes the old one for the next iteration

# %% ../../nbs/00b_core.criteria.ipynb 9
random = Criteria(torch.randn_like)

# %% ../../nbs/00b_core.criteria.ipynb 15
large_final = Criteria(torch.abs)

# %% ../../nbs/00b_core.criteria.ipynb 18
squared_final = Criteria(torch.square)

# %% ../../nbs/00b_core.criteria.ipynb 21
small_final = Criteria(compose(torch.abs, torch.neg))

# %% ../../nbs/00b_core.criteria.ipynb 24
large_init = Criteria(torch.abs, needs_init=True, return_init=True)

# %% ../../nbs/00b_core.criteria.ipynb 27
small_init = Criteria(compose(torch.abs, torch.neg), needs_init=True, return_init=True)

# %% ../../nbs/00b_core.criteria.ipynb 30
large_init_large_final = Criteria(torch.abs, needs_init=True, output_f=torch.min)

# %% ../../nbs/00b_core.criteria.ipynb 33
small_init_small_final = Criteria(torch.abs, needs_init=True, output_f=lambda x,y: torch.neg(torch.max(x,y)))

# %% ../../nbs/00b_core.criteria.ipynb 36
magnitude_increase = Criteria(torch.abs, needs_init=True, output_f= torch.sub)

# %% ../../nbs/00b_core.criteria.ipynb 39
movement = Criteria(noop, needs_init=True, output_f= lambda x,y: torch.abs(torch.sub(x,y)))

# %% ../../nbs/00b_core.criteria.ipynb 44
updating_magnitude_increase = Criteria(torch.abs, needs_update=True, output_f= lambda x,y: torch.sub(x,y))

# %% ../../nbs/00b_core.criteria.ipynb 47
updating_movement = Criteria(noop, needs_update=True, output_f= lambda x,y: torch.abs(torch.sub(x,y)))

# %% ../../nbs/00b_core.criteria.ipynb 50
movmag = Criteria(noop, needs_init=True, output_f=lambda x,y: torch.abs(torch.mul(x, torch.sub(x,y))))

# %% ../../nbs/00b_core.criteria.ipynb 53
updating_movmag = Criteria(noop, needs_update=True, output_f=lambda x,y: torch.abs(torch.mul(x, torch.sub(x,y))))

# %% ../../nbs/00b_core.criteria.ipynb 55
criterias = ('random', 'large_final', 'small_final', 'squared_final', 'small_init', 'small_final', 'large_init_large_final', 'small_init_small_final', 'magnitude_increase', 'movement', 'updating_magnitude_increase', 'updating_movement', 'updating_movmag')
def available_criterias():
    print(criterias)

# %% ../../nbs/00b_core.criteria.ipynb 76
def grad_crit(m, g):
    if g in granularities[m.__class__.__name__]: 
        dim = granularities[m.__class__.__name__][g]
        if m.weight.grad is not None:
            return (m.weight*m.weight.grad)[None].pow(2).mean(dim=dim, keepdim=True).squeeze(0)
        else: 
            return m.weight[None].pow(2).mean(dim=dim, keepdim=True).squeeze(0)
    else: raise NameError('Invalid Granularity') 
