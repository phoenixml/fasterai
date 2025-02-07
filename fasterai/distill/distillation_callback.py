# AUTOGENERATED! DO NOT EDIT! File to edit: ../../nbs/04_distill.knowledge_distillation.ipynb.

# %% auto 0
__all__ = ['KnowledgeDistillationCallback', 'get_model_layers', 'get_module_by_name', 'SoftTarget', 'Logits', 'Mutual',
           'Attention', 'ActivationBoundaries', 'FitNet', 'Similarity']

# %% ../../nbs/04_distill.knowledge_distillation.ipynb 18
from fastai.vision.all import *

import torch
import torch.nn as nn
import torch.nn.functional as F

from functools import reduce
from typing import Union

# %% ../../nbs/04_distill.knowledge_distillation.ipynb 20
class KnowledgeDistillationCallback(Callback):
    def __init__(self, teacher, loss, activations_student=None, activations_teacher=None, weight=0.5):
        self.stored_activation_student, self.stored_activation_teacher  = {}, {}
        store_attr()
        if self.activations_student is not None:
            self.activations_student, self.activations_teacher = listify(activations_student), listify(activations_teacher)
        
    def before_fit(self):
        if self.activations_student and self.activations_teacher : self.register_hooks()
        self.teacher.eval()

    def after_loss(self):
        teacher_pred = self.teacher(self.x)
        new_loss = self.loss(pred=self.pred, teacher_pred=teacher_pred, fm_s=self.stored_activation_student, fm_t=self.stored_activation_teacher)
        self.learn.loss_grad = torch.lerp(self.learn.loss_grad, new_loss, self.weight)
        self.learn.loss = self.learn.loss_grad.clone()
    
    def register_hooks(self):
        self.handles_st, self.handles_t = {}, {}
        for name_st, name_t in zip(self.activations_student, self.activations_teacher):
            self.handles_st[name_st] = get_module_by_name(self.learn, name_st).register_forward_hook(self.get_activation(self.stored_activation_student, name_st))
            self.handles_t[name_t] = get_module_by_name(self.teacher, name_t).register_forward_hook(self.get_activation(self.stored_activation_teacher, name_t))
        
    def get_activation(self, activation, name):
        def hook(model, input, output):
            activation[name] = output
        return hook
    
    def find_hook(self, m):
        save = []
        module_name = type(m).__name__
        for k, v in m._forward_hooks.items():
            save.append((module_name, k, v.__name__))
        return save
    
    def remove_hooks(self, handles):
        for k, v in handles.items():
            handles[k].remove()
    
    def after_fit(self):
        if self.activations_student and self.activations_teacher:
            self.remove_hooks(self.handles_t)
            self.remove_hooks(self.handles_st)

# %% ../../nbs/04_distill.knowledge_distillation.ipynb 21
def get_model_layers(model, getLayerRepr=False):
    layers = OrderedDict() if getLayerRepr else []
    def get_layers(net, prefix=[]):
        if hasattr(net, "_modules"):
            for name, layer in net._modules.items():
                if layer is None:
                    continue
                if getLayerRepr:
                    layers[".".join(prefix+[name])] = layer.__repr__()
                else:
                    layers.append(".".join(prefix + [name]))
                get_layers(layer, prefix=prefix+[name])

    get_layers(model)
    return layers


def get_module_by_name(module: Union[torch.Tensor, nn.Module],
                       access_string: str):

    names = access_string.split(sep='.')
    return reduce(getattr, names, module)

# %% ../../nbs/04_distill.knowledge_distillation.ipynb 23
def SoftTarget(pred, teacher_pred, T=5, **kwargs):
    return nn.KLDivLoss(reduction='batchmean')(F.log_softmax(pred/T, dim=1), F.softmax(teacher_pred/T, dim=1)) * (T*T)

def Logits(pred, teacher_pred, **kwargs):
    return F.mse_loss(pred, teacher_pred)

def Mutual(pred, teacher_pred, **kwargs):
    return nn.KLDivLoss(reduction='batchmean')(F.log_softmax(pred, dim=1), F.softmax(teacher_pred, dim=1))


def Attention(fm_s, fm_t, p=2, **kwargs):
    return sum([F.mse_loss(F.normalize(fm_s[name_st].pow(p).mean(1),dim=(1,2)), F.normalize(fm_t[name_t].pow(p).mean(1),dim=(1,2))) for name_st, name_t in zip(fm_s, fm_t)])

def ActivationBoundaries(fm_s, fm_t, m=2, **kwargs):
    return sum([((fm_s[name_st] + m).pow(2) * ((fm_s[name_st] > -m) & (fm_t[name_t] <= 0)).float() + (fm_s[name_st] - m).pow(2) * ((fm_s[name_st] <= m) & (fm_t[name_t] > 0)).float()).mean() for name_st, name_t in zip(fm_s, fm_t)])

def FitNet(fm_s, fm_t, **kwargs):
    return sum([F.mse_loss(fm_s[name_st],fm_t[name_t]) for name_st, name_t in zip(fm_s, fm_t)])

def Similarity(fm_s, fm_t, pred, p=2, **kwargs):
    return sum([F.mse_loss(F.normalize(fm_s[name_st].view(fm_s[name_st].size(0), -1) @ fm_s[name_st].view(fm_s[name_st].size(0), -1).t(), p=p, dim=1), F.normalize(fm_t[name_t].view(fm_t[name_t].size(0), -1) @ fm_t[name_t].view(fm_t[name_t].size(0), -1).t(), p=p, dim=1)) for name_st, name_t in zip(fm_s, fm_t)])
